# bot.py

import telebot
from telebot import types
import time
import json
from datetime import datetime
from config import Config
from database import Database
import logging

# ============================================
# 🔐 تنظیمات اولیه
# ============================================

# توکن‌ها از config میاد
bot = telebot.TeleBot(Config.BOT_TOKEN)
db = Database()

# لاگینگ برای دیباگ
logging.basicConfig(level=logging.INFO)

# ============================================
# 🎯 دکمه‌های شیشه‌ای (منوی اصلی)
# ============================================

def main_menu():
    """منوی اصلی ربات"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    buttons = [
        types.InlineKeyboardButton("🛒 محصولات", callback_data="products"),
        types.InlineKeyboardButton("🪙 سکه و تخفیف", callback_data="coins"),
        types.InlineKeyboardButton("📦 سفارشات من", callback_data="my_orders"),
        types.InlineKeyboardButton("📩 پشتیبانی", callback_data="support"),
        types.InlineKeyboardButton("🎁 تخفیف‌ها", callback_data="discounts"),
        types.InlineKeyboardButton("📢 کانال", url=Config.BRAND_CHANNEL),
        types.InlineKeyboardButton("🌐 وب‌سایت", url=Config.BRAND_WEBSITE),
        types.InlineKeyboardButton("📞 تماس", callback_data="contact")
    ]
    
    for btn in buttons:
        markup.add(btn)
    
    return markup

# ============================================
# 📌 کامند /start
# ============================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # ثبت کاربر در دیتابیس
    db.add_user(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    coins = db.get_coins(user_id)
    discount = db.get_discount(user_id)
    
    welcome_text = f"""
سلام {message.from_user.first_name}! 👋

به **{Config.BRAND_NAME}** خوش آمدید.

🎯 **ما ارائه‌دهنده:**
✅ طراحی سایت فروشگاهی
✅ اپلیکیشن موبایل و دسکتاپ
✅ سئو و بهینه‌سازی
✅ ربات هوشمند پشتیبانی

🪙 **سکه شما:** {coins}
🎁 **تخفیف شما:** {discount}%

📩 پشتیبانی: {Config.BRAND_SUPPORT}
📢 کانال: {Config.BRAND_CHANNEL}
🌐 سایت: {Config.BRAND_WEBSITE}

منوی اصلی رو انتخاب کنید 👇
"""
    
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        reply_markup=main_menu()
    )

# ============================================
# 📌 کامند /help
# ============================================

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
📖 **راهنمای کامل ربات دیجیتالایز**

🔹 `/start` - شروع مجدد
🔹 `/help` - این راهنما
🔹 `/products` - لیست محصولات
🔹 `/coins` - سکه و تخفیف
🔹 `/orders` - سفارشات من
🔹 `/support` - پشتیبانی

💡 **نکته:** 
برای خرید، از منوی اصلی استفاده کنید.
هر سفارش = ۵۰ سکه جایزه!

📩 پشتیبانی: {Config.BRAND_SUPPORT}
"""
    bot.send_message(message.chat.id, help_text)

# ============================================
# 📌 کامند /products
# ============================================

@bot.message_handler(commands=['products'])
def show_products(message):
    products_menu(message)

# ============================================
# 🛒 مدیریت محصولات
# ============================================

def products_menu(message):
    """نمایش لیست محصولات"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for pid, product in Config.PRODUCTS.items():
        btn = types.InlineKeyboardButton(
            f"{product['name']} - {product['price']:,} تومان",
            callback_data=f"product_{pid}"
        )
        markup.add(btn)
    
    btn_back = types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")
    markup.add(btn_back)
    
    bot.send_message(
        message.chat.id,
        "🛒 **محصولات دیجیتالایز:**\n\nلطفاً یکی از محصولات زیر رو انتخاب کنید:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_"))
def handle_product(call):
    product_id = call.data.replace("product_", "")
    product = Config.PRODUCTS.get(product_id)
    
    if not product:
        bot.answer_callback_query(call.id, "محصول یافت نشد!")
        return
    
    user_id = call.from_user.id
    discount = db.get_discount(user_id)
    final_price = product['price'] * (100 - discount) // 100
    
    text = f"""
