# manage.py
from getpass import getpass
from datetime import datetime

from flask_script import Manager

from OpenAgua import app, db
from OpenAgua.models import User, Role

manager = Manager(app)

@manager.command
def run():
    app.run(debug=False)

@manager.command
def create_admin():
    print("Add a new administrative account.")
    username = input("Username: ")
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
        password2 = getpass("Verify password: ")
        if password2 != password1:
            print("Passwords don't match. Please enter passwords again.")
            tries += 1
            
    if tries == 3:
        print('Max tries exceeded. Please start over.')
        return
    
    password = password1
    
    print("Creating admin account...", end=" ")
    
    # Create admin role
    admin_role = Role(name='admin') 
    
    # Create admin user
    admin_user = User(username=username,
                      email=email,
                      password=app.user_manager.hash_password(password),
                      is_active=1,
                      confirmed_at=datetime.utcnow())

    # Bind admin to role
    admin_user.roles.append(admin_role)
    
    # Store user and roles
    db.session.add(admin_user)
    db.session.commit()
    
    print("Done!")
    return

if __name__ == "__main__":
    manager.run()