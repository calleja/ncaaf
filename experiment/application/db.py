from flask_pymongo import PyMongo

from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    #notice how the connection is preserved as an attribute to g. A new conection to the db is est only if one is not open and attached to g
    if 'db' not in g:
        g.db = PyMongo(current_app, uri="mongodb://localhost:27017/stageprod_agg")
        #MONGO_URI = "mongodb://localhost:27017/stageprod_agg"
        #g.db.row_factory = sqlite3.Row
        
        ''' source code:
        def get_db():
            if 'db' not in g:
            g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        
        context:  sqlite3.connect(database[, timeout, detect_types, isolation_level, check_same_thread, factory, cached_statements, uri])¶
        ''' 
        
        #print("mongo object properly instantiated {}".format(mongo.server_info()))
        #verify proper instantiation
        
    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()
