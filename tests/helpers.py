from app import db, bcrypt
from app.models import User, Task

# Settings used only during testing
TEST_CONFIG = {
    "TESTING": True,
    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # temporary DB, vanishes after test
    "WTF_CSRF_ENABLED": False,    # re-enabled in the dedicated CSRF test
    "RATELIMIT_ENABLED": False,   # re-enabled in the dedicated rate-limit test
    "BCRYPT_LOG_ROUNDS": 4,       # faster hashing, tests only
}


def register(client, username="alice", email="alice@example.com",
             password="StrongPass123"):
    return client.post("/register", data={
        "username": username, "email": email,
        "password": password, "confirm": password,
    }, follow_redirects=True)


def login(client, username="alice", password="StrongPass123"):
    return client.post("/login", data={
        "username": username, "password": password,
    }, follow_redirects=True)


def make_admin(app, username="admin", password="AdminPass1234"):
    with app.app_context():
        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        db.session.add(User(username=username, email=username + "@example.com",
                            password_hash=hashed, role="admin"))
        db.session.commit()


def create_task(client, title="Study", description="Read chapter 1"):
    return client.post("/task/new", data={
        "title": title, "description": description,
    }, follow_redirects=True)


def get_task_id(app, title):
    with app.app_context():
        return Task.query.filter_by(title=title).first().id


def get_user_id(app, username):
    with app.app_context():
        return User.query.filter_by(username=username).first().id


def count_users(app):
    with app.app_context():
        return User.query.count()


def count_tasks(app):
    with app.app_context():
        return Task.query.count()