from connection import connection

session = {}

conn = connection(url='http://127.0.0.1:8080/json')
#conn = connection(url='http://hydra.openaguadss.org/json')
conn.login(username = 'root', password = '')    
project = conn.get_project_by_name('Monterrey')
projects = conn.call('get_projects',{})
networks = conn.call('get_networks',{'project_id':2})
scenarios = conn.call('get_scenarios', {'network_id':2})
node = conn.call('get_node',{'node_id':597})
print('finished')
