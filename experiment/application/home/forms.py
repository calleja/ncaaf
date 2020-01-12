from flask_wtf import FlaskForm
from wtforms import RadioField, BooleanField, SubmitField, StringField, SelectField, Form
from wtforms.validators import DataRequired

''' This contains all the elements of the web form, and will connect to the login.html protocol saved in the tamplates folder '''

class MainMenuForm(FlaskForm):
#notice that we are extending FlaskForm in the above class constructor
#coercing is necessary, however, it's indecipherable by the program ...  argument: 
    team1_selection = SelectField('select opponent', validators = [DataRequired()], coerce = int)
    team2_selection = SelectField('select another opponent', validators = [DataRequired()], coerce = int)
    
    submit = SubmitField('Submit')

