# database.py

import sqlite3
import json
from datetime import datetime
from config import Config

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('digitalize.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        """ایجاد جدول‌های مورد نیاز"""
        # جدول کاربران
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                coins INTEGER DEFAULT 0,
                total_orders INTEGER DEFAULT 0,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                referrer_id INTEGER
            )
        ''')
        
        # جدول سفارشات
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id TEXT,
                product_name TEXT,
                price INTEGER,
                discount INTEGER DEFAULT 0,
                final_price INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # جدول تراکنش‌های سکه
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS coin_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        self.conn.commit()
    
    # ============================================
    # 👤 مدیریت کاربران
    # ============================================
    
    def add_user(self, user_id, username=None, first_name=None, last_name=None):
        """افزودن کاربر جدید"""
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            self.conn.commit()
            
            # سکه ثبت‌نام بده
            self.add_coins(user_id, Config.COINS_PER_REGISTER, "ثبت‌نام در ربات")
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
    
    def get_user(self, user_id):
        """دریافت اطلاعات کاربر"""
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone()
    
    # ============================================
    # 🪙 مدیریت سکه
    # ============================================
    
    def add_coins(self, user_id, amount, reason):
        """افزودن سکه به کاربر"""
        try:
            self.cursor.execute('''
                UPDATE users SET coins = coins + ? WHERE user_id = ?
            ''', (amount, user_id))
            
            self.cursor.execute('''
                INSERT INTO coin_transactions (user_id, amount, reason)
                VALUES (?, ?, ?)
            ''', (user_id, amount, reason))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding coins: {e}")
            return False
    
    def get_coins(self, user_id):
        """دریافت تعداد سکه کاربر"""
        self.cursor.execute('SELECT coins FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    def get_discount(self, user_id):
        """محاسبه تخفیف بر اساس سکه"""
        coins = self.get_coins(user_id)
        discount = 0
        for threshold, rate in sorted(Config.DISCOUNT_RATES.items()):
            if coins >= threshold:
                discount = rate
        return discount
    
    # ============================================
    # 📦 مدیریت سفارشات
    # ============================================
    
    def create_order(self, user_id, product_id):
        """ایجاد سفارش جدید"""
        product = Config.PRODUCTS.get(product_id)
        if not product:
            return None
        
        discount = self.get_discount(user_id)
        final_price = product['price'] * (100 - discount) // 100
        
        self.cursor.execute('''
            INSERT INTO orders (user_id, product_id, product_name, price, discount, final_price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, product_id, product['name'], product['price'], discount, final_price))
        
        self.conn.commit()
        order_id = self.cursor.lastrowid
        
        # سکه برای ثبت سفارش
        self.add_coins(user_id, Config.COINS_PER_ORDER, "ثبت سفارش")
        
        return order_id
    
    def get_order(self, order_id):
        """دریافت اطلاعات سفارش"""
        self.cursor.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,))
        return self.cursor.fetchone()
    
    def update_order_status(self, order_id, status):
        """به‌روزرسانی وضعیت سفارش"""
        self.cursor.execute('''
            UPDATE orders SET status = ? WHERE order_id = ?
        ''', (status, order_id))
        self.conn.commit()
    
    def get_user_orders(self, user_id):
        """دریافت لیست سفارشات کاربر"""
        self.cursor.execute('''
            SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,))
        return self.cursor.fetchall()
    
    # ============================================
    # 📊 آمار
    # ============================================
    
    def get_stats(self):
        """دریافت آمار کلی"""
        self.cursor.execute('SELECT COUNT(*) FROM users')
        users = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM orders')
        orders = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT SUM(price) FROM orders WHERE status = "paid"')
        total = self.cursor.fetchone()[0] or 0
        
        return {
            'users': users,
            'orders': orders,
            'revenue': total
        }
    
    def close(self):
        self.conn.close()
