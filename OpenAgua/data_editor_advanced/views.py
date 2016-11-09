import os
import pandas
import base64

from flask import Blueprint, redirect, url_for, render_template, request, session, jsonify, json
from flask_security import login_required, current_user

from attrdict import AttrDict

from ..connection import *

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
    setup_id = None
    filters = {}
    config = {}
    
    setups = get_input_setups(session['study_id'])

    if 'input_id' in session and session['input_id'] is not None:
        setup_id = session['input_id']
        pivot = setups[setup_id]
        if pivot:
            filters = json.loads(pivot.filters)
            config = json.loads(pivot.config)

    pivot_params = {'setup_id': setup_id,
                    'setups': setups,
                    'filters': filters,
                    'config': config}

    return render_template('data-editor-advanced.html', ttypes=ttypes, pivot_params=pivot_params)

#@data_editor_advanced.route('/_load_chart')
#@login_required
#def load_chart():
    #session['input_id'] = request.args.get('pivot_id', type=int)
    #return jsonify(redirect=url_for('data_editor_advanced.main'))

@data_editor_advanced.route('/_load_input_data', methods=['GET', 'POST'])
@login_required
def load_pivot_data():
    
    if request.method == 'POST':
        load_hydrauser() # do this at the top of every page
        conn = make_connection(login=True)
        conn.load_active_study(include_data=True)
        res_attrs = conn.get_res_attrs()
        
        setup_id = int(request.json['setup_id'])
        if setup_id:
            input_setup = get_input_setup(session['study_id'], setup_id)
            setup = json.loads(input_setup.setup)
            filters = AttrDict(json.loads(input_setup.filters))
        else:
            filters = AttrDict(request.json['filters'])
            setup = {}
    
        filter_by_type = False
        filter_by_attr = False
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
                if filter_by_type and 'ttype_ids' in filters and conn.ttype_dict[ra.res_type] not in filters.ttype_ids:
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
                nseries = json.loads(value)
                for n, seriesjson in nseries.items():
                    series = pandas.read_json(json.dumps(seriesjson), typ='series')
                    for d, v in series.iteritems():
                        if type(v) == pandas.tslib.NaTType:
                            val = 0
                        else:
                            val = float(v)
                            
                        row = {
                            'scenario': scen_name,
                            'feature': ra.res_name,
                            'feature type': ra.res_type,
                            'variable': ra.attr_name,
                            'year': d.year,
                            'month': d.month,
                            'value': val,
                        }
                        row.update({'block': n}) # we can hide this client-side as needed
        
                        data.append(row)
                        
        return jsonify(setup=setup, data=data)
    
    return redirect(url_for('data_editor_advanced.main'))

@data_editor_advanced.route('/_save_setup', methods=['GET', 'POST'])
@login_required
def save_setup():

    if request.method == 'POST':

        study_id = session['study_id']

        name = request.form['name']
        description = request.form['description']
        filters = request.form['filters']
        setup = request.form['setup']

        setup_id = add_input_setup(db, study_id, name, description, filters, setup)

        return jsonify(setup_id = setup_id)

    return redirect(url_for('data_editor_advanced.main'))

@data_editor_advanced.route('/_delete_setup', methods=['GET', 'POST'])
@login_required
def delete_setup():

    if request.method == 'POST':

        setup_id = request.json['setup_id']
        result = delete_input_setup(db, session['study_id'], setup_id)

        return jsonify(result = result)

    return redirect(url_for('data_editor_advanced.main'))

@data_editor_advanced.route('/_save_data', methods=['GET', 'POST'])
@login_required
def save_data():

    if request.method == 'POST':

        setup = request.json['setup']
        data = request.json['data']

        return jsonify(error=0)

    return redirect(url_for('data_editor_advanced.main'))

