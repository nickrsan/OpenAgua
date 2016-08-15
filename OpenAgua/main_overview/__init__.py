from flask import Blueprint

main_overview = Blueprint('main_overview',
                       __name__,
                       template_folder='templates',
                       static_folder='static',
                       static_url_path='/main_overview/static')

from . import views
