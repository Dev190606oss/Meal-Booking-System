from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.db import query_db, execute_db, call_proc
from app.utils import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# -------------------------------------------------------------------------
# 1. ADMIN DASHBOARD
# -------------------------------------------------------------------------
@admin_bp.route("/")
@admin_required
def dashboard():
    # Fetch KPIs using aggregate queries
    stats = query_db(
        """SELECT 
               (SELECT COUNT(*) FROM Customer WHERE is_admin = 0) AS total_customers,
               (SELECT COUNT(*) FROM Restaurant WHERE is_active = 1) AS total_restaurants,
               (SELECT COUNT(*) FROM Meal WHERE is_available = 1) AS total_meals,
               (SELECT COUNT(*) FROM Booking) AS total_bookings,
               (SELECT COALESCE(SUM(total_amount), 0) FROM Booking WHERE status != 'Cancelled') AS total_revenue,
               (SELECT COUNT(*) FROM Offer WHERE is_active = 1 AND valid_to >= NOW()) AS active_offers""",
        one=True
    )

    # Recent 5 Bookings
    recent_bookings = query_db(
        """SELECT b.*, c.full_name AS customer_name, r.name AS restaurant_name
           FROM Booking b
           JOIN Customer c ON b.customer_id = c.customer_id
           JOIN Restaurant r ON b.restaurant_id = r.restaurant_id
           ORDER BY b.booking_date DESC
           LIMIT 5"""
    )

    # Status distribution
    status_counts = query_db(
        """SELECT status, COUNT(*) AS count 
           FROM Booking 
           GROUP BY status"""
    )

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_bookings=recent_bookings,
        status_counts=status_counts
    )

# -------------------------------------------------------------------------
# 2. MANAGE RESTAURANTS (CRUD)
# -------------------------------------------------------------------------
@admin_bp.route("/restaurants", methods=["GET", "POST"])
@admin_required
def restaurants():
    if request.method == "POST":
        action = request.form.get("action", "create")

        if action == "create":
            name = request.form.get("name", "").strip()
            cuisine = request.form.get("cuisine", "").strip()
            location = request.form.get("location", "").strip()
            delivery_time = int(request.form.get("delivery_time_min", 30))
            min_order = float(request.form.get("min_order_value", 0.0))
            description = request.form.get("description", "").strip()
            image_url = request.form.get("image_url", "").strip() or "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&q=80"

            if name and cuisine and location:
                execute_db(
                    """INSERT INTO Restaurant (name, cuisine, location, delivery_time_min, min_order_value, description, image_url, is_active)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, 1)""",
                    (name, cuisine, location, delivery_time, min_order, description, image_url)
                )
                flash(f"Restaurant '{name}' added successfully!", "success")
            else:
                flash("Name, cuisine, and location are required.", "danger")

        elif action == "edit":
            restaurant_id = int(request.form.get("restaurant_id"))
            name = request.form.get("name", "").strip()
            cuisine = request.form.get("cuisine", "").strip()
            location = request.form.get("location", "").strip()
            delivery_time = int(request.form.get("delivery_time_min", 30))
            min_order = float(request.form.get("min_order_value", 0.0))
            description = request.form.get("description", "").strip()
            image_url = request.form.get("image_url", "").strip()
            is_active = 1 if request.form.get("is_active") == "1" else 0

            execute_db(
                """UPDATE Restaurant 
                   SET name = %s, cuisine = %s, location = %s, delivery_time_min = %s, 
                       min_order_value = %s, description = %s, image_url = %s, is_active = %s
                   WHERE restaurant_id = %s""",
                (name, cuisine, location, delivery_time, min_order, description, image_url, is_active, restaurant_id)
            )
            flash(f"Restaurant '{name}' updated successfully.", "success")

        elif action == "delete":
            restaurant_id = int(request.form.get("restaurant_id"))
            execute_db("DELETE FROM Restaurant WHERE restaurant_id = %s", (restaurant_id,))
            flash("Restaurant and all its associated meals deleted.", "info")

        return redirect(url_for("admin.restaurants"))

    restaurant_list = query_db(
        """SELECT r.*, COUNT(m.meal_id) AS total_meals
           FROM Restaurant r
           LEFT JOIN Meal m ON r.restaurant_id = m.restaurant_id
           GROUP BY r.restaurant_id
           ORDER BY r.restaurant_id DESC"""
    )
    return render_template("admin/restaurants.html", restaurants=restaurant_list)

