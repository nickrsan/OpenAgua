import os

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

DEBUG = False
HYDRA_URL = 'http://127.0.0.1:8080/json'
HYDRA_ROOT_USERNAME = 'root'
HYDRA_ROOT_PASSWORD = ''
SECRET_KEY = 'a deep, dark secret'
SECRET_ENCRYPT_KEY = b'3SmE-pwbieJubimO2BM15nzAqxD6TTijeFrSAgwOZVU='
SQLALCHEMY_DATABASE_URI = 'sqlite:///{}/instance/users.sqlite'.format(APP_ROOT)

PYOMO_APP_PATH = os.path.join(APP_ROOT, 'pyomo_model', 'main.py')
PYOMO_CHECK_PATH = os.path.join(APP_ROOT, 'pyomo_model', 'utils.py')
PYOMO_APP_NAME = 'OpenAguaModel'
TEMPLATE_FILE = os.path.join(APP_ROOT,
                             'OpenAgua/static/hydra/templates/OpenAgua.zip')
SOLVER = "glpk"

# Flask-Security settings
SECURITY_FLASH_MESSAGES = True
SECURITY_PASSWORD_HASH = 'sha256_crypt'
SECURITY_PASSWORD_SALT = 'salty'
SECURITY_EMAIL_SENDER = 'no-reply@gmail.com'
#SECURITY_TOKEN_AUTHENTICATION_KEY
#SECURITY_TOKEN_AUTHENTICATION_HEADER

SECURITY_POST_REGISTER_VIEW = 'index'
SECURITY_POST_LOGIN_VIEW = 'user_home.home'
SECURITY_POST_CONFIRM_VIEW = 'user_home.home'

SECURITY_CONFIRMABLE = True
SECURITY_REGISTERABLE = True
SECURITY_RECOVERABLE = True
SECURITY_TRACKABLE = False
SECURITY_PASSWORDLESS = False
SECURITY_CHANGEABLE = True

SECURITY_LOGIN_WITHOUT_CONFIRMATION = False

SQLALCHEMY_TRACK_MODIFICATIONS = False