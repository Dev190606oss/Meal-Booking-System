-- ==========================================================
-- Meal Booking System - Relational Database Schema
-- Database Management System (DBMS) Project
-- ==========================================================

CREATE DATABASE IF NOT EXISTS meal_booking_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE meal_booking_db;

-- ----------------------------------------------------------
-- 1. CUSTOMER TABLE
-- ----------------------------------------------------------
DROP TABLE IF EXISTS Feedback;
DROP TABLE IF EXISTS Payment;
DROP TABLE IF EXISTS Booking_Item;
DROP TABLE IF EXISTS Booking;
DROP TABLE IF EXISTS Staff;
DROP TABLE IF EXISTS Meal;
DROP TABLE IF EXISTS Offer;
DROP TABLE IF EXISTS Restaurant;
DROP TABLE IF EXISTS Customer;

CREATE TABLE Customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address VARCHAR(255) NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_customer_email (email)
) ENGINE=InnoDB;

-- ----------------------------------------------------------
-- 2. RESTAURANT TABLE
-- ----------------------------------------------------------
CREATE TABLE Restaurant (
    restaurant_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    cuisine VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    rating DECIMAL(2,1) NOT NULL DEFAULT 4.0,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    image_url VARCHAR(500) NULL,
    description TEXT NULL,
    delivery_time_min INT NOT NULL DEFAULT 30,
    min_order_value DECIMAL(8,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_restaurant_rating CHECK (rating >= 1.0 AND rating <= 5.0),
    CONSTRAINT chk_restaurant_del_time CHECK (delivery_time_min > 0),
    CONSTRAINT chk_restaurant_min_order CHECK (min_order_value >= 0.00),
    INDEX idx_restaurant_location (location),
    INDEX idx_restaurant_cuisine (cuisine)
) ENGINE=InnoDB;

-- ----------------------------------------------------------
-- 3. MEAL TABLE
-- ----------------------------------------------------------
CREATE TABLE Meal (
    meal_id INT AUTO_INCREMENT PRIMARY KEY,
    restaurant_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price DECIMAL(8,2) NOT NULL,
    is_veg BOOLEAN NOT NULL DEFAULT 1,
    is_available BOOLEAN NOT NULL DEFAULT 1,
    rating DECIMAL(2,1) NOT NULL DEFAULT 4.5,
    description TEXT NULL,
    image_url VARCHAR(500) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_meal_price CHECK (price > 0.00),
    CONSTRAINT chk_meal_rating CHECK (rating >= 1.0 AND rating <= 5.0),
    CONSTRAINT fk_meal_restaurant FOREIGN KEY (restaurant_id)
        REFERENCES Restaurant(restaurant_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    INDEX idx_meal_category (category),
    INDEX idx_meal_price (price),
    INDEX idx_meal_restaurant (restaurant_id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------
-- 4. OFFER TABLE
-- ----------------------------------------------------------
CREATE TABLE Offer (
    offer_id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(30) NOT NULL UNIQUE,
    description VARCHAR(255) NOT NULL,
    discount_pct INT NOT NULL,
    max_discount DECIMAL(8,2) NOT NULL DEFAULT 100.00,
    min_order_amount DECIMAL(8,2) NOT NULL DEFAULT 0.00,
    valid_from DATETIME NOT NULL,
    valid_to DATETIME NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    CONSTRAINT chk_offer_discount_pct CHECK (discount_pct >= 1 AND discount_pct <= 100),
    CONSTRAINT chk_offer_max_discount CHECK (max_discount >= 0.00),
    CONSTRAINT chk_offer_min_order CHECK (min_order_amount >= 0.00),
    INDEX idx_offer_code (code)
) ENGINE=InnoDB;

-- ----------------------------------------------------------
-- 5. STAFF TABLE
-- ----------------------------------------------------------
CREATE TABLE Staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    restaurant_id INT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_staff_restaurant FOREIGN KEY (restaurant_id)
        REFERENCES Restaurant(restaurant_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ----------------------------------------------------------
-- 6. BOOKING TABLE
-- ----------------------------------------------------------
CREATE TABLE Booking (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_code VARCHAR(20) NOT NULL UNIQUE,
    customer_id INT NOT NULL,
    restaurant_id INT NOT NULL,
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('Pending', 'Confirmed', 'Preparing', 'Out for Delivery', 'Delivered', 'Cancelled') NOT NULL DEFAULT 'Confirmed',
    subtotal DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    discount_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    delivery_fee DECIMAL(10,2) NOT NULL DEFAULT 40.00,
    total_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    delivery_address TEXT NOT NULL,
    payment_method ENUM('COD', 'UPI', 'Card') NOT NULL DEFAULT 'COD',
    payment_status ENUM('Pending', 'Paid', 'Failed') NOT NULL DEFAULT 'Pending',
    offer_id INT NULL,
    special_instructions VARCHAR(255) NULL,
    CONSTRAINT chk_booking_subtotal CHECK (subtotal >= 0.00),
    CONSTRAINT chk_booking_discount CHECK (discount_amount >= 0.00),
    CONSTRAINT chk_booking_delivery CHECK (delivery_fee >= 0.00),
    CONSTRAINT chk_booking_total CHECK (total_amount >= 0.00),
    CONSTRAINT fk_booking_customer FOREIGN KEY (customer_id)
        REFERENCES Customer(customer_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_booking_restaurant FOREIGN KEY (restaurant_id)
        REFERENCES Restaurant(restaurant_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_booking_offer FOREIGN KEY (offer_id)
        REFERENCES Offer(offer_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    INDEX idx_booking_customer (customer_id),
    INDEX idx_booking_restaurant (restaurant_id),
    INDEX idx_booking_status (status),
    INDEX idx_booking_date (booking_date)
) ENGINE=InnoDB;

-- ----------------------------------------------------------
-- 7. BOOKING_ITEM TABLE (Junction Table)
-- ----------------------------------------------------------
CREATE TABLE Booking_Item (
    booking_item_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    meal_id INT NOT NULL,
    quantity INT NOT NULL,
    price_at_booking DECIMAL(8,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    CONSTRAINT chk_item_quantity CHECK (quantity > 0),
    CONSTRAINT chk_item_price CHECK (price_at_booking > 0.00),
    CONSTRAINT chk_item_subtotal CHECK (subtotal >= 0.00),
    CONSTRAINT fk_item_booking FOREIGN KEY (booking_id)
        REFERENCES Booking(booking_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_item_meal FOREIGN KEY (meal_id)
        REFERENCES Meal(meal_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    INDEX idx_item_booking (booking_id),
    INDEX idx_item_meal (meal_id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------
-- 8. PAYMENT TABLE
-- ----------------------------------------------------------
CREATE TABLE Payment (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL UNIQUE,
    payment_method ENUM('COD', 'UPI', 'Card') NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_status ENUM('Pending', 'Paid', 'Failed') NOT NULL DEFAULT 'Paid',
    transaction_ref VARCHAR(64) NOT NULL UNIQUE,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_payment_amount CHECK (amount >= 0.00),
    CONSTRAINT fk_payment_booking FOREIGN KEY (booking_id)
        REFERENCES Booking(booking_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ----------------------------------------------------------
-- 9. FEEDBACK TABLE
-- ----------------------------------------------------------
CREATE TABLE Feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    booking_id INT NOT NULL,
    meal_id INT NULL,
    rating INT NOT NULL,
    comment TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_feedback_rating CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT fk_feedback_customer FOREIGN KEY (customer_id)
        REFERENCES Customer(customer_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_feedback_booking FOREIGN KEY (booking_id)
        REFERENCES Booking(booking_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_feedback_meal FOREIGN KEY (meal_id)
        REFERENCES Meal(meal_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    INDEX idx_feedback_meal (meal_id),
    INDEX idx_feedback_booking (booking_id)
) ENGINE=InnoDB;
