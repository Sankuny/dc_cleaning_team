from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, TimeField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired, Email, EqualTo

# 📝 Formulario para solicitar un servicio
class RequestServiceForm(FlaskForm):
    service_type = SelectField('Service Type', validators=[DataRequired()])
    date = DateField('Preferred Date', validators=[DataRequired()])
    time = TimeField('Preferred Time', validators=[DataRequired()])
    address = StringField('Address')
    notes = TextAreaField('Additional Notes')
    submit = SubmitField('Request Service')

# 👤 Formulario para actualizar perfil
class UpdateProfileForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Update Info")

# 🔒 Formulario para cambiar contraseña
class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")]
    )
    submit = SubmitField("Update Password")
