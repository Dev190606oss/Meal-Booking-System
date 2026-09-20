-- ==========================================================
-- Meal Booking System - Stored Procedures
-- Encapsulating Business Logic & Administrative Analytics
-- ==========================================================

USE meal_booking_db;

DELIMITER $$

-- ----------------------------------------------------------
-- 1. PROCEDURE: GET ADMIN DASHBOARD STATS
-- Single call to fetch platform high-level summary KPIs
-- ----------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_get_admin_dashboard_stats$$

CREATE PROCEDURE sp_get_admin_dashboard_stats()
BEGIN
    SELECT 
        (SELECT COUNT(*) FROM Customer WHERE is_admin = 0) AS total_customers,
        (SELECT COUNT(*) FROM Restaurant WHERE is_active = 1) AS total_restaurants,
        (SELECT COUNT(*) FROM Meal WHERE is_available = 1) AS total_meals,
        (SELECT COUNT(*) FROM Booking) AS total_bookings,
        (SELECT COALESCE(SUM(total_amount), 0.00) FROM Booking WHERE status != 'Cancelled') AS total_revenue,
        (SELECT COUNT(*) FROM Offer WHERE is_active = 1 AND valid_to >= NOW()) AS active_offers;
END$$

-- ----------------------------------------------------------
-- 2. PROCEDURE: RESTAURANT REVENUE & SALES ANALYTICS
-- Calculates performance metrics grouped by restaurant
-- ----------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_get_restaurant_analytics$$

CREATE PROCEDURE sp_get_restaurant_analytics()
BEGIN
    SELECT 
        r.restaurant_id,
        r.name AS restaurant_name,
        r.location,
        r.cuisine,
        COUNT(b.booking_id) AS total_orders,
        SUM(CASE WHEN b.status = 'Delivered' THEN 1 ELSE 0 END) AS completed_orders,
        SUM(CASE WHEN b.status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
        COALESCE(SUM(CASE WHEN b.status != 'Cancelled' THEN b.total_amount ELSE 0.00 END), 0.00) AS total_revenue,
        COALESCE(ROUND(AVG(CASE WHEN b.status != 'Cancelled' THEN b.total_amount ELSE NULL END), 2), 0.00) AS avg_order_value,
        r.rating AS current_rating
    FROM Restaurant r
    LEFT JOIN Booking b ON r.restaurant_id = b.restaurant_id
    GROUP BY r.restaurant_id, r.name, r.location, r.cuisine, r.rating
    ORDER BY total_revenue DESC;
END$$

-- ----------------------------------------------------------
-- 3. PROCEDURE: CUSTOMER PROFILE & LIFETIME STATS
-- Computes customer order metrics and favorite cuisine
-- ----------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_get_customer_profile_stats$$

CREATE PROCEDURE sp_get_customer_profile_stats(IN p_customer_id INT)
BEGIN
    SELECT 
        c.customer_id,
        c.full_name,
        c.email,
        c.phone,
        c.address,
        c.created_at,
        COUNT(b.booking_id) AS total_orders,
        SUM(CASE WHEN b.status = 'Delivered' THEN 1 ELSE 0 END) AS delivered_orders,
        SUM(CASE WHEN b.status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
        COALESCE(SUM(CASE WHEN b.status != 'Cancelled' THEN b.total_amount ELSE 0.00 END), 0.00) AS total_spent,
        COALESCE(ROUND(AVG(CASE WHEN b.status != 'Cancelled' THEN b.total_amount ELSE NULL END), 2), 0.00) AS avg_order_value
    FROM Customer c
    LEFT JOIN Booking b ON c.customer_id = b.customer_id
    WHERE c.customer_id = p_customer_id
    GROUP BY c.customer_id, c.full_name, c.email, c.phone, c.address, c.created_at;
END$$

-- ----------------------------------------------------------
-- 4. PROCEDURE: VALIDATE AND APPLY PROMO OFFER
-- Checks code, expiry, minimum order value and computes discount
-- ----------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_validate_offer$$

CREATE PROCEDURE sp_validate_offer(
    IN p_code VARCHAR(30),
    IN p_subtotal DECIMAL(10,2),
    OUT p_is_valid BOOLEAN,
    OUT p_discount DECIMAL(10,2),
    OUT p_message VARCHAR(255),
    OUT p_offer_id INT
)
BEGIN
    DECLARE v_id INT;
    DECLARE v_pct INT;
    DECLARE v_max DECIMAL(8,2);
    DECLARE v_min DECIMAL(8,2);
    DECLARE v_active BOOLEAN;
    DECLARE v_from DATETIME;
    DECLARE v_to DATETIME;
    DECLARE v_calc DECIMAL(10,2);

    SET p_is_valid = FALSE;
    SET p_discount = 0.00;
    SET p_offer_id = NULL;

    SELECT offer_id, discount_pct, max_discount, min_order_amount, is_active, valid_from, valid_to
    INTO v_id, v_pct, v_max, v_min, v_active, v_from, v_to
    FROM Offer
    WHERE code = UPPER(p_code);

    IF v_id IS NULL THEN
        SET p_message = 'Invalid coupon code. Please check and try again.';
    ELSEIF v_active = 0 THEN
        SET p_message = 'This coupon code is currently disabled.';
    ELSEIF NOW() < v_from OR NOW() > v_to THEN
        SET p_message = 'This coupon code has expired.';
    ELSEIF p_subtotal < v_min THEN
        SET p_message = CONCAT('Minimum cart value of ₹', v_min, ' required for this coupon.');
    ELSE
        SET v_calc = ROUND((p_subtotal * v_pct) / 100.0, 2);
        IF v_calc > v_max THEN
            SET v_calc = v_max;
        END IF;

        SET p_is_valid = TRUE;
        SET p_discount = v_calc;
        SET p_offer_id = v_id;
        SET p_message = CONCAT(v_pct, '% discount applied successfully! You saved ₹', v_calc);
    END IF;
END$$

DELIMITER ;
