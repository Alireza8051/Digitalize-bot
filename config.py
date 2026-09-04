# config.py - این فایل رو هرگز به کسی نده!

import os
from dotenv import load_dotenv

load_dotenv()  # بارگذاری از فایل .env

class Config:
    # ============================================
    # 🔐 توکن‌های مخفی (از .env بخون)
    # ============================================
    
    # توکن اصلی ربات (از BotFather بگیر)
    BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    
    # توکن پرداخت (از بخش Wallet بگیر)
    PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN", "YOUR_PAYMENT_TOKEN_HERE")
    
    # ============================================
    # 💾 تنظیمات دیتابیس
    # ============================================
    
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///digitalize.db")
    
    # ============================================
    # 🎁 تنظیمات تخفیف‌ها و سکه
    # ============================================
    
    COINS_PER_ORDER = 50      # سکه برای هر سفارش
    COINS_PER_REFERRAL = 20   # سکه برای معرفی
    COINS_PER_REGISTER = 10   # سکه برای ثبت‌نام
    
    DISCOUNT_RATES = {
        100: 5,   # ۱۰۰ سکه = ۵٪ تخفیف
        200: 10,  # ۲۰۰ سکه = ۱۰٪ تخفیف
        500: 20,  # ۵۰۰ سکه = ۲۰٪ تخفیف
        1000: 30, # ۱۰۰۰ سکه = ۳۰٪ تخفیف
    }
    
    # ============================================
    # 🛒 محصولات و قیمت‌ها
    # ============================================
    
    PRODUCTS = {
        "website": {
            "name": "طراحی سایت فروشگاهی",
            "price": 10000000,
            "description": "سایت فروشگاهی کامل با پنل مدیریت"
        },
        "app_mobile": {
            "name": "اپلیکیشن موبایل",
            "price": 15000000,
            "description": "اپلیکیشن اندروید و iOS"
        },
        "app_desktop": {
            "name": "اپلیکیشن دسکتاپ",
            "price": 12000000,
            "description": "اپلیکیشن ویندوز و مک"
        },
        "template": {
            "name": "قالب اختصاصی",
            "price": 3000000,
            "description": "قالب متناسب با برند شما"
        },
        "seo": {
            "name": "سئو و بهینه‌سازی",
            "price": 3000000,
            "description": "بهبود رتبه در گوگل"
        },
        "bot": {
            "name": "ربات هوشمند",
            "price": 5000000,
            "description": "ربات پشتیبانی ۲۴/۷"
        }
    }
    
    # ============================================
    # 📢 اطلاعات برند
    # ============================================
    
    BRAND_NAME = "دیجیتالایز"
    BRAND_CHANNEL = "@digitalize"
    BRAND_SUPPORT = "@digitalize_admin"
    BRAND_WEBSITE = "https://digitalize.rf.gd"
