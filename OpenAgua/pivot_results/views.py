from flask import Blueprint, redirect, url_for, render_template, request, session, jsonify, json
from flask_security import login_required, current_user
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
    
    return render_template('pivot_results.html', ttypes=conn.ttypes)

@pivot_results.route('/_load_pivot_data')
@login_required
def load_results():
    load_hydrauser() # do this at the top of every page
    conn = make_connection(login=True)
    conn.load_active_study(include_data=True)
    res_attrs = conn.get_res_attrs()
    
    # in the future, data should be organized around perturbed values in scenario sets
    # headers should match the JavaScript code or read directly from this list
    data = []
    for sc in conn.network.scenarios:
        scen_name = sc.name
        for rs in sc.resourcescenarios:
            if rs.value.type != 'timeseries':
                continue
            if 'function' in json.loads(rs.value.metadata):
                continue # for now - need to fix
            ra = res_attrs[rs.resource_attr_id]
            
            # the following needs updating if more than one timeseries item, but it otherwise effective
            timeseries = pandas.read_json(json.dumps(json.loads(rs.value.value)['0']), typ='series')
            for d, v in timeseries.iteritems():
                year = d.year
                month = d.month
                if type(v) == pandas.tslib.NaTType:
                    value = 0
                else:
                    value = float(v)

                record = {
                    'scenario': scen_name,
                    'feature': ra.res_name,
                    'type': ra.res_type,
                    'variable': ra.attr_name,
                    'year': year,
                    'month': month,
                    'value': value}
                data.append(record)
    #results = {'data': data}
                
    #return json.dumps(results)
    return jsonify(data=data)


