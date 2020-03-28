"""App configuration."""
from os import environ


class Config:
    """Set Flask configuration vars from .env file."""

    # General Config
    SECRET_KEY = 'youwillneverguess'
    TESTING = True
    ENV = 'development'
    EXPLAIN_TEMPLATE_LOADING = True

    # Flask-Assets
    '''
    LESS_BIN = environ.get('LESS_BIN')
    ASSETS_DEBUG = environ.get('ASSETS_DEBUG')
    LESS_RUN_IN_DEBUG = environ.get('LESS_RUN_IN_DEBUG')
    '''

    # Static Assets
    '''
    STATIC_FOLDER = environ.get('STATIC_FOLDER')
    TEMPLATES_FOLDER = environ.get('TEMPLATES_FOLDER')
    COMPRESSOR_DEBUG = environ.get('COMPRESSOR_DEBUG')
    '''
    #Database
    #MONGO_URI = "mongodb://localhost:27017/stageprod_agg"
    #flask configuration variable
    MONGO_URI = "mongodb+srv://luis-owner:persyy1981@cluster0-rpjy6.mongodb.net/stageprod_agg?retryWrites=true&w=majority"
    
  
    
