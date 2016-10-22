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
boltons (16.5.0)
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

This assumes Hydra Platform and OpenAgua are run from the same Ubuntu Linux machine, and where OpenAgua is served to the world by uwsgi+nginx. The general setup process is described, followed by configurations as used on www.openagua.org.

## General process
The setup process can be broken down into the following steps:

1. Install nginx
2. Set up each respective base application (i.e., Hydra Platform and OpenAgua). For each application:
  a. Download the application
  b. Set up a virtual environment
  c. Install required Python packages within the virtual environment
  d. Install uwsgi from within the virtual environment
  e. Configure the application
  f. Create and configure a wsgi.py file to serve the application
  g. Create and configure a uWSGI configuration file
  g. Create and configure an application service
3. Configure nginx
4. Start (restart) each application service
5. Start (restart) nginx

## Setup for www.openagua.org

### 1. [Nginx notes forthcoming]

### 2. Set up each respective application.

#### Hydra Platform

a. Download Hydra Platform from GitHub as described above.

b. For the virtual environment, `virtuanenvwrapper` works well.

c. In the virtual environment for Hydra Platform, install dependencies (using `pip`) as described at https://github.com/UMWRG/HydraPlatform#hydraplatform. Some pointers for installing on Ubuntu:
* For mysql-connector-python: `sudo apt-get install python-mysql.connector`
* For bcrypt, make sure to install python-dev first: `sudo apt-get install python-dev`

d. Install uwsgi. From within the virtual environment: `pip install uwsgi'

e. Configure Hydra Platform:
* Specify the database that Hydra Platform will use in /HydraPlatform/config/hydra.ini.
* Create a new HydraServer folder next to HydraPlatform. This will hold the local configurations for running Hydra Server without affecting the original Hydra Platform.

f. In the case of Hydra Platform wsgi.py can just create a symbolic link directly to Hydra Server. From within the new HydraServer directory:
```
ln -s wsgi.py ../HydraPlatform/HydraServer/server.py
```

g. Create and configure uWSGI configuration file:

Create:
```
sudo nano /home/ubuntu/HydraServer/hydraserver.ini
```

Configure contents:
```
[uwsgi]
wsgi-file = wsgi.py

master = true
processes = 1

socket = hydraserver.sock
chmod-socket = 660
vacuum = true

die-on-term = true

logto = error.log
```
**IMPORTANT**: Processes should increase in the future once Hydra Server supports this. 

h. Create/configure the application service:

Create:
```
sudo nano /etc/systemd/system/hydraserver.service
```

Configure contents:
```
[Unit]
Description=uWSGI instance to serve HydraServer
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/HydraServer
Environment="PATH=/home/ubuntu/Env/hydraserver/bin"
Environment="PYTHONPATH=${PYTHONPATH}:/home/ubuntu/HydraPlatform/HydraLib/python:/home/ubuntu/HydraPlatform/HydraServer/python"
ExecStart=/home/ubuntu/Env/hydraserver/bin/uwsgi --ini hydraserver.ini

[Install]
WantedBy=multi-user.target
```

i. Create/configure the nginx site:

Create:
```
sudo nano /etc/nginx/sites-available/hydraplatform
```

Configure contents:
```
server {
    listen 80;
    listen [::]80;
    server_name hydra.openagua.org;

    location / {
        include uwsgi_params;
        uwsgi_pass unix:/home/ubuntu/HydraServer/hydraserver.sock;
    }
}

```

Enable site with a symbolic link:
```
sudo ln -s /etc/nginx/sites-available/hydraplatform /etc/nginx/sites-enabled/hydraplatform
```

#### OpenAgua

a. Install OpenAgua using git: From /var/www type `sudo git clone https://github.com/CentroDelAgua/OpenAgua.git`

b. Set up virtual environment

c. Install packages

d. Install uwsgi

e. Configure the application [OBSOLETE - TO BE UPDATED]:
* Set up /instance/config.py. In addition to the settings as described above, make sure to add:
        * HYDRA_URL (e.g., `HYDRA_URL = 'http://hydra-server.mysite.com/json'`)
        * SECRET_KEY

f. wsgi.py:

Create:
```
nano /home/ubuntu/OpenAgua/wsgi.py
```

Configure:
```
from OpenAgua import app

if __name__ == "__main__":
    app.run()
```

g. wsgi service configuration:

Create:
```
nano /home/ubuntu/OpenAgua/openagua.ini
```

Configure:
```
[uwsgi]
module = wsgi:app

master = true
processes = 5

socket = openagua.sock
chmod-socket = 660
vacuum = true

die-on-term = true

logto = instance/error.log
```

h. System service:

Create:
```
sudo nano /etc/systemd/system/openagua.service
```
Configure:
```
[Unit]
Description=uWSGI instance to serve OpenAgua
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/OpenAgua
Environment="PATH=/home/ubuntu/Env/openagua/bin"
ExecStart=/home/ubuntu/Env/openagua/bin/uwsgi --ini openagua.ini

[Install]
WantedBy=multi-user.target
```

i. nginx site:

Create:
```
sudo nano /etc/nginx/sites-available/openagua
```

Configure:
```
server {
    listen 80;
    listen [::]80;
    server_name test.openagua.org;

    location / {
        include uwsgi_params;
        uwsgi_pass unix:/home/ubuntu/OpenAgua/openagua.sock;
    }
}
```

Enable:
```
sudo ln -s /etc/nginx/sites-available/openagua /etc/nginx/sites-enabled/openagua
```

3. Start (restart) the application services:

Hydra Platform:
```
sudo systemctl start hydraserver.service
```

OpenAgua:
```
sudo systemctl start openagua.service
```

4. Start (restart) nginx:

[TO BE DOCUMENTED]

5. Update the website & services as needed.

a. GitHub contents can be easily updated. From within OpenAgua: `git pull`

b. The web applications can also be easily restarted: E.g.:
```
sudo systemctl restart openagua.service
```

There is no need to restart nginx.

# Settings

[To be completed]
