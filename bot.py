import os
import random
import datetime
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ================== НАСТРОЙКИ ==================
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
ALLOWED_CHAT = os.getenv("ALLOWED_CHAT")
PORT = int(os.getenv("PORT", 5000))

# Flask-приложение
flask_app = Flask(__name__)

# Telegram-приложение
application = Application.builder().token(TOKEN).build()

# ================== ДАННЫЕ ==================
# Промокоды
promo_codes = {
    "FREE777": {"uses": 5, "expires": "2025-09-10", "users": []},
    "WELCOME": {"uses": 10, "expires": "2025-09-30", "users": []}
}

# Таблица значений (1–64)
slot_table = {
    1: "🍷🍷🍷", 2: "🍒🍷🍷", 3: "🍋🍷🍷", 4: "7️⃣🍷🍷",
    5: "🍷🍒🍷", 6: "🍒🍒🍷", 7: "🍋🍒🍷", 8: "7️⃣🍒🍷",
    9: "🍷🍋🍷", 10: "🍒🍋🍷", 11: "🍋🍋🍷", 12: "7️⃣🍋🍷",
    13: "🍷7️⃣🍷", 14: "🍒7️⃣🍷", 15: "🍋7️⃣🍷", 16: "7️⃣7️⃣🍷",
    17: "🍷🍷🍒", 18: "🍒🍷🍒", 19: "🍋🍷🍒", 20: "🍒7️⃣🍒",
    21: "🍷🍒🍒", 22: "🍒🍒🍒", 23: "🍋🍒🍒", 24: "7️⃣🍒🍒",
    25: "🍷🍋🍒", 26: "🍒🍋🍒", 27: "🍋🍋🍒", 28: "7️⃣🍋🍒",
    29: "🍷7️⃣🍒", 30: "🍒7️⃣🍒", 31: "🍋7️⃣🍒", 32: "7️⃣7️⃣🍒",
    33: "🍷🍷🍋", 34: "🍒🍷🍋", 35: "🍋🍷🍋", 36: "7️⃣🍷🍋",
    37: "🍷🍒🍋", 38: "🍒🍒🍋", 39: "🍋🍒🍋", 40: "7️⃣🍒🍋",
    41: "🍷🍋🍋", 42: "🍒🍋🍋", 43: "🍋🍋🍋", 44: "7️⃣🍋🍋",
    45: "🍷7️⃣🍋", 46: "🍒7️⃣🍋", 47: "🍋7️⃣🍋", 48: "7️⃣7️⃣🍋",
    49: "🍷🍷7️⃣", 50: "🍒🍷7️⃣", 51: "🍋🍷7️⃣", 52: "7️⃣🍷7️⃣",
    53: "🍷🍒7️⃣", 54: "🍒🍒7️⃣", 55: "🍋🍒7️⃣", 56: "7️⃣🍒7️⃣",
    57: "🍷🍋7️⃣", 58: "🍒🍋7️⃣", 59: "🍋🍋7️⃣", 60: "7️⃣🍋7️⃣",
    61: "🍷7️⃣7️⃣", 62: "🍒7️⃣7️⃣", 63: "🍋7️⃣7️⃣", 64: "7️⃣7️⃣7️⃣"
}

# Фразы
jackpot_responses = [
    "🎉 Джекпот! Бог слот-машины улыбнулся!\n(ждите, админ свяжется с вами в течении 12 часов)",
    "🔥 Удача на твоей стороне, это три семёрки!\n(ждите, админ свяжется с вами в течении 12 часов)",
    "💰 Ты сорвал куш! Теперь можешь открывать казино.\n(ждите, админ свяжется с вами в течении 12 часов)",
    "🎰 777! Если бы это было в Вегасе — ты бы уже был миллионером.\n(ждите, админ свяжется с вами в течении 12 часов)"
]

medium_responses = [
    "🍋🍋🍋! Средний куш, забирай приз! 🤑\n(ждите, админ свяжется с вами в течении 12 часов)",
    "Лимончики сыграли! 🍋🍋🍋 — не джекпот, но приятно.\n(ждите, админ свяжется с вами в течении 12 часов)",
    "🍋🍋🍋 — кисленькая, но прибыльная комбинация.\n(ждите, админ свяжется с вами в течении 12 часов)"
]

small_responses = [
    "🍒🍒🍒! Маленький выигрыш, но начало есть! 🍒\n(ждите, админ свяжется с вами в течении 12 часов)",
    "Три вишенки 🍒🍒🍒 — держи утешительный приз.\n(ждите, админ свяжется с вами в течении 12 часов)",
    "🍒🍒🍒 — мелочь, а приятно.\n(ждите, админ свяжется с вами в течении 12 часов)"
]

lose_responses = [
    "❌ Не повезло... автомат смеётся.",
    "😅 Увы, сегодня без выигрыша.",
    "🙃 Почти! Но нет.",
    "🚬 Автомат съел монетку и молчит."
]

# ================== ФУНКЦИИ ==================
def check_group(update: Update) -> bool:
    chat = update.message.chat
    return chat.username == ALLOWED_CHAT

