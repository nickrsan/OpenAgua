# -*- coding: utf-8 -*-

import os

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

DEBUG = False
SECRET_KEY = 'a deep, dark secret'
SECRET_ENCRYPT_KEY = b'3SmE-pwbieJubimO2BM15nzAqxD6TTijeFrSAgwOZVU='
SQLALCHEMY_DATABASE_URI = 'sqlite:///{}/instance/users.sqlite'.format(APP_ROOT)

# Hydra Server settings
HYDRA_URL = 'http://127.0.0.1:8080/json' # to be stored with hydra user
HYDRA_ROOT_USERNAME = 'root' # to be stored privately; this is okay for local machines
HYDRA_ROOT_PASSWORD = ''

# Other Hydra Server-related settings
HYDRA_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f000Z' # must be the same as in hydra.ini
#HYDRA_DATETIME_FORMAT = '%Y-%m-%d' # must be the same as in hydra.ini
HYDRA_SEASONAL_YEAR = 9999 # not used yet
DEFAULT_HYDRA_TEMPLATE = 'OpenAgua'
DEFAULT_SCENARIO_NAME = 'Baseline'
UPLOADED_TEMPLATES_DEST = os.path.join(APP_ROOT, 'OpenAgua/static/hydra/templates')

# user files
USER_FILES = 'userfiles'

# OpenAgua settings
MONTH_FORMAT = '%m/%Y'
TIMESTEP_FORMAT = '%m/%Y'
AMCHART_DATE_FORMAT = 'MM/YYYY'

# Pyomo app settings
PYOMO_APP_PATH = os.path.join(APP_ROOT, 'pyomo_model', 'main.py')
PYOMO_CHECK_PATH = os.path.join(APP_ROOT, 'pyomo_model', 'checker.py')
PYOMO_APP_NAME = 'OpenAgua'
SOLVER = "glpk"
FORESIGHT = 'perfect' # to be set by user
TEMP_TI = '01/2000'
TEMP_TF = '12/2019'

# Flask-Security settings
SECURITY_FLASH_MESSAGES = True
SECURITY_PASSWORD_HASH = 'sha256_crypt'
SECURITY_PASSWORD_SALT = 'salty'
SECURITY_EMAIL_SENDER = 'no-reply@gmail.com'

SECURITY_POST_REGISTER_VIEW = 'index'
SECURITY_POST_LOGIN_VIEW = 'home.home_main'
SECURITY_POST_CONFIRM_VIEW = 'home.account_setup'

SECURITY_CONFIRMABLE = True
SECURITY_REGISTERABLE = True
SECURITY_RECOVERABLE = True
SECURITY_TRACKABLE = False
SECURITY_PASSWORDLESS = False
SECURITY_CHANGEABLE = True

SECURITY_LOGIN_WITHOUT_CONFIRMATION = False

SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask-Babel options
LANGUAGES = {
    'en': 'English',
    'es': 'Español',
    'zh_Hans': '中文（简体）',
    'zh_Hant': '中文（繁體）',
    'fr': 'Français',
    'de': 'Deutsch',
    'ru': 'русский',
    'it': 'Italiano',
    'hi': 'हिंदी',
    'ar': 'العربية',
    'pt': 'Português',
    'fa': 'فارسی',
    'ja': '日本語',
    'am': 'አማርኛ',
}

#paths

CHART_THUMBNAILS_PATH = os.path.join('thumbnails', 'charts')

#other options

DEFAULT_CHART_RENDERER = 'plotly'  # options: plotly, gchart