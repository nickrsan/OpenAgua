from connection import connection

session = {}

conn = connection(url='http://127.0.0.1:8080/json')
#conn = connection(url='http://hydra.openaguadss.org/json')
conn.login(username = 'root', password = '')    
#projects = conn.call('get_projects',{'userid':conn.user_id})
#project = conn.get_project_by_name('Monterrey')
#templates = conn.call('get_templates',{})
network = conn.call('get_network',{'network_id':12,'include_data':'N','template_id':7,'summary':'N'})
node = conn.call('get_node',{'node_id':597})
print('finished')
