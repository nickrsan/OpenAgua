from flask import Blueprint

net_editor = Blueprint('network_editor',
                       __name__,
                       template_folder='templates',
                       static_folder='static',
                       static_url_path='/network_editor/static')

from . import views
