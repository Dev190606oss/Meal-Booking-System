from flask import Flask, session
from app.config import Config
from datetime import datetime, timezone

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register Blueprints
    from app.routes.customer import customer_bp
    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(customer_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)

    # Custom Jinja Filters
    @app.template_filter("inr")
    def inr_filter(value):
        try:
            val = float(value)
            return f"₹{val:,.2f}"
        except (ValueError, TypeError):
            return f"₹{value}"

    @app.template_filter("format_dt")
    def format_dt_filter(value, fmt="%d %b %Y, %I:%M %p"):
        if not value:
            return ""
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except Exception:
                return value
        return value.strftime(fmt)

    # Context Processors for Templates
    @app.context_processor
    def inject_globals():
        cart_dict = session.get("cart", {})
        total_items = sum(cart_dict.values()) if isinstance(cart_dict, dict) else 0
        return {
            "current_user": {
                "id": session.get("customer_id"),
                "name": session.get("full_name"),
                "email": session.get("email"),
                "is_admin": session.get("is_admin", False),
                "phone": session.get("phone"),
                "address": session.get("address")
            },
            "cart_count": total_items
        }

    # Production Health Check Endpoint (For Render, Kubernetes, uptime monitors)
    @app.route("/health")
    def health_check():
        from app.db import test_db_connection
        db_status = test_db_connection()
        is_healthy = db_status["connected"] and db_status["database_exists"]
        status_code = 200 if is_healthy else 503
        return {
            "status": "healthy" if is_healthy else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": {
                "connected": db_status["connected"],
                "database_exists": db_status["database_exists"],
                "table_count": db_status["table_count"]
            }
        }, status_code

    # Error Handlers
    @app.errorhandler(404)
    def handle_not_found(e):
        from flask import render_template
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def handle_server_error(e):
        from flask import render_template
        return render_template("500.html"), 500

    return app
