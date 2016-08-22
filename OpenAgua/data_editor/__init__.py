from flask import Blueprint

data_editor = Blueprint('data_editor',
                          __name__,
                          template_folder='templates',
                          static_folder='static',
                          static_url_path='/data_editor/static')

from . import views