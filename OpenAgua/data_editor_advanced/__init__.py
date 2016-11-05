from flask import Blueprint

data_editor_advanced = Blueprint('data_editor_advanced',
                          __name__,
                          template_folder='templates',
                          static_folder='static',
                          static_url_path='/data_editor_advanced/static')

from . import views