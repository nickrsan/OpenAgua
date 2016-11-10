import os
import shutil
import zipfile
from boltons.iterutils import remap

# import element tree
import xml.etree.ElementTree as ET

from flask import render_template, redirect, url_for, request, session, json, \
     jsonify, flash
from flask_security import login_required, current_user

from flask_uploads import UploadSet, configure_uploads, ARCHIVES, secure_filename

from attrdict import AttrDict

from ..connection import make_connection, activate_study

# import blueprint definition
from . import manager
from OpenAgua import app, db

templates = UploadSet('templates', ARCHIVES)
configure_uploads(app, templates)

@manager.route('/manage/studies')
@login_required
def manage_studies():
    return render_template('studies_manager.html')

@manager.route('/manage/templates')
@login_required
def manage_templates():
    conn = make_connection()
    
    # get list of all templates
    templates = conn.call('get_templates', {})
    
    return render_template('templates_manager.html', templates=templates)

@manager.route('/manage/templates/_upload', methods=['GET', 'POST'])
@login_required
def upload_template():

    if request.method == 'POST' and 'template' in request.files:
        
        conn = make_connection()
        
        file = request.files['template']
        
        filename = secure_filename(file.filename)
        dst_dir = app.config['UPLOADED_TEMPLATES_DEST']
        base_tpl_name = filename[:-4]
        versions = []
        for dirname in os.listdir(dst_dir):
            dirpath = os.path.join(dst_dir, dirname)
            if os.path.isdir(dirpath) and base_tpl_name + '_v' in dirname:
                versions.append(int(dirname.split('_v')[-1].strip()))
        max_version = max(versions)
        tpl_name = '{}_v{}'.format(base_tpl_name, max_version + 1)
        
        #file.save(os.path.join(dst_dir, template_name + '.zip'))

        zf  = zipfile.ZipFile(file.stream)
        
        # load template
        template_xml_path = zf.namelist()[0]
        template_xml = zf.read(template_xml_path).decode('utf-8')

        root = ET.fromstring(template_xml)
        for name in root.iter('template_name'):
            name.text = tpl_name
        new_xml = ET.tostring(root).decode()
           
        resp = conn.call('upload_template_xml', {'template_xml': new_xml}) 
        members = zf.namelist()
        
        zf.extractall(dst_dir)
        src = os.path.join(dst_dir, base_tpl_name)
        dst = os.path.join(dst_dir, tpl_name)
        os.rename(src, dst)
        
        flash('Template %s uploaded successfully' % tpl_name, category='info')
    else:
        flash('Something went wrong.')
        
    return redirect(url_for('manager.manage_templates'))

@manager.route('/_save_as_new_template', methods=['GET', 'POST'])
@login_required
def save_as_new_template():
    
    if request.method == 'POST':
        conn = make_connection()
        template = AttrDict(request.json['template'])
        
        # rename template
        if ' Vers. ' in template.name:
            basename, version = template.name.split(' Vers. ')
            version = int(version) + 1
        else:
            basename = template.name
            version = 1
        
        result = conn.add_template_from_json(template, basename, version)
        
        return jsonify(result = json.dumps(result))
    
    return redirect(url_for('manager.manage_templates'))

@manager.route('/_modify_template', methods=['GET', 'POST'])
@login_required
def modify_template():
    
    if request.method == 'POST':
        conn = make_connection()
        template = AttrDict(request.json['template'])
        
        # QC the template
        def visit(path, key, value):
            if key in set(['cr_date']):
                return False
            #elif key in set(['id', 'template_id', 'type_id', 'attr_id']):
                #return key, None
            return key, value
        template = remap(dict(template), visit=visit)        
        
        result = conn.call('update_template', {'tmpl': dict(template)})    
        
        if 'faultcode' in result:
            result = -1
            
        return jsonify(result=result)
    
    return redirect(url_for('manager.manage_templates'))

@manager.route('/_delete_template', methods=['GET', 'POST'])
@login_required
def delete_template():
    
    if request.method == 'POST':
        
        conn = make_connection()
        template = request.json
        
        result = conn.call('delete_template', {'template_id': template['id']})
        
        if 'faultcode' in result:
            return_code = -1
        else:
            return_code = 1
            shutil.rmtree(os.path.join(app.config['UPLOADED_TEMPLATES_DEST'], template['name']), ignore_errors=True)

        return jsonify(return_code=return_code)
    
    return redirect(url_for('manager.manage_templates'))

@manager.route('/_hydra_call', methods=['GET', 'POST'])
@login_required
def hydra_call():
    conn = make_connection()
    
    func = request.args.get('func')
    args = request.args.get('args')
    args = json.loads(args)
    result = conn.call(func, args)
    
    return jsonify(result=result)