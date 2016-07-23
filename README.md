# OpenAguaDSS

<<<<<<< HEAD
=======
See [project info and documentation] (http://centrodelagua-decisiones.github.io/OpenAguaDSS/).

>>>>>>> refs/remotes/origin/master
## How to run on your local machine for development / testing

1. See below to set up OpenAguaDSS in your github folder.
2. Run Hydra Platform:
    * [general Hydra Platform information] (www.hydraplatform.org),
    * [download from GitHub] (https://github.com/UMWRG/HydraPlatform), or
    * [set up on Windows] (http://umwrg.github.io/HydraPlatform/tutorials/getting-started/server.html)
    
3. Run run.py (or run.bat on Windows)
4. Go to 127.0.0.1:5000 in your web browser.

## Setup

Please note the following *must* be specified in "/instance/config.py":
SECRET_KEY
This can be created in Python with the following code:
```
import os
secret_key = os.urandom(24)
```

And the following *may* be specified therein for local development security:
DEBUG
URL
USERNAME
PASSWORD
HYDRA_USERNAME
HYDRA_PASSWORD

## Documentation

### OpenAguaDSS
OpenAguaDSS is in the beginning stages of development. Documentation forthcoming.

### Hydra web service API
Documentation for Hydra Platform is under development. However, the following seem to be reliable:
* API functions: http://umwrg.github.io/HydraPlatform/devdocs/HydraServer/index.html#api-functions
* Example usage with JSON: http://umwrg.github.io/HydraPlatform/tutorials/plug-in/tutorial_json.html