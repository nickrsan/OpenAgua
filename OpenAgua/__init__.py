import os

# app.py or app/__init__.py
from flask import Flask, session
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_user import login_required, UserManager, UserMixin, SQLAlchemyAdapter
from flask_login import current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.base import MenuLink

# import blueprints
from .user_projects import user_projects
from .user_home import user_home
from .data_editor import data_editor
from .network_editor import net_editor
from .main_overview import main_overview
from .model_dashboard import model_dashboard
from .chart_maker import chart_maker

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
# Define the User data model. Make sure to add flask.ext.user UserMixin!!
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
    first_name = db.Column(db.String(100), nullable=False, server_default='')
    last_name = db.Column(db.String(100), nullable=False, server_default='')

    # Relationships
    roles = db.relationship('Role', secondary='user_roles',
            backref=db.backref('users', lazy='dynamic'))


# Define the Role data model
class Role(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

# Define the UserRoles data model
class UserRoles(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('role.id', ondelete='CASCADE'))

# Create all database tables
db.create_all()

# Setup Flask-User
db_adapter = SQLAlchemyAdapter(db, User)        # Register the User model
user_manager = UserManager(db_adapter, app)    # Initialize Flask-User

# Create admin user
#username = app.config['ADMIN_USERNAME']
#email = app.config['ADMIN_EMAIL']
#password = app.config['ADMIN_PASSWORD']
#if not User.query.filter(User.username==username).first():
    #administrator = User(username=username, email=email, active=True,
                         #password=user_manager.hash_password(password))
    #administrator.roles.append(Role(name='admin'))
    #db.session.add(administrator)
    #db.session.commit()

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
app.register_blueprint(data_editor, url_prefix='')
app.register_blueprint(net_editor, url_prefix='')
app.register_blueprint(model_dashboard, url_prefix='')
app.register_blueprint(chart_maker, url_prefix='')

# ============
# set up admin
# ============

admin = Admin(app, name='OpenAgua', template_mode='bootstrap3')

class UserView(ModelView):
    
    column_exclude_list = ['password', ]
    column_searchable_list = ['username', 'email']
    
    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role('admin') or current_user.has_role('superuser'):
            return True

    def inaccessible_callback(self, name, **kwargs):
        if current_user.is_authenticated:
            abort(403) # permission denied
        else:
            return redirect(url_for('login', next=request.url)) # divert to login 
        
class RoleView(ModelView):
    
    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role('admin') or current_user.has_role('superuser'):
            return True

    def inaccessible_callback(self, name, **kwargs):
        if current_user.is_authenticated:
            abort(403) # permission denied
        else:
            return redirect(url_for('login', next=request.url)) # divert to login 
    
# Add administrative views here
admin.add_view(UserView(User, db.session))
admin.add_view(RoleView(Role, db.session))

# Add menu links
admin.add_link(MenuLink(name='Sign out', url='/user/sign-out'))

## define a context processor for merging flask-admin's template context into the
## flask-security views.
#@security.context_processor
#def security_context_processor():
    #return dict(
        #admin_base_template=admin.base_template,
        #admin_view=admin.index_view,
        #h=admin_helpers,
        #get_url=url_for
    #)