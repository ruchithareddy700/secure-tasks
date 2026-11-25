from getpass import getpass

from app import create_app, db, bcrypt
from app.models import User

app = create_app()

with app.app_context():
    username = input("Admin username: ").strip()
    email = input("Admin email: ").strip()
    password = getpass("Admin password (min 10 chars, hidden as you type): ")

    if len(password) < 10:
        print("Password too short. Aborting.")
    elif User.query.filter_by(username=username).first():
        print("That username already exists. Aborting.")
    else:
        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        admin = User(username=username, email=email,
                     password_hash=hashed, role="admin")
        db.session.add(admin)
        db.session.commit()
        print("Admin '%s' created." % username)