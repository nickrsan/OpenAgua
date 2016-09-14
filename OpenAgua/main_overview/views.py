from flask import render_template
from flask_security import login_required

# import blueprint definition
from . import main_overview

@main_overview.route('/overview')
@login_required
def overview():    
    return render_template('overview.html') 