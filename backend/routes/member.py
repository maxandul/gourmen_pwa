from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField, DateField, IntegerField, FloatField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Email, Optional
from backend.extensions import db
from backend.models.member import Member, Funktion, NATIONALITAET_CHOICES, ZIMMERWUNSCH_CHOICES
from backend.models.member_sensitive import MemberSensitive
from backend.services.security import SecurityService, AuditAction, require_step_up

bp = Blueprint('member', __name__, url_prefix='/member')

class ProfileForm(FlaskForm):
    # Personal data
    vorname = StringField('Vorname/n (wie im Pass/ID)', validators=[DataRequired()])
    nachname = StringField('Nachname/n (wie im Pass/ID)', validators=[DataRequired()])
    rufname = StringField('Rufname')
    email = StringField('E-Mail', validators=[DataRequired(), Email()])
    telefon = StringField('Telefon')
    geburtsdatum = DateField('Geburtsdatum', validators=[Optional()])
    nationalitaet = SelectField('Nationalität', choices=NATIONALITAET_CHOICES, validators=[Optional()])
    zimmerwunsch = SelectField('Zimmerwunsch', choices=ZIMMERWUNSCH_CHOICES, validators=[Optional()])
    
    # Address data
    strasse = StringField('Straße')
    hausnummer = StringField('Hausnummer')
    plz = StringField('PLZ')
    ort = StringField('Ort')
    
    # Physical data
    koerpergroesse = IntegerField('Körpergröße (cm)', validators=[Optional()])
    koerpergewicht = IntegerField('Körpergewicht (kg)', validators=[Optional()])
    schuhgroesse = FloatField('Schuhgröße (EU)', validators=[Optional()])
    
    # Clothing data
    kleider_oberteil = StringField('Kleidergröße Oberteil')
    kleider_hosen = StringField('Kleidergröße Hosen')
    kleider_cap = StringField('Kleidergröße Cap')
    
    # Preferences
    spirit_animal = StringField('Spirit Animal')
    fuehrerschein = StringField('Führerschein (Kategorien)')
    
    # Hidden field to preserve active tab during form submission
    active_tab = HiddenField('active_tab', default='profile')
    
    submit = SubmitField('Speichern')

class SensitiveDataForm(FlaskForm):
    pass_nummer = StringField('Passnummer')
    pass_ausgestellt = StringField('Pass ausgestellt')
    pass_ablauf = StringField('Pass abläuft')
    id_nummer = StringField('ID-Nummer')
    id_ausgestellt = StringField('ID ausgestellt')
    id_ablauf = StringField('ID abläuft')
    allergien = TextAreaField('Allergien')
    
    # Hidden field to preserve active tab during form submission
    active_tab = HiddenField('active_tab', default='sensitive')
    
    submit = SubmitField('Speichern')

