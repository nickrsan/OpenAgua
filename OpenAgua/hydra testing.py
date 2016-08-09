from connection import connection
from conversions import *

session = {}

conn = connection(url='http://hydra.openaguadss.org/json')
conn.login(username = 'root', password = '')    

projects = conn.call('get_projects',{})

import random
name = 'test' + str(random.randint(1,10000))
new_net = {'project_id':project.id, 'name':name}
net = conn.call('add_network',{'net':new_net})
print(net)

print('finished')
