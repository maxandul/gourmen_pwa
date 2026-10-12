"""Shared storage-safe numeric fields; no domain-specific body-size limits."""
import math

from wtforms import IntegerField, FloatField
from wtforms.validators import Optional, NumberRange, ValidationError
from wtforms.widgets import TextInput


def optional_member_integer(label, *, text_input=False):
    options = {'widget': TextInput()} if text_input else {}
    return IntegerField(label, validators=[Optional(), NumberRange(
        min=0, max=2147483647,
        message='Bitte gib eine nicht negative ganze Zahl im unterstützten Zahlenbereich ein.',
    )], **options)


def _finite_non_negative(form, field):
    if field.data is not None and (not math.isfinite(field.data) or field.data < 0):
        raise ValidationError('Bitte gib eine endliche, nicht negative Zahl ein.')


def optional_member_float(label, *, text_input=False):
    options = {'widget': TextInput()} if text_input else {}
    return FloatField(label, validators=[Optional(), _finite_non_negative], **options)
