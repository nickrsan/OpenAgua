from flask import Blueprint

basic_results = Blueprint('basic_results',
                          __name__,
                          template_folder='templates',
                          static_folder='static',
                          static_url_path='/basic_results/static')

from . import views