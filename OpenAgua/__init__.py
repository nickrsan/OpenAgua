import os
from sys import stderr

# app.py or app/__init__.py
from flask import Flask
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required
from flask_security.forms import RegisterForm, StringField, Required

from flask_login import current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.base import MenuLink

# create the app
app = Flask(__name__, instance_relative_config=True)

app.config.from_object('config')
app.config.from_pyfile('config.py')

# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)

# import models and views
from OpenAgua import models, views

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)

class ExtendedRegisterForm(RegisterForm):
    firstname = StringField('First Name', [Required()])
    lastname = StringField('Last Name', [Required()])
    
security = Security(app, user_datastore,
                    register_form=ExtendedRegisterForm,
                    confirm_register_form=ExtendedRegisterForm)    

import OpenAgua.views

# import blueprints
from .projects_manager import projects_manager
from .home import user_home
from .data_editor import data_editor
from .network_editor import net_editor
from .main_overview import main_overview
from .model_dashboard import model_dashboard
from .results_explorer import results_explorer
from .chart_maker import chart_maker

# register blueprints
app.register_blueprint(user_home, url_prefix='')
app.register_blueprint(projects_manager, url_prefix='')
app.register_blueprint(main_overview, url_prefix='')
app.register_blueprint(data_editor, url_prefix='')
app.register_blueprint(net_editor, url_prefix='')
app.register_blueprint(model_dashboard, url_prefix='')
app.register_blueprint(results_explorer, url_prefix='')
app.register_blueprint(chart_maker, url_prefix='')

# set up admin
admin = Admin(app, name=__name__, template_mode='bootstrap3')

class UserView(ModelView):
    
    column_exclude_list = ['password', ]
    column_searchable_list = ['email']
    
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
admin.add_view(UserView(models.User, db.session))
admin.add_view(RoleView(models.Role, db.session))

# Add menu links
admin.add_link(MenuLink(name='Sign out', url='/logout'))
