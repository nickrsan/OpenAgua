from flask import Blueprint, redirect, url_for, render_template, request, session, jsonify, json
from flask_security import login_required, current_user

from attrdict import AttrDict

from ..connection import connection, make_connection, save_data, load_hydrauser
#from ..utils import hydra_timeseries, d2o, eval_scalar, eval_timeseries, eval_function, eval_data

import pandas

# blueprint definition
from . import pivot_results

@pivot_results.route('/pivot_results')
@login_required
def main():
    load_hydrauser() # do this at the top of every page
    conn = make_connection(login=True)
    conn.load_active_study()
    #res_attrs = conn.get_res_attrs()
    return render_template('pivot_results.html', ttypes=conn.ttypes)

@pivot_results.route('/_load_pivot_data')
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
        filter_by_attr = True
    
    # in the future, data should be organized around perturbed values in scenario sets
    # headers should match the JavaScript code or read directly from this list
    data = []
    for sc in conn.network.scenarios:
        scen_name = sc.name
        for rs in sc.resourcescenarios:
            
            ra = res_attrs[rs.resource_attr_id]
            
            if rs.value.type != 'timeseries':
                continue
            if 'function' in json.loads(rs.value.metadata):
                continue # for now - need to fix
            
            # add filters here
            if filter_by_attr and rs.attr_id not in filters.attr_ids:
                continue            
            if filter_by_type and conn.ttype_dict[ra.res_type] not in filters.ttype_ids:
                continue
            
            if filter_by_attr and filters.attr_ids: # attrs are columns
                valname = ra.attr_name
                ra_record = {}
            else: # attrs are in rows
                valname = 'value'
                ra_record = {'variable': ra.attr_name}
            ra_record.update({
                'scenario': scen_name,
                'feature': ra.res_name,
                'feature type': ra.res_type
            })
            # the following needs updating if more than one timeseries item, but it is otherwise effective
            timeseries = pandas.read_json(json.dumps(json.loads(rs.value.value)['0']), typ='series')
            for d, v in timeseries.iteritems():
                record = ra_record.copy()
                
                if type(v) == pandas.tslib.NaTType:
                    value = 0
                else:
                    value = float(v)
                    
                record.update({'year': d.year, 'month': d.month, valname: value})
                data.append(record)

    return jsonify(data=data)


