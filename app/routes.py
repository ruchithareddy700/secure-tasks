import logging

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, session,
)
from flask_login import login_user, logout_user, login_required, current_user

from . import db, bcrypt, limiter
from .forms import RegisterForm, LoginForm
from .models import User

main = Blueprint("main", __name__)


@main.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed,
        )  # role defaults to "user" - nobody can self-register as admin
        db.session.add(user)
        db.session.commit()
        logging.info("New user registered: %s", user.username)
        flash("Account created. Please log in.")
        return redirect(url_for("main.login"))
    return render_template("register.html", form=form)


@main.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            session.permanent = True  # activates the 15-minute timeout
            logging.info("Login success: %s", user.username)
            return redirect(url_for("main.dashboard"))
        logging.warning(
            "Login FAILED for username '%s' from %s",
            form.username.data, request.remote_addr,
        )
        flash("Invalid username or password.")  # same message either way
    return render_template("login.html", form=form)


@main.route("/logout", methods=["POST"])
@login_required
def logout():
    logging.info("Logout: %s", current_user.username)
    logout_user()
    return redirect(url_for("main.login"))


@main.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html")