async def do_spin(update: Update, context: ContextTypes.DEFAULT_TYPE, mention: str, promo: bool = False):
    await asyncio.sleep(2)
    value = random.randint(1, 64) if promo else update.message.dice.value
    combo = slot_table.get(value, f"неизвестно ({value})")

    chat = update.message.chat
    msg_link = f"https://t.me/{chat.username}/{update.message.message_id}" if chat.username else "(группа приватная)"

    if combo == "7️⃣7️⃣7️⃣":
        reply = f"{mention} покрутил и выпало:\n {combo}\n{random.choice(jackpot_responses)}"
        await context.bot.send_message(ADMIN_ID, f"🔥 У {mention} ДЖЕКПОТ! 🎰 ({combo})\nСсылка: {msg_link}")
    elif combo == "🍋🍋🍋":
        reply = f"{mention} покрутил и выпало:\n {combo}\n{random.choice(medium_responses)}"
        await context.bot.send_message(ADMIN_ID, f"⚡ У {mention} средний выигрыш! 🍋🍋🍋 ({combo})\nСсылка: {msg_link}")
    elif combo == "🍒🍒🍒":
        reply = f"{mention} покрутил и выпало:\n {combo}\n{random.choice(small_responses)}"
        await context.bot.send_message(ADMIN_ID, f"🍒 У {mention} маленький выигрыш! 🍒🍒🍒 ({combo})\nСсылка: {msg_link}")
    else:
        reply = f"{mention} покрутил и выпало:\n {combo}\n{random.choice(lose_responses)}"

    await update.message.reply_text(reply)

# ===== команды и обработчики =====
async def promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_group(update):
        await update.message.reply_text("⚠️ Я работаю только в группе @dukasino_g")
        return
    if not context.args:
        await update.message.reply_text("❓ Использование: /promo КОД")
        return
    code = context.args[0].upper()
    user = update.message.from_user
    mention = f"@{user.username}" if user.username else user.first_name
    user_id = user.id
    if code not in promo_codes:
        await update.message.reply_text(f"❌ Промокод {code} не существует.")
        return
    promo_data = promo_codes[code]
    today = datetime.date.today()
    expiry = datetime.date.fromisoformat(promo_data["expires"])
    if today > expiry:
        await update.message.reply_text(f"⏳ Промокод {code} истёк ({promo_data['expires']}).")
        return
    if promo_data["uses"] <= 0:
        await update.message.reply_text(f"❌ Промокод {code} уже израсходован.")
        return
    if user_id in promo_data["users"]:
        await update.message.reply_text(f"⚠️ Ты уже использовал промокод {code}.")
        return
    promo_data["uses"] -= 1
    promo_data["users"].append(user_id)
    await update.message.reply_text(f"✅ Промокод {code} активирован! Бесплатный прокрут запускается...")
    await do_spin(update, context, mention, promo=True)

async def add_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if len(context.args) != 3:
        await update.message.reply_text("⚠ Использование: /addpromo КОД ЧИСЛО YYYY-MM-DD")
        return
    code, count, expiry = context.args
    if not count.isdigit():
        await update.message.reply_text("⚠ Число должно быть целым.")
        return
    try:
        datetime.date.fromisoformat(expiry)
    except ValueError:
        await update.message.reply_text("⚠ Неверный формат даты (YYYY-MM-DD).")
        return
    promo_codes[code.upper()] = {"uses": int(count), "expires": expiry, "users": []}
    await update.message.reply_text(f"✅ Промокод {code.upper()} добавлен: {count} использований, до {expiry}.")

async def list_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if not promo_codes:
        await update.message.reply_text("📭 Нет активных промокодов.")
        return
    text = "🎟 Активные промокоды:\n"
    for k, v in promo_codes.items():
        text += f"{k} → {v['uses']} использований, до {v['expires']}, {len(v['users'])} использовали\n"
    await update.message.reply_text(text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_group(update):
        await update.message.reply_text("⚠️ Я работаю только в группе @dukasino_g")
        return
    await update.message.reply_text("Привет! 🎰 Отправь 🎰 чтобы испытать удачу.\nА ещё можно активировать промокод: /promo КОД")

async def handle_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_group(update):
        await update.message.reply_text("⚠️ Я работаю только в группе @dukasino_g")
        return
    if update.message and update.message.dice:
        emoji = update.message.dice.emoji
        user = update.message.from_user
        mention = f"@{user.username}" if user.username else user.first_name
        if emoji == "🎰":
            await do_spin(update, context, mention, promo=False)
        else:
            await asyncio.sleep(2)
            await update.message.reply_text(f"{emoji} Выпало: {update.message.dice.value}")

# ================== WEBHOOK ==================
@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

async def set_webhook():
    url = os.getenv("RENDER_EXTERNAL_URL")
    webhook_url = f"{url}/{TOKEN}"
    await application.bot.set_webhook(webhook_url)
    print(f"Webhook установлен: {webhook_url}")

def main():
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("promo", promo))
    application.add_handler(CommandHandler("addpromo", add_promo))
    application.add_handler(CommandHandler("listpromo", list_promo))
    application.add_handler(MessageHandler(filters.Dice.ALL, handle_dice))
    asyncio.get_event_loop().run_until_complete(set_webhook())
    flask_app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()
