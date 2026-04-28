from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.models.admin import Admin
from app.extensions import db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):
            login_user(admin)
            return redirect(url_for("admin.index"))

        flash("نام کاربری یا رمز عبور اشتباه است.", "danger")

    return render_template("admin/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("باموفقیت خارج شدید.")
    return redirect(url_for("auth.login"))
