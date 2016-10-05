from os.path import join
import zipfile

from flask import render_template, redirect, url_for, request, session, json, \
     jsonify, flash
from flask_security import login_required, current_user

from flask_uploads import UploadSet, configure_uploads, ARCHIVES

from ..connection import make_connection, \
     activate_study

# import blueprint definition
from . import manager
from OpenAgua import app, db

templates = UploadSet('templates', ARCHIVES)
configure_uploads(app, templates)

@manager.route('/manage/templates')
@login_required
def manage_templates():
    conn = make_connection()
    
    # get list of all templates
    templates = conn.call('get_templates', {})
    
    return render_template('templates_manager.html',
                           templates=templates)


@manager.route('/manage/templates/_upload', methods=['GET', 'POST'])
@login_required
def upload_template():

    if request.method == 'POST' and 'template' in request.files:
        
        conn = make_connection()
        
        template = request.files['template']
        
        filename = templates.save(template)

        zf  = zipfile.ZipFile(template.stream)
        
        # load template
        template_xml_path = zf.namelist()[0]
        template_xml = zf.read(template_xml_path).decode('utf-8')
        resp = conn.call('upload_template_xml',
                                {'template_xml': template_xml}) 
        zf.extractall(path=app.config['UPLOADED_TEMPLATES_DEST'])
        
        template_name = template_xml_path.split('/')[0]
        flash('Template %s uploaded successfully' % template_name, category='info')
    else:
        flash('Something went wrong.')
        
    return redirect(url_for('manager.manage_templates'))
        
@manager.route('/_get_templates_for_network')
@login_required
def get_templates_for_network():
    conn = make_connection()
    network_id = request.args.get('network_id')
    if network_id is not None:
        network_id = int(network_id)
        net = conn.call('get_network', {'network_id': network_id})
        tpls = conn.call('get_templates', {})
        
        net_tpl_ids = [t.template_id for t in net.types]
        net_tpls = [tpl for tpl in tpls if tpl.id in net_tpl_ids]
    else:
        net_tpls = []
    return jsonify(templates=net_tpls)

@manager.route('/_hydra_call', methods=['GET', 'POST'])
@login_required
def hydra_call():
    conn = make_connection()
    
    func = request.args.get('func')
    args = request.args.get('args')
    args = json.loads(args)
    result = conn.call(func, args)
    
    return jsonify(result=result)