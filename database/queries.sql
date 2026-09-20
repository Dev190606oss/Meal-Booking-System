-- ==========================================================
-- Meal Booking System - Showcase SQL Queries
-- Demonstrating Core Relational Database Concepts (DBMS)
-- ==========================================================

USE meal_booking_db;

-- ----------------------------------------------------------
-- 1. RETRIEVE ALL ACTIVE RESTAURANTS (Basic SELECT & WHERE)
-- ----------------------------------------------------------
SELECT 
    restaurant_id,
    name,
    cuisine,
    location,
    rating,
    delivery_time_min,
    min_order_value
FROM Restaurant
WHERE is_active = 1
ORDER BY rating DESC, name ASC;

-- ----------------------------------------------------------
-- 2. ALL AVAILABLE MEALS WITH RESTAURANT DETAILS (INNER JOIN)
-- ----------------------------------------------------------
SELECT 
    m.meal_id,
    m.name AS meal_name,
    m.category,
    m.price,
    m.is_veg,
    m.rating AS meal_rating,
    r.name AS restaurant_name,
    r.location AS restaurant_location
FROM Meal m
INNER JOIN Restaurant r ON m.restaurant_id = r.restaurant_id
WHERE m.is_available = 1 AND r.is_active = 1
ORDER BY m.category ASC, m.price ASC;

-- ----------------------------------------------------------
-- 3. MEALS BY SPECIFIC RESTAURANT (PARAMETERIZED FILTER)
-- ----------------------------------------------------------
SELECT 
    meal_id,
    name,
    category,
    price,
    is_veg,
    rating,
    description
FROM Meal
WHERE restaurant_id = 1 AND is_available = 1
ORDER BY category, price ASC;

-- ----------------------------------------------------------
-- 4. MEALS BY CATEGORY WITH PRICE RANGE (MULTIPLE CONDITIONS)
-- ----------------------------------------------------------
SELECT 
    m.name,
    m.category,
    m.price,
    r.name AS restaurant_name,
    r.location
FROM Meal m
JOIN Restaurant r ON m.restaurant_id = r.restaurant_id
WHERE m.category = 'North Indian'
  AND m.price BETWEEN 100.00 AND 300.00
  AND m.is_available = 1
ORDER BY m.price ASC;

-- ----------------------------------------------------------
-- 5. SEARCH MEALS OR RESTAURANTS (LIKE / PATTERN MATCHING)
-- ----------------------------------------------------------
SELECT 
    m.meal_id,
    m.name AS meal_name,
    m.category,
    m.price,
    r.name AS restaurant_name,
    r.location
FROM Meal m
JOIN Restaurant r ON m.restaurant_id = r.restaurant_id
WHERE (m.name LIKE '%paneer%' OR m.category LIKE '%paneer%' OR r.name LIKE '%paneer%')
  AND m.is_available = 1;

-- ----------------------------------------------------------
-- 6. CUSTOMER BOOKING HISTORY WITH ITEMS (MULTI-TABLE JOIN)
-- ----------------------------------------------------------
SELECT 
    b.booking_code,
    b.booking_date,
    r.name AS restaurant_name,
    b.status,
    b.subtotal,
    b.discount_amount,
    b.delivery_fee,
    b.total_amount,
    b.payment_method,
    p.payment_status,
    GROUP_CONCAT(CONCAT(bi.quantity, 'x ', m.name) SEPARATOR ', ') AS ordered_items
FROM Booking b
JOIN Restaurant r ON b.restaurant_id = r.restaurant_id
JOIN Booking_Item bi ON b.booking_id = bi.booking_id
JOIN Meal m ON bi.meal_id = m.meal_id
LEFT JOIN Payment p ON b.booking_id = p.booking_id
WHERE b.customer_id = 1
GROUP BY b.booking_id, b.booking_code, b.booking_date, r.name, b.status, b.subtotal, b.discount_amount, b.delivery_fee, b.total_amount, b.payment_method, p.payment_status
ORDER BY b.booking_date DESC;

