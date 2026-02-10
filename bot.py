print("BOT FILE LOADED")

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "8063211094:AAGa-1CP3L1EsWaQAo3EjANqXQEahrcfDEs"
CHANNEL_USERNAME = "@vpn_eagleir"

async def is_member(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print("MEMBER CHECK ERROR:", e)
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📥 دریافت VPN", callback_data="get_vpn")]]
    await update.message.reply_text(
        "سلام 👋\nبرای دریافت VPN روی دکمه زیر بزن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not await is_member(context.bot, user_id):
        await query.message.reply_text(
            f"❌ اول عضو کانال شو:\n{CHANNEL_USERNAME}\n\nبعد دوباره تلاش کن."
        )
        return

    try:
        with open("config.txt", "r", encoding="utf-8") as f:
            config = f.read().strip()

        await query.message.reply_text(f"✅ کانفیگت 👇\n\n`{config}`", parse_mode="Markdown")
    except Exception as e:
        await query.message.reply_text("⚠️ خطا در خواندن کانفیگ")
        print("CONFIG ERROR:", e)

if __name__ == "__main__":
    print("STARTING BOT...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("BOT IS RUNNING")
    app.run_polling()

    input("PRESS ENTER TO EXIT")
