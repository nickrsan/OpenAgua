from flask import Blueprint

projects_manager = Blueprint('projects_manager',
                             __name__,
                             template_folder='templates',
                             static_folder='static',
                             static_url_path='/projects_manager/static')

from . import views
