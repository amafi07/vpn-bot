from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import os
import json
import random
import datetime
import nest_asyncio

# ----------- Event Loop Fix for Railway -----------
nest_asyncio.apply()

# ---------- Config from Environment ----------
ADMIN_ID = int(os.getenv("ADMIN_ID", "1123292102"))  # توکن خودت رو جای 123456789 بذار
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CARD_NUMBER = os.getenv("CARD_NUMBER", "0000-0000-0000-0000")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "")  # @yourchannel

# ---------- Utils ----------
def load_json(path):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ---------- Plans ----------
plans = {
    "1m": {"name": "یک ماهه", "price": 100_000, "days": 30},
    "3m": {"name": "سه ماهه", "price": 250_000, "days": 90},
}

# ---------- Check Channel Join ----------
async def is_user_joined(context, user_id):
    if not CHANNEL_USERNAME:
        return True
    try:
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id
        )
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ---------- Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎁 دریافت کانفیگ رایگان", callback_data="free")],
        [InlineKeyboardButton("🛒 خرید اشتراک", callback_data="buy")]
    ]
    await update.message.reply_text(
        "👋 خوش اومدی!\n\nبرای دریافت کانفیگ رایگان اول عضو کانال شو 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ---------- Free Config ----------
async def free_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(update.effective_user.id)

    # چک عضویت
    joined = await is_user_joined(context, update.effective_user.id)
    if not joined:
        keyboard = [[
            InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME.strip('@vpn_eagleir')}"),
        ],[
            InlineKeyboardButton("✅ عضو شدم", callback_data="check_join")
        ]]
        await query.edit_message_text(
            "❌ برای دریافت کانفیگ رایگان باید عضو کانال بشی:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    users = load_json("data/free_users.json")
    if user_id in users:
        await query.edit_message_text("⚠️ شما قبلاً کانفیگ رایگان رو دریافت کردید.")
        return

    configs = load_json("data/configs.json")
    free_configs = configs.get("free", ["کانفیگ رایگان موجود نیست"])
    config = random.choice(free_configs)

    users[user_id] = {"config": config, "date": str(datetime.date.today())}
    save_json("data/free_users.json", users)

    await query.edit_message_text(f"🎁 کانفیگ رایگان شما:\n\n{config}\n\n⚠️ فقط یک‌بار قابل دریافت است")

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await free_config(update, context)

# ---------- Paid Plans ----------
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🟢 یک ماهه", callback_data="plan_1m")],
        [InlineKeyboardButton("🔵 سه ماهه", callback_data="plan_3m")],
    ]
    await query.edit_message_text(
        "پلن مورد نظر رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    plan_key = query.data.replace("plan_", "")
    orders = load_json("data/orders.json")
    orders[user_id] = {"plan": plan_key, "status": "waiting"}
    save_json("data/orders.json", orders)

    await query.edit_message_text(
        f"✅ پلن انتخاب شد\n\n💳 مبلغ: {plans[plan_key]['price']:,} تومان\n🏦 کارت: {CARD_NUMBER}\n\n📸 بعد از پرداخت، رسید رو ارسال کن"
    )

async def receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    orders = load_json("data/orders.json")

    if user_id in orders and orders[user_id]["status"] == "waiting":
        await context.bot.send_message(
            ADMIN_ID,
            f"📥 رسید جدید از {user_id}\nپلن: {orders[user_id]['plan']}",
        )
        orders[user_id]["status"] = "sent"
        save_json("data/orders.json", orders)
        await update.message.reply_text("✅ رسید ارسال شد، منتظر تایید ادمین")

async def admin_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    user_id = update.message.text.replace("/confirm ", "")
    users = load_json("data/users.json")
    orders = load_json("data/orders.json")
    configs = load_json("data/configs.json")
    plan = orders[user_id]["plan"]
    config = random.choice(configs.get(plan, ["کانفیگ موجود نیست"]))
    expire = datetime.date.today() + datetime.timedelta(days=plans[plan]["days"])
    users[user_id] = {"config": config, "expire": str(expire)}
    save_json("data/users.json", users)
    await context.bot.send_message(
        user_id,
        f"📦 کانفیگ شما:\n{config}\n⏳ انقضا: {expire}",
    )

async def myconfig(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    users = load_json("data/users.json")
    if user_id not in users:
        await query.edit_message_text(
            "❌ اشتراک فعالی نداری\n\nاول از بخش 🛒 خرید اشتراک اقدام کن"
        )
        return
    await query.edit_message_text(
        f"📦 کانفیگ شما:\n\n{users[user_id]['config']}\n\n⏳ انقضا: {users[user_id]['expire']}"
    )

# ---------- Main ----------
async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("confirm", admin_confirm))

    # Callbacks
    application.add_handler(CallbackQueryHandler(free_config, pattern="^free$"))
    application.add_handler(CallbackQueryHandler(check_join, pattern="^check_join$"))
    application.add_handler(CallbackQueryHandler(buy, pattern="^buy$"))
    application.add_handler(CallbackQueryHandler(select_plan, pattern="^plan_"))
    application.add_handler(CallbackQueryHandler(myconfig, pattern="^myconfig$"))

    # Messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receipt))

    print("🔥 VPN Sales Bot Running")
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

    }
    save_json("data/free_users.json", users)

    msg = f"🎁 کانفیگ رایگان شما:\n\n{config}\n\n⚠️ فقط یک‌بار قابل دریافت است"
    if query:
        await query.edit_message_text(msg)
    else:
        await update.message.reply_text(msg)

