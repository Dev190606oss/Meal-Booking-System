from functools import wraps
from flask import session, redirect, url_for, flash, request
import random
import time
from app.db import query_db

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "customer_id" not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "customer_id" not in session or not session.get("is_admin"):
            flash("Administrator privileges required to access this area.", "danger")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def generate_booking_code():
    """Generates unique booking code like MB1042."""
    prefix = "MB"
    suffix = random.randint(1000, 9999)
    # Check if exists, retry if collision
    while True:
        code = f"{prefix}{suffix}"
        row = query_db("SELECT booking_id FROM Booking WHERE booking_code = %s", (code,), one=True)
        if not row:
            return code
        suffix = random.randint(1000, 9999)

def calculate_cart_totals(cart_dict, offer_code=None):
    """
    Validates cart items against the MySQL database, ensuring up-to-date prices
    and calculates subtotal, discounts, delivery fee, and grand total.
    cart_dict structure: { meal_id_str: quantity_int }
    """
    if not cart_dict:
        return {
            "items": [],
            "total_items": 0,
            "subtotal": 0.0,
            "discount": 0.0,
            "delivery_fee": 0.0,
            "grand_total": 0.0,
            "restaurant_id": None,
            "restaurant_name": None,
            "applied_offer": None,
            "offer_error": None
        }

    meal_ids = list(map(int, cart_dict.keys()))
    if not meal_ids:
        return {
            "items": [],
            "total_items": 0,
            "subtotal": 0.0,
            "discount": 0.0,
            "delivery_fee": 0.0,
            "grand_total": 0.0,
            "restaurant_id": None,
            "restaurant_name": None,
            "applied_offer": None,
            "offer_error": None
        }

    placeholders = ", ".join(["%s"] * len(meal_ids))
    sql = f"""
        SELECT m.meal_id, m.name, m.category, m.price, m.is_veg, m.is_available,
               m.image_url, r.restaurant_id, r.name AS restaurant_name
        FROM Meal m
        JOIN Restaurant r ON m.restaurant_id = r.restaurant_id
        WHERE m.meal_id IN ({placeholders})
    """
    meals = query_db(sql, tuple(meal_ids))

    items = []
    subtotal = 0.0
    total_items = 0
    restaurant_id = None
    restaurant_name = None

    for m in meals:
        mid_str = str(m["meal_id"])
        qty = int(cart_dict.get(mid_str, 0))
        if qty <= 0:
            continue
        item_subtotal = float(m["price"]) * qty
        subtotal += item_subtotal
        total_items += qty
        restaurant_id = m["restaurant_id"]
        restaurant_name = m["restaurant_name"]

        items.append({
            "meal_id": m["meal_id"],
            "name": m["name"],
            "category": m["category"],
            "price": float(m["price"]),
            "is_veg": bool(m["is_veg"]),
            "is_available": bool(m["is_available"]),
            "image_url": m["image_url"],
            "quantity": qty,
            "subtotal": item_subtotal,
            "restaurant_id": m["restaurant_id"],
            "restaurant_name": m["restaurant_name"]
        })

    # Validate offer if requested
    discount = 0.0
    applied_offer = None
    offer_error = None

    if offer_code and subtotal > 0:
        offer = query_db(
            """SELECT offer_id, code, description, discount_pct, max_discount, 
                      min_order_amount, valid_from, valid_to, is_active
               FROM Offer WHERE code = %s""",
            (offer_code.strip().upper(),),
            one=True
        )

        if not offer:
            offer_error = "Invalid promo code."
        elif not offer["is_active"]:
            offer_error = "This promo code is inactive."
        else:
            # Check date
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            valid_from = str(offer["valid_from"])
            valid_to = str(offer["valid_to"])
            if now < valid_from or now > valid_to:
                offer_error = "This promo code has expired."
            elif subtotal < float(offer["min_order_amount"]):
                offer_error = f"Minimum order of ₹{float(offer['min_order_amount']):.0f} required for {offer['code']}."
            else:
                pct = float(offer["discount_pct"])
                max_disc = float(offer["max_discount"])
                calc_discount = round((subtotal * pct) / 100.0, 2)
                discount = min(calc_discount, max_disc)
                applied_offer = {
                    "offer_id": offer["offer_id"],
                    "code": offer["code"],
                    "description": offer["description"],
                    "discount_pct": offer["discount_pct"],
                    "discount_amount": discount
                }

    delivery_fee = 40.00 if subtotal > 0 else 0.0
    grand_total = max(0.0, round(subtotal - discount + delivery_fee, 2))

    return {
        "items": items,
        "total_items": total_items,
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "delivery_fee": delivery_fee,
        "grand_total": grand_total,
        "restaurant_id": restaurant_id,
        "restaurant_name": restaurant_name,
        "applied_offer": applied_offer,
        "offer_error": offer_error
    }