@bp.route('/')
@login_required
def index():
    """Member main overview page"""
    # Get the last order for the current user
    from backend.models.merch_order import MerchOrder
    last_order = MerchOrder.query.filter_by(member_id=current_user.id).order_by(MerchOrder.created_at.desc()).first()
    
    return render_template('member/index.html', last_order=last_order, use_v2_design=True)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page"""
    form = ProfileForm(prefix='profile')
    
    if request.method == 'GET':
        # Personal data
        form.vorname.data = current_user.vorname
        form.nachname.data = current_user.nachname
        form.rufname.data = current_user.rufname
        form.email.data = current_user.email
        form.telefon.data = current_user.telefon
        form.geburtsdatum.data = current_user.geburtsdatum
        form.nationalitaet.data = current_user.nationalitaet
        form.zimmerwunsch.data = current_user.zimmerwunsch
        
        # Address data
        form.strasse.data = current_user.strasse
        form.hausnummer.data = current_user.hausnummer
        form.plz.data = current_user.plz
        form.ort.data = current_user.ort
        
        # Physical data
        form.koerpergroesse.data = current_user.koerpergroesse
        form.koerpergewicht.data = current_user.koerpergewicht
        form.schuhgroesse.data = current_user.schuhgroesse
        
        # Clothing data
        form.kleider_oberteil.data = current_user.kleider_oberteil
        form.kleider_hosen.data = current_user.kleider_hosen
        form.kleider_cap.data = current_user.kleider_cap
        
        # Preferences
        form.spirit_animal.data = current_user.spirit_animal
        form.fuehrerschein.data = current_user.fuehrerschein
        
        # Set active_tab field based on query parameter
        form.active_tab.data = request.args.get('tab', 'profile')
    
    # Determine active tab (prioritize form data for POST, then query params, then default)
    # For POST requests, form data takes precedence to preserve tab state during submission
    if request.method == 'POST':
        active_tab = request.form.get('active_tab') or request.args.get('tab') or 'profile'
    else:
        active_tab = request.args.get('tab') or 'profile'
    
    # Initialize sensitive form (only if needed)
    sensitive_form = None
    sensitive_data_decrypted = None
    
    # Handle Sensitive Tab
    if active_tab == 'sensitive':
        # Check step-up access
        if not SecurityService.check_step_up_access():
            # Redirect to step-up with return to this tab
            return redirect(url_for('auth.step_up', next=url_for('member.profile', tab='sensitive')))
        
        # User has step-up access, initialize sensitive form
        sensitive_form = SensitiveDataForm(prefix='sensitive')
        
        # Get or create sensitive data record
        sensitive_data = MemberSensitive.query.filter_by(member_id=current_user.id).first()
        
        if request.method == 'GET':
            # Set active_tab field based on query parameter
            sensitive_form.active_tab.data = request.args.get('tab', 'sensitive')
            
            if sensitive_data:
                try:
                    sensitive_data_decrypted = SecurityService.decrypt_json(sensitive_data.payload_encrypted)
                    
                    # Populate form
                    sensitive_form.pass_nummer.data = sensitive_data_decrypted.get('pass_nummer', '')
                    sensitive_form.pass_ausgestellt.data = sensitive_data_decrypted.get('pass_ausgestellt', '')
                    sensitive_form.pass_ablauf.data = sensitive_data_decrypted.get('pass_ablauf', '')
                    sensitive_form.id_nummer.data = sensitive_data_decrypted.get('id_nummer', '')
                    sensitive_form.id_ausgestellt.data = sensitive_data_decrypted.get('id_ausgestellt', '')
                    sensitive_form.id_ablauf.data = sensitive_data_decrypted.get('id_ablauf', '')
                    sensitive_form.allergien.data = sensitive_data_decrypted.get('allergien', '')
                    
                    # Log access
                    SecurityService.log_audit_event(
                        AuditAction.READ_SENSITIVE_SELF, 'member_sensitive', current_user.id
                    )
                except Exception as e:
                    # If decryption fails, clear the corrupted data
                    flash('Sensible Daten waren beschädigt und wurden zurückgesetzt.', 'warning')
                    db.session.delete(sensitive_data)
                    db.session.commit()
                    sensitive_data_decrypted = {}
            else:
                sensitive_data_decrypted = {}
        
        elif sensitive_form.validate_on_submit():
            # Update sensitive data
            data = {
                'pass_nummer': sensitive_form.pass_nummer.data,
                'pass_ausgestellt': sensitive_form.pass_ausgestellt.data,
                'pass_ablauf': sensitive_form.pass_ablauf.data,
                'id_nummer': sensitive_form.id_nummer.data,
                'id_ausgestellt': sensitive_form.id_ausgestellt.data,
                'id_ablauf': sensitive_form.id_ablauf.data,
                'allergien': sensitive_form.allergien.data
            }
            
            encrypted_data = SecurityService.encrypt_json(data)
            
            if sensitive_data:
                sensitive_data.payload_encrypted = encrypted_data
            else:
                sensitive_data = MemberSensitive(
                    member_id=current_user.id,
                    payload_encrypted=encrypted_data
                )
                db.session.add(sensitive_data)
            
            db.session.commit()
            
            # Log update
            SecurityService.log_audit_event(
                AuditAction.UPDATE_SENSITIVE_SELF, 'member_sensitive', current_user.id
            )
            
            flash('Sensible Daten erfolgreich gespeichert', 'success')
            return redirect(url_for('member.profile', tab='sensitive'))
    
    # Handle Profile Tab form submission
    if active_tab == 'profile' and request.method == 'POST':
        is_valid = form.validate_on_submit()
        
        if not is_valid:
            # Show validation errors
            flash('Bitte überprüfe deine Eingaben. Es gibt Fehler im Formular.', 'error')
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'error')
        else:
            # Personal data
            current_user.vorname = form.vorname.data
            current_user.nachname = form.nachname.data
            current_user.rufname = form.rufname.data
            current_user.email = form.email.data
            current_user.telefon = form.telefon.data
            current_user.geburtsdatum = form.geburtsdatum.data
            current_user.nationalitaet = form.nationalitaet.data
            current_user.zimmerwunsch = form.zimmerwunsch.data
            
            # Address data
            current_user.strasse = form.strasse.data
            current_user.hausnummer = form.hausnummer.data
            current_user.plz = form.plz.data
            current_user.ort = form.ort.data
            
            # Physical data
            current_user.koerpergroesse = form.koerpergroesse.data
            current_user.koerpergewicht = form.koerpergewicht.data
            current_user.schuhgroesse = form.schuhgroesse.data
            
            # Clothing data
            current_user.kleider_oberteil = form.kleider_oberteil.data
            current_user.kleider_hosen = form.kleider_hosen.data
            current_user.kleider_cap = form.kleider_cap.data
            
            # Preferences
            current_user.spirit_animal = form.spirit_animal.data
            current_user.fuehrerschein = form.fuehrerschein.data
            
            db.session.commit()
            flash('Profil erfolgreich aktualisiert', 'success')
            return redirect(url_for('member.profile', tab='profile'))
    
    return render_template('member/profile.html', 
                         form=form,
                         sensitive_form=sensitive_form,
                         sensitive_data=sensitive_data_decrypted,
                         active_tab=active_tab,
                         has_step_up=SecurityService.check_step_up_access(),
                         use_v2_design=True)

@bp.route('/security')
@login_required
def security():
    """Security settings page"""
    return render_template('member/security.html', use_v2_design=True)

@bp.route('/technical')
@login_required
def technical():
    """Technical settings page"""
    return render_template('member/technical.html', use_v2_design=True)

@bp.route('/merch')
@login_required
def merch():
    """Merch overview page"""
    from backend.models.merch_article import MerchArticle
    from backend.models.merch_variant import MerchVariant
    from backend.models.merch_order import MerchOrder
    
    # Get active articles
    articles = MerchArticle.query.filter_by(is_active=True).all()
    # Enrich articles with variants and available colors (used by template/JS)
    for article in articles:
        variants = MerchVariant.query.filter_by(article_id=article.id, is_active=True).all()
        article.variants = variants
        article.available_colors = sorted({v.color for v in variants}) if variants else []
    
    # Get user's orders
    user_orders = MerchOrder.query.filter_by(member_id=current_user.id).order_by(MerchOrder.created_at.desc()).all()
    
    return render_template('member/merch/index.html', articles=articles, orders=user_orders, use_v2_design=True)

@bp.route('/merch/order', methods=['GET', 'POST'])
@login_required
def merch_order():
    """Merch order page"""
    from backend.models.merch_article import MerchArticle
    from backend.models.merch_variant import MerchVariant
    from backend.models.merch_order import MerchOrder, OrderStatus
    from backend.models.merch_order_item import MerchOrderItem
    import uuid
    from datetime import datetime
    
    if request.method == 'POST':
        try:
            # Create new order
            order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            order = MerchOrder(
                member_id=current_user.id,
                order_number=order_number,
                status=OrderStatus.BESTELLT,
                total_member_price_rappen=0,
                total_supplier_price_rappen=0,
                total_profit_rappen=0
            )
            db.session.add(order)
            db.session.flush()  # Get the order ID
            
            total_member_price = 0
            total_supplier_price = 0
            total_profit = 0
            
            # Process each article (now with multiple variants per article)
            for article in MerchArticle.query.filter_by(is_active=True).all():
                # Get arrays of colors, sizes, and quantities for this article
                colors = request.form.getlist(f'color_{article.id}[]')
                sizes = request.form.getlist(f'size_{article.id}[]')
                quantities = request.form.getlist(f'quantity_{article.id}[]')
                
                # Process each variant row for this article
                for color, size, quantity_str in zip(colors, sizes, quantities):
                    quantity = int(quantity_str or 0)
                    
                    if quantity > 0 and color and size:
                        # Find the variant
                        variant = MerchVariant.query.filter_by(
                            article_id=article.id,
                            color=color,
                            size=size,
                            is_active=True
                        ).first()
                        
                        if variant:
                            # Create order item
                            item = MerchOrderItem(
                                order_id=order.id,
                                article_id=article.id,
                                variant_id=variant.id,
                                quantity=quantity,
                                unit_member_price_rappen=variant.member_price_rappen,
                                unit_supplier_price_rappen=variant.supplier_price_rappen,
                                total_member_price_rappen=quantity * variant.member_price_rappen,
                                total_supplier_price_rappen=quantity * variant.supplier_price_rappen,
                                total_profit_rappen=quantity * (variant.member_price_rappen - variant.supplier_price_rappen)
                            )
                            db.session.add(item)
                            
                            total_member_price += item.total_member_price_rappen
                            total_supplier_price += item.total_supplier_price_rappen
                            total_profit += item.total_profit_rappen
            
            # Update order totals
            order.total_member_price_rappen = total_member_price
            order.total_supplier_price_rappen = total_supplier_price
            order.total_profit_rappen = total_profit
            
            db.session.commit()
            flash('Bestellung erfolgreich aufgegeben!', 'success')
            return redirect(url_for('member.merch_orders'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Aufgeben der Bestellung: {str(e)}', 'error')
    
    # GET request - show form
    # Get active articles with their variants
    articles = MerchArticle.query.filter_by(is_active=True).all()
    
    # Get all variants for each article and prepare available colors
    for article in articles:
        article.variants = MerchVariant.query.filter_by(article_id=article.id, is_active=True).all()
        # Get unique colors for this article
        article.available_colors = list(set([variant.color for variant in article.variants]))
    
    return render_template('member/merch/order.html', articles=articles, use_v2_design=True)

@bp.route('/merch/orders')
@login_required
def merch_orders():
    """User's merch orders"""
    from backend.models.merch_order import MerchOrder
    
    orders = MerchOrder.query.filter_by(member_id=current_user.id).order_by(MerchOrder.created_at.desc()).all()
    
    return render_template('member/merch/orders.html', orders=orders, use_v2_design=True)

