'''
Dash practice... provision Dash with a Flask server 
'''
#import testDashToDelete
#import basicBuildEvolved
import dropdownAppConstruction_flask_dashserver_TESTING_callbackFunct
import os
from flask import Flask, redirect, url_for
        
server = Flask(__name__)
app = dropdownAppConstruction_flask_dashserver_TESTING_callbackFunct.controller(server)
#app = basicBuildEvolved.controller(server)


#specify the port
port = int(os.environ.get("PORT",5000))

'''
@app.route('/')
def hello():
    return
'''
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port = port)
    #app.run_server(host='0.0.0.0', debug=True, port = port)
