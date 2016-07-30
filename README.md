# OpenAguaDSS

See [project info] (http://centrodelagua-decisiones.github.io/OpenAguaDSS/).

## How to run on your local machine for development / testing

1. See below to set up OpenAguaDSS in your github folder.
<<<<<<< HEAD
2. Run Hydra Platform
3. Run run.py (or run.bat on Windows)
4. Go to 127.0.0.1:5000 in your web browser.
5. Log in with "admin@gmail.com" and "password".
=======
2. For now, use Hydra Modeller to set up a test project, as follows:
  a. Create a project called "Monterrey"
  b. Import the template [WEAP.zip on GitHub] (https://github.com/rheinheimer/Hydra-WEAPTemplate).
  c. Create a network "base_network", using the WEAP template.
  d. Exit Hydra Modeller
3. Run Hydra Platform
4. Run run.py (or run.bat on Windows)
5. Go to 127.0.0.1:5000 in your web browser.
6. Log in with "admin@gmail.com" and "password".
>>>>>>> refs/remotes/origin/development

## Setup

### Set up Hydra Platform
* [general Hydra Platform information] (www.hydraplatform.org),
* [download from GitHub] (https://github.com/UMWRG/HydraPlatform), or
* [set up on Windows] (http://umwrg.github.io/HydraPlatform/tutorials/getting-started/server.html)

### Set up OpenAguaDSS (for running on your own machine). Technically, you can run OpenAgua on your local machine as is, without further configuration. However, you can change some local configuration settings thus:

1. Create an "/instance" folder.
2. In "/instance", create config.py
3. In the new config.py, you can now add the following, specified as, e.g. `DEBUG=True`.
  * SECRET_KEY. This can be created in Python with the urandom function in the os. I.e. `import os` followed by `os.urandom(24)`.
  * DEBUG
  * HYDRA_URL
  * USERNAME
  * PASSWORD
  * HYDRA_USERNAME
  * HYDRA_PASSWORD

## Documentation

### OpenAguaDSS
OpenAguaDSS is in the beginning stages of development. Documentation forthcoming.

### Hydra web service API
Documentation for Hydra Platform is under development. However, the following seem to be reliable:
* API functions: http://umwrg.github.io/HydraPlatform/devdocs/HydraServer/index.html#api-functions
* Example usage with JSON: http://umwrg.github.io/HydraPlatform/tutorials/plug-in/tutorial_json.html