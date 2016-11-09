from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin

from OpenAgua import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    new_user = db.Column(db.Boolean(), server_default='1')

    # other info
    firstname = db.Column(db.String(50))
    lastname = db.Column(db.String(50))
    organization = db.Column(db.String(50))
    
    # relationships
    roles = db.relationship('Role', secondary='user_roles', backref=db.backref('users', lazy='dynamic'))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class UserRoles(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    User_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    Role_id = db.Column(db.Integer(), db.ForeignKey('role.id', ondelete='CASCADE'))
    
# Hydra user objects

class HydraUser(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    hydra_url_id = db.Column(db.Integer(), db.ForeignKey('hydra_url.id', ondelete='CASCADE'))
    hydra_userid = db.Column(db.Integer(), nullable=False)
    hydra_username = db.Column(db.String(50), nullable=False)
    hydra_password = db.Column(db.String(255), nullable=False)
    hydra_sessionid = db.Column(db.String(255), nullable=False, server_default='')

class HydraUrl(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    url = db.Column(db.String(255), nullable=False)
    
class Study(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False, server_default='')
    hydra_user_id = db.Column(db.Integer(), db.ForeignKey('hydra_user.id', ondelete='CASCADE'))
    project_id = db.Column(db.Integer(), nullable=False)
    network_id = db.Column(db.Integer(), nullable=False)
    template_id = db.Column(db.Integer(), nullable=False)
    active = db.Column(db.Boolean(), nullable=False)
    
    # relationships
    charts = db.relationship('Chart', backref='study', lazy='dynamic')
    inputsetups = db.relationship('InputSetup', backref='study', lazy='dynamic')
    
# User-saved objects

class Chart(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    study_id = db.Column(db.Integer(), db.ForeignKey('study.id', ondelete='CASCADE'))
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(255), server_default='')
    thumbnail = db.Column(db.String(255), nullable=False)
    filters = db.Column(db.Text(), nullable=False)
    setup = db.Column(db.Text(), nullable=False)
    
class InputSetup(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    study_id = db.Column(db.Integer(), db.ForeignKey('study.id', ondelete='CASCADE'))
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(255), server_default='')
    filters = db.Column(db.Text(), nullable=False)
    setup = db.Column(db.Text(), nullable=False)
    
    