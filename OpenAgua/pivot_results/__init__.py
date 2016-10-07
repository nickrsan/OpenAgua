from flask import Blueprint

pivot_results = Blueprint('pivot_results',
                          __name__,
                          template_folder='templates',
                          static_folder='static',
                          static_url_path='/pivot_results/static')

from . import views