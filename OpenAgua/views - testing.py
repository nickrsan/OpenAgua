from connection import connection
from conversions import *

url = 'http://127.0.0.1:8080/json'
hydra_username = 'root'
hydra_password = ''

conn = connection(url=url)
conn.login(username = hydra_username, password = hydra_password)
session_id = conn.session_id
user_id = conn.get_user_by_name(hydra_username)

# load / create project
project_name = 'Monterrey'
try:
    project = conn.get_project_by_name(project_name)
except:
    proj = dict(name = project_name)
    project = conn.add_project(proj)
project_id = project.id
project_id = project_id

# load / create / activate network
network_name = 'base_network'
exists = conn.call('network_exists', {'project_id':project_id, 'network_name':network_name})
if exists=='Y':
    network = conn.get_network_by_name(project_id, network_name)
else:
    net = dict(
        project_id = project_id,
        name = network_name,
        description = 'Prototype DSS network for Monterrey'
    )
    network = conn.call('add_network', {'net':net})
network_id = network.id
activated = conn.call('activate_network', {'network_id':network_id})