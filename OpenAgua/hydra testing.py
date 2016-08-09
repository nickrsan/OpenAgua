from connection import connection
from conversions import *

session = {}

conn = connection(url='http://127.0.0.1:8080/json')
conn.login(username = 'root', password = '')    

project = conn.call('get_project_by_name',{'project_name':'Monterrey'})

import random
name = 'test' + str(random.randint(1,10000))
new_net = {'project_id':project.id, 'name':name}
net = conn.call('add_network',{'net':new_net})
print(net)

print('finished')
