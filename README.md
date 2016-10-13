This describes how to set up and run OpenAgua, including configuration settings.

See details of technologies used see the [OpenAgua wiki](https://github.com/CentroDelAgua/OpenAgua/wiki). Website use documentation is forthcoming.

# Setup/run on local machine

These setup instructions are general, for both Windows and Linux. This is untested on OSX, but presumably setup should be similar to that for Linux.

OpenAgua connects to Hydra Platform. So, Hydra Platform needs to be available, either locally or remotely. This assumes Hydra Platform will be run locally. In this case, the first step is to make sure Hydra Platform is running, after which OpenAgua may be run.

**IMPORTANT**: For the time being, even a local setup requires an internet connection, to load externally-hosted JavaScript libraries. This will change in the future.

## Hydra Platform
* [general Hydra Platform information] (www.hydraplatform.org),
* [download from GitHub] (https://github.com/UMWRG/HydraPlatform), or
* [set up on Windows] (http://umwrg.github.io/HydraPlatform/tutorials/getting-started/server.html)
* **IMPORTANT**: Hydra Platform requires Python 2.7, but OpenAgua requires Python 3.5. This needs to be accounted for, either by changing batch file scripts used to run the respective applications, or setting up virtual environments. On Windows, for example, if Python 3.5 is your main Python, you can change the second-to-last line of *run_server.bat* (found in `/Hydra Platform/Hydra Server/`) to something like `C:\python27\python server.py`, depending on where Python 2.7 is installed.

## OpenAgua

### Install

OpenAgua was built on Python 3.5, so this should be installed first. Earlier versions of Python 3 might also work, but there's no guarantee. Other requirements follow.

__All platforms__:

All platforms require the following Python modules (version numbers are for reference based on existing setup; other versions may work too):
```
attrdict (2.0.0)
cryptography (1.5)
flask (0.11.1)
flask_admin (1.4.2)
flask_babel (0.11.1)
flask_migrate (2.0.0)
flask_script (2.0.5)
flask_security (1.7.5)
flask_sqlalchemy (2.1.1)
flask_uploads (0.2.1)
pandas (0.18.1)
pymysql (0.7.9)
pyomo (4.4.1)
python_dateutil (2.5.3)
requests (2.11.1)
webcolors (1.5)
```

__Windows-specific__:

No specific issues.

__Linux-specific__:

Two potential issues exist, but others may also exist (consult Google if troubles arise, and let us know so we can document the issues here!):

1. *pip3* should be used instead of *pip* (for installing Python 3.x modules). At least on Amazon's default Ubuntu, *pip3* is not installed by default, so this should be installed: `sudo apt-get install pip3`.

2. Encryption-related modules may need to be compiled during installation. Consult the Internet if trouble arises.

### Modify settings

Settings are found in the top-level config.py. An explanation of all settings is found below.

There are a few settings that should be set on a machine-specific basis, whether on a local machine or on a web server. These are stored in a folder called "instance" under the top-level OpenAgua folder:

1. Create an "/instance" folder. This folder stores machine-specific settings and the user database.
2. In "/instance", create "config.py". This new file contains settings that will supercede settings in the main "config.py". For example, you can overwrite default debug settings, as: `DEBUG=True`.
3. At a minimum, set the following parameters (values are examples only; your settings may be different):
```
# Flask-Mail settings
MAIL_USERNAME = 'admin@mysite.com'
MAIL_PASSWORD = 'password'
MAIL_SERVER = 'smtp.mysite.com'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USE_TLS = False
```
NB: This assumes email confirmation is needed. However, if a local machine is used, email confirmation can be switched off with `SECURITY_LOGIN_WITHOUT_CONFIRMATION = True` in config.py (This needs to be confirmed!).

Optionally, set other parameters as desired. For example, the OpenAgua user database (`SQLALCHEMY_DATABASE_URI`) can be specified here. For SQLite, see the example in the default config.py file. For MySQL: `mysql+pymysql://username:password@xxxxx.xxxxx.com/dbname`.

Note that SECRET_KEY can be created in Python with the urandom function in the os module. I.e. `import os` followed by `os.urandom(24)`. IMPORTANT: This should be set in `\instance\config.py` in a production environment! 

### Create user database

To create the initial user database, from the main OpenAgua directory, execute the following commands sequentially:

1. `python manage.py db init`
2. `python manage.py db migrate`
3. `python manage.py db upgrade`

### Create admin user

To create an admin user, from the main OpenAgua directory execute `python manage.py addsuperuser`. You will then be prompted to add an email address and password for the account. If you want to cancel the process, just hit enter a few times to exit.

## Run

1. Run Hydra Platform, or make sure HYDRA_URL points to a working Hydra Platform server (Hydra Server).
2. Run OpenAgua/run.py (`python run.py`, or `run.bat` on Windows)
3. Go to http://127.0.0.1:5000 in your web browser.
4. Register and/or login. Note that internet access is required during registration, as an email confirmation is sent for confirmation during the process.

# Setup/serve as web server

This assumes Hydra Platform and OpenAgua are run from the same Ubuntu Linux machine, and where OpenAgua is served to the world by uwsgi+nginx.

## Hydra Platform

1. Install Hydra Platform and dependencies as described at https://github.com/UMWRG/HydraPlatform#hydraplatform. Some pointers for installing on Ubuntu:
* For mysql-connector-python: `sudo apt-get install python-mysql.connector`
* For bcrypt, make sure to install python-dev first: `sudo apt-get install python-dev`
2. Specify the database that Hydra Platform will use in /HydraPlatform/config/hydra.ini. By default this is a local SQLite database, but any SQL database can be used, such as MySQL, which is what OpenAguaDSS.org uses.
3. Decide on hosting configuration. Hydra Platform comes with its own web interface, so can be configured either as a server available only to the local machine (which OpenAgua can still access), or as a public web server with the built-in user interface exposed to the world.
a. If a non-public server is used, follow step 4. on https://github.com/UMWRG/HydraPlatform#installation to run the server: `chmod +x run_server.sh i(i. ./run_server.sh`.
b. If a public server is used, Apache2 needs to be configured as described below.

## OpenAgua

1. Install OpenAgua using git: From /var/www type `sudo git clone https://github.com/CentroDelAgua/OpenAgua.git`
2. Set up /instance/config.py. In addition to the settings as described above, make sure to add:
  * HYDRA_URL (e.g., `HYDRA_URL = 'http://hydra-server.mysite.com/json'`)
  * SECRET_KEY
3. Change the owner of the instance folder to allow the web server to create/modify the user database (users.sqlite). From the main OpenAguaDSS folder, type `sudo chown www-data:www-data instance`. www-data is the Apache2 user, and would be different for other web servers.
4. Set up Apache2, as described below.

## uwsgi + nginx

[To be completed]

# Settings

[To be completed]
















