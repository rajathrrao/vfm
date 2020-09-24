from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import InputRequired, Email, Length

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=1, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=4, max=80)])
    remember = BooleanField('remember me')
    login = SubmitField("Login")

class RegisterForm(FlaskForm):
    username = StringField('Name of department(Username)', validators=[InputRequired(), Length(min=1, max=15)])
    email = StringField('username', validators=[InputRequired(), Length(min=1, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=4, max=80)])
    register = SubmitField("Add user")

class ModifyForm(FlaskForm):
    username = StringField('Name of department(Username)')
    email = StringField('username', validators=[Length(min=1, max=15)])
    password = PasswordField('password', validators=[Length(min=4, max=80)])
    modify = SubmitField("Modify user")