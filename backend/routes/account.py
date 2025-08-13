from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField, DateField, IntegerField, FloatField, BooleanField
from wtforms.validators import DataRequired, Email, Optional
from backend.extensions import db
from backend.models.member import Member, Funktion
from backend.models.member_sensitive import MemberSensitive
from backend.services.security import SecurityService, AuditAction, require_step_up

bp = Blueprint('account', __name__)

class ProfileForm(FlaskForm):
    # Personal data
    vorname = StringField('Vorname/n (wie im Pass/ID)', validators=[DataRequired()])
    nachname = StringField('Nachname/n (wie im Pass/ID)', validators=[DataRequired()])
    rufname = StringField('Rufname')
    email = StringField('E-Mail', validators=[DataRequired(), Email()])
    telefon = StringField('Telefon')
    geburtsdatum = DateField('Geburtsdatum', validators=[Optional()])
    nationalitaet = StringField('Nationalität')
    
    # Address data
    strasse = StringField('Straße')
    hausnummer = StringField('Hausnummer')
    plz = StringField('PLZ')
    ort = StringField('Ort')
    
    # Association data
    funktion = SelectField('Funktion', choices=[
        (Funktion.MEMBER.value, 'Member'),
        (Funktion.VEREINSPRAESIDENT.value, 'Vereinspräsident'),
        (Funktion.KOMMISSIONSPRAESIDENT.value, 'Kommissionspräsident'),
        (Funktion.SCHATZMEISTER.value, 'Schatzmeister'),
        (Funktion.MARKETINGCHEF.value, 'Marketingchef'),
        (Funktion.REISEKOMMISSAR.value, 'Reisekommissar'),
        (Funktion.RECHNUNGSPRUEFER.value, 'Rechnungsprüfer')
    ])
    beitrittsjahr = IntegerField('Beitrittsjahr', validators=[Optional()])
    vorstandsmitglied = BooleanField('Vorstandsmitglied')
    
    # Physical data
    koerpergroesse = IntegerField('Körpergröße (cm)', validators=[Optional()])
    koerpergewicht = IntegerField('Körpergewicht (kg)', validators=[Optional()])
    schuhgroesse = FloatField('Schuhgröße (EU)', validators=[Optional()])
    
    # Clothing data
    kleider_oberteil = StringField('Kleidergröße Oberteil')
    kleider_hosen = StringField('Kleidergröße Hosen')
    kleider_cap = StringField('Kleidergröße Cap')
    
    # Preferences
    zimmerwunsch = StringField('Zimmerwunsch')
    spirit_animal = StringField('Spirit Animal')
    fuehrerschein = StringField('Führerschein (Kategorien)')
    
    submit = SubmitField('Speichern')

