-- ==========================================================
-- Meal Booking System - Database Views
-- Demonstrating Relational View Abstractions & Aggregations
-- ==========================================================

USE meal_booking_db;

-- ----------------------------------------------------------
-- 1. RESTAURANT SUMMARY VIEW
-- Consolidates restaurant information with aggregated menu statistics
-- ----------------------------------------------------------
DROP VIEW IF EXISTS v_restaurant_summary;

CREATE VIEW v_restaurant_summary AS
SELECT 
    r.restaurant_id,
    r.name AS restaurant_name,
    r.cuisine,
    r.location,
    r.rating AS restaurant_rating,
    r.delivery_time_min,
    r.min_order_value,
    r.image_url,
    COUNT(m.meal_id) AS total_meals,
    COALESCE(MIN(m.price), 0.00) AS min_price,
    COALESCE(MAX(m.price), 0.00) AS max_price,
    COALESCE(ROUND(AVG(m.price), 2), 0.00) AS avg_meal_price
FROM Restaurant r
LEFT JOIN Meal m ON r.restaurant_id = m.restaurant_id AND m.is_available = 1
WHERE r.is_active = 1
GROUP BY r.restaurant_id, r.name, r.cuisine, r.location, r.rating, r.delivery_time_min, r.min_order_value, r.image_url;

-- ----------------------------------------------------------
-- 2. POPULAR MEALS VIEW
-- Top ordered meals across all restaurants with revenue metrics
-- ----------------------------------------------------------
DROP VIEW IF EXISTS v_popular_meals;

CREATE VIEW v_popular_meals AS
SELECT 
    m.meal_id,
    m.name AS meal_name,
    m.category,
    m.price,
    m.is_veg,
    m.rating AS meal_rating,
    m.image_url,
    r.restaurant_id,
    r.name AS restaurant_name,
    r.location AS restaurant_location,
    COALESCE(COUNT(bi.booking_item_id), 0) AS total_orders_count,
    COALESCE(SUM(bi.quantity), 0) AS total_units_sold,
    COALESCE(SUM(bi.subtotal), 0.00) AS total_revenue_generated
FROM Meal m
JOIN Restaurant r ON m.restaurant_id = r.restaurant_id
LEFT JOIN Booking_Item bi ON m.meal_id = bi.meal_id
GROUP BY m.meal_id, m.name, m.category, m.price, m.is_veg, m.rating, m.image_url, r.restaurant_id, r.name, r.location;

-- ----------------------------------------------------------
-- 3. BOOKING SUMMARY VIEW
-- Detailed join between Booking, Customer, Restaurant, Offer, and Payment
-- ----------------------------------------------------------
DROP VIEW IF EXISTS v_booking_summary;

CREATE VIEW v_booking_summary AS
SELECT 
    b.booking_id,
    b.booking_code,
    b.booking_date,
    b.status AS booking_status,
    b.subtotal,
    b.discount_amount,
    b.delivery_fee,
    b.total_amount,
    b.delivery_address,
    b.payment_method,
    b.payment_status,
    c.customer_id,
    c.full_name AS customer_name,
    c.email AS customer_email,
    c.phone AS customer_phone,
    r.restaurant_id,
    r.name AS restaurant_name,
    r.location AS restaurant_location,
    o.code AS applied_offer_code,
    p.transaction_ref,
    p.payment_status AS actual_payment_status,
    COUNT(bi.booking_item_id) AS total_distinct_items,
    COALESCE(SUM(bi.quantity), 0) AS total_items_quantity
FROM Booking b
JOIN Customer c ON b.customer_id = c.customer_id
JOIN Restaurant r ON b.restaurant_id = r.restaurant_id
LEFT JOIN Offer o ON b.offer_id = o.offer_id
LEFT JOIN Payment p ON b.booking_id = p.booking_id
LEFT JOIN Booking_Item bi ON b.booking_id = bi.booking_id
GROUP BY b.booking_id, b.booking_code, b.booking_date, b.status, b.subtotal, b.discount_amount, b.delivery_fee, b.total_amount, b.delivery_address, b.payment_method, b.payment_status, c.customer_id, c.full_name, c.email, c.phone, r.restaurant_id, r.name, r.location, o.code, p.transaction_ref, p.payment_status;

-- ----------------------------------------------------------
-- 4. CUSTOMER STATS VIEW
-- Customer lifetime spend and ordering behavior
-- ----------------------------------------------------------
DROP VIEW IF EXISTS v_customer_stats;

CREATE VIEW v_customer_stats AS
SELECT 
    c.customer_id,
    c.full_name,
    c.email,
    c.phone,
    c.address,
    c.created_at,
    COUNT(b.booking_id) AS total_bookings,
    SUM(CASE WHEN b.status = 'Delivered' THEN 1 ELSE 0 END) AS delivered_bookings,
    SUM(CASE WHEN b.status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_bookings,
    COALESCE(SUM(CASE WHEN b.status != 'Cancelled' THEN b.total_amount ELSE 0 END), 0.00) AS total_spent,
    COALESCE(ROUND(AVG(CASE WHEN b.status != 'Cancelled' THEN b.total_amount ELSE NULL END), 2), 0.00) AS avg_booking_value
FROM Customer c
LEFT JOIN Booking b ON c.customer_id = b.customer_id
WHERE c.is_admin = 0
GROUP BY c.customer_id, c.full_name, c.email, c.phone, c.address, c.created_at;
