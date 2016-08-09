# app.py or app/__init__.py
from flask import Flask

# import blueprints
from .projects_manager import projects
from .network_editor import net_editor
from .model_dashboard import model_dashboard

app = Flask(__name__, instance_relative_config=True)

app.config.from_object('config')
app.config.from_pyfile('config.py')

import OpenAgua.views

# register blueprints
app.register_blueprint(projects, url_prefix='')
app.register_blueprint(net_editor, url_prefix='')
app.register_blueprint(model_dashboard, url_prefix='')
