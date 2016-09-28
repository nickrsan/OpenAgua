from flask import Blueprint

results_explorer = Blueprint('results_explorer',
                          __name__,
                          template_folder='templates',
                          static_folder='static',
                          static_url_path='/results_explorer/static')

from . import views