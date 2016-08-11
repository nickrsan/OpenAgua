from flask import Blueprint

user_projects = Blueprint('user_projects',
                       __name__,
                       template_folder='templates',
                       static_folder='static',
                       static_url_path='/user_projects/static')

from . import views
