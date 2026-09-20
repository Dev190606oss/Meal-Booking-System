from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import query_db, execute_db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please provide both email and password.", "danger")
            return render_template("login.html", email=email)

        user = query_db(
            "SELECT customer_id, full_name, email, password_hash, is_admin, phone, address FROM Customer WHERE email = %s",
            (email,),
            one=True
        )

        if user and check_password_hash(user["password_hash"], password):
            session["customer_id"] = user["customer_id"]
            session["full_name"] = user["full_name"]
            session["email"] = user["email"]
            session["is_admin"] = bool(user["is_admin"])
            session["phone"] = user["phone"]
            session["address"] = user["address"]

            flash(f"Welcome back, {user['full_name']}!", "success")
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            if user["is_admin"]:
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("customer.home"))
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template("login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not all([full_name, email, phone, address, password]):
            flash("All fields are required.", "danger")
            return render_template("register.html", form_data=request.form)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("register.html", form_data=request.form)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html", form_data=request.form)

        # Check existing customer
        existing = query_db("SELECT customer_id FROM Customer WHERE email = %s", (email,), one=True)
        if existing:
            flash("An account with this email already exists. Please log in.", "warning")
            return redirect(url_for("auth.login"))

        password_hash = generate_password_hash(password)
        res = execute_db(
            """INSERT INTO Customer (full_name, email, password_hash, phone, address, is_admin)
               VALUES (%s, %s, %s, %s, %s, 0)""",
            (full_name, email, password_hash, phone, address)
        )

        session["customer_id"] = res["last_id"]
        session["full_name"] = full_name
        session["email"] = email
        session["is_admin"] = False
        session["phone"] = phone
        session["address"] = address

        flash("Account created successfully! Enjoy discovering delicious meals.", "success")
        return redirect(url_for("customer.home"))

    return render_template("register.html")

@auth_bp.route("/demo-login/<role>")
def demo_login(role):
    """1-Click login designed for fast portfolio review without manual typing."""
    if role == "admin":
        user = query_db("SELECT * FROM Customer WHERE email = 'admin@mealbooking.com'", one=True)
    else:
        user = query_db("SELECT * FROM Customer WHERE email = 'rahul.sharma@example.com'", one=True)

    if user:
        session["customer_id"] = user["customer_id"]
        session["full_name"] = user["full_name"]
        session["email"] = user["email"]
        session["is_admin"] = bool(user["is_admin"])
        session["phone"] = user["phone"]
        session["address"] = user["address"]
        flash(f"Logged in as Demo {role.capitalize()} ({user['full_name']})", "info")
        if user["is_admin"]:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("customer.home"))
    
    flash("Demo user not found in database.", "danger")
    return redirect(url_for("auth.login"))

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("customer.home"))
