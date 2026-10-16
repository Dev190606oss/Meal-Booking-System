-- ==========================================================
-- Meal Booking System - Seed Data
-- Realistic sample data for Pune restaurants, meals, and bookings
-- ==========================================================

USE meal_booking_db;

-- ----------------------------------------------------------
-- 1. SEED CUSTOMERS & ADMIN (Default password: password123)
-- ----------------------------------------------------------
-- Password hash generated via werkzeug.security generate_password_hash('password123')
SET @default_pass = 'scrypt:32768:8:1$xtVyNHlOOBpeoDGL$6414b70b01492e84dbfd1213cf980c53937bac0b2a19a1171d17056c42200c475e60392c5d30dd0310b3b710e92505a3da1d47dee823ec04b079af8c28f5ab41';

INSERT IGNORE INTO Customer (customer_id, full_name, email, password_hash, phone, address, is_admin) VALUES
(1, 'Rahul Sharma', 'rahul.sharma@example.com', @default_pass, '9822012345', 'Flat 402, Mayur Colony, Kothrud, Pune - 411038', 0),
(2, 'Priya Kulkarni', 'priya.kulkarni@example.com', @default_pass, '9822056789', 'B-12, Rohan Tarang, Wakad Road, Baner, Pune - 411045', 0),
(3, 'Amit Deshmukh', 'amit.deshmukh@example.com', @default_pass, '9822098765', 'Row House 4, Nyati Estate, Viman Nagar, Pune - 411014', 0),
(4, 'Neha Joshi', 'neha.joshi@example.com', @default_pass, '9822043210', 'Plot 18, Model Colony, Shivajinagar, Pune - 411016', 0),
(5, 'Administrator', 'admin@mealbooking.com', @default_pass, '9890000000', 'Central Operations Hub, FC Road, Pune - 411004', 1);

