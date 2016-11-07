import os
import pandas
import base64

from flask import Blueprint, redirect, url_for, render_template, request,\
     session, jsonify, json
from flask_security import login_required, current_user

from attrdict import AttrDict

from ..connection import connection, make_connection, save_data,\
     load_hydrauser, add_chart, get_study_chart, get_study_chart_names

from ..utils import empty_hydra_timeseries

from OpenAgua import app, db

# blueprint definition
from . import data_editor_advanced

@data_editor_advanced.route('/advanced_data_editor')
@login_required
def main():
    load_hydrauser() # do this at the top of every page
    conn = make_connection(login=True)
    conn.load_active_study()
    
    res_attrs = conn.get_res_attrs()
    conn.ttypes.copy()
    node_attrs = conn.call('get_all_node_attributes', {'network_id': session['network_id'], 'template_id': conn.template.id})
    node_types = []
    for na in node_attrs:
        res_type = res_attrs[na.id].res_type
        if res_type not in node_types:
            node_types.append(res_type)
    link_attrs = conn.call('get_all_link_attributes', {'network_id': session['network_id'], 'template_id': conn.template.id})
    link_types = []
    for la in link_attrs:
        res_type = res_attrs[la.id].res_type
        if res_type not in link_types:
            link_types.append(res_type)
            
    ttypes = {}
    for tt in conn.ttypes:
        ttype = conn.ttypes[tt]
        if ttype.resource_type == 'NODE' and ttype.name in node_types:
            ttypes[tt] = ttype
        elif ttype.resource_type == 'LINK' and ttype.name in link_types:
            ttypes[tt] = ttype
        else:
            continue
        tattrs = [ta for ta in ttypes[tt].typeattrs if ta.is_var == 'N']
        if len(tattrs):
            ttypes[tt]['typeattrs'] = tattrs
        else:
            ttypes.pop(tt) # don't show types with nothing to input

    # default setup
    pivot_id = None
    filters = {}
    config = {}

    if 'input_id' in session and session['input_id'] is not None:
        pivot_id = session['input_id']
        pivot = get_study_input(session['study_id'], pivot_id)
        if pivot:
            filters = json.loads(pivot.filters)
            config = json.loads(pivot.config)            

    #saved_names = get_study_input_names(session['pivot_id'])
    saved_names = []

    pivot_params = {'pivot_id': pivot_id,
                    'saved_names': saved_names,
                    'filters': filters,
                    'config': config}

    return render_template('data-editor-advanced.html', ttypes=ttypes, pivot_params=pivot_params)

#@data_editor_advanced.route('/_load_chart')
#@login_required
#def load_chart():
    #session['input_id'] = request.args.get('pivot_id', type=int)
    #return jsonify(redirect=url_for('data_editor_advanced.main'))

@data_editor_advanced.route('/_load_pivot_data')
@login_required
def load_pivot_data():
    load_hydrauser() # do this at the top of every page
    conn = make_connection(login=True)
    conn.load_active_study(include_data=True)
    res_attrs = conn.get_res_attrs()

    filter_by_type = False
    filter_by_attr = False
    filters = AttrDict(json.loads(request.args.get('filters')))
    if filters and filters.filterby == 'res_type':
        filter_by_type = True
        if 'attr_ids' in filters and filters.attr_ids:
            filter_by_attr = True

    data = []
    
    # load the data
    for sc in conn.network.scenarios:
        scen_name = sc.name
        
        resourcescenarios = {rs.resource_attr_id: rs for rs in sc.resourcescenarios}
        for raid in res_attrs:
        #for rs in sc.resourcescenarios:

            ra = res_attrs[raid]
            
            # basic filters
            if ra.is_var == 'Y':
                continue
            if ra.res_type == 'Junction':
                continue
            if ra.data_type != 'timeseries':
                continue # change later depending on type
            
            # user-specified filters
            if filter_by_attr and ra.attr_id not in filters.attr_ids:
                continue            
            if filter_by_type and conn.ttype_dict[ra.res_type] not in filters.ttype_ids:
                continue     
            
            if raid in resourcescenarios.keys():
                rs = resourcescenarios[raid]
                value = rs.value.value
                metadata = json.loads(rs.value.metadata)
            else:
                value = json.dumps(empty_hydra_timeseries())
                metadata = {}
                #continue

            if 'function' in metadata and len(metadata['function']):
                #continue # for now - need to fix
                pass

            # the following needs updating if more than one timeseries item, but it is otherwise effective
            timeseries = pandas.read_json(json.dumps(json.loads(value)['0']), typ='series')
            for d, v in timeseries.iteritems():
                if type(v) == pandas.tslib.NaTType:
                    val = 0
                else:
                    val = float(v)

                data.append({
                    'scenario': scen_name,
                    'feature': ra.res_name,
                    'feature type': ra.res_type,
                    'variable': ra.attr_name,
                    'year': d.year,
                    'month': d.month,
                    'value': val
                })

    return jsonify(data=data)

@data_editor_advanced.route('/_save_chart', methods=['GET', 'POST'])
@login_required
def save_chart():

    if request.method == 'POST':

        hydrastudy_id = session['study_id']

        thumbnail = request.form['thumbnail']
        name = request.form['name']
        description = request.form['description']
        filters = request.form['filters']
        setup = request.form['setup']

        # save image to file
        userfiles = os.path.join(app.config['USER_FILES'], str(current_user.id)) # testing for now
        thumbnailspath = app.config['CHART_THUMBNAILS_PATH']
        thumbnailsabspath = os.path.join(userfiles, thumbnailspath)
        if not os.path.exists(thumbnailsabspath):
            os.makedirs(thumbnailsabspath)
        filename = '{}.png'.format(name.replace(' ', '-'))
        thumbnailabspath = os.path.join(userfiles, thumbnailspath, filename)

        imgstr = thumbnail.split(',')[1].encode()
        with open(thumbnailabspath, "wb") as f:
            f.write(base64.decodestring(imgstr))

        add_chart(db, hydrastudy_id, name, description, filename, filters, setup)

        return jsonify(result = 0)

    return redirect(url_for('data_editor_advanced.main'))