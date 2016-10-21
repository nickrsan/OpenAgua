from collections import OrderedDict

from flask import session, redirect, url_for, render_template, request, g
from flask_security import login_required, current_user
from flask_babel import refresh

from OpenAgua import app, babel

from .connection import connection

app.secret_key = app.config['SECRET_KEY']

# Internationalization / localization
from config import LANGUAGES
@babel.localeselector
def get_locale():
    return session['language']

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home.home_main'))
    else:
        if '_fresh' not in session:
            session['language'] = request.accept_languages.best_match(LANGUAGES.keys())
        languages = OrderedDict(sorted(LANGUAGES.items()))
        return render_template('index.html', languages=languages)

@app.route('/_change_locale')
def change_locale():
    session['language'] = request.args.get('locale')
    refresh()
    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