-- ----------------------------------------------------------
-- 2. SEED RESTAURANTS
-- ----------------------------------------------------------
INSERT IGNORE INTO Restaurant (restaurant_id, name, cuisine, location, rating, is_active, image_url, description, delivery_time_min, min_order_value) VALUES
(1, 'Spice Route', 'North Indian, Mughlai', 'Kothrud', 4.8, 1, 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=800&q=80', 'Authentic North Indian rich gravies, charcoal tandoor specials, and slow-cooked curries prepared using royal heritage recipes.', 30, 200.00),
(2, 'Urban Tadka', 'North Indian, Street Food', 'Baner', 4.6, 1, 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&q=80', 'Vibrant Punjabi dhabha taste served in a modern urban bistro. Known for buttery naans, spicy paneer dishes, and refreshing lassis.', 35, 150.00),
(3, 'Curry Corner', 'South Indian, Coastal', 'Karve Nagar', 4.7, 1, 'https://images.unsplash.com/photo-1610057099443-fde8c4d50f91?w=800&q=80', 'Crispy dosas, fluffy thatte idlis, coconut-infused coastal curries, and aromatic filter coffee served hot from the pot.', 25, 100.00),
(4, 'The Breakfast Club', 'Continental, Fast Food', 'Aundh', 4.5, 1, 'https://images.unsplash.com/photo-1533089860892-a7c6f0a88666?w=800&q=80', 'Artisanal pancakes, loaded breakfast platters, signature grilled sourdough sandwiches, and specialty hand-crafted beverages.', 30, 180.00),
(5, 'Wok Street', 'Chinese, Pan-Asian', 'Viman Nagar', 4.6, 1, 'https://images.unsplash.com/photo-1541696432-82c6da8ce7bf?w=800&q=80', 'Sizzling wok bowls, fiery Schezwan noodles, steamed dim sums, and crispy Asian appetisers packed with authentic flavours.', 35, 200.00),
(6, 'Pune Bites', 'Maharashtrian, Fast Food', 'Shivajinagar', 4.9, 1, 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=800&q=80', 'Famous Puneri Misal Pav, Sabudana Vada, Kothimbir Vadi, Puran Poli, and refreshing Sol Kadhi made fresh every morning.', 20, 100.00),
(7, 'Deccan Delights', 'North Indian, Biryani', 'Koregaon Park', 4.7, 1, 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=800&q=80', 'Royal Dum Biryanis layered with long-grain basmati, fragrant saffron, tender marinated meats, and exotic whole spices.', 40, 250.00),
(8, 'Green Leaf Bistro', 'Beverages, Desserts', 'Hadapsar', 4.4, 1, 'https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=800&q=80', 'Wholesome natural salads, cold-pressed juices, chia seed bowls, and guilt-free artisan desserts crafted for healthy eaters.', 25, 150.00);

-- ----------------------------------------------------------
-- 3. SEED MEALS
-- ----------------------------------------------------------
INSERT IGNORE INTO Meal (meal_id, restaurant_id, name, category, price, is_veg, is_available, rating, description, image_url) VALUES
-- Spice Route (1)
(1, 1, 'Paneer Butter Masala', 'North Indian', 280.00, 1, 1, 4.8, 'Cottage cheese cubes simmered in a velvety tomato and cashew butter gravy, finished with kasuri methi.', 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=600&q=80'),
(2, 1, 'Dal Makhani', 'North Indian', 240.00, 1, 1, 4.9, 'Black lentils slow-cooked overnight on charcoal with butter and cream for an authentic smoky flavour.', 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&q=80'),
(3, 1, 'Butter Garlic Naan (2 pcs)', 'North Indian', 90.00, 1, 1, 4.7, 'Traditional clay oven leavened flatbread brushed with garlic butter and fresh cilantro.', 'https://images.unsplash.com/photo-1601050690117-94f5f6fa8bd7?w=600&q=80'),
(4, 1, 'Murgh Dum Biryani', 'North Indian', 340.00, 0, 1, 4.8, 'Fragrant basmati rice slow-cooked on dum with succulent chicken and whole aromatic spices.', 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&q=80'),
(5, 1, 'Gulab Jamun with Rabdi', 'Desserts', 140.00, 1, 1, 4.9, 'Golden fried milk dumplings soaked in saffron sugar syrup served alongside chilled rich rabdi.', 'https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=600&q=80'),

-- Urban Tadka (2)
(6, 2, 'Amritsari Kulcha with Chole', 'North Indian', 210.00, 1, 1, 4.7, 'Crispy flaky potato-stuffed kulcha served with spicy pindi chole and tangy onion tamarind chutney.', 'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&q=80'),
(7, 2, 'Kadhai Paneer', 'North Indian', 270.00, 1, 1, 4.6, 'Paneer and crunchy bell peppers tossed in a robust freshly pounded coriander and cumin spice blend.', 'https://images.unsplash.com/photo-1567184109270-b2db1797e782?w=600&q=80'),
(8, 2, 'Dahi Ke Kebab', 'Fast Food', 190.00, 1, 1, 4.5, 'Crispy outside and creamy hung yogurt spiced with cardamom inside, served with mint dip.', 'https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600&q=80'),
(9, 2, 'Patiala Sweet Lassi', 'Beverages', 90.00, 1, 1, 4.8, 'Thick traditional churned yogurt topped with a dollop of fresh clotted cream and pistachios.', 'https://images.unsplash.com/photo-1571006682855-90059bf15d48?w=600&q=80'),

-- Curry Corner (3)
(10, 3, 'Mysore Masala Dosa', 'South Indian', 130.00, 1, 1, 4.9, 'Golden crispy rice crepe smeared with fiery red garlic chutney and stuffed with spiced potato masala.', 'https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=600&q=80'),
(11, 3, 'Ghee Podi Idli (4 pcs)', 'South Indian', 110.00, 1, 1, 4.8, 'Steamed soft rice cakes tossed in fragrant gunpowder podi and desi cow ghee.', 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=600&q=80'),
(12, 3, 'Medu Vada (2 pcs)', 'South Indian', 90.00, 1, 1, 4.7, 'Crispy lentil donuts fried to golden perfection, served with sambar and fresh coconut chutney.', 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&q=80'),
(13, 3, 'South Indian Filter Coffee', 'Beverages', 60.00, 1, 1, 4.9, 'Classic chicory blend decoction frothed high with creamy hot milk in traditional brass davarah.', 'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=600&q=80'),

-- The Breakfast Club (4)
(14, 4, 'Classic Pancakes Platter', 'Fast Food', 220.00, 1, 1, 4.6, 'Three fluffy buttermilk pancakes stacked with maple syrup, whipped butter, and fresh seasonal berries.', 'https://images.unsplash.com/photo-1528198642995-17a82448b2d7?w=600&q=80'),
(15, 4, 'Grilled Cheese & Corn Panini', 'Fast Food', 180.00, 1, 1, 4.5, 'Sourdough bread grilled with gooey cheddar, mozzarella, sweet corn, and jalapeños.', 'https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=600&q=80'),
(16, 4, 'Nutella Waffles', 'Desserts', 210.00, 1, 1, 4.7, 'Crispy Belgian waffle smothered in Belgian chocolate hazelnut spread with vanilla bean ice cream.', 'https://images.unsplash.com/photo-1562376552-0d160a2f238d?w=600&q=80'),
(17, 4, 'Iced Hazelnut Latte', 'Beverages', 150.00, 1, 1, 4.6, 'Double shot espresso shaken with chilled milk and toasted hazelnut syrup over ice.', 'https://images.unsplash.com/photo-1517701550927-30cf4ba1dba5?w=600&q=80'),

-- Wok Street (5)
(18, 5, 'Veg Hakka Noodles', 'Chinese', 180.00, 1, 1, 4.6, 'Wok-tossed noodles with shredded cabbage, carrots, bell peppers, and savoury soy sauce.', 'https://images.unsplash.com/photo-1585032226651-759b368d7246?w=600&q=80'),
(19, 5, 'Schezwan Fried Rice', 'Chinese', 190.00, 1, 1, 4.7, 'Fiery stir-fried jasmine rice with garden greens and house-made pungent Schezwan chili paste.', 'https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=600&q=80'),
(20, 5, 'Chili Paneer Dry', 'Chinese', 230.00, 1, 1, 4.8, 'Crispy cottage cheese wok-tossed with scallions, capsicum, green chilies, and dark soy.', 'https://images.unsplash.com/photo-1567184109270-b2db1797e782?w=600&q=80'),
(21, 5, 'Crispy Honey Chili Potatoes', 'Fast Food', 170.00, 1, 1, 4.5, 'Crisp potato fingers glazed in sticky honey chili sauce topped with toasted white sesame.', 'https://images.unsplash.com/photo-1585032226651-759b368d7246?w=600&q=80'),

-- Pune Bites (6)
(22, 6, 'Puneri Special Misal Pav', 'Fast Food', 120.00, 1, 1, 4.9, 'Fiery sprouted moth bean curry served with crunchy farsan, chopped onions, lemon, and soft pavs.', 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&q=80'),
(23, 6, 'Crispy Kothimbir Vadi (6 pcs)', 'Fast Food', 95.00, 1, 1, 4.8, 'Steamed cilantro and gram flour cakes tempered and deep-fried to crisp perfection.', 'https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600&q=80'),
(24, 6, 'Puran Poli with Desi Ghee (2 pcs)', 'Desserts', 130.00, 1, 1, 4.9, 'Traditional sweet flatbread stuffed with chana dal and jaggery spiced with nutmeg and cardamom.', 'https://images.unsplash.com/photo-1601050690117-94f5f6fa8bd7?w=600&q=80'),
(25, 6, 'Authentic Sol Kadhi', 'Beverages', 60.00, 1, 1, 4.8, 'Digestive Konkani pink drink made from pure coconut milk, tangy kokum, garlic, and green chilies.', 'https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=600&q=80'),

-- Deccan Delights (7)
(26, 7, 'Royal Hyderabadi Veg Biryani', 'North Indian', 260.00, 1, 1, 4.7, 'Marinated vegetables layered with aged basmati, saffron milk, fried onions, and fresh mint.', 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&q=80'),
(27, 7, 'Mutton Galouti Kebab (4 pcs)', 'North Indian', 380.00, 0, 1, 4.8, 'Melt-in-mouth smoked lamb patties prepared with 32 secret Lucknowi spices, served with sheermal.', 'https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600&q=80'),
(28, 7, 'Shahi Tukda', 'Desserts', 150.00, 1, 1, 4.7, 'Ghee-fried bread soaked in aromatic cardamom syrup topped with saffron rabdi and silver vark.', 'https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=600&q=80'),

-- Green Leaf Bistro (8)
(29, 8, 'Mediterranean Quinoa Salad', 'Fast Food', 240.00, 1, 1, 4.5, 'Fluffy organic quinoa tossed with English cucumbers, cherry tomatoes, olives, and lemon dressing.', 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=600&q=80'),
(30, 8, 'Dragon Fruit & Berry Smoothie Bowl', 'Desserts', 230.00, 1, 1, 4.6, 'Thick frozen dragon fruit blend topped with chia seeds, toasted almonds, and organic granola.', 'https://images.unsplash.com/photo-1590080875515-8a3a8dc5735e?w=600&q=80'),
(31, 8, 'Cold-Pressed Green Detox Juice', 'Beverages', 140.00, 1, 1, 4.4, 'Fresh cold-pressed blend of green apple, celery, cucumber, baby spinach, and fresh ginger.', 'https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=600&q=80');

-- ----------------------------------------------------------
-- 4. SEED OFFERS
-- ----------------------------------------------------------
INSERT IGNORE INTO Offer (offer_id, code, description, discount_pct, max_discount, min_order_amount, valid_from, valid_to, is_active) VALUES
(1, 'WELCOME50', '50% off on your first booking up to ₹100', 50, 100.00, 199.00, '2026-01-01 00:00:00', '2027-12-31 23:59:59', 1),
(2, 'FIRSTORDER', 'Flat 20% discount on entire food cart', 20, 150.00, 250.00, '2026-01-01 00:00:00', '2027-12-31 23:59:59', 1),
(3, 'WEEKEND20', 'Weekend special 20% off on orders above ₹300', 20, 120.00, 300.00, '2026-01-01 00:00:00', '2027-12-31 23:59:59', 1),
(4, 'PUNESPECIAL', 'Flat 15% discount across all top Pune eateries', 15, 80.00, 150.00, '2026-01-01 00:00:00', '2027-12-31 23:59:59', 1),
(5, 'EXPIRED10', 'Expired promo code for testing validity logic', 10, 50.00, 100.00, '2025-01-01 00:00:00', '2025-06-30 23:59:59', 0);

-- ----------------------------------------------------------
-- 5. SEED STAFF
-- ----------------------------------------------------------
INSERT IGNORE INTO Staff (staff_id, name, role, phone, email, restaurant_id, is_active) VALUES
(1, 'Suresh Jadhav', 'Manager', '9822100001', 'suresh.j@spiceroute.com', 1, 1),
(2, 'Ganesh More', 'Head Chef', '9822100002', 'ganesh.m@spiceroute.com', 1, 1),
(3, 'Vikram Shinde', 'Delivery Partner', '9822100003', 'vikram.s@logistics.com', NULL, 1),
(4, 'Santosh Patil', 'Manager', '9822100004', 'santosh.p@urbantadka.com', 2, 1),
(5, 'Mahesh Gaikwad', 'Delivery Partner', '9822100005', 'mahesh.g@logistics.com', NULL, 1),
(6, 'Deepak Kamble', 'Manager', '9822100006', 'deepak.k@punebites.com', 6, 1);

-- ----------------------------------------------------------
-- 6. SEED BOOKINGS, ITEMS, PAYMENTS, FEEDBACK
-- ----------------------------------------------------------
-- Order 1: Delivered order from Spice Route for Customer Rahul Sharma
INSERT IGNORE INTO Booking (booking_id, booking_code, customer_id, restaurant_id, booking_date, status, subtotal, discount_amount, delivery_fee, total_amount, delivery_address, payment_method, payment_status, offer_id, special_instructions) VALUES
(1, 'MB1001', 1, 1, '2026-09-15 13:30:00', 'Delivered', 520.00, 100.00, 40.00, 460.00, 'Flat 402, Mayur Colony, Kothrud, Pune - 411038', 'UPI', 'Paid', 1, 'Please send extra green chutney and onions.');

INSERT IGNORE INTO Booking_Item (booking_item_id, booking_id, meal_id, quantity, price_at_booking, subtotal) VALUES
(1, 1, 1, 1, 280.00, 280.00), -- Paneer Butter Masala
(2, 1, 2, 1, 240.00, 240.00); -- Dal Makhani

INSERT IGNORE INTO Payment (payment_id, booking_id, payment_method, amount, payment_status, transaction_ref, payment_date) VALUES
(1, 1, 'UPI', 460.00, 'Paid', 'TXN_UPI_9837192837', '2026-09-15 13:31:12');

INSERT IGNORE INTO Feedback (feedback_id, customer_id, booking_id, meal_id, rating, comment, created_at) VALUES
(1, 1, 1, 1, 5, 'The paneer butter masala was exceptionally rich and fresh. Arrived piping hot!', '2026-09-15 14:45:00');

-- Order 2: Delivered order from Pune Bites for Customer Priya Kulkarni
INSERT IGNORE INTO Booking (booking_id, booking_code, customer_id, restaurant_id, booking_date, status, subtotal, discount_amount, delivery_fee, total_amount, delivery_address, payment_method, payment_status, offer_id, special_instructions) VALUES
(2, 'MB1002', 2, 6, '2026-09-16 09:15:00', 'Delivered', 345.00, 51.75, 40.00, 333.25, 'B-12, Rohan Tarang, Baner, Pune - 411045', 'Card', 'Paid', 4, 'Extra spicy rassa for the misal.');

INSERT IGNORE INTO Booking_Item (booking_item_id, booking_id, meal_id, quantity, price_at_booking, subtotal) VALUES
(3, 2, 22, 1, 120.00, 120.00), -- Misal Pav
(4, 2, 23, 1, 95.00, 95.00),   -- Kothimbir Vadi
(5, 2, 24, 1, 130.00, 130.00); -- Puran Poli with Desi Ghee

-- Order 3: Out for Delivery order from Curry Corner for Rahul Sharma
INSERT IGNORE INTO Booking (booking_id, booking_code, customer_id, restaurant_id, booking_date, status, subtotal, discount_amount, delivery_fee, total_amount, delivery_address, payment_method, payment_status, offer_id, special_instructions) VALUES
(3, 'MB1003', 1, 3, '2026-09-20 14:00:00', 'Out for Delivery', 300.00, 60.00, 40.00, 280.00, 'Flat 402, Mayur Colony, Kothrud, Pune - 411038', 'COD', 'Pending', 3, 'Please ring the doorbell.');

INSERT IGNORE INTO Booking_Item (booking_item_id, booking_id, meal_id, quantity, price_at_booking, subtotal) VALUES
(6, 3, 10, 1, 130.00, 130.00), -- Mysore Masala Dosa
(7, 3, 11, 1, 110.00, 110.00), -- Ghee Podi Idli
(8, 3, 13, 1, 60.00, 60.00);   -- Filter Coffee

-- Order 4: Confirmed order from Urban Tadka for Amit Deshmukh
INSERT IGNORE INTO Booking (booking_id, booking_code, customer_id, restaurant_id, booking_date, status, subtotal, discount_amount, delivery_fee, total_amount, delivery_address, payment_method, payment_status, offer_id, special_instructions) VALUES
(4, 'MB1004', 3, 2, '2026-09-20 15:00:00', 'Confirmed', 480.00, 0.00, 40.00, 520.00, 'Row House 4, Nyati Estate, Viman Nagar, Pune - 411014', 'UPI', 'Paid', NULL, 'Less oil in gravies please.');

INSERT IGNORE INTO Booking_Item (booking_item_id, booking_id, meal_id, quantity, price_at_booking, subtotal) VALUES
(9, 4, 6, 1, 210.00, 210.00),  -- Amritsari Kulcha
(10, 4, 7, 1, 270.00, 270.00); -- Kadhai Paneer

INSERT IGNORE INTO Payment (payment_id, booking_id, payment_method, amount, payment_status, transaction_ref, payment_date) VALUES
(2, 4, 'UPI', 520.00, 'Paid', 'TXN_UPI_8830182741', '2026-09-20 15:01:45');