📦 **{product['name']}**

📝 {product['description']}

💰 قیمت: {product['price']:,} تومان
🎁 تخفیف شما: {discount}%
💵 قیمت نهایی: {final_price:,} تومان

🪙 سکه شما: {db.get_coins(user_id)}

برای خرید، دکمه زیر رو بزنید.
"""
    
    markup = types.InlineKeyboardMarkup()
    btn_buy = types.InlineKeyboardButton(
        "🛒 خرید", 
        callback_data=f"buy_{product_id}"
    )
    btn_back = types.InlineKeyboardButton("🔙 بازگشت", callback_data="products_back")
    markup.add(btn_buy, btn_back)
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

# ============================================
# 💳 پرداخت و خرید
# ============================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_buy(call):
    product_id = call.data.replace("buy_", "")
    user_id = call.from_user.id
    
    # ایجاد سفارش
    order_id = db.create_order(user_id, product_id)
    
    if not order_id:
        bot.answer_callback_query(call.id, "خطا در ایجاد سفارش!")
        return
    
    order = db.get_order(order_id)
    product = Config.PRODUCTS.get(product_id)
    
    # دکمه‌های پرداخت
    markup = types.InlineKeyboardMarkup()
    btn_pay = types.InlineKeyboardButton(
        "💳 پرداخت", 
        callback_data=f"pay_{order_id}"
    )
    btn_cancel = types.InlineKeyboardButton(
        "❌ انصراف", 
        callback_data=f"cancel_order_{order_id}"
    )
    markup.add(btn_pay, btn_cancel)
    
    text = f"""
✅ **سفارش ثبت شد!**

🆔 شماره سفارش: {order_id}
📦 محصول: {product['name']}
💰 قیمت: {order[5]:,} تومان
🎁 تخفیف: {order[6]}%
💵 مبلغ قابل پرداخت: {order[7]:,} تومان

🪙 سکه دریافت کردید: +{Config.COINS_PER_ORDER}

برای پرداخت، روی دکمه زیر کلیک کنید.
"""
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def handle_payment(call):
    order_id = int(call.data.replace("pay_", ""))
    user_id = call.from_user.id
    
    # شبیه‌سازی پرداخت
    # در حالت واقعی، اینجا درگاه پرداخت رو وصل کن
    
    # به‌روزرسانی وضعیت سفارش
    db.update_order_status(order_id, "paid")
    
    # اضافه کردن سکه اضافی
    db.add_coins(user_id, 10, "پرداخت موفق")
    
    markup = types.InlineKeyboardMarkup()
    btn_track = types.InlineKeyboardButton("📦 پیگیری سفارش", callback_data="my_orders")
    btn_back = types.InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")
    markup.add(btn_track, btn_back)
    
    text = f"""
✅ **پرداخت با موفقیت انجام شد!**

🆔 شماره سفارش: {order_id}
✅ وضعیت: پرداخت شده

🎁 سکه اضافی: +۱۰

📩 برای پیگیری سفارش، با پشتیبانی تماس بگیرید:
{Config.BRAND_SUPPORT}
"""
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id, "پرداخت موفق ✅")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_order_"))
def cancel_order(call):
    order_id = int(call.data.replace("cancel_order_", ""))
    
    db.update_order_status(order_id, "cancelled")
    
    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")
    markup.add(btn_back)
    
    bot.edit_message_text(
        "❌ سفارش لغو شد.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )
    bot.answer_callback_query(call.id, "سفارش لغو شد")

# ============================================
# 🪙 مدیریت سکه و تخفیف
# ============================================

@bot.message_handler(commands=['coins'])
def show_coins(message):
    coins_menu(message)

def coins_menu(message):
    user_id = message.from_user.id
    coins = db.get_coins(user_id)
    discount = db.get_discount(user_id)
    
    text = f"""
🪙 **سکه و تخفیف شما**

💰 تعداد سکه: **{coins}** سکه

🎁 تخفیف فعلی: **{discount}%**