# -------------------------------------------------------------------------
# 3. MANAGE MEALS (CRUD)
# -------------------------------------------------------------------------
@admin_bp.route("/meals", methods=["GET", "POST"])
@admin_required
def meals():
    if request.method == "POST":
        action = request.form.get("action", "create")

        if action == "create":
            restaurant_id = int(request.form.get("restaurant_id"))
            name = request.form.get("name", "").strip()
            category = request.form.get("category", "").strip()
            price = float(request.form.get("price", 0.0))
            is_veg = 1 if request.form.get("is_veg") == "1" else 0
            is_available = 1 if request.form.get("is_available") == "1" else 0
            description = request.form.get("description", "").strip()
            image_url = request.form.get("image_url", "").strip() or "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&q=80"

            if name and category and price > 0:
                execute_db(
                    """INSERT INTO Meal (restaurant_id, name, category, price, is_veg, is_available, description, image_url)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (restaurant_id, name, category, price, is_veg, is_available, description, image_url)
                )
                flash(f"Meal '{name}' created successfully!", "success")
            else:
                flash("Name, category, and a positive price are required.", "danger")

        elif action == "edit":
            meal_id = int(request.form.get("meal_id"))
            restaurant_id = int(request.form.get("restaurant_id"))
            name = request.form.get("name", "").strip()
            category = request.form.get("category", "").strip()
            price = float(request.form.get("price", 0.0))
            is_veg = 1 if request.form.get("is_veg") == "1" else 0
            is_available = 1 if request.form.get("is_available") == "1" else 0
            description = request.form.get("description", "").strip()
            image_url = request.form.get("image_url", "").strip()

            execute_db(
                """UPDATE Meal 
                   SET restaurant_id = %s, name = %s, category = %s, price = %s, 
                       is_veg = %s, is_available = %s, description = %s, image_url = %s
                   WHERE meal_id = %s""",
                (restaurant_id, name, category, price, is_veg, is_available, description, image_url, meal_id)
            )
            flash(f"Meal '{name}' updated successfully.", "success")

        elif action == "delete":
            meal_id = int(request.form.get("meal_id"))
            execute_db("DELETE FROM Meal WHERE meal_id = %s", (meal_id,))
            flash("Meal deleted successfully.", "info")

        elif action == "toggle_availability":
            meal_id = int(request.form.get("meal_id"))
            execute_db("UPDATE Meal SET is_available = NOT is_available WHERE meal_id = %s", (meal_id,))
            flash("Meal availability toggled.", "success")

        return redirect(url_for("admin.meals"))

    meals_list = query_db(
        """SELECT m.*, r.name AS restaurant_name
           FROM Meal m
           JOIN Restaurant r ON m.restaurant_id = r.restaurant_id
           ORDER BY m.meal_id DESC"""
    )
    restaurants = query_db("SELECT restaurant_id, name FROM Restaurant WHERE is_active = 1 ORDER BY name ASC")
    categories = ["North Indian", "South Indian", "Chinese", "Fast Food", "Desserts", "Beverages"]

    return render_template(
        "admin/meals.html",
        meals=meals_list,
        restaurants=restaurants,
        categories=categories
    )

# -------------------------------------------------------------------------
# 4. MANAGE OFFERS (CRUD)
# -------------------------------------------------------------------------
@admin_bp.route("/offers", methods=["GET", "POST"])
@admin_required
def offers():
    if request.method == "POST":
        action = request.form.get("action", "create")

        if action == "create":
            code = request.form.get("code", "").strip().upper()
            description = request.form.get("description", "").strip()
            discount_pct = int(request.form.get("discount_pct", 10))
            max_discount = float(request.form.get("max_discount", 100.0))
            min_order = float(request.form.get("min_order_amount", 0.0))
            valid_from = request.form.get("valid_from")
            valid_to = request.form.get("valid_to")

            if code and description and valid_from and valid_to:
                execute_db(
                    """INSERT INTO Offer (code, description, discount_pct, max_discount, min_order_amount, valid_from, valid_to, is_active)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, 1)""",
                    (code, description, discount_pct, max_discount, min_order, valid_from, valid_to)
                )
                flash(f"Coupon '{code}' added successfully!", "success")
            else:
                flash("All offer fields are required.", "danger")

        elif action == "toggle_active":
            offer_id = int(request.form.get("offer_id"))
            execute_db("UPDATE Offer SET is_active = NOT is_active WHERE offer_id = %s", (offer_id,))
            flash("Offer status updated.", "info")

        elif action == "delete":
            offer_id = int(request.form.get("offer_id"))
            execute_db("DELETE FROM Offer WHERE offer_id = %s", (offer_id,))
            flash("Offer deleted.", "info")

        return redirect(url_for("admin.offers"))

    offers_list = query_db("SELECT * FROM Offer ORDER BY offer_id DESC")
    return render_template("admin/offers.html", offers=offers_list)

# -------------------------------------------------------------------------
# 5. MANAGE BOOKINGS
# -------------------------------------------------------------------------
@admin_bp.route("/bookings", methods=["GET", "POST"])
@admin_required
def bookings():
    if request.method == "POST":
        booking_id = int(request.form.get("booking_id"))
        new_status = request.form.get("status")
        valid_statuses = ['Pending', 'Confirmed', 'Preparing', 'Out for Delivery', 'Delivered', 'Cancelled']
        
        if new_status in valid_statuses:
            execute_db("UPDATE Booking SET status = %s WHERE booking_id = %s", (new_status, booking_id))
            
            # If marked delivered and payment was COD, update payment status to Paid
            if new_status == "Delivered":
                execute_db("UPDATE Payment SET payment_status = 'Paid' WHERE booking_id = %s", (booking_id,))
                
            flash(f"Booking status updated to '{new_status}'.", "success")
        return redirect(url_for("admin.bookings"))

    status_filter = request.args.get("status", "")
    sql = """
        SELECT b.*, c.full_name AS customer_name, c.phone AS customer_phone,
               r.name AS restaurant_name, p.transaction_ref,
               GROUP_CONCAT(CONCAT(bi.quantity, 'x ', m.name) SEPARATOR ', ') AS item_summary
        FROM Booking b
        JOIN Customer c ON b.customer_id = c.customer_id
        JOIN Restaurant r ON b.restaurant_id = r.restaurant_id
        JOIN Booking_Item bi ON b.booking_id = bi.booking_id
        JOIN Meal m ON bi.meal_id = m.meal_id
        LEFT JOIN Payment p ON b.booking_id = p.booking_id
    """
    args = []
    if status_filter:
        sql += " WHERE b.status = %s"
        args.append(status_filter)

    sql += " GROUP BY b.booking_id ORDER BY b.booking_date DESC"
    booking_list = query_db(sql, args)

    return render_template(
        "admin/bookings.html",
        bookings=booking_list,
        selected_status=status_filter,
        statuses=['Pending', 'Confirmed', 'Preparing', 'Out for Delivery', 'Delivered', 'Cancelled']
    )

# -------------------------------------------------------------------------
# 6. MANAGE CUSTOMERS
# -------------------------------------------------------------------------
@admin_bp.route("/customers")
@admin_required
def customers():
    customer_list = query_db(
        """SELECT c.customer_id, c.full_name, c.email, c.phone, c.address, c.created_at,
                  COUNT(b.booking_id) AS total_orders,
                  COALESCE(SUM(CASE WHEN b.status != 'Cancelled' THEN b.total_amount ELSE 0 END), 0) AS total_spent
           FROM Customer c
           LEFT JOIN Booking b ON c.customer_id = b.customer_id
           WHERE c.is_admin = 0
           GROUP BY c.customer_id
           ORDER BY total_spent DESC"""
    )
    return render_template("admin/customers.html", customers=customer_list)

# -------------------------------------------------------------------------
# 7. DATABASE ANALYTICS & REPORTS (DBMS Aggregates Showcase)
# -------------------------------------------------------------------------
@admin_bp.route("/analytics")
@admin_required
def analytics():
    # 1. Most ordered meals
    top_meals = query_db(
        """SELECT m.name AS meal_name, m.category, r.name AS restaurant_name,
                  COUNT(bi.booking_item_id) AS order_count,
                  SUM(bi.quantity) AS total_quantity,
                  SUM(bi.subtotal) AS gross_sales
           FROM Meal m
           JOIN Restaurant r ON m.restaurant_id = r.restaurant_id
           JOIN Booking_Item bi ON m.meal_id = bi.meal_id
           JOIN Booking b ON bi.booking_id = b.booking_id
           WHERE b.status != 'Cancelled'
           GROUP BY m.meal_id, m.name, m.category, r.name
           ORDER BY total_quantity DESC
           LIMIT 5"""
    )

    # 2. Revenue by restaurant
    restaurant_revenue = query_db(
        """SELECT r.name AS restaurant_name, r.location,
                  COUNT(b.booking_id) AS total_orders,
                  COALESCE(SUM(b.total_amount), 0) AS total_revenue
           FROM Restaurant r
           LEFT JOIN Booking b ON r.restaurant_id = b.restaurant_id AND b.status != 'Cancelled'
           GROUP BY r.restaurant_id, r.name, r.location
           ORDER BY total_revenue DESC"""
    )

    # 3. Status Distribution
    status_distribution = query_db(
        """SELECT status, COUNT(*) AS count,
                  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM Booking), 1) AS percentage
           FROM Booking
           GROUP BY status
           ORDER BY count DESC"""
    )

    # 4. Ratings summary
    ratings_summary = query_db(
        """SELECT f.rating, COUNT(*) AS count
           FROM Feedback f
           GROUP BY f.rating
           ORDER BY f.rating DESC"""
    )

    # 5. Average Order Value and General Metrics
    overview = query_db(
        """SELECT 
               ROUND(AVG(total_amount), 2) AS avg_order_value,
               MAX(total_amount) AS max_order_value,
               MIN(total_amount) AS min_order_value,
               ROUND(AVG(subtotal), 2) AS avg_subtotal,
               ROUND(SUM(discount_amount), 2) AS total_discounts_given
           FROM Booking
           WHERE status != 'Cancelled'""",
        one=True
    )

    return render_template(
        "admin/analytics.html",
        top_meals=top_meals,
        restaurant_revenue=restaurant_revenue,
        status_distribution=status_distribution,
        ratings_summary=ratings_summary,
        overview=overview
    )
