from flask import Blueprint

study_overview = Blueprint('study_overview',
                       __name__,
                       template_folder='templates',
                       static_folder='static',
                       static_url_path='/study_overview/static')

from . import views