📊 **سطح تخفیف‌ها:**
• ۱۰۰ سکه = ۵٪ تخفیف
• ۲۰۰ سکه = ۱۰٪ تخفیف
• ۵۰۰ سکه = ۲۰٪ تخفیف
• ۱۰۰۰ سکه = ۳۰٪ تخفیف

🔹 هر سفارش = +۵۰ سکه
🔹 معرفی دوستان = +۲۰ سکه
🔹 ثبت‌نام در کانال = +۱۰ سکه

💡 برای استفاده از تخفیف، کافیه سفارش بدید!
"""
    
    markup = types.InlineKeyboardMarkup()
    btn_products = types.InlineKeyboardButton("🛒 خرید با تخفیف", callback_data="products")
    btn_back = types.InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")
    markup.add(btn_products, btn_back)
    
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# ============================================
# 📦 سفارشات من
# ============================================

@bot.message_handler(commands=['orders'])
def my_orders(message):
    show_orders(message)

def show_orders(message):
    user_id = message.from_user.id
    orders = db.get_user_orders(user_id)
    
    if not orders:
        text = "📦 **شما هیچ سفارشی ندارید.**\nبرای خرید از منوی اصلی اقدام کنید."
        markup = types.InlineKeyboardMarkup()
        btn_products = types.InlineKeyboardButton("🛒 محصولات", callback_data="products")
        markup.add(btn_products)
        bot.send_message(message.chat.id, text, reply_markup=markup)
        return
    
    text = "📦 **سفارشات شما:**\n\n"
    for order in orders[:5]:  # ۵ سفارش آخر
        status_emoji = {
            'pending': '⏳',
            'paid': '✅',
            'cancelled': '❌'
        }.get(order[6], '❓')
        
        text += f"""
🆔 #{order[0]} - {order[3]}
💰 {order[7]:,} تومان
وضعیت: {status_emoji} {order[6]}
📅 {order[8][:10]}
---
"""
    
    markup = types.InlineKeyboardMarkup()
    btn_products = types.InlineKeyboardButton("🛒 خرید جدید", callback_data="products")
    btn_back = types.InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")
    markup.add(btn_products, btn_back)
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# ============================================
# 📩 پشتیبانی
# ============================================

@bot.message_handler(commands=['support'])
def show_support(message):
    support_menu(message)

def support_menu(message):
    text = f"""
📩 **پشتیبانی دیجیتالایز**

👤 پشتیبان: {Config.BRAND_SUPPORT}
📢 کانال: {Config.BRAND_CHANNEL}
🌐 سایت: {Config.BRAND_WEBSITE}

⏰ پاسخگویی: ۲۴/۷

💬 **سوالات متداول:**
۱. هزینه طراحی سایت چقدره؟
۲. چقدر طول میکشه؟
۳. آیا پشتیبانی دارید؟
۴. چطور سفارش بدم؟

برای سوالات بیشتر، با پشتیبان تماس بگیرید.
"""
    
    markup = types.InlineKeyboardMarkup()
    btn_admin = types.InlineKeyboardButton(
        "📩 تماس با پشتیبان", 
        url=f"https://ble.ir/{Config.BRAND_SUPPORT.replace('@', '')}"
    )
    btn_channel = types.InlineKeyboardButton(
        "📢 عضویت در کانال", 
        url=Config.BRAND_CHANNEL
    )
    btn_faq = types.InlineKeyboardButton("❓ سوالات متداول", callback_data="faq")
    btn_back = types.InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")
    markup.add(btn_admin, btn_channel, btn_faq, btn_back)
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# ============================================
# ❓ سوالات متداول
# ============================================

@bot.callback_query_handler(func=lambda call: call.data == "faq")
def show_faq(call):
    text = """
❓ **سوالات متداول**

**س: هزینه طراحی سایت چقدره؟**
ج: از ۱۰ میلیون تومان به بالا، بسته به امکانات.

**س: چقدر طول میکشه؟**
ج: معمولاً ۲-۴ هفته کاری.

**س: آیا پشتیبانی دارید؟**
ج: بله، ۲۴/۷ از طریق @digitalize_admin

