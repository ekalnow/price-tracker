from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, URL, Optional, ValidationError
import re

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class URLForm(FlaskForm):
    url = StringField('Product URL', validators=[DataRequired(), URL()])
    submit = SubmitField('Add URL')
    
    def validate_url(self, url):
        # Check if URL is from a supported platform
        if not (re.search(r'(salla\.sa|salla\.com)', url.data) or re.search(r'(zid\.store|zid\.sa)', url.data)):
            raise ValidationError('URL must be from Salla or Zid platforms.')

class URLBatchForm(FlaskForm):
    urls = TextAreaField('Product URLs (one per line)', validators=[DataRequired()])
    submit = SubmitField('Add URLs')
    
class ProductFilterForm(FlaskForm):
    platform = SelectField('Platform', choices=[('all', 'All'), ('salla', 'Salla'), ('zid', 'Zid')], default='all')
    price_min = FloatField('Min Price', validators=[Optional()])
    price_max = FloatField('Max Price', validators=[Optional()])
    sort_by = SelectField('Sort By', choices=[
        ('name', 'Name'), 
        ('price_asc', 'Price (Low to High)'), 
        ('price_desc', 'Price (High to Low)'),
        ('change_asc', 'Price Change % (Low to High)'),
        ('change_desc', 'Price Change % (High to Low)'),
        ('updated', 'Last Updated')
    ], default='updated')
    submit = SubmitField('Apply Filter')

class PriceAlertForm(FlaskForm):
    alert_type = SelectField('Alert Type', choices=[
        ('below', 'Price drops below'),
        ('above', 'Price rises above'),
        ('percentage_change', 'Price changes by percentage')
    ])
    target_price = FloatField('Target Price', validators=[Optional()])
    percentage_threshold = FloatField('Percentage Change (%)', validators=[Optional()])
    submit = SubmitField('Set Alert')

class ScheduleForm(FlaskForm):
    interval = SelectField('Check Interval', choices=[
        ('60', 'Hourly'),
        ('360', 'Every 6 Hours'),
        ('720', 'Every 12 Hours'),
        ('1440', 'Daily'),
        ('10080', 'Weekly'),
    ], default='1440')
    custom_interval = IntegerField('Custom Interval (minutes)', validators=[Optional()])
    submit = SubmitField('Update Schedule')
