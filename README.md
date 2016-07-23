# OpenAguaDSS

## How to run on your local machine for development / testing

1. See below to set up OpenAguaDSS in your github folder.
2. Run Hydra Platform*
3. Run run.py (or run.bat on Windows)
4. Go to 127.0.0.1:5000 in your web browser.
*NB: For general information about Hydra Platform, see: www.hydraplatform.org. Or download Hydra Platform from https://github.com/UMWRG/HydraPlatform.For setting up Hydra Platform on Windows, see:
http://umwrg.github.io/HydraPlatform/tutorials/getting-started/server.html.

## Setup

Please note the following *must* be specified in "/instance/config.py":
SECRET_KEY
This can be created in Python with the following code:
>>>import os
>>>secret_key = os.urandom(24)

And the following *may* be specified therein for local development security:
DEBUG
URL
USERNAME
PASSWORD
HYDRA_USERNAME
HYDRA_PASSWORD

## Documentation
For web API calls see:
-- API functions: http://umwrg.github.io/HydraPlatform/devdocs/HydraServer/index.html#api-functions
-- Example usage with JSON: http://umwrg.github.io/HydraPlatform/tutorials/plug-in/tutorial_json.html