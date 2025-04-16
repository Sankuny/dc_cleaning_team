from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, TimeField, SubmitField, SelectField
from wtforms.validators import DataRequired
from wtforms import PasswordField
from wtforms.validators import DataRequired, EqualTo
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, BooleanField, DateField, TimeField
from wtforms.validators import DataRequired

class RequestServiceForm(FlaskForm):
    service_type = SelectField('Service Type', validators=[DataRequired()])

    date = DateField('Preferred Date', validators=[DataRequired()])
    time = TimeField('Preferred Time', validators=[DataRequired()])
    address = StringField('Address')
    notes = TextAreaField('Additional Notes')

    # Campos nuevos para servicio recurrente
    recurrent = BooleanField('Recurrent Service')
    frequency = SelectField('Frequency')  # sin choices aquí
    
    submit = SubmitField('Request Service')



class UpdateProfileForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Update Info")

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm New Password", validators=[
        DataRequired(), EqualTo("new_password", message="Passwords must match.")
    ])
    submit = SubmitField("Update Password")