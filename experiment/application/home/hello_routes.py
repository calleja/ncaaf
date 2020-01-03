from .forms import MainMenuForm
from flask import Blueprint, render_template, flash, redirect, request, session, url_for, make_response, current_app, g
from datetime import datetime
import numpy as np
import os
import pymongo
from wtforms import RadioField, BooleanField, SubmitField, StringField, SelectField, Form
from application.db import get_db
from application import mongo

#name of Blueprint obj = "hello_bp"
hello_bp = Blueprint('hello_bp', __name__,
                     template_folder='templates')

#access the mongodb via app.mongo
@hello_bp.route('/',methods=['GET','POST'])
def landing():
    #render templates /home/landingPage.html; as explained at the bottom: https://flask.palletsprojects.com/en/1.0.x/blueprints/
    def get_db_connection():
        con = getattr(g, 'mongo', None)
        if con is None:
            g.con = con = connection_pool.get_connection()
        return con
    
    #db = get_db()
    form = MainMenuForm(csrf_enabled=False)
    assert form is not None, "MainMenuForm object is none"
    assert form.team1_selection is not None, "form object doesn't contain team1_selection attribute"
    assert type(form.team1_selection) is SelectField, "team1 selection is not a field object"
    #in order for current_app to be available, a request must have been issued... app_context must be instantiated... should test whether it's available somewhere in code... KIM ea request gets its own application context. The app_context can stand on its own w/o the request context
    teamlist = sorted(list(mongo.db['teststats'].distinct('teamname')))
    #convert list to a list of tuples
    team_tups = [(i,val) for i, val in enumerate(teamlist,1)]
    form.team2_selection.choices = team_tups
    form.team1_selection.choices = team_tups
    return(render_template('/home/landingPage.html', form = form))
    #return("Hello World")