# ---------- Check Join Button ----------
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await free_config(update, context)

# ---------- Paid Plans ----------
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🟢 یک ماهه", callback_data="plan_1m")],
        [InlineKeyboardButton("🔵 سه ماهه", callback_data="plan_3m")],
    ]
    await query.edit_message_text(
        "پلن مورد نظر رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    plan_key = query.data.replace("plan_", "")
    orders = load_json("data/orders.json")
    orders[user_id] = {"plan": plan_key, "status": "waiting"}
    save_json("data/orders.json", orders)

    await query.edit_message_text(
        f"""
✅ پلن انتخاب شد

💳 مبلغ: {plans[plan_key]['price']:,} تومان
🏦 کارت: {CARD_NUMBER}

📸 بعد از پرداخت، رسید رو ارسال کن
"""
    )

async def receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    orders = load_json("data/orders.json")

    if user_id in orders and orders[user_id]["status"] == "waiting":
        await context.bot.send_message(
            ADMIN_ID,
            f"📥 رسید جدید از {user_id}\nپلن: {orders[user_id]['plan']}",
        )
        orders[user_id]["status"] = "sent"
        save_json("data/orders.json", orders)
        await update.message.reply_text("✅ رسید ارسال شد، منتظر تایید ادمین")

async def admin_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    user_id = update.message.text.replace("/confirm ", "")
    users = load_json("data/users.json")
    orders = load_json("data/orders.json")
    configs = load_json("data/configs.json")
    plan = orders[user_id]["plan"]
    config = random.choice(configs.get(plan, ["کانفیگ موجود نیست"]))
    expire = datetime.date.today() + datetime.timedelta(days=plans[plan]["days"])
    users[user_id] = {"config": config, "expire": str(expire)}
    save_json("data/users.json", users)
    await context.bot.send_message(
        user_id,
        f"📦 کانفیگ شما:\n{config}\n⏳ انقضا: {expire}",
    )

async def myconfig(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    users = load_json("data/users.json")
    if user_id not in users:
        await query.edit_message_text(
            "❌ اشتراک فعالی نداری\n\nاول از بخش 🛒 خرید اشتراک اقدام کن"
        )
        return
    await query.edit_message_text(
        f"📦 کانفیگ شما:\n\n{users[user_id]['config']}\n\n⏳ انقضا: {users[user_id]['expire']}"
    )

# ---------- Main ----------
async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("confirm", admin_confirm))

    # CallbackQuery Handlers
    application.add_handler(CallbackQueryHandler(free_config, pattern="^free$"))
    application.add_handler(CallbackQueryHandler(check_join, pattern="^check_join$"))
    application.add_handler(CallbackQueryHandler(buy, pattern="^buy$"))
    application.add_handler(CallbackQueryHandler(select_plan, pattern="^plan_"))
    application.add_handler(CallbackQueryHandler(myconfig, pattern="^myconfig$"))

    # Message Handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receipt))

    print("🔥 VPN Sales Bot Running")
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

