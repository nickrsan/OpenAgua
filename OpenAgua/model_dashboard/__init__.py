from flask import Blueprint

model_dashboard = Blueprint('model_dashboard',
                       __name__,
                       template_folder='templates',
                       static_folder='static',
                       static_url_path='/model_dashboard/static')

from . import views
