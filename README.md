# Meal Booking System

> **Smart Meal Discovery & Booking Platform**  
> *A practical, production-ready DBMS portfolio project built with Python, Flask, and MySQL.*

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask 3.1](https://img.shields.io/badge/Flask-3.1-black.svg)](https://flask.palletsprojects.com/)
[![MySQL 8.0+](https://img.shields.io/badge/MySQL-8.0%2B-orange.svg)](https://www.mysql.com/)
[![Tests](https://img.shields.io/badge/Tests-18%20Passed-brightgreen.svg)](tests/test_app.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Meal Booking System** is a full-featured, database-driven food discovery and ordering web platform inspired by modern consumer food delivery services. Built specifically to showcase robust **Database Management System (DBMS)** principles, the project combines industrial-strength relational schema design (3NF, domain constraints, foreign key cascades, triggers, stored procedures, and views) with an interactive, responsive web user interface.

---

## 📸 Overview & Highlights

- **Pure Relational Database Backbone**: Backed by a normalized MySQL schema featuring 9 core tables, foreign key constraints (`CASCADE` & `SET NULL`), domain `CHECK` constraints, unique keys, and multi-query atomic transactions.
- **Realistic Pune Eateries Catalog**: Curated sample data featuring 8 Pune restaurants and 31 authentic dishes across Pune localities (**Kothrud, Baner, Karve Nagar, Aundh, Viman Nagar, Shivajinagar, Koregaon Park, Hadapsar**).
- **Interactive UI (No Bloated Frameworks)**: Clean, modern interface built with semantic HTML5, modern CSS3 variables, and vanilla JavaScript for dynamic cart operations, live toast notifications, Veg/Non-Veg indicators, and coupon application.
- **Built-in CLI Database Manager (`database/init_db.py`)**: Reproducible, idempotent setup and health verification utility with automatic delimiter handling for triggers and stored procedures.
- **Pre-Flight Diagnostics on Startup**: `python run.py` automatically validates database connectivity and schema readiness before launching the server, displaying troubleshooting advice if MySQL is unreachable.
- **1-Click Test Personas**: Instant login buttons for both **Customer** and **Administrator** roles with pre-loaded order histories and analytics.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend** | Python 3.10+, Flask 3.1 | Modular route blueprints, session management, secure cookie handling |
| **Database** | MySQL 8.0+ / 9.x | Relational storage, integrity constraints, ACID transactions, stored routines |
| **Driver** | PyMySQL 1.1 + Cryptography | Pure Python MySQL driver supporting dictionary cursors and modern auth (`caching_sha2_password`) |
| **Configuration** | python-dotenv 1.0 | Environment-based configuration loaded securely from `.env` |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript | Responsive grid, cards, interactive modals, toasts, badge indicators |
| **Design & Typography** | Font Awesome 6, Plus Jakarta Sans | Modern culinary aesthetic and typography |

---

## 🗄️ Database Design & Relational Schema

The database model (`meal_booking_db`) consists of 9 normalized entities in Third Normal Form (3NF):

```mermaid
erDiagram
    Customer ||--o{ Booking : places
    Customer ||--o{ Feedback : writes
    Restaurant ||--o{ Meal : offers
    Restaurant ||--o{ Booking : receives
    Restaurant ||--o{ Staff : employs
    Booking ||--|{ Booking_Item : contains
    Meal ||--o{ Booking_Item : included_in
    Booking ||--|| Payment : settled_via
    Offer ||--o{ Booking : discounts
    Booking ||--o{ Feedback : evaluated_in
    Meal ||--o{ Feedback : reviewed_in

    Customer {
        int customer_id PK
        varchar full_name
        varchar email UK
        varchar password_hash
        varchar phone
        varchar address
        boolean is_admin
        timestamp created_at
    }

    Restaurant {
        int restaurant_id PK
        varchar name
        varchar cuisine
        varchar location
        decimal rating
        boolean is_active
        int delivery_time_min
        decimal min_order_value
    }

    Meal {
        int meal_id PK
        int restaurant_id FK
        varchar name
        varchar category
        decimal price
        boolean is_veg
        boolean is_available
        decimal rating
    }

    Booking {
        int booking_id PK
        varchar booking_code UK
        int customer_id FK
        int restaurant_id FK
        enum status
        decimal subtotal
        decimal discount_amount
        decimal delivery_fee
        decimal total_amount
        enum payment_method
        enum payment_status
    }

    Booking_Item {
        int booking_item_id PK
        int booking_id FK
        int meal_id FK
        int quantity
        decimal price_at_booking
        decimal subtotal
    }

    Payment {
        int payment_id PK
        int booking_id FK
        enum payment_method
        decimal amount
        enum payment_status
        varchar transaction_ref UK
    }

    Offer {
        int offer_id PK
        varchar code UK
        int discount_pct
        decimal max_discount
        decimal min_order_amount
        datetime valid_to
        boolean is_active
    }
```

### Core Entities & Constraints

1. **`Customer`**: User accounts with secure password hashing (Werkzeug scrypt/PBKDF2), unique email constraints, and admin privilege flags.
2. **`Restaurant`**: Operating parameters including `CHECK (delivery_time_min > 0)`, `CHECK (rating BETWEEN 1.0 AND 5.0)`, and minimum order values.
3. **`Meal`**: Dishes linked via foreign key to `Restaurant` with `CHECK (price > 0.00)`, category, dietary tags (`is_veg`), and stock availability.
4. **`Booking`**: Master order record with unique order codes (e.g. `MB1001`), delivery coordinates, and status lifecycle (`Pending`, `Confirmed`, `Preparing`, `Out for Delivery`, `Delivered`, `Cancelled`).
5. **`Booking_Item`**: Many-to-Many junction table recording frozen unit price (`price_at_booking`) and item subtotal to safeguard against future menu price updates.
6. **`Payment`**: Financial records tracking payment mode (`COD`, `UPI`, `Card`), transaction references, and settlement timestamps.
7. **`Offer`**: Promotional coupons enforcing minimum cart values, discount caps, percentage bounds (`CHECK (discount_pct BETWEEN 1 AND 100)`), and temporal validity windows (`valid_from` to `valid_to`).
8. **`Feedback`**: Customer ratings (`1-5` stars) and reviews linked to delivered orders.
9. **`Staff`**: Delivery logistics and restaurant operational assignments.

---

## 💡 DBMS Concepts Demonstrated

| Concept | Implementation in Project | SQL Script Reference |
| :--- | :--- | :--- |
| **Relational Schema & DDL** | Primary keys, foreign keys with `ON DELETE CASCADE` / `SET NULL`, `UNIQUE`, `NOT NULL`, `DEFAULT` | `database/schema.sql` |
| **Domain Constraints** | `CHECK (price > 0)`, `CHECK (rating BETWEEN 1 AND 5)`, `CHECK (quantity > 0)` | `database/schema.sql` |
| **Relational Views** | 4 analytical views: `v_restaurant_summary`, `v_popular_meals`, `v_booking_summary`, `v_customer_stats` | `database/views.sql` |
| **Database Triggers** | `trg_prevent_unavailable_meal`, `trg_update_meal_rating_after_feedback`, `trg_update_restaurant_rating_after_feedback` | `database/triggers.sql` |
| **Stored Procedures** | `sp_get_admin_dashboard_stats`, `sp_get_restaurant_analytics`, `sp_get_customer_profile_stats`, `sp_validate_offer` | `database/procedures.sql` |
| **Relational Queries** | Multi-table joins (`INNER JOIN`, `LEFT JOIN`), `GROUP BY`, `HAVING`, `WHERE`, `ORDER BY`, subqueries | `database/queries.sql` |
| **ACID Transactions** | Multi-query atomic checkout (inserting `Booking`, multiple `Booking_Item` rows, and `Payment` in a single transaction) | `app/db.py` & `app/routes/customer.py` |

---

## 📁 Project Structure

```text
Meal-Booking-System-DBMS/
├── LICENSE
├── README.md                       # Comprehensive setup and technical guide
├── requirements.txt                # Python runtime dependencies
├── .env.example                    # Safe configuration template
├── .gitignore                      # Git exclusion rules
├── run.py                          # Flask application launcher with pre-flight checks
│
├── database/                       # Relational database scripts & CLI tool
│   ├── __init__.py                 # Database package marker
│   ├── init_db.py                  # Idempotent DB setup, check, and reset utility
│   ├── schema.sql                  # DDL: Database, tables, constraints, indexes
│   ├── seed.sql                    # Realistic sample data (Pune restaurants & dishes)
│   ├── views.sql                   # Relational views for analytics & reporting
│   ├── triggers.sql                # Data integrity & automated rating triggers
│   ├── procedures.sql              # Stored procedures for business logic
│   └── queries.sql                 # 13 categorized showcase DBMS queries
│
├── app/
│   ├── __init__.py                 # Flask application factory, filters, template context
│   ├── config.py                   # Centralized environment configuration
│   ├── db.py                       # PyMySQL pooling, dict cursors, transactions, diagnostics
│   ├── utils.py                    # Cart calculations, booking codes, auth decorators
│   │
│   ├── routes/
│   │   ├── auth.py                 # Login, register, demo 1-click login, logout
│   │   ├── customer.py             # Discovery, filters, cart, checkout, order tracking
│   │   └── admin.py                # Operations dashboard, CRUD, SQL analytics
│   │
│   ├── templates/                  # Modular Jinja2 templates
│   │   ├── base.html               # Shared layout, navbar, toasts, footer
│   │   ├── home.html               # Landing hero, categories, offers, popular meals
│   │   ├── restaurants.html        # Restaurant catalog with Pune locality filter
│   │   ├── restaurant_detail.html  # Categorized menu with quick add
│   │   ├── meals.html              # Multi-filter dish catalog & sorting
│   │   ├── meal_detail.html        # Dish details & verified reviews
│   │   ├── cart.html               # Quantity modifiers & coupon validation
│   │   ├── checkout.html           # Address & simulated payment method
│   │   ├── order_confirmation.html # Booking ID receipt & status summary
│   │   ├── orders.html             # Order history with status badges
│   │   ├── order_detail.html       # Status timeline & 5-star review submission
│   │   ├── offers.html             # Active coupons & expired coupon showcase
│   │   ├── profile.html            # Profile edit & lifetime aggregate stats
│   │   ├── login.html              # Sign in with instant 1-click test buttons
│   │   ├── register.html           # New account registration
│   │   └── admin/
│   │       ├── layout.html         # Persistent admin navigation tabs
│   │       ├── dashboard.html      # Operational KPI metric cards
│   │       ├── restaurants.html    # Restaurant CRUD modal
│   │       ├── meals.html          # Menu item CRUD & stock toggles
│   │       ├── offers.html         # Promo offer management
│   │       ├── bookings.html       # Order status progression pipeline
│   │       ├── customers.html      # User accounts & order spend table
│   │       └── analytics.html      # Deep SQL aggregate charts
│   │
│   └── static/
│       ├── css/
│       │   └── style.css           # Design system, cards, animations, responsive layout
│       └── js/
│           └── main.js             # Cart AJAX, toasts, mobile toggle, modal controller
│
└── tests/
    └── test_app.py                 # Automated test suite (18 unit & integration tests)
```

---

## 🚀 Cross-Platform Installation & Setup

### Prerequisites

- **Python**: Version `3.10` or higher (`python3 --version` or `python --version`)
- **MySQL Server**: Version `8.0` or higher (`mysql --version`)
- **Git**: (`git --version`)

---

### Option A: Linux Mint / Ubuntu

#### 1. Install System Prerequisites
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv mysql-server git
```

#### 2. Ensure MySQL Server is Running
```bash
sudo systemctl enable mysql
sudo systemctl start mysql
sudo systemctl status mysql
```

#### 3. Create Dedicated Database & User
Log into the MySQL root shell:
```bash
sudo mysql
```
Execute the following SQL commands:
```sql
CREATE DATABASE IF NOT EXISTS meal_booking_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'meal_user'@'localhost' IDENTIFIED BY 'meal_password123';
GRANT ALL PRIVILEGES ON meal_booking_db.* TO 'meal_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 4. Clone the Repository & Setup Virtual Environment
```bash
git clone https://github.com/Dev190606oss/Meal-Booking-System-DBMS.git
cd Meal-Booking-System-DBMS

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 5. Configure `.env`
```bash
cp .env.example .env
```
Open `.env` in your text editor (`nano .env`) and set your credentials:
```ini
FLASK_APP=run.py
FLASK_DEBUG=0
HOST=127.0.0.1
PORT=5000
SECRET_KEY=meal_booking_system_super_secret_key_2026

DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=meal_booking_db
DB_USER=meal_user
DB_PASSWORD=meal_password123
```

#### 6. Initialize the Database
Run the built-in database setup utility:
```bash
python database/init_db.py
```
*(Or verify health anytime with `python database/init_db.py --check`)*

#### 7. Run Automated Tests
```bash
python -m unittest -v tests/test_app.py
```

#### 8. Start the Web Server
```bash
python run.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

### Option B: macOS (Intel & Apple Silicon)

#### 1. Install Prerequisites via Homebrew
If Homebrew is not installed, install it from [brew.sh](https://brew.sh/).
```bash
brew install python mysql git
```

#### 2. Start MySQL Service
```bash
brew services start mysql
```
*Verify that MySQL is listening:*
```bash
# Verify process status
brew services list

# Check port (defaults to 3306)
lsof -i :3306
```

#### 3. Create Database & User
```bash
mysql -u root
```
*(If your root user has a password, run `mysql -u root -p` instead).*
```sql
CREATE DATABASE IF NOT EXISTS meal_booking_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'meal_user'@'localhost' IDENTIFIED BY 'meal_password123';
GRANT ALL PRIVILEGES ON meal_booking_db.* TO 'meal_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 4. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/Dev190606oss/Meal-Booking-System-DBMS.git
cd Meal-Booking-System-DBMS

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 5. Configure `.env`
```bash
cp .env.example .env
```
Update `.env` with your settings:
```ini
FLASK_APP=run.py
FLASK_DEBUG=0
HOST=127.0.0.1
PORT=5000
SECRET_KEY=meal_booking_system_super_secret_key_2026

DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=meal_booking_db
DB_USER=meal_user
DB_PASSWORD=meal_password123
```
*(Note: If you have a custom MySQL instance running on port `3307`, set `DB_PORT=3307`).*

#### 6. Initialize Database & Run Server
```bash
python database/init_db.py
python -m unittest -v tests/test_app.py
python run.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)**.

---

### Option C: Windows (PowerShell)

#### 1. Install Prerequisites
- Install **Python 3.10+** from [python.org](https://www.python.org/downloads/) (ensure **"Add Python to PATH"** is checked during installation).
- Install **MySQL Community Server 8.0+** from [mysql.com](https://dev.mysql.com/downloads/installer/).

#### 2. Verify MySQL Service
Open PowerShell as Administrator:
```powershell
Get-Service MySQL*
# If stopped:
net start MySQL80
```

#### 3. Create Database and Dedicated User
Launch the MySQL Command Line Client or run:
```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
```
Run the SQL setup statements:
```sql
CREATE DATABASE IF NOT EXISTS meal_booking_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'meal_user'@'localhost' IDENTIFIED BY 'meal_password123';
GRANT ALL PRIVILEGES ON meal_booking_db.* TO 'meal_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 4. Clone Repository & Setup Virtual Environment
Open PowerShell in your workspace:
```powershell
git clone https://github.com/Dev190606oss/Meal-Booking-System-DBMS.git
cd Meal-Booking-System-DBMS

# Allow script execution in current PowerShell session if restricted
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned

python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### 5. Configure `.env`
```powershell
Copy-Item .env.example .env
```
Edit `.env` using Notepad:
```powershell
notepad .env
```
Set your database credentials:
```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=meal_booking_db
DB_USER=meal_user
DB_PASSWORD=meal_password123
```

#### 6. Initialize Database & Launch Application
```powershell
python database/init_db.py
python -m unittest -v tests/test_app.py
python run.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## 🗃️ Database Initialization CLI Reference

The repository provides a robust command-line utility at `database/init_db.py`:

```bash
# Safe initial setup (warns and prompts before resetting if tables already exist)
python database/init_db.py

# Check database schema health, view status, triggers, and record counts (Non-destructive)
python database/init_db.py --check

# Force drop and recreate all tables, views, triggers, and stored procedures
python database/init_db.py --reset

# Bypass interactive prompt (useful for CI/CD or scripted environments)
python database/init_db.py --reset --force

# Re-run seed data without dropping existing schema
python database/init_db.py --seed-only

# Setup schema, views, triggers, and routines without seed data
python database/init_db.py --skip-seed
```

### Manual SQL Initialization (Alternative)
If you prefer using the native MySQL CLI client directly, run the scripts in exact dependency order:

```bash
mysql -u meal_user -p meal_booking_db < database/schema.sql
mysql -u meal_user -p meal_booking_db < database/seed.sql
mysql -u meal_user -p meal_booking_db < database/views.sql
mysql -u meal_user -p meal_booking_db < database/triggers.sql
mysql -u meal_user -p meal_booking_db < database/procedures.sql
```

---

## 🔑 Demo & Test Credentials

The application includes 1-click test login buttons on the Login page (`/login`):

| Persona | Email | Password | Pre-loaded Data |
| :--- | :--- | :--- | :--- |
| **Customer** | `rahul.sharma@example.com` | `password123` | Active bookings, delivery address in Kothrud, past delivered orders |
| **Admin** | `admin@mealbooking.com` | `password123` | Full access to operational dashboard, CRUD modals, and SQL analytics |

---

## 🧪 Testing

The repository includes comprehensive automated unit and integration tests covering database connectivity, routing, cart logic, coupon validation, triggers, views, and stored procedures:

```bash
# Run complete test suite
python -m unittest -v tests/test_app.py

# Run database health check
python database/init_db.py --check
```

---

## 🔧 Troubleshooting Guide

### 1. `Can't connect to MySQL server on '127.0.0.1'` / `Connection refused`
- **Cause**: MySQL daemon is stopped or listening on another port.
- **Solution**:
  - Linux/Ubuntu: `sudo systemctl start mysql`
  - macOS: `brew services start mysql`
  - Windows: `net start MySQL80`
  - Check which port MySQL is using: `lsof -i :3306` (Unix) or `netstat -ano | findstr 3306` (Windows). If using port 3307, update `DB_PORT=3307` in your `.env`.

### 2. `Access denied for user 'root'@'localhost'` (Error 1045)
- **Cause**: Incorrect password or MySQL authentication plugin mismatch.
- **Solution**:
  - Verify credentials in `.env`.
  - Instead of passwordless root, create a dedicated user:
    ```sql
    CREATE USER 'meal_user'@'localhost' IDENTIFIED BY 'meal_password123';
    GRANT ALL PRIVILEGES ON meal_booking_db.* TO 'meal_user'@'localhost';
    FLUSH PRIVILEGES;
    ```
  - Put `DB_USER=meal_user` and `DB_PASSWORD=meal_password123` in `.env`.

### 3. `Unknown database 'meal_booking_db'` (Error 1049)
- **Cause**: Database has not been created yet.
- **Solution**: Run `python database/init_db.py` to automatically create and populate the database.

### 4. `Address already in use: Port 5000`
- **Cause**: Another service (or macOS AirPlay Receiver) is using port 5000.
- **Solution**:
  - Set a different port in `.env`: `PORT=5001` or `PORT=8000`.
  - On macOS: Disable **AirPlay Receiver** under *System Settings &rarr; General &rarr; AirDrop & Handoff*.
  - Kill the occupying process: `lsof -ti :5000 | xargs kill -9`.

### 5. `Missing required environment variables` / Default values loaded
- **Cause**: `.env` file does not exist in the project root directory.
- **Solution**: Run `cp .env.example .env` and verify the values.

### 6. `Virtual environment script execution disabled` (Windows PowerShell)
- **Cause**: PowerShell execution policy blocks running scripts.
- **Solution**: Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` in PowerShell before running `.\venv\Scripts\Activate.ps1`.

---

## 📄 License
This project is open-source and licensed under the [MIT License](LICENSE). Feel free to fork, customize, and use this repository for your college portfolio or coursework.
