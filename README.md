# Project information

See [project info] (http://centrodelagua-decisiones.github.io/OpenAguaDSS/).

# Setup/use on local machine

## Hydra Platform

* [general Hydra Platform information] (www.hydraplatform.org),
* [download from GitHub] (https://github.com/UMWRG/HydraPlatform), or
* [set up on Windows] (http://umwrg.github.io/HydraPlatform/tutorials/getting-started/server.html)

## OpenAgua

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
SECRET_KEY = 'T\xa0P\x00\xcf\xa4O\xea\x0bZ\xbd\xd6\xef\x03p\xc0w\x9c;\x01\xfd>\xc9\xc4'
```

Note that SECRET_KEY can be created in Python with the urandom function in the os. I.e. `import os` followed by `os.urandom(24)`. IMPORTANT: This should be set here in a production environment!

## Run

1. See below to set up OpenAguaDSS in your github folder.
2. For now, use Hydra Modeller to set up a test project, as follows:
  a. Create a project called "Monterrey"
  b. Import the template [WEAP.zip on GitHub] (https://github.com/rheinheimer/Hydra-WEAPTemplate).
  c. Create a network "base_network", using the WEAP template.
  d. Exit Hydra Modeller
3. Run Hydra Platform
4. Run run.py (or run.bat on Windows)
5. Go to 127.0.0.1:5000 in your web browser.
6. Log in with "admin@gmail.com" and "password".

# Setup/use as a web server on Linux

This assumes a simple configuration, whereby Hydra Platform and OpenAgua are run from the same machine (which may not be efficient) and where OpenAgua is served to the world by Apache2 on an Ubuntu machine. Setup of Hydra Platform, OpenAgua and Apache2 are described here.

## Hydra Platform

1. Install Hydra Platform and dependencies as described at https://github.com/UMWRG/HydraPlatform#hydraplatform.
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




















