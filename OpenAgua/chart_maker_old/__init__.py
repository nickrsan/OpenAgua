from flask import Blueprint

chart_maker = Blueprint('chart_maker',
                       __name__,
                       template_folder='templates',
                       static_folder='static',
                       static_url_path='/chart_maker/static')

from . import views
