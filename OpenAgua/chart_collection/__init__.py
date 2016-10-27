from flask import Blueprint

chart_collection = Blueprint('chart_collection',
                          __name__,
                          template_folder='templates',
                          static_folder='static',
                          static_url_path='/chart_collection/static')

from . import views