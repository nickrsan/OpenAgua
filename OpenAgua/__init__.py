import os

# app.py or app/__init__.py
from flask import Flask
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_user import login_required, UserManager, UserMixin, SQLAlchemyAdapter

# import blueprints
from .user_projects import user_projects
from .user_home import user_home
from .network_editor import net_editor
from .main_overview import main_overview
from .model_dashboard import model_dashboard

app = Flask('OpenAgua', instance_relative_config=True)

app.config.from_object('config')
app.config.from_pyfile('config.py')

# ============
# set up users
# ============

# Initialize Flask extensions
db = SQLAlchemy(app)                            # Initialize Flask-SQLAlchemy
mail = Mail(app)                                # Initialize Flask-Mail

# Define the User data model. Make sure to add flask.ext.user UserMixin !!!
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    # User authentication information
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    reset_password_token = db.Column(db.String(100), nullable=False, server_default='')

    # User email information
    email = db.Column(db.String(255), nullable=False, unique=True)
    confirmed_at = db.Column(db.DateTime())

    # User information
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='0')

# Create all database tables
db.create_all()

# Setup Flask-User
db_adapter = SQLAlchemyAdapter(db, User)        # Register the User model
user_manager = UserManager(db_adapter, app)     # Initialize Flask-User

# ====================
# Load top-level views
# ====================

import OpenAgua.views

# ===================
# register blueprints
# ===================

app.register_blueprint(user_home, url_prefix='')
app.register_blueprint(user_projects, url_prefix='')
app.register_blueprint(main_overview, url_prefix='')
app.register_blueprint(net_editor, url_prefix='')
app.register_blueprint(model_dashboard, url_prefix='')