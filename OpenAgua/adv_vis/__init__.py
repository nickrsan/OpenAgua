from flask import Blueprint

adv_vis = Blueprint('adv_vis',
                       __name__,
                       template_folder='templates',
                       static_folder='static',
                       static_url_path='/adv_vis/static')

from . import views
