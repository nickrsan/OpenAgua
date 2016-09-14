# manage.py
from getpass import getpass
from datetime import datetime
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from OpenAgua import app, db
from OpenAgua.models import *

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)

@manager.command
def addsuperuser():
    '''
    Add a user with admin privledges.
    '''
    
    role = Role.query.filter(Role.name == 'superuser').first()
    if not role:
        role = Role(name='superuser')
        db.session.add(role)

    email = input("Email: ")
    user = User.query.filter(User.email == email).first()
    if user:
        print('Email already exists. Exiting.')
        return
    
    password1 = True
    password2 = False
    tries = 0
    maxtries = 3
    while not password1 == password2 and tries < maxtries:
        password1 = None
        while not password1:
            password1 = getpass("Password: ")
            if not password1:
                print("Password cannot be blank. Please try again.")
                tries += 1
            if tries == maxtries:
                break
        else:
            password2 = getpass("Verify password: ")
            if password2 != password1 and not failed:
                print("Passwords don't match. Please enter passwords again.")
                tries += 1
            
    if tries == maxtries:
        print('Max tries exceeded. Please start over.')
        return
    
    password = password1
    
    print("Creating account...", end=" ")
    
    # Create user
    user = User(username=username,
                email=email,
                password=app.user_manager.hash_password(password),
                active=True,
                confirmed_at=datetime.utcnow())

    # Bind admin to role
    user.roles.append(role)
    
    # Store user and roles
    db.session.add(user)
    db.session.commit()
    
    print("Done!")

if __name__ == "__main__":
    manager.run()