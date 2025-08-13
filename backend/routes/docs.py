from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, URL
from backend.extensions import db
from backend.models.document import Document, DocumentCategory, DocumentVisibility
from backend.services.security import SecurityService, AuditAction, require_step_up

bp = Blueprint('docs', __name__)

class DocumentForm(FlaskForm):
    title = StringField('Titel', validators=[DataRequired()])
    url = StringField('URL', validators=[DataRequired(), URL()])
    category = SelectField('Kategorie', choices=[
        (DocumentCategory.VEREIN.value, 'Verein'),
        (DocumentCategory.EVENT.value, 'Event'),
        (DocumentCategory.FOTO.value, 'Foto'),
        (DocumentCategory.STATUTEN.value, 'Statuten'),
        (DocumentCategory.SONST.value, 'Sonst')
    ], validators=[DataRequired()])
    visibility = SelectField('Sichtbarkeit', choices=[
        (DocumentVisibility.PUBLIC.value, 'Öffentlich'),
        (DocumentVisibility.MEMBER.value, 'Mitglieder'),
        (DocumentVisibility.ADMIN.value, 'Admin')
    ], validators=[DataRequired()])
    submit = SubmitField('Speichern')

@bp.route('/')
@login_required
def index():
    """Documents list"""
    # Get documents based on user permissions
    if current_user.is_admin():
        documents = Document.query.filter_by(deleted_at=None).order_by(Document.created_at.desc()).all()
    else:
        documents = Document.query.filter(
            Document.deleted_at.is_(None),
            Document.visibility.in_([DocumentVisibility.PUBLIC, DocumentVisibility.MEMBER])
        ).order_by(Document.created_at.desc()).all()
    
    return render_template('docs/index.html', documents=documents)

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    """Create new document"""
    form = DocumentForm()
    
    if form.validate_on_submit():
        document = Document(
            title=form.title.data,
            url=form.url.data,
            category=DocumentCategory(form.category.data),
            visibility=DocumentVisibility(form.visibility.data),
            uploader_id=current_user.id
        )
        
        db.session.add(document)
        db.session.commit()
        
        flash('Dokument erfolgreich erstellt', 'success')
        return redirect(url_for('docs.index'))
    
    return render_template('docs/create.html', form=form)

@bp.route('/<int:doc_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(doc_id):
    """Edit document"""
    document = Document.query.get_or_404(doc_id)
    
    # Check permissions
    if not (current_user.is_admin() or document.uploader_id == current_user.id):
        flash('Keine Berechtigung zum Bearbeiten dieses Dokuments', 'error')
        return redirect(url_for('docs.index'))
    
    form = DocumentForm(obj=document)
    
    if form.validate_on_submit():
        document.title = form.title.data
        document.url = form.url.data
        document.category = DocumentCategory(form.category.data)
        document.visibility = DocumentVisibility(form.visibility.data)
        
        db.session.commit()
        flash('Dokument erfolgreich bearbeitet', 'success')
        return redirect(url_for('docs.index'))
    
    return render_template('docs/edit.html', form=form, document=document)

@bp.route('/<int:doc_id>/delete', methods=['POST'])
@login_required
def delete(doc_id):
    """Soft delete document"""
    document = Document.query.get_or_404(doc_id)
    
    # Check permissions
    if not (current_user.is_admin() or document.uploader_id == current_user.id):
        flash('Keine Berechtigung zum Löschen dieses Dokuments', 'error')
        return redirect(url_for('docs.index'))
    
    document.deleted_at = datetime.utcnow()
    db.session.commit()
    
    SecurityService.log_audit_event(
        AuditAction.DELETE_DOC_SOFT, 'document', doc_id
    )
    
    flash('Dokument erfolgreich gelöscht', 'success')
    return redirect(url_for('docs.index'))

@bp.route('/<int:doc_id>/restore', methods=['POST'])
@login_required
def restore(doc_id):
    """Restore deleted document"""
    document = Document.query.get_or_404(doc_id)
    
    # Check permissions
    if not (current_user.is_admin() or document.uploader_id == current_user.id):
        flash('Keine Berechtigung zum Wiederherstellen dieses Dokuments', 'error')
        return redirect(url_for('docs.trash'))
    
    document.deleted_at = None
    db.session.commit()
    
    flash('Dokument erfolgreich wiederhergestellt', 'success')
    return redirect(url_for('docs.trash'))

@bp.route('/trash')
@login_required
def trash():
    """Deleted documents"""
    if not current_user.is_admin():
        flash('Nur Admins können den Papierkorb einsehen', 'error')
        return redirect(url_for('docs.index'))
    
    documents = Document.query.filter(
        Document.deleted_at.isnot(None)
    ).order_by(Document.deleted_at.desc()).all()
    
    return render_template('docs/trash.html', documents=documents)

@bp.route('/<int:doc_id>/hard-delete', methods=['POST'])
@login_required
@require_step_up
def hard_delete(doc_id):
    """Hard delete document (admin only)"""
    if not current_user.is_admin():
        flash('Nur Admins können Dokumente endgültig löschen', 'error')
        return redirect(url_for('docs.trash'))
    
    document = Document.query.get_or_404(doc_id)
    
    SecurityService.log_audit_event(
        AuditAction.DELETE_DOC_HARD, 'document', doc_id
    )
    
    db.session.delete(document)
    db.session.commit()
    
    flash('Dokument endgültig gelöscht', 'success')
    return redirect(url_for('docs.trash'))

# Import here to avoid circular imports
from datetime import datetime 