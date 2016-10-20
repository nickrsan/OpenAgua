from flask import session, redirect, url_for, render_template, request, g
from flask_security import login_required, current_user

from OpenAgua import app, babel

from .connection import connection

app.secret_key = app.config['SECRET_KEY']

# Internationalization / localization
from config import LANGUAGES
@babel.localeselector
def get_locale():
    user = getattr(g, 'user', None)
    if user is not None:
        return user.locale    
    return request.accept_languages.best_match(LANGUAGES.keys())

@app.route('/')
def index():    
    if current_user.is_authenticated:
        return redirect(url_for('home.home_main'))
    else:
        return render_template('index.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


