import unittest
import os
import sys
import pymysql

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.config import Config
from app.db import query_db, execute_db, call_proc, get_db_connection, test_db_connection
from database.init_db import parse_sql_file, check_database

class MealBookingSystemTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    def test_01_database_connection(self):
        """1 & 2: Application startup and MySQL database connection."""
        row = query_db("SELECT 1 AS alive", one=True)
        self.assertIsNotNone(row)
        self.assertEqual(row["alive"], 1)

    def test_02_home_page(self):
        """3: Home page rendering with hero, search, categories, and offers."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Good food.", response.data)
        self.assertIn(b"Simple booking.", response.data)
        self.assertIn(b"Featured Restaurants", response.data)
        self.assertIn(b"Popular Dishes", response.data)

    def test_03_restaurant_listing_and_filter(self):
        """4 & 7: Restaurant listing, location filter, and cuisine search."""
        res_all = self.client.get("/restaurants")
        self.assertEqual(res_all.status_code, 200)
        self.assertIn(b"Spice Route", res_all.data)
        self.assertIn(b"Pune Bites", res_all.data)

        # Filter by Pune locality Kothrud
        res_loc = self.client.get("/restaurants?location=Kothrud")
        self.assertEqual(res_loc.status_code, 200)
        self.assertIn(b"Spice Route", res_loc.data)
        self.assertNotIn(b"Urban Tadka", res_loc.data)

        # Search by keyword
        res_search = self.client.get("/restaurants?q=Chinese")
        self.assertEqual(res_search.status_code, 200)
        self.assertIn(b"Wok Street", res_search.data)

    def test_04_restaurant_detail(self):
        """8: Restaurant detail page with categorized dishes."""
        response = self.client.get("/restaurants/1")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Spice Route", response.data)
        self.assertIn(b"North Indian", response.data)
        self.assertIn(b"Paneer Butter Masala", response.data)

    def test_05_meal_listing_search_and_sort(self):
        """5, 6, 7: Meal catalog with keyword search, category filter, veg toggle, and sorting."""
        # Search meals
        res_search = self.client.get("/meals?q=Biryani")
        self.assertEqual(res_search.status_code, 200)
        self.assertIn(b"Biryani", res_search.data)

        # Veg filter
        res_veg = self.client.get("/meals?veg=1")
        self.assertEqual(res_veg.status_code, 200)
        self.assertIn(b"veg-icon", res_veg.data)

        # Sort price asc
        res_sort = self.client.get("/meals?sort=price_asc")
        self.assertEqual(res_sort.status_code, 200)

        # Category filter
        res_cat = self.client.get("/meals?category=Desserts")
        self.assertEqual(res_cat.status_code, 200)
        self.assertIn(b"Gulab Jamun", res_cat.data)

    def test_06_meal_details(self):
        """8: Individual meal detail view with reviews."""
        response = self.client.get("/meals/1")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Paneer Butter Masala", response.data)
        self.assertIn(b"Spice Route", response.data)

    def test_07_cart_operations(self):
        """9, 10, 11, 12: Add to cart, quantity update, remove item, offer application."""
        # Add meal #1
        res1 = self.client.post("/cart/add", data={"meal_id": 1, "quantity": 1}, headers={"X-Requested-With": "XMLHttpRequest"})
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.get_json()["cart_count"], 1)

        # Increment quantity
        res2 = self.client.post("/cart/update", data={"meal_id": 1, "quantity": 3}, headers={"X-Requested-With": "XMLHttpRequest"})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.get_json()["cart_count"], 3)

        # Check cart view
        res_cart = self.client.get("/cart")
        self.assertEqual(res_cart.status_code, 200)
        self.assertIn(b"Paneer Butter Masala", res_cart.data)

        # Apply WELCOME50
        res_offer = self.client.post("/cart/apply-offer", data={"offer_code": "WELCOME50"}, follow_redirects=True)
        self.assertEqual(res_offer.status_code, 200)
        self.assertIn(b"WELCOME50 APPLIED", res_offer.data)

        # Remove item
        res_rem = self.client.post("/cart/remove", data={"meal_id": 1}, follow_redirects=True)
        self.assertEqual(res_rem.status_code, 200)
        self.assertIn(b"Your Cart is Currently Empty", res_rem.data)

    def test_08_offer_validations(self):
        """12 & 27: Offer validity rules: invalid code, expired code, and min order amount."""
        # Add item worth 120
        self.client.post("/cart/add", data={"meal_id": 22, "quantity": 1}, follow_redirects=True)

        # 1. Non-existent code
        res1 = self.client.post("/cart/apply-offer", data={"offer_code": "FAKECODE99"}, follow_redirects=True)
        self.assertIn(b"Invalid promo code", res1.data)

        # 2. Expired code
        res2 = self.client.post("/cart/apply-offer", data={"offer_code": "EXPIRED10"}, follow_redirects=True)
        self.assertIn(b"This promo code is inactive", res2.data)

        # 3. Minimum order not met (WEEKEND20 requires 300, cart has 120)
        res3 = self.client.post("/cart/apply-offer", data={"offer_code": "WEEKEND20"}, follow_redirects=True)
        self.assertIn(b"Minimum order", res3.data)

        # Clean cart
        self.client.post("/cart/clear", follow_redirects=True)

    def test_09_auth_registration_and_login(self):
        """Authentication flow: register, login, session validation, logout."""
        # Register new user
        test_email = "test.user.pune@example.com"
        execute_db("DELETE FROM Customer WHERE email = %s", (test_email,))

        reg_data = {
            "full_name": "Test Pune User",
            "email": test_email,
            "phone": "9822998877",
            "address": "Baner Pashan Link Rd, Pune",
            "password": "mypassword123",
            "confirm_password": "mypassword123"
        }
        res_reg = self.client.post("/register", data=reg_data, follow_redirects=True)
        self.assertEqual(res_reg.status_code, 200)
        self.assertIn(b"Account created successfully", res_reg.data)

        # Duplicate registration should be rejected
        res_dup = self.client.post("/register", data=reg_data, follow_redirects=True)
        self.assertEqual(res_dup.status_code, 200)
        self.assertIn(b"already exists", res_dup.data)

        # Logout
        self.client.get("/logout", follow_redirects=True)

        # Login with wrong password
        res_fail = self.client.post("/login", data={"email": test_email, "password": "wrongpassword"}, follow_redirects=True)
        self.assertIn(b"Invalid email or password", res_fail.data)

        # Login with correct password
        res_ok = self.client.post("/login", data={"email": test_email, "password": "mypassword123"}, follow_redirects=True)
        self.assertIn(b"Welcome back", res_ok.data)

        # Cleanup
        execute_db("DELETE FROM Customer WHERE email = %s", (test_email,))

    def test_10_checkout_and_booking_creation(self):
        """13, 14, 15, 16, 17: Place booking, verify Booking, Booking_Item, and Payment rows."""
        # Login as Rahul Sharma
        self.client.get("/demo-login/customer", follow_redirects=True)

        # Add 2x Mysore Masala Dosa (id 10, price 130) = 260
        self.client.post("/cart/add", data={"meal_id": 10, "quantity": 2}, follow_redirects=True)

        # Checkout
        checkout_payload = {
            "phone": "9822012345",
            "delivery_address": "Flat 402, Mayur Colony, Kothrud, Pune",
            "payment_method": "Card",
            "special_instructions": "Make it extra crisp please"
        }
        res_chk = self.client.post("/checkout", data=checkout_payload, follow_redirects=True)
        self.assertEqual(res_chk.status_code, 200)
        self.assertIn(b"Order Confirmed!", res_chk.data)

        # Verify DB records
        booking = query_db("SELECT * FROM Booking ORDER BY booking_id DESC LIMIT 1", one=True)
        self.assertIsNotNone(booking)
        self.assertEqual(booking["payment_method"], "Card")
        self.assertEqual(booking["payment_status"], "Paid")
        self.assertEqual(float(booking["subtotal"]), 260.00)
        self.assertEqual(float(booking["total_amount"]), 300.00) # 260 + 40 del fee

        # Verify Booking_Item
        items = query_db("SELECT * FROM Booking_Item WHERE booking_id = %s", (booking["booking_id"],))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["meal_id"], 10)
        self.assertEqual(items[0]["quantity"], 2)

        # Verify Payment record
        payment = query_db("SELECT * FROM Payment WHERE booking_id = %s", (booking["booking_id"],), one=True)
        self.assertIsNotNone(payment)
        self.assertEqual(float(payment["amount"]), 300.00)

        # Verify booking shows up in My Orders
        res_orders = self.client.get("/orders")
        self.assertIn(booking["booking_code"].encode(), res_orders.data)

        # Verify Order Detail view
        res_detail = self.client.get(f"/orders/{booking['booking_code']}")
        self.assertIn(b"Mysore Masala Dosa", res_detail.data)

    def test_11_feedback_and_triggers(self):
        """18 & 21: Delivery lifecycle, feedback submission, and database triggers."""
        # 1. Login as Admin and mark latest booking as Delivered
        self.client.get("/demo-login/admin", follow_redirects=True)
        booking = query_db("SELECT booking_id, booking_code FROM Booking ORDER BY booking_id DESC LIMIT 1", one=True)
        self.client.post("/admin/bookings", data={"booking_id": booking["booking_id"], "status": "Delivered"}, follow_redirects=True)

        # 2. Login as Customer and submit Feedback
        self.client.get("/demo-login/customer", follow_redirects=True)
        res_fb = self.client.post(
            f"/orders/{booking['booking_code']}/feedback",
            data={"rating": 5, "comment": "Delicious and hot!", "meal_id": 10},
            follow_redirects=True
        )
        self.assertEqual(res_fb.status_code, 200)

        # 3. Verify Feedback is stored in MySQL
        fb = query_db("SELECT * FROM Feedback WHERE booking_id = %s", (booking["booking_id"],), one=True)
        self.assertIsNotNone(fb)
        self.assertEqual(fb["rating"], 5)

        # 4. Verify trigger trg_prevent_unavailable_meal blocks ordering unavailable dish
        execute_db("UPDATE Meal SET is_available = 0 WHERE meal_id = 9999") # ensure meal exists or use meal #31
        # Create a test meal marked unavailable
        meal_unavail = execute_db(
            "INSERT INTO Meal (restaurant_id, name, category, price, is_available) VALUES (1, 'Unavailable Dish', 'Beverages', 50, 0)"
        )
        unavail_id = meal_unavail["last_id"]

        conn = get_db_connection()
        with self.assertRaises(pymysql.err.OperationalError):
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO Booking_Item (booking_id, meal_id, quantity, price_at_booking, subtotal) VALUES (%s, %s, 1, 50, 50)",
                    (booking["booking_id"], unavail_id)
                )
        conn.close()

        # Clean up test meal
        execute_db("DELETE FROM Meal WHERE meal_id = %s", (unavail_id,))

    def test_12_profile_and_aggregates(self):
        """19: Customer profile information and SQL aggregate queries."""
        # Ensure base name
        execute_db("UPDATE Customer SET full_name = 'Rahul Sharma' WHERE customer_id = 1")
        self.client.get("/demo-login/customer", follow_redirects=True)
        response = self.client.get("/profile")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Total Orders", response.data)
        self.assertIn(b"Total Spent", response.data)
        self.assertIn(b"Rahul Sharma", response.data)

        # Test profile address update
        update_data = {
            "full_name": "Rahul S. Sharma",
            "phone": "9822099999",
            "address": "Flat 502, Mayur Colony, Kothrud, Pune"
        }
        res_upd = self.client.post("/profile", data=update_data, follow_redirects=True)
        self.assertEqual(res_upd.status_code, 200)
        self.assertIn(b"Profile updated successfully", res_upd.data)

        # Reset back
        execute_db("UPDATE Customer SET full_name = 'Rahul Sharma' WHERE customer_id = 1")

    def test_13_admin_crud_and_analytics(self):
        """20 to 28: Admin dashboard KPIs, CRUD on Restaurants, Meals, Offers, and Analytics queries."""
        self.client.get("/demo-login/admin", follow_redirects=True)

        # 1. Dashboard
        res_dash = self.client.get("/admin/")
        self.assertEqual(res_dash.status_code, 200)
        self.assertIn(b"Operational Dashboard", res_dash.data)

        # 2. Customers List
        res_cust = self.client.get("/admin/customers")
        self.assertEqual(res_cust.status_code, 200)
        self.assertIn(b"Customer Database", res_cust.data)

        # 3. Analytics
        res_ana = self.client.get("/admin/analytics")
        self.assertEqual(res_ana.status_code, 200)
        self.assertIn(b"Relational SQL Aggregation Showcase", res_ana.data)
        self.assertIn(b"Most Ordered Dishes", res_ana.data)
        self.assertIn(b"Revenue by Restaurant", res_ana.data)

        # 4. CRUD: Add and Edit Offer
        res_off = self.client.post(
            "/admin/offers",
            data={
                "action": "create",
                "code": "TESTCODE50",
                "description": "50% off test offer",
                "discount_pct": 50,
                "max_discount": 200,
                "min_order_amount": 100,
                "valid_from": "2026-01-01T00:00",
                "valid_to": "2027-01-01T00:00"
            },
            follow_redirects=True
        )
        self.assertEqual(res_off.status_code, 200)
        self.assertIn(b"TESTCODE50", res_off.data)

        # Delete the test offer
        off_row = query_db("SELECT offer_id FROM Offer WHERE code = 'TESTCODE50'", one=True)
        self.client.post("/admin/offers", data={"action": "delete", "offer_id": off_row["offer_id"]}, follow_redirects=True)

    def test_14_stored_procedures(self):
        """28 & 30: Direct verification of MySQL stored procedures."""
        # 1. Dashboard stats procedure
        stats = call_proc("sp_get_admin_dashboard_stats")
        self.assertIsNotNone(stats)
        self.assertGreater(stats[0]["total_restaurants"], 0)
        self.assertGreater(stats[0]["total_meals"], 0)

        # 2. Restaurant analytics procedure
        rest_stats = call_proc("sp_get_restaurant_analytics")
        self.assertIsNotNone(rest_stats)
        self.assertGreater(len(rest_stats), 0)

        # 3. Customer profile stats procedure
        cust_stats = call_proc("sp_get_customer_profile_stats", (1,))
        self.assertIsNotNone(cust_stats)
        self.assertEqual(cust_stats[0]["customer_id"], 1)

    def test_15_test_db_connection_diagnostic(self):
        """Pre-flight database diagnostic check and table verification."""
        diag = test_db_connection()
        self.assertTrue(diag["connected"])
        self.assertTrue(diag["database_exists"])
        self.assertEqual(diag["table_count"], 9)
        self.assertIn("Customer", diag["tables"])
        self.assertIn("Restaurant", diag["tables"])
        self.assertIn("Meal", diag["tables"])
        self.assertIn("Booking", diag["tables"])
        self.assertIn("Booking_Item", diag["tables"])
        self.assertIn("Payment", diag["tables"])
        self.assertIn("Offer", diag["tables"])
        self.assertIn("Staff", diag["tables"])
        self.assertIn("Feedback", diag["tables"])

    def test_16_views_direct_queries(self):
        """Direct queries on database views."""
        # 1. v_restaurant_summary
        rest_summary = query_db("SELECT * FROM v_restaurant_summary")
        self.assertGreater(len(rest_summary), 0)
        self.assertIn("avg_meal_price", rest_summary[0])
        self.assertIn("total_meals", rest_summary[0])

        # 2. v_popular_meals
        popular = query_db("SELECT * FROM v_popular_meals")
        self.assertGreater(len(popular), 0)
        self.assertIn("total_revenue_generated", popular[0])
        self.assertIn("total_units_sold", popular[0])

        # 3. v_customer_stats
        cust_stats = query_db("SELECT * FROM v_customer_stats WHERE customer_id = 1", one=True)
        self.assertIsNotNone(cust_stats)
        self.assertIn("total_bookings", cust_stats)
        self.assertIn("total_spent", cust_stats)

        # 4. v_booking_summary
        booking_summary = query_db("SELECT * FROM v_booking_summary")
        self.assertGreater(len(booking_summary), 0)
        self.assertIn("booking_code", booking_summary[0])

    def test_17_env_example_matches_config(self):
        """Verify .env.example contains necessary database and application variables."""
        env_example_path = os.path.join(os.path.dirname(__file__), "..", ".env.example")
        self.assertTrue(os.path.exists(env_example_path))
        with open(env_example_path, "r", encoding="utf-8") as f:
            content = f.read()
        for required_var in ["DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME", "SECRET_KEY", "HOST", "PORT"]:
            self.assertIn(required_var, content, f"Missing {required_var} in .env.example")

    def test_18_init_db_parser(self):
        """Verify SQL parser splits triggers and procedures respecting DELIMITER commands."""
        base_dir = os.path.join(os.path.dirname(__file__), "..")
        triggers_file = os.path.join(base_dir, "database", "triggers.sql")
        procs_file = os.path.join(base_dir, "database", "procedures.sql")

        trig_stmts = parse_sql_file(triggers_file)
        self.assertGreaterEqual(len(trig_stmts), 3)

        proc_stmts = parse_sql_file(procs_file)
        self.assertGreaterEqual(len(proc_stmts), 4)

        report = check_database()
        self.assertTrue(report["connected"])
        self.assertTrue(report["database_exists"])
        self.assertEqual(len(report["tables"]), 9)
        self.assertEqual(len(report["views"]), 4)
        self.assertEqual(len(report["triggers"]), 3)
        self.assertEqual(len(report["procedures"]), 4)

    def test_19_health_endpoint(self):
        """Verify production /health endpoint returns 200 and JSON status."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["database"]["connected"])
        self.assertEqual(data["database"]["table_count"], 9)

    def test_20_order_cancellation_workflow(self):
        """Verify order cancellation for Pending/Confirmed orders and refund simulation."""
        # Login as customer
        self.client.get("/demo-login/customer", follow_redirects=True)

        # Create a confirmed booking
        self.client.post("/cart/add", data={"meal_id": 1, "quantity": 1}, follow_redirects=True)
        res_chk = self.client.post("/checkout", data={
            "phone": "9822012345",
            "delivery_address": "Test Kothrud Pune",
            "payment_method": "UPI",
            "special_instructions": "Test cancel order"
        }, follow_redirects=True)
        self.assertEqual(res_chk.status_code, 200)

        # Find the latest booking
        booking = query_db("SELECT * FROM Booking ORDER BY booking_id DESC LIMIT 1", one=True)
        self.assertEqual(booking["status"], "Confirmed")

        # Cancel the booking
        res_cancel = self.client.post(f"/orders/{booking['booking_code']}/cancel", follow_redirects=True)
        self.assertEqual(res_cancel.status_code, 200)
        self.assertIn(b"successfully cancelled", res_cancel.data)

        # Verify DB status
        updated_booking = query_db("SELECT status, payment_status FROM Booking WHERE booking_id = %s", (booking["booking_id"],), one=True)
        self.assertEqual(updated_booking["status"], "Cancelled")

        payment = query_db("SELECT payment_status FROM Payment WHERE booking_id = %s", (booking["booking_id"],), one=True)
        self.assertEqual(payment["payment_status"], "Refunded")

        # Re-cancelling should be rejected cleanly
        res_re_cancel = self.client.post(f"/orders/{booking['booking_code']}/cancel", follow_redirects=True)
        self.assertIn(b"cannot be cancelled", res_re_cancel.data)

    def test_21_database_url_parsing(self):
        """Verify that urlparse correctly extracts components from DATABASE_URL."""
        from urllib.parse import urlparse, unquote
        test_url = "mysql://render_user:p%40ssword123@dbs.render.com:3308/production_meal_db"
        parsed = urlparse(test_url)
        self.assertEqual(unquote(parsed.username), "render_user")
        self.assertEqual(unquote(parsed.password), "p@ssword123")
        self.assertEqual(parsed.hostname, "dbs.render.com")
        self.assertEqual(parsed.port, 3308)
        self.assertEqual(parsed.path.lstrip("/"), "production_meal_db")

    def test_22_custom_error_handlers(self):
        """Verify custom 404 handler returns styled 404 page."""
        response = self.client.get("/non-existent-route-for-testing-404")
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"Dish or Page Not Found (404)", response.data)

if __name__ == "__main__":
    unittest.main()
