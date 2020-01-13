from flask import Flask, g
from flask_pymongo import PyMongo
import datetime

# Globally accessible libraries
mongo = PyMongo()

def get_db(app):
        #using mongo here as an extension
        #global object, instantiating
        #mongo = PyMongo() - a pymongo instance
        #initialize extension
        #init_app is a substitute for PyMongo() constructor
        #mongo = mongo.init_app(app)
        mongo = PyMongo(app, uri="mongodb://localhost:27017/stageprod_agg")
        #print("mongo object properly instantiated {}".format(mongo.server_info()))
        #verify proper instantiation
        
        return mongo
    
    
    
def create_app():
    """Initialize the core application. Funct is called from wsgi.py"""
    #must set static_folder to None or blueprint specific static folders will be overriden
    app = Flask(__name__, instance_relative_config=False, static_folder = None)
    app.config.from_object('config.Config') #a class sitting at the top-most directory (config.py); app.config is directory aware 
    
    # Initialize Plugins
    mongo.init_app(app)
    #read more about flask_pymongo: https://buildmedia.readthedocs.org/media/pdf/flask-pymongo/2.3.0/flask-pymongo.pdf
    #mongo2 = get_db(app)
    #db connection est and tested on 12/29/19
    '''print(list(mongo2.db['teststats'].find({'teamname':'LSU', "stats_list": 
    {'$elemMatch': { 'statlabel' : "Passing_Yards_per_Completion", "games_through" : datetime.datetime.strptime("2019-09-07","%Y-%m-%d")}}})))
    
    ''' #turning off for now; worked on 12/29/19
    '''
    @app.route('/')
    def index():
        return "<h1>Hello, World!</h1>"
    '''
    #from . import db
    #db.init_app(app)
    #g['mongo'] = get_db(app)
    #print(list(g['mongo'].db['teststats'].find({'teamname':'LSU', "stats_list": {'$elemMatch': { 'statlabel' : "Passing_Yards_per_Completion", "games_through" : datetime.datetime.strptime("2019-09-07","%Y-%m-%d")}}})))
    with app.app_context():
        #instantiating an application factory (above)
        
        #the above is verified and a connection is est here
        
        #hello_bp is a Blueprint object
        from .home.hello_routes import hello_bp
        
        #case when the landing page is in the same folder as the applicaiton initi; look for a "routes.py"

        # Register Blueprints within context so that scope of all variables includes the runtime workspace of these blueprints
        app.register_blueprint(hello_bp)
        
    return app
