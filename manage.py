# manage.py
from getpass import getpass
from datetime import datetime

from flask_script import Manager

from OpenAgua import app, db
from OpenAgua.models import User, Role

manager = Manager(app)

@manager.option('-r', '--role', dest='role_name', default='general')
def adduser(role_name):
    '''
    Add a new user.
    
    -r --role Specify a role: admin, superuser, or user. Default = user.
    '''
    
    # Add role?
    role = Role.query.filter(Role.name == role_name).first()
    if not role:
        add_role = input('"%s" role doesn\'t exist. Continue and create new role? (Y/N): ' % role_name)
        if add_role.lower()=='y':
            role = Role(name=role_name)
            db.session.add(role)
            print('"%s" role created!' % role_name)
        else:
            print('User addition canceled.')
            return
    
    username = input("Username: ")
    
    user = User.query.filter(User.username == username).first()
    if user:
        print('User already exists. Exiting.')
        return
    
    email = input("Email: ")
    password1 = True
    password2 = False
    tries = 0
    while not password1 == password2 and tries < 3:
        password1 = None
        while not password1:
            password1 = getpass("Password: ")
            if not password1:
                print("Password cannot be blank. Please try again.")
                tries += 1
                if tries == 3:
                    break                
        password2 = getpass("Verify password: ")
        if password2 != password1:
            print("Passwords don't match. Please enter passwords again.")
            tries += 1
            
    if tries == 3:
        print('Max tries exceeded. Please start over.')
        return
    
    password = password1
    
    print("Creating account...", end=" ")
    
    # Create user
    user = User(username=username,
                email=email,
                password=app.user_manager.hash_password(password),
                is_active=1,
                confirmed_at=datetime.utcnow())

    # Bind admin to role
    user.roles.append(role)
    
    # Store user and roles
    db.session.add(user)
    db.session.commit()
    
    print("Done!")
    return

if __name__ == "__main__":
    manager.run()