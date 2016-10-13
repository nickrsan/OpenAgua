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
        if filters.attr_ids:
            filter_by_attr = True
    
    data = []
    if filter_by_attr:
        datadict = {} # we will postprocess the data
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
            
            # the following needs updating if more than one timeseries item, but it is otherwise effective
            timeseries = pandas.read_json(json.dumps(json.loads(rs.value.value)['0']), typ='series')
            for d, v in timeseries.iteritems():
                if type(v) == pandas.tslib.NaTType:
                    value = 0
                else:
                    value = float(v)
                
                if filter_by_attr: # attrs are columns
                    key = (scen_name, ra.res_name, ra.res_type, d.year, d.month)
                    if key not in datadict:
                        datadict[key] = {}
                    datadict[key][ra.attr_name] = value
                else: # attrs are in rows
                    data.append({
                        'scenario': scen_name,
                        'feature': ra.res_name,
                        'feature type': ra.res_type,
                        'variable': ra.attr_name,
                        'year': d.year,
                        'month': d.month,
                        'value': value
                    })
    if filter_by_attr:
        data = []
        headers = ['scenario','feature','feature type','year','month']
        #variables = data.items()[0].keys()
        for key in datadict:
            row = {}
            for i, n in enumerate(headers):
                row[n] = key[i]
            for i, v in enumerate(datadict[key].keys()):
                row[v] = datadict[key][v]
            data.append(row)
        
    return jsonify(data=data)


