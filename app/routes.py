import logging

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, session, abort,
)
from flask_login import login_user, logout_user, login_required, current_user

from . import db, bcrypt, limiter
from .forms import RegisterForm, LoginForm, TaskForm
from .models import User, Task
from .decorators import admin_required

main = Blueprint("main", __name__)



# AUTHENTICATION

@main.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed,
        )
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
            session.permanent = True
            logging.info("Login success: %s", user.username)
            return redirect(url_for("main.dashboard"))
        logging.warning(
            "Login FAILED for username '%s' from %s",
            form.username.data, request.remote_addr,
        )
        flash("Invalid username or password.")
    return render_template("login.html", form=form)


@main.route("/logout", methods=["POST"])
@login_required
def logout():
    logging.info("Logout: %s", current_user.username)
    logout_user()
    return redirect(url_for("main.login"))



# TASKS - CRUD
def get_own_task_or_404(task_id):
    """Return the task only if it belongs to the logged-in user."""
    task = db.session.get(Task, task_id)
    if task is None:
        abort(404)
    if task.user_id != current_user.id:
        logging.warning(
            "IDOR attempt: user '%s' tried to access task %s owned by user id %s",
            current_user.username, task_id, task.user_id,
        )
        abort(404)
    return task


# READ (list)
@main.route("/")
@login_required
def dashboard():
    tasks = (
        Task.query.filter_by(user_id=current_user.id)
        .order_by(Task.created_at.desc())
        .all()
    )
    return render_template("dashboard.html", tasks=tasks)


# CREATE
@main.route("/task/new", methods=["GET", "POST"])
@login_required
def create_task():
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            user_id=current_user.id,
        )
        db.session.add(task)
        db.session.commit()
        logging.info("Task %s created by %s", task.id, current_user.username)
        flash("Task created.")
        return redirect(url_for("main.dashboard"))
    return render_template("task_form.html", form=form, heading="New task")


# UPDATE
@main.route("/task/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    task = get_own_task_or_404(task_id)
    form = TaskForm(obj=task)
    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        db.session.commit()
        logging.info("Task %s updated by %s", task.id, current_user.username)
        flash("Task updated.")
        return redirect(url_for("main.dashboard"))
    return render_template("task_form.html", form=form, heading="Edit task")


# DELETE
@main.route("/task/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    task = get_own_task_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    logging.info("Task %s deleted by %s", task_id, current_user.username)
    flash("Task deleted.")
    return redirect(url_for("main.dashboard"))



# ADMIN
@main.route("/admin")
@admin_required
def admin_panel():
    users = User.query.order_by(User.id).all()
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return render_template("admin.html", users=users, tasks=tasks)


@main.route("/admin/task/<int:task_id>/delete", methods=["POST"])
@admin_required
def admin_delete_task(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        abort(404)
    db.session.delete(task)
    db.session.commit()
    logging.info("ADMIN %s deleted task %s", current_user.username, task_id)
    flash("Task deleted by admin.")
    return redirect(url_for("main.admin_panel"))


@main.route("/admin/user/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    if user.id == current_user.id:
        flash("You cannot delete your own account.")
        return redirect(url_for("main.admin_panel"))
    username = user.username
    db.session.delete(user)
    db.session.commit()
    logging.info("ADMIN %s deleted user '%s'", current_user.username, username)
    flash("User '%s' deleted." % username)
    return redirect(url_for("main.admin_panel"))


# ERROR HANDLERS
@main.app_errorhandler(400)
def bad_request(e):
    return render_template("error.html", code=400,
                           msg="Bad request. Your form may have expired - please try again."), 400


@main.app_errorhandler(401)
def unauthorized(e):
    return render_template("error.html", code=401,
                           msg="Please log in to continue."), 401


@main.app_errorhandler(403)
def forbidden(e):
    return render_template("error.html", code=403,
                           msg="You do not have permission to access this page."), 403


@main.app_errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404,
                           msg="The page you asked for was not found."), 404


@main.app_errorhandler(429)
def too_many(e):
    return render_template("error.html", code=429,
                           msg="Too many requests. Please wait a minute and try again."), 429


@main.app_errorhandler(500)
def server_error(e):
    logging.error("Server error: %s", e)
    return render_template("error.html", code=500,
                           msg="Something went wrong on our side."), 500