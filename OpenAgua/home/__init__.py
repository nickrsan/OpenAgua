from flask import Blueprint

user_home = Blueprint('user_home',
                       __name__,
                       template_folder='templates',
                       static_folder='static',
                       static_url_path='/user_home/static')

from . import views
