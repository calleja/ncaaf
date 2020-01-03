Issues:

1) CSRF of forms requires SECRET_KEY: for some reason, my app does not see the secret key despite it being defined in the .env file

2) Unable to persist the mongo object despite instantiating it in __init__.py and importing current_app. Need to learn the scope of current_app and potentially need to identify how to persist flask-mongo objects in a app factory/blueprint framework
