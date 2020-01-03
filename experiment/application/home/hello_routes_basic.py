from .forms import MainMenuForm
from flask import Blueprint, render_template, flash, redirect, request, session, url_for, make_response, current_app
from datetime import datetime
import numpy as np
import os
import pymongo
from wtforms import RadioField, BooleanField, SubmitField, StringField, SelectField, Form
#from app import mongo

hello_bp = Blueprint('hello_bp', __name__,
                     template_folder='templates')

@hello_bp.route('/',methods=['GET','POST'])
def index():
        return "<h1>Hello, World!</h1>"
