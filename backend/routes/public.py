from flask import (
    Blueprint,
    current_app,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user
from backend.extensions import db
from backend.models.member import Member
from datetime import datetime

from backend.services.monatsessen_stats import (
    get_landing_extras,
    get_landing_restaurant_table,
)

bp = Blueprint('public', __name__)

NEWLINE = chr(10)

LANDING_HITLIST_TEASER = 5
RESTAURANTS_PER_PAGE = 10


@bp.route('/')
def landing():
    """Landing page - redirects to dashboard if user is logged in (unless explicitly requested)"""
    # Only redirect to dashboard if user is authenticated AND didn't explicitly request landing page
    show_landing = request.args.get('show', '0') == '1'
    
    if current_user.is_authenticated and not show_landing:
        return redirect(url_for('dashboard.index'))

    try:
        now = datetime.utcnow()
        landing_extra = get_landing_extras(now)
        teaser_rows, _, _, _, hitlist_baseline_total = get_landing_restaurant_table(
            now,
            page=1,
            per_page=LANDING_HITLIST_TEASER,
            query=None,
        )

        # Public stats
        member_count = Member.query.filter_by(is_active=True).count()
        
        # Hero „Restaurant-Count“ = gleiche Regeln wie Hitlist (ohne Textsuche).
        restaurant_count = hitlist_baseline_total

        return render_template(
            'public/landing.html',
            member_count=member_count,
            restaurant_count=restaurant_count,
            next_essen_date=landing_extra['next_essen_date'],
            next_essen_restaurant=landing_extra.get('next_essen_restaurant'),
            hitlist_teaser_rows=teaser_rows,
        )
    except Exception:
        # Fallback if database is not ready
        return render_template(
            'public/landing.html',
            member_count=0,
            restaurant_count=0,
            next_essen_date=None,
            next_essen_restaurant=None,
            hitlist_teaser_rows=[],
        )


@bp.route('/ueber-uns')
def about():
    """Oeffentliche Infoseite Verein / Leitbild / Aktivitaeten."""
    return render_template('public/about.html')


@bp.route('/restaurants')
def restaurants():
    """Öffentliche vollständige Gourmen-Hitlist mit Suche und Pagination."""
    try:
        page_raw = request.args.get('page', '1')
        try:
            page = int(page_raw)
        except (TypeError, ValueError):
            page = 1
        if page < 1:
            page = 1

        now = datetime.utcnow()
        table_query = (request.args.get('q') or '').strip()
        hitlist_sort = (request.args.get('sort') or 'rating').strip().lower()
        if hitlist_sort not in ('rating', 'recent', 'name'):
            hitlist_sort = 'rating'
        table_rows, table_total, table_total_pages, table_page, hitlist_baseline_total = (
            get_landing_restaurant_table(
                now,
                page=page,
                per_page=RESTAURANTS_PER_PAGE,
                query=table_query or None,
                sort=hitlist_sort,
            )
        )

        return render_template(
            'public/restaurants.html',
            table_rows=table_rows,
            table_total=table_total,
            table_page=table_page,
            table_total_pages=table_total_pages,
            table_query=table_query,
            restaurant_count=hitlist_baseline_total,
            hitlist_sort=hitlist_sort,
        )
    except Exception:
        return render_template(
            'public/restaurants.html',
            table_rows=[],
            table_total=0,
            table_page=1,
            table_total_pages=1,
            table_query='',
            restaurant_count=0,
            hitlist_sort='rating',
        )

def _public_base_url() -> str:
    """Absolute Basis-URL fuer robots.txt und sitemap.xml."""
    return current_app.config.get('PUBLIC_APP_BASE_URL', 'https://www.gourmen.ch').rstrip('/')


# Oeffentliche Seiten, die in den Suchindex gehoeren. Alles andere (Login,
# Dashboard, Vereinsbereich) bleibt bewusst draussen.
SITEMAP_ENDPOINTS = [
    ('public.landing', '1.0', 'weekly'),
    ('public.about', '0.8', 'monthly'),
    ('public.restaurants', '0.8', 'weekly'),
]

# Interne Bereiche, die Crawler nicht anfassen sollen.
ROBOTS_DISALLOW = [
    '/auth/',
    '/dashboard/',
    '/events/',
    '/member/',
    '/admin/',
    '/billbro/',
    '/ggl/',
    '/ratings/',
    '/accounting/',
    '/docs/',
    '/notifications/',
    '/calendar/',
    '/api/',
    '/health',
    '/test',
]


@bp.route('/robots.txt')
def robots_txt():
    """robots.txt inklusive Sitemap-Verweis.

    Lieferte vorher 404. Google kommt zwar auch ohne robots.txt zurecht, aber
    ohne den Sitemap-Hinweis fehlt Crawlern der Einstiegspunkt in eine Site,
    auf die kaum jemand von aussen verlinkt - und die internen Bereiche waren
    nirgends explizit ausgeschlossen.
    """
    base = _public_base_url()

    lines = ['User-agent: *']
    lines.extend('Disallow: ' + path for path in ROBOTS_DISALLOW)
    lines.append('')
    lines.append('Sitemap: ' + base + '/sitemap.xml')
    lines.append('')

    response = make_response(NEWLINE.join(lines))
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    response.headers['Cache-Control'] = 'public, max-age=86400'
    return response


@bp.route('/sitemap.xml')
def sitemap_xml():
    """XML-Sitemap der oeffentlichen Seiten.

    Klein, aber der Weg, ueber den eine Site ohne eingehende Links ueberhaupt
    erst gefunden und gecrawlt wird. In der Google Search Console einreichen.
    """
    base = _public_base_url()
    lastmod = datetime.utcnow().date().isoformat()

    entries = []
    for endpoint, priority, changefreq in SITEMAP_ENDPOINTS:
        try:
            loc = base + url_for(endpoint)
        except Exception:
            continue
        entries.append(
            '  <url>'
            + NEWLINE + '    <loc>' + loc + '</loc>'
            + NEWLINE + '    <lastmod>' + lastmod + '</lastmod>'
            + NEWLINE + '    <changefreq>' + changefreq + '</changefreq>'
            + NEWLINE + '    <priority>' + priority + '</priority>'
            + NEWLINE + '  </url>'
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>' + NEWLINE
        + '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + NEWLINE
        + NEWLINE.join(entries) + NEWLINE
        + '</urlset>' + NEWLINE
    )

    response = make_response(xml)
    response.headers['Content-Type'] = 'application/xml; charset=utf-8'
    response.headers['Cache-Control'] = 'public, max-age=86400'
    return response


@bp.route('/health/db')
def health_db():
    """Database health check"""
    try:
        # Simple database query
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'ok', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'error', 'database': 'disconnected', 'error': str(e)}), 503

# Service Worker: einzige Route `GET /sw.js` in `backend/app.py` (App-Factory), damit keine doppelte Registrierung entsteht.
