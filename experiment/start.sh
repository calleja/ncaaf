# start.sh: a shell script for unlix/linux... to execute, simply type out the filepath into a shell command line

export FLASK_APP=wsgi.py
export FLASK_DEBUG=1
export APP_CONFIG_FILE=config.py
flask run
