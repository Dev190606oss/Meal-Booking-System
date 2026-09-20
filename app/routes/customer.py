from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.db import query_db, execute_db, get_transaction_cursor
from app.utils import login_required, generate_booking_code, calculate_cart_totals
import time

customer_bp = Blueprint("customer", __name__)

# -------------------------------------------------------------------------
# 1. HOME / LANDING PAGE
# -------------------------------------------------------------------------
@customer_bp.route("/")
def home():
    # Featured Top Rated Restaurants
    featured_restaurants = query_db(
        """SELECT r.*, COUNT(m.meal_id) AS total_meals
           FROM Restaurant r
           LEFT JOIN Meal m ON r.restaurant_id = m.restaurant_id AND m.is_available = 1
           WHERE r.is_active = 1
           GROUP BY r.restaurant_id
           ORDER BY r.rating DESC, r.name ASC
           LIMIT 6"""
    )

    # Popular Meals across Pune
    popular_meals = query_db(
        """SELECT m.*, r.name AS restaurant_name, r.location AS restaurant_location
           FROM Meal m
           JOIN Restaurant r ON m.restaurant_id = r.restaurant_id
           WHERE m.is_available = 1 AND r.is_active = 1
           ORDER BY m.rating DESC, m.price ASC
           LIMIT 8"""
    )

    # Active Promotions
    active_offers = query_db(
        """SELECT * FROM Offer 
           WHERE is_active = 1 AND valid_from <= NOW() AND valid_to >= NOW()
           ORDER BY discount_pct DESC
           LIMIT 3"""
    )

    categories = [
        {"name": "North Indian", "icon": "fa-bowl-food", "image": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&q=80"},
        {"name": "South Indian", "icon": "fa-plate-wheat", "image": "https://images.unsplash.com/photo-1610057099443-fde8c4d50f91?w=400&q=80"},
        {"name": "Chinese", "icon": "fa-fire-burner", "image": "https://images.unsplash.com/photo-1541696432-82c6da8ce7bf?w=400&q=80"},
        {"name": "Fast Food", "icon": "fa-burger", "image": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&q=80"},
        {"name": "Desserts", "icon": "fa-ice-cream", "image": "https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=400&q=80"},
        {"name": "Beverages", "icon": "fa-mug-hot", "image": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=400&q=80"}
    ]

    return render_template(
        "home.html",
        featured_restaurants=featured_restaurants,
        popular_meals=popular_meals,
        active_offers=active_offers,
        categories=categories
    )

# -------------------------------------------------------------------------
# 2. RESTAURANTS CATALOG & DETAIL
# -------------------------------------------------------------------------
@customer_bp.route("/restaurants")
def restaurants():
    cuisine_filter = request.args.get("cuisine", "").strip()
    location_filter = request.args.get("location", "").strip()
    search_query = request.args.get("q", "").strip()

    sql = """
        SELECT r.*, COUNT(m.meal_id) AS total_meals, 
               COALESCE(MIN(m.price), 0) AS min_price,
               COALESCE(MAX(m.price), 0) AS max_price
        FROM Restaurant r
        LEFT JOIN Meal m ON r.restaurant_id = m.restaurant_id AND m.is_available = 1
        WHERE r.is_active = 1
    """
    args = []

    if search_query:
        sql += " AND (r.name LIKE %s OR r.cuisine LIKE %s OR r.location LIKE %s)"
        pattern = f"%{search_query}%"
        args.extend([pattern, pattern, pattern])

    if cuisine_filter:
        sql += " AND r.cuisine LIKE %s"
        args.append(f"%{cuisine_filter}%")

    if location_filter:
        sql += " AND r.location = %s"
        args.append(location_filter)

    sql += " GROUP BY r.restaurant_id ORDER BY r.rating DESC, r.name ASC"

    restaurant_list = query_db(sql, args)
    locations = query_db("SELECT DISTINCT location FROM Restaurant WHERE is_active = 1 ORDER BY location ASC")

    return render_template(
        "restaurants.html",
        restaurants=restaurant_list,
        locations=[l["location"] for l in locations],
        selected_location=location_filter,
        selected_cuisine=cuisine_filter,
        search_query=search_query
    )

@customer_bp.route("/restaurants/<int:restaurant_id>")
def restaurant_detail(restaurant_id):
    restaurant = query_db(
        "SELECT * FROM Restaurant WHERE restaurant_id = %s AND is_active = 1",
        (restaurant_id,),
        one=True
    )
    if not restaurant:
        flash("Restaurant not found or currently closed.", "warning")
        return redirect(url_for("customer.restaurants"))

    # Fetch meals grouped by category
    meals = query_db(
        """SELECT * FROM Meal 
           WHERE restaurant_id = %s AND is_available = 1 
           ORDER BY category ASC, rating DESC, price ASC""",
        (restaurant_id,)
    )

    # Group meals by category
    categorized_meals = {}
    for m in meals:
        cat = m["category"]
        if cat not in categorized_meals:
            categorized_meals[cat] = []
        categorized_meals[cat].append(m)

    return render_template(
        "restaurant_detail.html",
        restaurant=restaurant,
        categorized_meals=categorized_meals,
        total_meals=len(meals)
    )

# -------------------------------------------------------------------------
# 3. MEALS CATALOG (SEARCH, FILTERS, SORTS)
# -------------------------------------------------------------------------
@customer_bp.route("/meals")
def meals():
    search_query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    restaurant_id = request.args.get("restaurant_id", "").strip()
    veg_only = request.args.get("veg", "").strip()
    sort_by = request.args.get("sort", "rating_desc").strip()
    max_price = request.args.get("max_price", "").strip()

    sql = """
        SELECT m.*, r.name AS restaurant_name, r.location AS restaurant_location, r.cuisine AS restaurant_cuisine
        FROM Meal m
        JOIN Restaurant r ON m.restaurant_id = r.restaurant_id
        WHERE m.is_available = 1 AND r.is_active = 1
    """
    args = []

    if search_query:
        sql += " AND (m.name LIKE %s OR m.category LIKE %s OR r.name LIKE %s OR m.description LIKE %s)"
        pattern = f"%{search_query}%"
        args.extend([pattern, pattern, pattern, pattern])

    if category:
        sql += " AND m.category = %s"
        args.append(category)

    if restaurant_id and restaurant_id.isdigit():
        sql += " AND m.restaurant_id = %s"
        args.append(int(restaurant_id))

    if veg_only == "1":
        sql += " AND m.is_veg = 1"

    if max_price and max_price.isdigit():
        sql += " AND m.price <= %s"
        args.append(float(max_price))

    # Sorting
    if sort_by == "price_asc":
        sql += " ORDER BY m.price ASC"
    elif sort_by == "price_desc":
        sql += " ORDER BY m.price DESC"
    elif sort_by == "rating_desc":
        sql += " ORDER BY m.rating DESC, m.price ASC"
    elif sort_by == "name_asc":
        sql += " ORDER BY m.name ASC"
    else:
        sql += " ORDER BY m.rating DESC"

    meal_list = query_db(sql, args)
    restaurants = query_db("SELECT restaurant_id, name FROM Restaurant WHERE is_active = 1 ORDER BY name ASC")
    categories = ["North Indian", "South Indian", "Chinese", "Fast Food", "Desserts", "Beverages"]

    return render_template(
        "meals.html",
        meals=meal_list,
        categories=categories,
        restaurants=restaurants,
        selected_category=category,
        selected_restaurant=restaurant_id,
        veg_only=veg_only,
        sort_by=sort_by,
        max_price=max_price,
        search_query=search_query
    )

@customer_bp.route("/meals/<int:meal_id>")
def meal_detail(meal_id):
    meal = query_db(
        """SELECT m.*, r.name AS restaurant_name, r.location AS restaurant_location, r.rating AS restaurant_rating
           FROM Meal m
           JOIN Restaurant r ON m.restaurant_id = r.restaurant_id
           WHERE m.meal_id = %s""",
        (meal_id,),
        one=True
    )
    if not meal:
        flash("Meal not found.", "warning")
        return redirect(url_for("customer.meals"))

    reviews = query_db(
        """SELECT f.*, c.full_name AS customer_name
           FROM Feedback f
           JOIN Customer c ON f.customer_id = c.customer_id
           WHERE f.meal_id = %s
           ORDER BY f.created_at DESC
           LIMIT 5""",
        (meal_id,)
    )

    return render_template("meal_detail.html", meal=meal, reviews=reviews)

# -------------------------------------------------------------------------
# 4. CART & OFFER INTERACTIONS
# -------------------------------------------------------------------------
@customer_bp.route("/cart")
def cart():
    cart_dict = session.get("cart", {})
    offer_code = session.get("applied_offer_code")
    cart_data = calculate_cart_totals(cart_dict, offer_code)
    
    # If the applied coupon became invalid (e.g. min subtotal not met)
    if offer_code and not cart_data["applied_offer"] and cart_data["offer_error"]:
        flash(cart_data["offer_error"], "warning")
        session.pop("applied_offer_code", None)

    active_offers = query_db(
        "SELECT * FROM Offer WHERE is_active = 1 AND valid_to >= NOW() ORDER BY discount_pct DESC"
    )

    return render_template("cart.html", cart=cart_data, active_offers=active_offers)

@customer_bp.route("/cart/add", methods=["POST"])
def cart_add():
    meal_id = request.form.get("meal_id")
    quantity = int(request.form.get("quantity", 1))

    if not meal_id:
        return jsonify({"success": False, "message": "Meal ID is required."}), 400

    meal = query_db(
        "SELECT meal_id, restaurant_id, name, is_available FROM Meal WHERE meal_id = %s",
        (meal_id,),
        one=True
    )
    if not meal or not meal["is_available"]:
        return jsonify({"success": False, "message": "Meal is unavailable."}), 400

    cart_dict = session.get("cart", {})

    # Check restaurant consistency: cart can only contain meals from one restaurant at a time
    if cart_dict:
        sample_mid = next(iter(cart_dict.keys()))
        existing_meal = query_db("SELECT restaurant_id FROM Meal WHERE meal_id = %s", (sample_mid,), one=True)
        if existing_meal and existing_meal["restaurant_id"] != meal["restaurant_id"]:
            # Restaurant conflict
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({
                    "success": False,
                    "conflict": True,
                    "message": "Your cart contains meals from another restaurant. Would you like to reset your cart?"
                }), 409
            flash("Your cart was reset because items must be from the same restaurant.", "info")
            cart_dict = {}

    cart_dict[str(meal_id)] = cart_dict.get(str(meal_id), 0) + quantity
    session["cart"] = cart_dict

    total_count = sum(cart_dict.values())
    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({
            "success": True,
            "message": f"Added {meal['name']} to cart!",
            "cart_count": total_count
        })

    flash(f"Added {meal['name']} to your cart!", "success")
    return redirect(request.referrer or url_for("customer.cart"))

@customer_bp.route("/cart/update", methods=["POST"])
def cart_update():
    meal_id = request.form.get("meal_id")
    quantity = int(request.form.get("quantity", 1))

    cart_dict = session.get("cart", {})
    if meal_id in cart_dict:
        if quantity > 0:
            cart_dict[meal_id] = quantity
        else:
            cart_dict.pop(meal_id, None)
    
    session["cart"] = cart_dict
    offer_code = session.get("applied_offer_code")
    cart_data = calculate_cart_totals(cart_dict, offer_code)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({
            "success": True,
            "cart": cart_data,
            "cart_count": sum(cart_dict.values())
        })

    return redirect(url_for("customer.cart"))

@customer_bp.route("/cart/remove", methods=["POST"])
def cart_remove():
    meal_id = request.form.get("meal_id")
    cart_dict = session.get("cart", {})
    if meal_id in cart_dict:
        cart_dict.pop(meal_id, None)
    session["cart"] = cart_dict
    flash("Item removed from cart.", "info")
    return redirect(url_for("customer.cart"))

@customer_bp.route("/cart/apply-offer", methods=["POST"])
def cart_apply_offer():
    code = request.form.get("offer_code", "").strip().upper()
    cart_dict = session.get("cart", {})
    cart_data = calculate_cart_totals(cart_dict, code)

    if cart_data["applied_offer"]:
        session["applied_offer_code"] = code
        flash(f"Coupon {code} applied successfully! You saved ₹{cart_data['discount']:.2f}", "success")
    else:
        err = cart_data["offer_error"] or "Could not apply coupon."
        flash(err, "danger")

    return redirect(url_for("customer.cart"))

@customer_bp.route("/cart/remove-offer", methods=["POST"])
def cart_remove_offer():
    session.pop("applied_offer_code", None)
    flash("Promo code removed.", "info")
    return redirect(url_for("customer.cart"))

@customer_bp.route("/cart/clear", methods=["POST"])
def cart_clear():
    session.pop("cart", None)
    session.pop("applied_offer_code", None)
    flash("Cart cleared.", "info")
    return redirect(url_for("customer.restaurants"))

# -------------------------------------------------------------------------
# 5. CHECKOUT & BOOKING PLACEMENT
# -------------------------------------------------------------------------
@customer_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart_dict = session.get("cart", {})
    offer_code = session.get("applied_offer_code")
    cart_data = calculate_cart_totals(cart_dict, offer_code)

    if not cart_data["items"]:
        flash("Your cart is empty. Add meals before checking out.", "warning")
        return redirect(url_for("customer.restaurants"))

    customer = query_db(
        "SELECT * FROM Customer WHERE customer_id = %s",
        (session["customer_id"],),
        one=True
    )

    if request.method == "POST":
        delivery_address = request.form.get("delivery_address", "").strip()
        phone = request.form.get("phone", "").strip()
        payment_method = request.form.get("payment_method", "COD").strip()
        special_instructions = request.form.get("special_instructions", "").strip()

        if not delivery_address or not phone:
            flash("Please provide a valid delivery address and phone number.", "danger")
            return render_template("checkout.html", cart=cart_data, customer=customer)

        if payment_method not in ["COD", "UPI", "Card"]:
            payment_method = "COD"

        booking_code = generate_booking_code()
        restaurant_id = cart_data["restaurant_id"]
        offer_id = cart_data["applied_offer"]["offer_id"] if cart_data["applied_offer"] else None
        
        # Payment status simulation
        payment_status = "Paid" if payment_method in ["UPI", "Card"] else "Pending"

        try:
            with get_transaction_cursor() as cursor:
                # 1. Insert into Booking
                cursor.execute(
                    """INSERT INTO Booking 
                       (booking_code, customer_id, restaurant_id, status, subtotal, discount_amount, delivery_fee, 
                        total_amount, delivery_address, payment_method, payment_status, offer_id, special_instructions)
                       VALUES (%s, %s, %s, 'Confirmed', %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        booking_code,
                        session["customer_id"],
                        restaurant_id,
                        cart_data["subtotal"],
                        cart_data["discount"],
                        cart_data["delivery_fee"],
                        cart_data["grand_total"],
                        delivery_address,
                        payment_method,
                        payment_status,
                        offer_id,
                        special_instructions
                    )
                )
                booking_id = cursor.lastrowid

                # 2. Insert Booking_Item records
                for itm in cart_data["items"]:
                    cursor.execute(
                        """INSERT INTO Booking_Item 
                           (booking_id, meal_id, quantity, price_at_booking, subtotal)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (
                            booking_id,
                            itm["meal_id"],
                            itm["quantity"],
                            itm["price"],
                            itm["subtotal"]
                        )
                    )

                # 3. Insert Payment record
                txn_ref = f"TXN_{payment_method}_{int(time.time())}_{booking_id}"
                cursor.execute(
                    """INSERT INTO Payment 
                       (booking_id, payment_method, amount, payment_status, transaction_ref)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (
                        booking_id,
                        payment_method,
                        cart_data["grand_total"],
                        payment_status,
                        txn_ref
                    )
                )

            # Clear session cart on successful transaction
            session.pop("cart", None)
            session.pop("applied_offer_code", None)

            flash("Your meal booking has been placed successfully!", "success")
            return redirect(url_for("customer.order_confirmation", booking_code=booking_code))

        except Exception as e:
            flash(f"Error processing booking: {str(e)}", "danger")
            return render_template("checkout.html", cart=cart_data, customer=customer)

    return render_template("checkout.html", cart=cart_data, customer=customer)

# -------------------------------------------------------------------------
# 6. ORDER CONFIRMATION & TRACKING
# -------------------------------------------------------------------------
@customer_bp.route("/order-confirmation/<booking_code>")
@login_required
def order_confirmation(booking_code):
    booking = query_db(
        """SELECT b.*, r.name AS restaurant_name, r.location AS restaurant_location,
                  r.delivery_time_min, p.transaction_ref
           FROM Booking b
           JOIN Restaurant r ON b.restaurant_id = r.restaurant_id
           LEFT JOIN Payment p ON b.booking_id = p.booking_id
           WHERE b.booking_code = %s AND b.customer_id = %s""",
        (booking_code, session["customer_id"]),
        one=True
    )
    if not booking:
        flash("Order confirmation not found.", "warning")
        return redirect(url_for("customer.orders"))

    items = query_db(
        """SELECT bi.*, m.name AS meal_name, m.is_veg
           FROM Booking_Item bi
           JOIN Meal m ON bi.meal_id = m.meal_id
           WHERE bi.booking_id = %s""",
        (booking["booking_id"],)
    )

    return render_template("order_confirmation.html", booking=booking, items=items)

# -------------------------------------------------------------------------
# 7. MY ORDERS & ORDER DETAILS
# -------------------------------------------------------------------------
@customer_bp.route("/orders")
@login_required
def orders():
    customer_orders = query_db(
        """SELECT b.*, r.name AS restaurant_name, r.location AS restaurant_location,
                  COUNT(bi.booking_item_id) AS items_count,
                  GROUP_CONCAT(CONCAT(bi.quantity, 'x ', m.name) SEPARATOR ', ') AS item_summary
           FROM Booking b
           JOIN Restaurant r ON b.restaurant_id = r.restaurant_id
           JOIN Booking_Item bi ON b.booking_id = bi.booking_id
           JOIN Meal m ON bi.meal_id = m.meal_id
           WHERE b.customer_id = %s
           GROUP BY b.booking_id
           ORDER BY b.booking_date DESC""",
        (session["customer_id"],)
    )
    return render_template("orders.html", orders=customer_orders)

@customer_bp.route("/orders/<booking_code>")
@login_required
def order_detail(booking_code):
    booking = query_db(
        """SELECT b.*, r.name AS restaurant_name, r.location AS restaurant_location,
                  r.cuisine AS restaurant_cuisine, p.transaction_ref, o.code AS offer_code
           FROM Booking b
           JOIN Restaurant r ON b.restaurant_id = r.restaurant_id
           LEFT JOIN Payment p ON b.booking_id = p.booking_id
           LEFT JOIN Offer o ON b.offer_id = o.offer_id
           WHERE b.booking_code = %s AND b.customer_id = %s""",
        (booking_code, session["customer_id"]),
        one=True
    )
    if not booking:
        flash("Order not found.", "warning")
        return redirect(url_for("customer.orders"))

    items = query_db(
        """SELECT bi.*, m.name AS meal_name, m.is_veg, m.image_url,
                  f.rating AS feedback_rating, f.comment AS feedback_comment
           FROM Booking_Item bi
           JOIN Meal m ON bi.meal_id = m.meal_id
           LEFT JOIN Feedback f ON f.booking_id = bi.booking_id AND f.meal_id = bi.meal_id
           WHERE bi.booking_id = %s""",
        (booking["booking_id"],)
    )

    # General booking feedback
    booking_feedback = query_db(
        "SELECT * FROM Feedback WHERE booking_id = %s AND meal_id IS NULL",
        (booking["booking_id"],),
        one=True
    )

    return render_template(
        "order_detail.html",
        booking=booking,
        items=items,
        booking_feedback=booking_feedback
    )

# -------------------------------------------------------------------------
# 8. FEEDBACK SUBMISSION
# -------------------------------------------------------------------------
@customer_bp.route("/orders/<booking_code>/feedback", methods=["POST"])
@login_required
def submit_feedback(booking_code):
    booking = query_db(
        "SELECT booking_id, status FROM Booking WHERE booking_code = %s AND customer_id = %s",
        (booking_code, session["customer_id"]),
        one=True
    )
    if not booking:
        flash("Invalid booking.", "danger")
        return redirect(url_for("customer.orders"))

    if booking["status"] != "Delivered":
        flash("Feedback can only be submitted for delivered orders.", "warning")
        return redirect(url_for("customer.order_detail", booking_code=booking_code))

    rating = int(request.form.get("rating", 5))
    comment = request.form.get("comment", "").strip()
    meal_id = request.form.get("meal_id")
    meal_id = int(meal_id) if meal_id and meal_id.isdigit() else None

    # Check if already reviewed
    existing = query_db(
        "SELECT feedback_id FROM Feedback WHERE booking_id = %s AND customer_id = %s AND (meal_id = %s OR (meal_id IS NULL AND %s IS NULL))",
        (booking["booking_id"], session["customer_id"], meal_id, meal_id),
        one=True
    )

    if existing:
        execute_db(
            "UPDATE Feedback SET rating = %s, comment = %s WHERE feedback_id = %s",
            (rating, comment, existing["feedback_id"])
        )
        flash("Your review has been updated! Thank you.", "success")
    else:
        execute_db(
            """INSERT INTO Feedback (customer_id, booking_id, meal_id, rating, comment)
               VALUES (%s, %s, %s, %s, %s)""",
            (session["customer_id"], booking["booking_id"], meal_id, rating, comment)
        )
        flash("Thank you for your valuable feedback!", "success")

    return redirect(url_for("customer.order_detail", booking_code=booking_code))

# -------------------------------------------------------------------------
# 9. OFFERS PAGE
# -------------------------------------------------------------------------
@customer_bp.route("/offers")
def offers():
    active_offers = query_db(
        """SELECT * FROM Offer 
           WHERE is_active = 1 AND valid_to >= NOW() 
           ORDER BY discount_pct DESC"""
    )
    expired_offers = query_db(
        """SELECT * FROM Offer 
           WHERE is_active = 0 OR valid_to < NOW() 
           ORDER BY valid_to DESC"""
    )
    return render_template("offers.html", active_offers=active_offers, expired_offers=expired_offers)

# -------------------------------------------------------------------------
# 10. CUSTOMER PROFILE
# -------------------------------------------------------------------------
@customer_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    customer_id = session["customer_id"]

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        if full_name and phone and address:
            execute_db(
                "UPDATE Customer SET full_name = %s, phone = %s, address = %s WHERE customer_id = %s",
                (full_name, phone, address, customer_id)
            )
            session["full_name"] = full_name
            session["phone"] = phone
            session["address"] = address
            flash("Profile updated successfully.", "success")
        else:
            flash("All fields are required.", "danger")

    customer = query_db("SELECT * FROM Customer WHERE customer_id = %s", (customer_id,), one=True)
    
    # DBMS Aggregate queries for customer summary
    stats = query_db(
        """SELECT 
               COUNT(b.booking_id) AS total_orders,
               COALESCE(SUM(CASE WHEN b.status != 'Cancelled' THEN b.total_amount ELSE 0 END), 0) AS total_spent,
               COALESCE(ROUND(AVG(CASE WHEN b.status != 'Cancelled' THEN b.total_amount ELSE NULL END), 2), 0) AS avg_order_value,
               SUM(CASE WHEN b.status = 'Delivered' THEN 1 ELSE 0 END) AS delivered_orders
           FROM Customer c
           LEFT JOIN Booking b ON c.customer_id = b.customer_id
           WHERE c.customer_id = %s
           GROUP BY c.customer_id""",
        (customer_id,),
        one=True
    )

    # Favorite restaurant / cuisine
    fav_cuisine = query_db(
        """SELECT r.cuisine, COUNT(*) AS count
           FROM Booking b
           JOIN Restaurant r ON b.restaurant_id = r.restaurant_id
           WHERE b.customer_id = %s AND b.status != 'Cancelled'
           GROUP BY r.cuisine
           ORDER BY count DESC
           LIMIT 1""",
        (customer_id,),
        one=True
    )

    return render_template(
        "profile.html",
        customer=customer,
        stats=stats,
        fav_cuisine=fav_cuisine["cuisine"] if fav_cuisine else "Exploring"
    )
