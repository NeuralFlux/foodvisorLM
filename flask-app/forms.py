from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length, Regexp


class GTINForm(FlaskForm):
    gtin = StringField(
        'Product Code', validators=[
            DataRequired(),
            Length(min=8, max=15),
            Regexp("^[0-9]+$")
        ]
    )
