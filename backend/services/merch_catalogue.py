"""Read-only catalogue projections, never replace persistent relationships."""
from backend.models.merch_article import MerchArticle
from backend.models.merch_variant import MerchVariant


def catalogue_context():
    articles = MerchArticle.query.filter_by(is_active=True).order_by(MerchArticle.id).all()
    variants = {article.id: [] for article in articles}
    if articles:
        rows = (MerchVariant.query.join(MerchArticle)
                .filter(MerchArticle.is_active.is_(True), MerchVariant.is_active.is_(True))
                .order_by(MerchVariant.article_id, MerchVariant.id).all())
        for variant in rows:
            if variant.article_id in variants:
                variants[variant.article_id].append(variant)
    colors = {aid: sorted({variant.color for variant in rows}) for aid, rows in variants.items()}
    return dict(articles=articles, catalogue_variants=variants, catalogue_colors=colors)
