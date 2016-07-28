from connection import connection
from conversions import *

session = {}

conn = connection(url='http://127.0.0.1:8080/json')
conn.login(username = 'root', password = '')    
session['session_id'] = conn.session_id
user = conn.get_user_by_name('root')
user_id = user.id

project = conn.call('get_project_by_name',{'project_name':'Monterrey'})
network = conn.call('get_network_by_name',{'project_id':project.id, 'network_name':'base_network'})
names = [p.name for p in projects]

print('finished')