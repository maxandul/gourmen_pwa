from flask_wtf import FlaskForm
from wtforms import IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional

class EventRatingForm(FlaskForm):
    """Form for rating an event"""
    
    food_rating = IntegerField('Essen', validators=[
        DataRequired(message='Bitte bewerten Sie das Essen'),
        NumberRange(min=1, max=5, message='Bewertung muss zwischen 1 und 5 liegen')
    ])
    
    drinks_rating = IntegerField('Getränke', validators=[
        DataRequired(message='Bitte bewerten Sie die Getränke'),
        NumberRange(min=1, max=5, message='Bewertung muss zwischen 1 und 5 liegen')
    ])
    
    service_rating = IntegerField('Bedienung', validators=[
        DataRequired(message='Bitte bewerten Sie die Bedienung'),
        NumberRange(min=1, max=5, message='Bewertung muss zwischen 1 und 5 liegen')
    ])
    
    highlights = TextAreaField('Highlights (optional)', validators=[
        Optional()
    ])
    
    submit = SubmitField('Bewertung speichern')
