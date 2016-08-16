from subprocess import Popen

appname = 'openaguamodel'
appfile = appname + '.py'

args = dict(
    app = appname,
    url = 'http://127.0.0.1:8080/json',
    #user = 'root',
    #pw = 'password',
    nid = 5,
    tid = 3,
    scids = '[1,2,3,4,5]',
    ti = '1/2000',
    tf = '12/2000',
    tsf = '%m/%Y',
    log = 'logs')

call = 'python %s' % appname
for k, v in args.iteritems():
    call += ' -%s %s' % (k, v)
resp = Popen(call)

print('finished')