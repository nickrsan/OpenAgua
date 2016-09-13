from flask_sqlalchemy import SQLAlchemy
from flask_user import UserMixin

db = SQLAlchemy()

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
    organization = db.Column(db.String(100), nullable=False, server_default='')
    
    # Meta information
    new_user = db.Column(db.Boolean(), nullable=False, server_default='1')

    # Relationships
    roles = db.relationship('Role', secondary='user_roles',
            backref=db.backref('users', lazy='dynamic'))

class Role(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

class UserRoles(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('role.id', ondelete='CASCADE'))
    
# Hydra Server settings

class HydraUrl(db.Model):
    __tablename__ = 'hydraurl'
    id = db.Column(db.Integer(), primary_key=True)
    hydra_url = db.Column(db.String(255), nullable=False)

class HydraUser(db.Model):
    #id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), primary_key=True)
    hydra_url_id = db.Column(db.Integer(), db.ForeignKey('hydraurl.id'), primary_key=True)
    hydra_userid = db.Column(db.Integer(), nullable=False, primary_key=True)
    hydra_username = db.Column(db.String(50), nullable=False)
    hydra_password = db.Column(db.String(255), nullable=False)
    hydra_sessionid = db.Column(db.String(255), nullable=False, server_default='')
    
#class UserHydra(db.Model):
    #id = db.Column(db.Integer(), primary_key=True)
    #user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    #hydra_url_id = db.Column(db.Integer(), db.ForeignKey('hydraurl.id', ondelete='CASCADE'))
    #hydra_user_id = db.Column(db.Integer(), db.ForeignKey('hydrauser.id', ondelete='CASCADE'))
    