**س: تخفیف دارید؟**
ج: بله، ۳۰٪ تخفیف برای سفارش اول.

**س: چطور سفارش بدم؟**
ج: از طریق ربات یا تماس با پشتیبان.

**س: سکه چیه؟**
ج: امتیازهایی که با ثبت سفارش و فعالیت جمع میشه و تخفیف میده.
"""
    
    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("🔙 بازگشت", callback_data="support_back")
    markup.add(btn_back)
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

# ============================================
# 🎁 تخفیف‌ها
# ============================================

@bot.callback_query_handler(func=lambda call: call.data == "discounts")
def show_discounts(call):
    user_id = call.from_user.id
    coins = db.get_coins(user_id)
    discount = db.get_discount(user_id)
    
    text = f"""
🎁 **تخفیف‌های ویژه دیجیتالایز**

🔥 **تخفیف ۳۰٪** برای اولین سفارش

🪙 **تخفیف با سکه:**
• ۱۰۰ سکه = ۵٪ تخفیف
• ۲۰۰ سکه = ۱۰٪ تخفیف
• ۵۰۰ سکه = ۲۰٪ تخفیف
• ۱۰۰۰ سکه = ۳۰٪ تخفیف

💰 **سکه شما:** {coins}
🎁 **تخفیف فعلی:** {discount}%

📢 **تخفیف‌های مناسبت‌ها**
در ایام خاص، تخفیف‌های ویژه داریم.

💡 برای استفاده از تخفیف، کافیه سفارش بدید!
"""
    
    markup = types.InlineKeyboardMarkup()
    btn_products = types.InlineKeyboardButton("🛒 خرید با تخفیف", callback_data="products")
    btn_back = types.InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")
    markup.add(btn_products, btn_back)
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

# ============================================
# 📞 تماس با ما
# ============================================

@bot.callback_query_handler(func=lambda call: call.data == "contact")
def show_contact(call):
    text = f"""
📞 **ارتباط با دیجیتالایز**

👤 پشتیبان: {Config.BRAND_SUPPORT}
📢 کانال: {Config.BRAND_CHANNEL}
🌐 سایت: {Config.BRAND_WEBSITE}

سریع‌ترین راه، پیام به پشتیبان هست.
"""
    
    markup = types.InlineKeyboardMarkup()
    btn_admin = types.InlineKeyboardButton(
        "📩 تماس با پشتیبان",
        url=f"https://ble.ir/{Config.BRAND_SUPPORT.replace('@', '')}"
    )
    btn_back = types.InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")
    markup.add(btn_admin, btn_back)
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

# ============================================
# 🔙 مدیریت بازگشت‌ها
# ============================================

@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_to_main(call):
    send_welcome(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "products_back")
def products_back(call):
    products_menu(call.message)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "support_back")
def support_back(call):
    support_menu(call.message)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "my_orders")
def orders_back(call):
    show_orders(call.message)
    bot.answer_callback_query(call.id)

# ============================================
# 📊 آمار ربات (فقط برای ادمین)
# ============================================

@bot.message_handler(commands=['stats'])
def show_stats(message):
    # فقط ادمین می‌تونه ببینه
    if str(message.from_user.id) != "YOUR_ADMIN_ID":
        bot.reply_to(message, "⛔ شما دسترسی ندارید!")
        return
    
    stats = db.get_stats()
    
    text = f"""
📊 **آمار ربات دیجیتالایز**

👤 کاربران: {stats['users']}
📦 سفارشات: {stats['orders']}
💰 درآمد کل: {stats['revenue']:,} تومان

📈 وضعیت: فعال ✅
"""
    bot.reply_to(message, text)

# ============================================
# 🚀 اجرای ربات
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("🤖 ربات دیجیتالایز راه‌اندازی شد!")
    print(f"📢 کانال: {Config.BRAND_CHANNEL}")
    print(f"📩 پشتیبانی: {Config.BRAND_SUPPORT}")
    print("=" * 50)
    
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"⚠️ خطا: {e}")
            time.sleep(10)
