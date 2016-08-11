import os

# app.py or app/__init__.py
from flask import Flask

# import blueprints
from .user_projects import user_projects
from .user_home import user_home
from .network_editor import net_editor
from .model_dashboard import model_dashboard

app = Flask('OpenAgua', instance_relative_config=True)

app.config.from_object('config')
app.config.from_pyfile('config.py')

import OpenAgua.views

# register blueprints
app.register_blueprint(user_home, url_prefix='')
app.register_blueprint(user_projects, url_prefix='')
app.register_blueprint(net_editor, url_prefix='')
app.register_blueprint(model_dashboard, url_prefix='')