-- ----------------------------------------------------------
-- 7. MOST ORDERED MEALS (GROUP BY, SUM, ORDER BY, LIMIT)
-- ----------------------------------------------------------
SELECT 
    m.meal_id,
    m.name AS meal_name,
    m.category,
    r.name AS restaurant_name,
    COUNT(bi.booking_item_id) AS times_ordered,
    SUM(bi.quantity) AS total_units_sold,
    SUM(bi.subtotal) AS gross_revenue
FROM Meal m
JOIN Restaurant r ON m.restaurant_id = r.restaurant_id
JOIN Booking_Item bi ON m.meal_id = bi.meal_id
JOIN Booking b ON bi.booking_id = b.booking_id
WHERE b.status != 'Cancelled'
GROUP BY m.meal_id, m.name, m.category, r.name
ORDER BY total_units_sold DESC
LIMIT 5;

-- ----------------------------------------------------------
-- 8. RESTAURANT ORDER STATISTICS (AGGREGATION WITH CASE EXPRESSION)
-- ----------------------------------------------------------
SELECT 
    r.restaurant_id,
    r.name AS restaurant_name,
    r.location,
    COUNT(b.booking_id) AS total_orders,
    SUM(CASE WHEN b.status = 'Delivered' THEN 1 ELSE 0 END) AS completed_orders,
    SUM(CASE WHEN b.status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
    COALESCE(ROUND(AVG(b.total_amount), 2), 0.00) AS avg_order_value
FROM Restaurant r
LEFT JOIN Booking b ON r.restaurant_id = b.restaurant_id
GROUP BY r.restaurant_id, r.name, r.location
ORDER BY total_orders DESC;

-- ----------------------------------------------------------
-- 9. REVENUE BY RESTAURANT (GROUP BY, HAVING, ORDER BY)
-- Demonstrating HAVING to filter restaurants with substantial sales
-- ----------------------------------------------------------
SELECT 
    r.name AS restaurant_name,
    r.cuisine,
    r.location,
    COALESCE(SUM(b.total_amount), 0.00) AS total_revenue
FROM Restaurant r
JOIN Booking b ON r.restaurant_id = b.restaurant_id
WHERE b.status != 'Cancelled'
GROUP BY r.restaurant_id, r.name, r.cuisine, r.location
HAVING total_revenue > 0.00
ORDER BY total_revenue DESC;

-- ----------------------------------------------------------
-- 10. HIGHEST RATED MEALS (FILTER BY RATING & ORDER BY)
-- ----------------------------------------------------------
SELECT 
    m.name AS meal_name,
    m.category,
    m.price,
    m.rating,
    r.name AS restaurant_name,
    r.location
FROM Meal m
JOIN Restaurant r ON m.restaurant_id = r.restaurant_id
WHERE m.rating >= 4.8 AND m.is_available = 1
ORDER BY m.rating DESC, m.name ASC;

-- ----------------------------------------------------------
-- 11. CURRENTLY ACTIVE & VALID OFFERS (DATE & BOOLEAN FILTER)
-- ----------------------------------------------------------
SELECT 
    code,
    description,
    discount_pct,
    max_discount,
    min_order_amount,
    valid_to
FROM Offer
WHERE is_active = 1 
  AND valid_from <= NOW() 
  AND valid_to >= NOW()
ORDER BY discount_pct DESC;

-- ----------------------------------------------------------
-- 12. CUSTOMER ORDER SUMMARY (AGGREGATION & SUBQUERY)
-- ----------------------------------------------------------
SELECT 
    c.customer_id,
    c.full_name,
    c.email,
    c.phone,
    COUNT(b.booking_id) AS total_orders,
    COALESCE(SUM(b.total_amount), 0.00) AS total_spent,
    (
        SELECT r.cuisine 
        FROM Booking b2 
        JOIN Restaurant r ON b2.restaurant_id = r.restaurant_id 
        WHERE b2.customer_id = c.customer_id 
        GROUP BY r.cuisine 
        ORDER BY COUNT(*) DESC 
        LIMIT 1
    ) AS favorite_cuisine
FROM Customer c
LEFT JOIN Booking b ON c.customer_id = b.customer_id AND b.status != 'Cancelled'
WHERE c.is_admin = 0
GROUP BY c.customer_id, c.full_name, c.email, c.phone
ORDER BY total_spent DESC;
