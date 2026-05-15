"""Merch-Artikelbilder: Drive-Download, Redis-Zwischenspeicher, ETag.

Spec: docs/capabilities/merch.md Sektion 8.
"""

from __future__ import annotations

import hashlib
import logging

from flask import current_app

from backend.models.merch_v2 import MerchArticle
from backend.services.drive_storage import (
    DriveError,
    DriveNotConfiguredError,
    DriveStorageService,
)

logger = logging.getLogger(__name__)


class MerchImageService:
    """Proxy-Helfer fuer GET /merch/image/<article_id>."""

    CACHE_DATA = 'merch:img:data:'
    CACHE_MIME = 'merch:img:mime:'
    CACHE_ETAG = 'merch:img:etag:'
    CACHE_PREFIX = 'merch:img:'

    _redis_by_url: dict[str, object] = {}

    @classmethod
    def cache_key_for_article(cls, article_id: int) -> str:
        """Logischer Bucket-Schluessel (Anzeige/Debug); Redis nutzt CACHE_* Prefix."""
        return f'{cls.CACHE_PREFIX}{int(article_id)}'

    @classmethod
    def invalidate_article_cache(cls, article_id: int) -> None:
        """Nach Bild-Austausch am Artikel aufrufen."""
        r = cls._redis_conn()
        if not r:
            return
        aid = str(int(article_id))
        try:
            r.delete(
                cls.CACHE_DATA + aid,
                cls.CACHE_MIME + aid,
                cls.CACHE_ETAG + aid,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning('Merch Bild-Cache invalidate fehlgeschlagen: %s', exc)

    @classmethod
    def _redis_conn(cls):
        url = current_app.config.get('REDIS_URL')
        if not url:
            return None
        if url not in cls._redis_by_url:
            import redis

            cls._redis_by_url[url] = redis.Redis.from_url(
                url,
                decode_responses=False,
            )
        return cls._redis_by_url[url]

    @classmethod
    def _ttl_seconds(cls) -> int:
        return int(current_app.config.get('MERCH_IMAGE_CACHE_TTL_SECONDS', 86400))

    @classmethod
    def _etag_for(cls, modified_time: str | None, payload: bytes) -> str:
        seed = f'{modified_time or ""}:{len(payload)}'.encode()
        return hashlib.sha256(seed).hexdigest()

    @classmethod
    def _read_cache(cls, article_id: int) -> tuple[bytes, str, str] | None:
        r = cls._redis_conn()
        if not r:
            return None
        aid = str(int(article_id))
        try:
            data = r.get(cls.CACHE_DATA + aid)
            mime_b = r.get(cls.CACHE_MIME + aid)
            etag_b = r.get(cls.CACHE_ETAG + aid)
            if not data or not mime_b or not etag_b:
                return None
            return (
                data,
                mime_b.decode('utf-8'),
                etag_b.decode('utf-8'),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning('Merch Bild-Cache read fehlgeschlagen: %s', exc)
            return None

    @classmethod
    def _write_cache(
        cls,
        article_id: int,
        payload: bytes,
        mime: str,
        etag: str,
    ) -> None:
        r = cls._redis_conn()
        if not r:
            return
        aid = str(int(article_id))
        ttl = cls._ttl_seconds()
        try:
            pipe = r.pipeline()
            pipe.set(cls.CACHE_DATA + aid, payload, ex=ttl)
            pipe.set(cls.CACHE_MIME + aid, mime.encode('utf-8'), ex=ttl)
            pipe.set(cls.CACHE_ETAG + aid, etag.encode('utf-8'), ex=ttl)
            pipe.execute()
        except Exception as exc:  # noqa: BLE001
            logger.warning('Merch Bild-Cache write fehlgeschlagen: %s', exc)

    @classmethod
    def load_image_for_article(cls, article_id: int) -> dict:
        """Laedt Bildbytes (Redis, sonst Drive). Feature-Flag hier ausgewertet."""
        if not current_app.config.get('MERCH_V2_ENABLED'):
            return {'success': False, 'reason': 'feature_disabled'}

        article = MerchArticle.query.get(article_id)
        if not article:
            return {'success': False, 'reason': 'article_not_found'}

        fid = (article.image_drive_file_id or '').strip()
        if not fid:
            return {'success': False, 'reason': 'no_image'}

        cached = cls._read_cache(article_id)
        if cached:
            data, mime, etag = cached
            return {
                'success': True,
                'payload': data,
                'mime': mime,
                'etag': etag,
                'cache_hit': True,
            }

        try:
            payload, mime, _name, modified = (
                DriveStorageService.download_binary_by_file_id(fid)
            )
        except DriveNotConfiguredError:
            return {'success': False, 'reason': 'drive_not_configured'}
        except DriveError as exc:
            logger.info('Merch Bild Drive-Download fehlgeschlagen: %s', exc)
            return {'success': False, 'reason': 'drive_error', 'error': str(exc)}

        etag = cls._etag_for(modified, payload)
        cls._write_cache(article_id, payload, mime, etag)
        return {
            'success': True,
            'payload': payload,
            'mime': mime,
            'etag': etag,
            'cache_hit': False,
        }
