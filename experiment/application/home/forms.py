from flask_wtf import FlaskForm
from wtforms import RadioField, BooleanField, SubmitField, StringField, SelectField, Form

''' This contains all the elements of the web form, and will connect to the login.html protocol saved in the tamplates folder '''

class MainMenuForm(FlaskForm):
#notice that we are extending FlaskForm in the above class constructor
    #teamlist = sorted(list(app.mongo['stageprod_agg']['teststats'].distinct('teamname')))
    #convert list to a list of tuples
    #team_tups = [(i,val) for i, val in enumerate(lista,1)]
    #the below are subclasses with their own attributes, which we invoke in the login.html template
    #team1_selection=StringField('Opponent 1')
    #team2_selection=StringField('Opponent 2')
    team1_selection = SelectField(choices = [('UM','UM'),('BYU','BYU'),('UCI','UCI')])
    team2_selection = SelectField(choices = [('UM','UM'),('BYU','BYU'),('UCI','UCI')])
    #str_selection=StringField('Activity', validators=[DataRequired])
    submit = SubmitField('Submit')

