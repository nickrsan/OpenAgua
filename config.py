DEBUG = False
HYDRA_URL = 'http://127.0.0.1:8080/json'
HYDRA_USERNAME = 'root'
HYDRA_PASSWORD = ''
HYDRA_PROJECT_NAME = 'Monterrey'
HYDRA_NETWORK_NAME = 'base_network'
HYDRA_TEMPLATE_NAME = 'WEAP'
SECRET_KEY = '\xef0d\xd8\xb3\xcd\xb0\x04u\x05\x12\xc64\x1d\x00Ld\x8bh\xd5\x81+a\x00'
SQLALCHEMY_DATABASE_URI = 'sqlite:///basic_app.sqlite'

# Flask-User settings
USER_APP_NAME = "OpenAguaDSS"
#USER_LOGIN_TEMPLATE  ='login.html'
#USER_REGISTER_TEMPLATE ='register.html'
#USER_CHANGE_PASSWORD_TEMPLATE ='change_password.html'
#USER_PROFILE_TEMPLATE = 'user_profile.html'
#USER_MANAGE_EMAILS_TEMPLATE = 'manage_emails.html'
#USER_FORGOT_PASSWORD_TEMPLATE = 'forgot_password.html'
#USER_CHANGE_USERNAME_TEMPLATE = 'change_username.html'
#USER_INVITE_TEMPLATE = 'invite.html'
#USER_INVITE_ACCEPT_TEMPLATE = 'register_accept.html'
#USER_RESET_PASSWORD_TEMPLATE = 'reset_password.html'
USER_AFTER_LOGIN_ENDPOINT='user_home.home'
#USER_AFTER_RESET_PASSWORD_ENDPOINT='special_page'
#USER_AFTER_REGISTER_ENDPOINT = 'user.login'
#USER_AFTER_REGISTER_ENDPOINT = 'special_page'
#USER_AFTER_CHANGE_PASSWORD_ENDPOINT  = 'special_page'
#USER_AFTER_CHANGE_USERNAME_ENDPOINT = 'special_page'

# The following Flask-Mail settings should be customized and added to instance/config.py
#MAIL_USERNAME = 'email@example.com'
#MAIL_PASSWORD = 'password'
#MAIL_DEFAULT_SENDER = '"Sender" <noreply@example.com>'
#MAIL_SERVER = 'smtp.gmail.com'
#MAIL_PORT = 465
#MAIL_USE_SSL = True
#MAIL_USE_TLS = False
