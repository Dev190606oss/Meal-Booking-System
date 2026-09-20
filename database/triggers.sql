-- ==========================================================
-- Meal Booking System - Database Triggers
-- Demonstrating Data Integrity & Automated Business Rules
-- ==========================================================

USE meal_booking_db;

DELIMITER $$

-- ----------------------------------------------------------
-- 1. TRIGGER: PREVENT BOOKING UNAVAILABLE MEALS
-- Ensures no items can be added to an order if the meal is marked unavailable
-- ----------------------------------------------------------
DROP TRIGGER IF EXISTS trg_prevent_unavailable_meal$$

CREATE TRIGGER trg_prevent_unavailable_meal
BEFORE INSERT ON Booking_Item
FOR EACH ROW
BEGIN
    DECLARE meal_status INT;
    DECLARE meal_title VARCHAR(150);

    SELECT is_available, name INTO meal_status, meal_title
    FROM Meal
    WHERE meal_id = NEW.meal_id;

    IF meal_status = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Order rejected: Selected meal is currently out of stock or unavailable';
    END IF;
END$$

-- ----------------------------------------------------------
-- 2. TRIGGER: AUTO-UPDATE MEAL RATING ON NEW FEEDBACK
-- Automatically computes new average rating for a meal whenever customer rates it
-- ----------------------------------------------------------
DROP TRIGGER IF EXISTS trg_update_meal_rating_after_feedback$$

CREATE TRIGGER trg_update_meal_rating_after_feedback
AFTER INSERT ON Feedback
FOR EACH ROW
BEGIN
    DECLARE avg_rate DECIMAL(2,1);

    IF NEW.meal_id IS NOT NULL THEN
        SELECT ROUND(AVG(rating), 1) INTO avg_rate
        FROM Feedback
        WHERE meal_id = NEW.meal_id;

        IF avg_rate IS NOT NULL THEN
            UPDATE Meal
            SET rating = avg_rate
            WHERE meal_id = NEW.meal_id;
        END IF;
    END IF;
END$$

-- ----------------------------------------------------------
-- 3. TRIGGER: AUTO-UPDATE RESTAURANT RATING ON NEW FEEDBACK
-- Automatically adjusts restaurant rating based on its meal feedbacks
-- ----------------------------------------------------------
DROP TRIGGER IF EXISTS trg_update_restaurant_rating_after_feedback$$

CREATE TRIGGER trg_update_restaurant_rating_after_feedback
AFTER INSERT ON Feedback
FOR EACH ROW
BEGIN
    DECLARE rest_id INT;
    DECLARE avg_rest_rate DECIMAL(2,1);

    -- Find the restaurant associated with the booking
    SELECT restaurant_id INTO rest_id
    FROM Booking
    WHERE booking_id = NEW.booking_id;

    IF rest_id IS NOT NULL THEN
        SELECT ROUND(AVG(f.rating), 1) INTO avg_rest_rate
        FROM Feedback f
        JOIN Booking b ON f.booking_id = b.booking_id
        WHERE b.restaurant_id = rest_id;

        IF avg_rest_rate IS NOT NULL THEN
            UPDATE Restaurant
            SET rating = avg_rest_rate
            WHERE restaurant_id = rest_id;
        END IF;
    END IF;
END$$

DELIMITER ;
