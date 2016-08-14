from subprocess import Popen

appname = 'openagua_model/model.py'

args = dict(
    url = 'http://127.0.0.1:8080/json',
    nid = 5,
    tid = 3,
    scids = '[1,2,3]',
    ti = '1/2000',
    tf = '12/2000')
    
call = 'python %s' % appname
for k, v in args.iteritems():
    call += ' -%s %s' % (k, v)
print(call)
resp = Popen(call)

print('finished')