import os

DEBUG = False
HYDRA_URL = 'http://127.0.0.1:8080/json'
HYDRA_USERNAME = 'root'
HYDRA_PASSWORD = ''
HYDRA_PROJECT_NAME = 'Monterrey'
HYDRA_NETWORK_NAME = 'base_network'
HYDRA_TEMPLATE_NAME = 'WEAP'
SECRET_KEY = '\xef0d\xd8\xb3\xcd\xb0\x04u\x05\x12\xc64\x1d\x00Ld\x8bh\xd5\x81+a\x00'
SQLALCHEMY_DATABASE_URI = 'sqlite:///users.sqlite'

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
HYDRA_APPS_DIR = os.path.join(APP_ROOT, 'hydra_apps')

# Flask-User settings
USER_APP_NAME = "OpenAguaDSS"
USER_LOGIN_TEMPLATE  = 'admin/signin.html'
USER_REGISTER_TEMPLATE = 'admin/register.html'
#USER_CHANGE_PASSWORD_TEMPLATE = 'change_password.html'
#USER_PROFILE_TEMPLATE = 'user_profile.html'
#USER_MANAGE_EMAILS_TEMPLATE = 'manage_emails.html'
#USER_FORGOT_PASSWORD_TEMPLATE = 'forgot_password.html'
#USER_CHANGE_USERNAME_TEMPLATE = 'change_username.html'
#USER_INVITE_TEMPLATE = 'invite.html'
#USER_INVITE_ACCEPT_TEMPLATE = 'register_accept.html'
#USER_RESET_PASSWORD_TEMPLATE = 'reset_password.html'
USER_AFTER_LOGIN_ENDPOINT = 'user_home.home'
USER_AFTER_LOGOUT_ENDPOINT = 'index'
#USER_AFTER_RESET_PASSWORD_ENDPOINT = 'special_page'
#USER_AFTER_REGISTER_ENDPOINT = 'special_page'
#USER_AFTER_CHANGE_PASSWORD_ENDPOINT = 'special_page'
#USER_AFTER_CHANGE_USERNAME_ENDPOINT = 'special_page'

USER_ENABLE_CHANGE_PASSWORD = True  # Allow users to change their password
USER_ENABLE_CHANGE_USERNAME = False  # Allow users to change their username
USER_ENABLE_CONFIRM_EMAIL = True  # Force users to confirm their email
USER_ENABLE_FORGOT_PASSWORD = True  # Allow users to reset their passwords
USER_ENABLE_EMAIL = True  # Register with Email
USER_ENABLE_REGISTRATION = True  # Allow new users to register
USER_ENABLE_RETYPE_PASSWORD = True  # Prompt for `retype password` in:
USER_ENABLE_USERNAME = True  # Register and Login with username
