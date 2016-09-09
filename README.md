This describes how to set up and run OpenAgua.

See technical details and general usage [here](http://centrodelagua-decisiones.github.io/OpenAguaDSS/).

# Setup/run on local machine

These setup instructions are general, for both Windows and Linux. This is untested on OSX, but presumably setup should be similar to that for Linux.

OpenAgua connects to Hydra Platform. So, Hydra Platform needs to be available, either locally or remotely. This assumes Hydra Platform will be run locally. In this case, the first step is to make sure Hydra Platform is running, after which OpenAgua may be run. 

## Hydra Platform

* [general Hydra Platform information] (www.hydraplatform.org),
* [download from GitHub] (https://github.com/UMWRG/HydraPlatform), or
* [set up on Windows] (http://umwrg.github.io/HydraPlatform/tutorials/getting-started/server.html)

## OpenAgua

### Requirements

OpenAgua was built on Python 3.5, so this should be installed first. Earlier versions of Python 3 should also work, but there's no guarantee. Other requirements follow.

__Windows-specific__:

The main (only?) issue is that *flask_user* depends on *PyCrypto*, which needs to compile some binaries during installation (apparently due to export laws they cannot be provided within the United States). Two options exist:

1. Compile on your own machine using [Visual Studio 2015 Community Edition](https://www.visualstudio.com/en-us/downloads/download-visual-studio-vs.aspx), which is the only binary compiler for Python 3.5+.

2. Find a pre-compiled version of *PyCrypto* for Python 3.5. One is [available on GitHub](https://github.com/sfbahr/PyCrypto-Wheels). See instructions there to install.

__Linux-specific__:

Two potential issues exist, but others may also exist (consult Google if troubles arise, and let us know so we can document the issues here!):

1. *pip3* should be used instead of *pip* (for installing Python 3.x modules). At least on Amazon's default Ubuntu, *pip3* is not installed by default, so this should be installed: `sudo apt-get install pip3`.

2. As with Windows, encryption-related modules need to be compiled during installation. On Amazon's Ubuntu, install *libffi-dev* (`sudo apt-get install libffi-dev`) to be able to install *bcrypt*, a dependency of *flask_user*. On other setups, make sure the following are also installed: *libpython3-dev*, *python3-dev*, *libffi* and *libffi-dev*.

__All platforms__:

All platforms require the following Python modules (see also requirements.txt):
```
flask
flask_sqlalchemy
flask_user
flask_admin
flask_migrate
flask_script
requests
pandas
webcolors
pyomo
```

These can be installed individually (e.g., `pip install flask`) or together (i.e., `pip install requirements.txt`)

### Settings

NOTE: This assumes email confirmation is needed. However, if a local machine is used, email confirmation can be switched off in the configuration setting with the `USER_ENABLE_CONFIRM_EMAIL` setting in config.py.

There are a few settings that should be set on a machine-specific basis, whether on a local machine or on a web server. These are stored in a folder called "instance" under the top-level OpenAguaDSS folder:

1. Create an "/instance" folder. This folder stores machine-specific settings and the user database.
2. In "/instance", create "config.py". This new file contains settings that will supercede settings in the main "config.py". For example, you can overwrite default debug settings, as: `DEBUG=True`.
3. At a minimum, set the following parameters (values are examples only; your settings may be different):
```
# Flask-Mail settings
MAIL_USERNAME = 'admin@mysite.com'
MAIL_PASSWORD = 'password'
MAIL_DEFAULT_SENDER = '"OpenAgua robot" <noreply@mysite.com>'
MAIL_SERVER = 'smtp.mysite.com'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USE_TLS = False

# Optionally, set other parameters as desired:
HYDRA_URL = 'http://127.0.0.1:8080/json'
DEBUG = False
SECRET_KEY = 'a secret key'
```

The OpenAgua user database (`SQLALCHEMY_DATABASE_URI`) can be specified here too. For SQLite, see the example in the default config.py file. For MySQL: `mysql+pymysql://username:password@xxxxx.xxxxx.com/dbname`. Note the `pymysql`; this means that pymysql should be installed: `pip3 install pymysql`.

Note that SECRET_KEY can be created in Python with the urandom function in the os. I.e. `import os` followed by `os.urandom(24)`. IMPORTANT: This should be set here in a production environment!

## Run

1. See below to set up OpenAguaDSS in your github folder.
2. Run Hydra Platform, or make sure HYDRA_URL points to a working Hydra Platform server (Hydra Server).
3. Run OpenAguaDSS/run.py (or run.bat on Windows)
4. Go to 127.0.0.1:5000 in your web browser.
5. Register and/or login. Note that internet access is required during registration, as an email confirmation is sent for confirmation during the process.

# Setup/serve as web server

This assumes a simple configuration, whereby Hydra Platform and OpenAgua are run from the same Ubuntu Linux machine (which may not be efficient) and where OpenAgua is served to the world by Apache2. Setup of Hydra Platform, OpenAgua and Apache2 are described here. If you are serving from Windows, you are on your own, but presumably the setup will be similar.

FUTURE: Consolidate this setup with the instructions for a local setup above, since much of the process is similar.

## Hydra Platform

1. Install Hydra Platform and dependencies as described at https://github.com/UMWRG/HydraPlatform#hydraplatform. Some pointers for installing on Ubuntu:
* For mysql-connector-python: `sudo apt-get install python-mysql.connector`
* For bcrypt, make sure to install python-dev first: `sudo apt-get install python-dev`
2. Specify the database that Hydra Platform will use in /HydraPlatform/config/hydra.ini. By default this is a local SQLite database, but any SQL database can be used, such as MySQL, which is what OpenAguaDSS.org uses.
3. Decide on hosting configuration. Hydra Platform comes with its own web interface, so can be configured either as a server available only to the local machine (which OpenAgua can still access), or as a public web server with the built-in user interface exposed to the world.
a. If a non-public server is used, follow step 4. on https://github.com/UMWRG/HydraPlatform#installation to run the server: `chmod +x run_server.sh i(i. ./run_server.sh`.
b. If a public server is used, Apache2 needs to be configured as described below.

## OpenAgua

1. Install OpenAgua using git: From /var/www type `sudo git clone https://github.com/CentroDelAgua-Decisiones/OpenAguaDSS.git`
2. Set up /instance/config.py. In addition to the settings as described above, make sure to add:
  * HYDRA_URL (e.g., `HYDRA_URL = 'http://hydra-server.mysite.com/json'`)
  * SECRET_KEY
3. Change the owner of the instance folder to allow the web server to create/modify the user database (users.sqlite). From the main OpenAguaDSS folder, type `sudo chown www-data:www-data instance`. www-data is the Apache2 user, and would be different for other web servers.
4. Set up Apache2, as described below.

## Apache2

*ALERT: This section is no longer valid since upgrading OpenAgua to Python 3. These instructions will change to Nginx instead of Apache*

Both Hydra Platform and OpenAgua can be served by Apache2 to the public using virtual hosts. In this example, Hydra Platform is served on hydra-server.mysite.com, while OpenAgua is served on www.mysite.com. Of course, if only OpenAgua is to be available to the public, then Hydra Platform is simply omitted from this.

On Ubuntu, two separate configuration files can be prepared, both located in /etc/apache2/sites-available. Each file might be called, for example, hydra-platform.conf and openagua.conf, respectively. The configuration file for **Hydra Platform** can be as follows (this assumes HydraPlatform is located in /var/www):

```
WSGIPythonPath /var/www/HydraPlatform/HydraServer/python:/var/www/HydraPlatform/HydraLib/python

<VirtualHost *:80>
    ServerName hydra-server.mysite.com
    ServerAdmin admin@mysite.com

    WSGIScriptAlias / /var/www/HydraPlatform/HydraServer/hydra.wsgi

    WSGIDaemonProcess hydra-server user=www-data processes=1 display-name=%{GROUP} python-path=/var/www/HydraPlatform/HydraServer/$
    WSGIProcessGroup hydra-server

    <Directory /var/www/HydraPlatform/HydraServer/>
	WSGIApplicationGroup %{GLOBAL}
	Order deny,allow
	Allow from all
    </Directory>

    <LocationMatch ".*(py|pyc)$">
	Order deny,allow
	Deny from all
    </LocationMatch>
    
	ErrorLog ${APACHE_LOG_DIR}/error-hydra-server.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined

    LogLevel warn
    
</VirtualHost>
```

openagua.conf, for **OpenAgua**, would look similar:

```
<VirtualHost *:80>
    ServerName test.mysite.com
    ServerAdmin admin@mysite.com

    WSGIDaemonProcess openagua user=www-data threads=5 display-name=%{GROUP}
    WSGIScriptAlias / /var/www/OpenAguaDSS/openagua.wsgi

    <Directory /var/www/OpenAguaDSS/OpenAgua/>
	WSGIProcessGroup openagua
	WSGIApplicationGroup %{GLOBAL}
	Order allow,deny
	Allow from all
    </Directory>

    <LocationMatch ".*(py|pyc)$">
	Order deny,allow
	Deny from all
    </LocationMatch>
    
	ErrorLog ${APACHE_LOG_DIR}/error-hydra-server.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined

    LogLevel warn
    
</VirtualHost>
```

To understand what these actually mean, you'll have to look elsewhere. One thing to note, however, is that both of these point to a .wsgi file. These are already included with the respective distributions.

To enable these, use the command `sudo a2ensite hydra-server` and `sudo a2ensite openagua`. Once these are enabled, restart Apache2 with `service apache2 restart`.

Voila! OpenAgua should now be available on test.mysite.com while Hydra Server should be available at hydra-server.mysite.com. This assumes, of course, you have configured your site's DNS appropriately.

Note that these configuration settings would differ between Linux distributions.

# OpenAgua technologies and methods

For now, this documentation is organized around the main user areas of the website, focusing on technical aspects (technologies involved, methods used, etc.), but also use in some cases. General help for the registered user is found on the site itself, under "Help".

## General

### Data management - Hydra Platform
As mentioned above, OpenAgua is built on Hydra Platform for data organization and management. Documentation for Hydra Platform is under development. However, the following seem to be reliable:
* [API functions](http://umwrg.github.io/HydraPlatform/devdocs/HydraServer/index.html#api-functions)
* [Example usage with JSON](http://umwrg.github.io/HydraPlatform/tutorials/plug-in/tutorial_json.html)

### Back end

OpenAgua uses a mix of [**JavaScript**](https://www.javascript.com) and [**jQuery**](https://jquery.com/) for client-side work and [**Flask**](http://flask.pocoo.org), "a microframework for [**Python**](https://www.python.org) based on [**Werkzeug**](http://werkzeug.pocoo.org), [**Jinja 2**](http://jinja.pocoo.org/docs/dev/) and good intentions. Server-side work includes serving individual webpages and interactions with Hydra Platform, among other various functions. The use of Python enables easy introduction of custom Python modules as needed. OpenAgua takes as much advantage as possible of the Jinja 2 templating system that Flask uses.

Many extensions have been written for Flask. Some of these are used by OpenAgua, as explained below.

### Front end

OpenAgua's front end is built using [**Bootstrap 3**](http://getbootstrap.com).

## Site security: registration, login, etc.
Site security is managed by Flask_User. Flask_User, in turn, uses a mix of other Flask extensions.

## Home

Documentation forthcoming.

## Manage

The "Manage" section allows the user to manage HP _projects_, _networks_, and _templates_.

The overall steps in creating a project + template + network are as follows (main HP functions involved in parentheses):
1. Add a project (*add_project*)
2. Add a network (*add_network*), selecting a template to add at the same time. The only available template for now is "OpenAgua"; this is created automatically if it doesn't already exist. During network creation, a default "Baseline" scenario (*add_scenario*) is created for the new network, similar to Hydra Modeller. 

For project/network creation, HP functions are called as follows:
1. *add_project*
2. *add_network*
3. *apply_template_to_network*
4. *add_scenario*

### Projects

* **Add Project**: This uses HP's _add_project_ function.

### Networks

* **Add Network**: This uses HP's _add_network_ function with the user's active project.

### Templates

The OpenAgua user cannot currently add a template via the interface.

## Network Editor

* **Add node**: The HP functions *add_node* is used, with the user's active *network_id*.
* **Add link**: The HP function *add_link* is used, with the user's active *network_id*.

## Data Editor

The basic data editor consists of three areas:

1. Variable selector,
2. Data editor and
3. Data preview

### Variable selector
The variable selector consists of dropdowns using [**boostrap-select**](https://silviomoreto.github.io/bootstrap-select/).

### Data editor
Currently, the data editor only allows editing the "descriptor" field of the database. Text data is displayed and edited using the [**Ace** code editor](https://ace.c9.io).

Python code is entered here. This code is evaluated using the evaluate function found in evaluator.py. Essentially, a string representation of a function is created, with the entered code as the body of the function. All lines are indented appropriately as needed for Python. The function is then called by the evaluator and assigned to a variable. The function is run once per time step.

The last line of the user-entered code is automatically prepended with "return ", such that the user doesn't need to. This is most useful for simple cases, such as a constant value:

```python
5
```

However, the evaluator also automatically detects the presence of a "return " in the last line, such that the user may also include a return as desired. So `return x` on the last line is the same as `x`. In many cases, including `return` is simply a matter of personal preference. But this is particularly useful if a return is nested in the last part of a conditional statement. To demonstrate, the following three versions of code input yield the exact same result when evaluated:

```python
if date.month in [6,7,8]:
    x = 0.5
else:
    x = 1
x
```
```python
if date.month in [6,7,8]:
    x = 0.5
else:
    x = 1
return x
```

```python
if date.month in [6,7,8]:
    return 0.5
else:
    return 1
```

This scheme enables the user to import, enter custom functions directly into the code, etc. In the future, this will also enable offering a range of custom Python functions. It will also allow the user to create, store, re-use, and share custom functions.

The last three examples above should raise a question: where does "date" come from? OpenAgua will include several built-in variables available for use. For now, this only includes the date of the function call. In the future, however, this will expand to include others as needed.

## Scenario Builder

Not built yet.

## Model Dashboard

Documentation forthcoming.

## Results Overview

Not built yet.

## Chart Maker

Not built yet. For now, there is an example chart built using [**Plotly**](http://plot.ly). The intent is to build a control panel for building Plotly graphs.

## My Charts

Not built yet.

## Charts Dashboard

Not built yet.

## Advanced

## Data Exporter

Not built yet. This might be best deferred to the Hydra Platform Web Interface.




















