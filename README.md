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

# Documentation

## OpenAguaDSS

OpenAguaDSS is in the beginning stages of development. Documentation forthcoming.

## Hydra web service API

Documentation for Hydra Platform is under development. However, the following seem to be reliable:
* API functions: http://umwrg.github.io/HydraPlatform/devdocs/HydraServer/index.html#api-functions
* Example usage with JSON: http://umwrg.github.io/HydraPlatform/tutorials/plug-in/tutorial_json.html