class SensitiveDataForm(FlaskForm):
    pass_nummer = StringField('Passnummer')
    pass_ausgestellt = StringField('Pass ausgestellt')
    pass_ablauf = StringField('Pass abläuft')
    id_nummer = StringField('ID-Nummer')
    id_ausgestellt = StringField('ID ausgestellt')
    id_ablauf = StringField('ID abläuft')
    fuehrerschein = StringField('Führerschein')
    allergien = TextAreaField('Allergien')
    submit = SubmitField('Speichern')

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page"""
    form = ProfileForm()
    
    if request.method == 'GET':
        # Personal data
        form.vorname.data = current_user.vorname
        form.nachname.data = current_user.nachname
        form.rufname.data = current_user.rufname
        form.email.data = current_user.email
        form.telefon.data = current_user.telefon
        form.geburtsdatum.data = current_user.geburtsdatum
        form.nationalitaet.data = current_user.nationalitaet
        
        # Address data
        form.strasse.data = current_user.strasse
        form.hausnummer.data = current_user.hausnummer
        form.plz.data = current_user.plz
        form.ort.data = current_user.ort
        
        # Association data
        form.funktion.data = current_user.funktion.value if current_user.funktion else Funktion.MEMBER.value
        form.beitrittsjahr.data = current_user.beitrittsjahr
        form.vorstandsmitglied.data = current_user.vorstandsmitglied
        
        # Physical data
        form.koerpergroesse.data = current_user.koerpergroesse
        form.koerpergewicht.data = current_user.koerpergewicht
        form.schuhgroesse.data = current_user.schuhgroesse
        
        # Clothing data
        form.kleider_oberteil.data = current_user.kleider_oberteil
        form.kleider_hosen.data = current_user.kleider_hosen
        form.kleider_cap.data = current_user.kleider_cap
        
        # Preferences
        form.zimmerwunsch.data = current_user.zimmerwunsch
        form.spirit_animal.data = current_user.spirit_animal
        form.fuehrerschein.data = current_user.fuehrerschein
    
    if form.validate_on_submit():
        # Personal data
        current_user.vorname = form.vorname.data
        current_user.nachname = form.nachname.data
        current_user.rufname = form.rufname.data
        current_user.email = form.email.data
        current_user.telefon = form.telefon.data
        current_user.geburtsdatum = form.geburtsdatum.data
        current_user.nationalitaet = form.nationalitaet.data
        
        # Address data
        current_user.strasse = form.strasse.data
        current_user.hausnummer = form.hausnummer.data
        current_user.plz = form.plz.data
        current_user.ort = form.ort.data
        
        # Association data
        current_user.funktion = Funktion(form.funktion.data)
        current_user.beitrittsjahr = form.beitrittsjahr.data
        current_user.vorstandsmitglied = form.vorstandsmitglied.data
        
        # Physical data
        current_user.koerpergroesse = form.koerpergroesse.data
        current_user.koerpergewicht = form.koerpergewicht.data
        current_user.schuhgroesse = form.schuhgroesse.data
        
        # Clothing data
        current_user.kleider_oberteil = form.kleider_oberteil.data
        current_user.kleider_hosen = form.kleider_hosen.data
        current_user.kleider_cap = form.kleider_cap.data
        
        # Preferences
        current_user.zimmerwunsch = form.zimmerwunsch.data
        current_user.spirit_animal = form.spirit_animal.data
        current_user.fuehrerschein = form.fuehrerschein.data
        
        db.session.commit()
        flash('Profil erfolgreich aktualisiert', 'success')
        return redirect(url_for('account.profile'))
    
    return render_template('account/profile.html', form=form)

@bp.route('/sensitive', methods=['GET', 'POST'])
@login_required
@require_step_up
def sensitive_data():
    """Sensitive data management"""
    form = SensitiveDataForm()
    
    # Get or create sensitive data record
    sensitive_data = MemberSensitive.query.filter_by(member_id=current_user.id).first()
    
    if request.method == 'GET':
        unmask = request.args.get('unmask', type=bool)
        
        if sensitive_data:
            try:
                data = SecurityService.decrypt_json(sensitive_data.payload_encrypted)
                
                if not unmask:
                    # Mask sensitive fields
                    fields_to_mask = ['pass_nummer', 'pass_ausgestellt', 'pass_ablauf', 
                                    'id_nummer', 'id_ausgestellt', 'id_ablauf', 
                                    'fuehrerschein', 'allergien']
                    data = SecurityService.mask_sensitive_data(data, fields_to_mask)
                
                # Log access
                SecurityService.log_audit_event(
                    AuditAction.READ_SENSITIVE_SELF, 'member_sensitive', current_user.id
                )
            except Exception as e:
                # If decryption fails, clear the corrupted data
                flash('Sensible Daten waren beschädigt und wurden zurückgesetzt.', 'warning')
                db.session.delete(sensitive_data)
                db.session.commit()
                data = {}
        else:
            data = {}
        
        # Populate form with existing data
        if data:
            form.pass_nummer.data = data.get('pass_nummer', '')
            form.pass_ausgestellt.data = data.get('pass_ausgestellt', '')
            form.pass_ablauf.data = data.get('pass_ablauf', '')
            form.id_nummer.data = data.get('id_nummer', '')
            form.id_ausgestellt.data = data.get('id_ausgestellt', '')
            form.id_ablauf.data = data.get('id_ablauf', '')
            form.fuehrerschein.data = data.get('fuehrerschein', '')
            form.allergien.data = data.get('allergien', '')
        
        return render_template('account/sensitive.html', form=form, data=data, unmasked=unmask)
    
    elif form.validate_on_submit():
        # Update sensitive data
        data = {
            'pass_nummer': form.pass_nummer.data,
            'pass_ausgestellt': form.pass_ausgestellt.data,
            'pass_ablauf': form.pass_ablauf.data,
            'id_nummer': form.id_nummer.data,
            'id_ausgestellt': form.id_ausgestellt.data,
            'id_ablauf': form.id_ablauf.data,
            'fuehrerschein': form.fuehrerschein.data,
            'allergien': form.allergien.data
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
        return redirect(url_for('account.sensitive_data'))
    
    # Check for CSRF token errors and redirect to step-up if needed
    if form.errors and 'csrf_token' in form.errors:
        flash('Sicherheitstoken abgelaufen. Bitte authentifizieren Sie sich erneut.', 'warning')
        return redirect(url_for('auth.step_up', next=request.url))
    
    # Form validation failed, re-render with errors
    return render_template('account/sensitive.html', form=form, data={}, unmasked=False)

@bp.route('/members')
@login_required
def members():
    """Members list"""
    members = Member.query.filter_by(is_active=True).order_by(Member.nachname, Member.vorname).all()
    return render_template('account/members.html', members=members)

# Import here to avoid circular imports
from datetime import datetime 