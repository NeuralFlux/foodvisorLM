from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField
from wtforms.validators import Length, Regexp


class GTINForm(FlaskForm):
    barcode_val = StringField('barcode value', validators=[
            Length(min=3, max=15),
            Regexp("^[0-9]+$")
    ])
    barcode_image = HiddenField('barcode')
