from flask import Blueprint

manager = Blueprint('manager',
                 __name__,
                 template_folder='templates',
                 static_folder='static',
                 static_url_path='/manager/static')

from . import manager
