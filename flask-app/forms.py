from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField


class GTINForm(FlaskForm):
    barcode_image = HiddenField('barcode')
