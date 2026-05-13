"""Unit-Tests fuer DriveStorageService – reine Funktionen ohne Drive-API.

Schwerpunkte: Filename-Sanitization (Capability 7.4) und SVG-Sanitization
(Capability 11.3 – Pflicht fuer Marketing-Use-Case).

Tests die einen echten Drive-Zugriff brauchen (Upload, Move, Permissions)
sind hier bewusst nicht enthalten; sie laufen manuell gegen ein Test-Drive.
"""

import pytest

from backend.services.drive_storage import (
    DriveSanitizationError,
    sanitize_drive_filename,
    sanitize_svg_bytes,
)


# ---------------------------------------------------------------------------
# Filename-Sanitization
# ---------------------------------------------------------------------------


class TestSanitizeDriveFilename:
    def test_simple_pdf(self) -> None:
        assert sanitize_drive_filename("Statuten 2024", "pdf") == "Statuten 2024.pdf"

    def test_strips_illegal_chars(self) -> None:
        assert (
            sanitize_drive_filename("Hallo / Welt: <Test>", "pdf")
            == "Hallo - Welt- -Test-.pdf"
        )

    def test_strips_backslash_and_pipe(self) -> None:
        assert sanitize_drive_filename("a\\b|c", "txt") == "a-b-c.txt"

    def test_collapses_whitespace(self) -> None:
        assert sanitize_drive_filename("  Lots   of   spaces  ", "pdf") == "Lots of spaces.pdf"

    def test_trims_trailing_dots_and_spaces(self) -> None:
        # Windows mag keine trailing dots; Drive ist tolerant, aber wir
        # halten uns an die strengere Regel.
        assert sanitize_drive_filename("Datei...", "pdf") == "Datei.pdf"

    def test_empty_title_falls_back_to_untitled(self) -> None:
        assert sanitize_drive_filename("", "pdf") == "Untitled.pdf"

    def test_only_illegal_chars(self) -> None:
        assert sanitize_drive_filename("///", "pdf") == "Untitled.pdf"

    def test_truncates_to_150_chars(self) -> None:
        title = "a" * 200
        result = sanitize_drive_filename(title, "pdf")
        # Basis-Teil ist 150 Zeichen, plus ".pdf" = 154
        assert result.endswith(".pdf")
        assert len(result.rsplit(".", 1)[0]) == 150

    def test_extension_with_leading_dot(self) -> None:
        assert sanitize_drive_filename("test", ".pdf") == "test.pdf"

    def test_no_extension_returns_basename(self) -> None:
        assert sanitize_drive_filename("Notiz", None) == "Notiz"
        assert sanitize_drive_filename("Notiz", "") == "Notiz"

    def test_control_chars_removed(self) -> None:
        # Tabs/Newlines werden zu '-' und dann durch Whitespace-Normalize gestrippt.
        assert sanitize_drive_filename("a\nb\tc", "pdf").startswith("a-")


# ---------------------------------------------------------------------------
# SVG-Sanitization
# ---------------------------------------------------------------------------


SAFE_SVG = (
    b'<?xml version="1.0" encoding="UTF-8"?>'
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
    b'<circle cx="5" cy="5" r="3" fill="#dc693c"/>'
    b"</svg>"
)


class TestSanitizeSvgBytes:
    def test_passes_safe_svg_through(self) -> None:
        out = sanitize_svg_bytes(SAFE_SVG)
        assert b"<circle" in out
        assert b"<script" not in out

    def test_strips_script_tag(self) -> None:
        svg = (
            b'<svg xmlns="http://www.w3.org/2000/svg">'
            b'<script>alert(1)</script>'
            b'<circle cx="5" cy="5" r="3"/></svg>'
        )
        out = sanitize_svg_bytes(svg)
        assert b"<script" not in out
        assert b"alert" not in out
        assert b"<circle" in out

    def test_strips_onclick_handler(self) -> None:
        svg = (
            b'<svg xmlns="http://www.w3.org/2000/svg">'
            b'<rect width="10" height="10" onclick="alert(1)" fill="red"/>'
            b"</svg>"
        )
        out = sanitize_svg_bytes(svg)
        assert b"onclick" not in out
        assert b"alert" not in out
        # Restliches Markup bleibt.
        assert b"<rect" in out
        assert b"red" in out

    def test_strips_onload_on_svg_root(self) -> None:
        svg = (
            b'<svg xmlns="http://www.w3.org/2000/svg" onload="evil()">'
            b'<circle cx="5" cy="5" r="3"/></svg>'
        )
        out = sanitize_svg_bytes(svg)
        assert b"onload" not in out
        assert b"evil" not in out

    def test_strips_external_href(self) -> None:
        svg = (
            b'<svg xmlns="http://www.w3.org/2000/svg" '
            b'xmlns:xlink="http://www.w3.org/1999/xlink">'
            b'<a xlink:href="http://evil.example/x"><circle cx="5" cy="5" r="3"/></a>'
            b"</svg>"
        )
        out = sanitize_svg_bytes(svg)
        # Kein externer Link mehr
        assert b"evil.example" not in out
        # Inhalt (circle) bleibt
        assert b"<circle" in out

    def test_keeps_fragment_href(self) -> None:
        svg = (
            b'<svg xmlns="http://www.w3.org/2000/svg" '
            b'xmlns:xlink="http://www.w3.org/1999/xlink">'
            b'<defs><circle id="c1" cx="5" cy="5" r="3"/></defs>'
            b'<use xlink:href="#c1"/>'
            b"</svg>"
        )
        out = sanitize_svg_bytes(svg)
        # Fragment-Verweis bleibt erlaubt
        assert b"#c1" in out

    def test_strips_javascript_href(self) -> None:
        svg = (
            b'<svg xmlns="http://www.w3.org/2000/svg" '
            b'xmlns:xlink="http://www.w3.org/1999/xlink">'
            b'<a xlink:href="javascript:alert(1)"><circle cx="5" cy="5" r="3"/></a>'
            b"</svg>"
        )
        out = sanitize_svg_bytes(svg)
        assert b"javascript" not in out
        assert b"alert" not in out

    def test_strips_foreignobject_tag(self) -> None:
        svg = (
            b'<svg xmlns="http://www.w3.org/2000/svg">'
            b'<foreignObject><iframe src="x"/></foreignObject>'
            b'<circle cx="5" cy="5" r="3"/></svg>'
        )
        out = sanitize_svg_bytes(svg)
        assert b"foreignObject" not in out
        assert b"iframe" not in out

    def test_rejects_malformed_xml(self) -> None:
        with pytest.raises(DriveSanitizationError):
            sanitize_svg_bytes(b"<svg><not closed")

    def test_rejects_xml_with_external_entity(self) -> None:
        # defusedxml soll DTD-/Entity-Angriffe blockieren.
        attack = (
            b'<?xml version="1.0"?>'
            b'<!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]>'
            b'<svg xmlns="http://www.w3.org/2000/svg">&x;</svg>'
        )
        with pytest.raises(DriveSanitizationError):
            sanitize_svg_bytes(attack)
