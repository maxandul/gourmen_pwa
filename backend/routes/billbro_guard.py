"""Shared route boundary for simple mutations before financial finalization."""
from functools import wraps
from flask import abort, flash, jsonify, redirect, request, url_for
from flask_login import current_user
from backend.extensions import db
from backend.models.event import Event
from backend.services.billbro_state import BillBroStateService


def before_billbro_finalization(view):
    @wraps(view)
    def guarded(event_id, *args, **kwargs):
        event = Event.query.filter_by(id=event_id).populate_existing().with_for_update().first_or_404()
        if not event.is_visible_to(current_user):
            abort(403)
        if BillBroStateService.requires_correction(event):
            db.session.rollback()
            message = 'Abrechnung oder Forderungen vorhanden. Diese Änderung benötigt eine Korrektur mit Vorschau und Begründung; der direkte Weg ist gesperrt.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(error=message, correction_required=True), 409
            flash(message, 'error')
            return redirect(url_for('events.detail', event_id=event_id, tab='billbro'))
        return view(event_id, *args, **kwargs)
    return guarded