@bp.route('/merch/order/<int:order_id>')
@login_required
def merch_order_detail(order_id):
    """Order detail page"""
    from backend.models.merch_order import MerchOrder
    
    order = MerchOrder.query.filter_by(id=order_id, member_id=current_user.id).first_or_404()
    
    return render_template('member/merch/order_detail.html', order=order, use_v2_design=True)

@bp.route('/merch/order/<int:order_id>/edit', methods=['GET', 'POST'])
@login_required
def merch_order_edit(order_id):
    """Edit merch order (only if status is BESTELLT)"""
    from backend.models.merch_article import MerchArticle
    from backend.models.merch_variant import MerchVariant
    from backend.models.merch_order import MerchOrder, OrderStatus
    from backend.models.merch_order_item import MerchOrderItem
    
    # Load the order and verify ownership + status
    order = MerchOrder.query.filter_by(id=order_id, member_id=current_user.id).first_or_404()
    
    # Check if order can be edited
    if order.status != OrderStatus.BESTELLT:
        flash('Diese Bestellung kann nicht mehr bearbeitet werden.', 'error')
        return redirect(url_for('member.merch_order_detail', order_id=order_id))
    
    if request.method == 'POST':
        try:
            # Delete old order items
            MerchOrderItem.query.filter_by(order_id=order.id).delete()
            
            total_member_price = 0
            total_supplier_price = 0
            total_profit = 0
            
            # Process each article (now with multiple variants per article)
            for article in MerchArticle.query.filter_by(is_active=True).all():
                # Get arrays of colors, sizes, and quantities for this article
                colors = request.form.getlist(f'color_{article.id}[]')
                sizes = request.form.getlist(f'size_{article.id}[]')
                quantities = request.form.getlist(f'quantity_{article.id}[]')
                
                # Process each variant row for this article
                for color, size, quantity_str in zip(colors, sizes, quantities):
                    quantity = int(quantity_str or 0)
                    
                    if quantity > 0 and color and size:
                        # Find the variant
                        variant = MerchVariant.query.filter_by(
                            article_id=article.id,
                            color=color,
                            size=size,
                            is_active=True
                        ).first()
                        
                        if variant:
                            # Create new order item
                            item = MerchOrderItem(
                                order_id=order.id,
                                article_id=article.id,
                                variant_id=variant.id,
                                quantity=quantity,
                                unit_member_price_rappen=variant.member_price_rappen,
                                unit_supplier_price_rappen=variant.supplier_price_rappen,
                                total_member_price_rappen=quantity * variant.member_price_rappen,
                                total_supplier_price_rappen=quantity * variant.supplier_price_rappen,
                                total_profit_rappen=quantity * (variant.member_price_rappen - variant.supplier_price_rappen)
                            )
                            db.session.add(item)
                            
                            total_member_price += item.total_member_price_rappen
                            total_supplier_price += item.total_supplier_price_rappen
                            total_profit += item.total_profit_rappen
            
            # Update order totals
            order.total_member_price_rappen = total_member_price
            order.total_supplier_price_rappen = total_supplier_price
            order.total_profit_rappen = total_profit
            
            db.session.commit()
            flash('Bestellung erfolgreich aktualisiert!', 'success')
            return redirect(url_for('member.merch_order_detail', order_id=order.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Aktualisieren der Bestellung: {str(e)}', 'error')
    
    # GET request - show form with existing data
    articles = MerchArticle.query.filter_by(is_active=True).all()
    
    # Prepare existing order data (now supporting multiple items per article)
    existing_items = {}  # article_id -> list of items
    for item in order.order_items:
        if item.article_id not in existing_items:
            existing_items[item.article_id] = []
        existing_items[item.article_id].append({
            'color': item.variant.color,
            'size': item.variant.size,
            'quantity': item.quantity
        })
    
    # Get all variants for each article
    for article in articles:
        article.variants = MerchVariant.query.filter_by(article_id=article.id, is_active=True).all()
        article.available_colors = list(set([variant.color for variant in article.variants]))
        
        # Pre-fill existing data if available (now as a list)
        article.existing_items = existing_items.get(article.id, [])
    
    return render_template('member/merch/order_edit.html', articles=articles, order=order, use_v2_design=True)

@bp.route('/members')
@login_required
def members():
    """Members list"""
    members = Member.query.filter_by(is_active=True).order_by(Member.nachname, Member.vorname).all()
    return render_template('member/members.html', members=members, use_v2_design=True)

# Import here to avoid circular imports
from datetime import datetime
