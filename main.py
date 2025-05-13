import asyncio
from telethon import TelegramClient, events
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, ContextTypes, filters

# --- Constants ---
API_ID, API_HASH, SNIPER_BOT, CHANNELS = range(4)
user_data_store = {}

# --- Telegram Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Set API ID", callback_data="set_api_id")],
        [InlineKeyboardButton("Set API Hash", callback_data="set_api_hash")],
        [InlineKeyboardButton("Set Target Bot", callback_data="set_sniper_bot")],
        [InlineKeyboardButton("Set Channels", callback_data="set_channels")],
        [InlineKeyboardButton("Start Sniping", callback_data="start_sniping")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to the Channel Sniper Bot!\n\n"
        "Set your API credentials, target bot, and channels to start forwarding messages.\n\n"
        "Made by @yyeir",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    await query.edit_message_text(f"Please send your {choice.replace('_', ' ').title()}:")
    context.user_data['awaiting'] = choice

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    key = context.user_data.get('awaiting')
    if not key:
        return

    value = update.message.text
    if user_id not in user_data_store:
        user_data_store[user_id] = {}

    if key == "set_channels":
        user_data_store[user_id][key] = value.split()
    else:
        user_data_store[user_id][key] = value

    await update.message.reply_text(f"{key.replace('_', ' ').title()} set successfully.")
    context.user_data['awaiting'] = None
    print(f"User {user_id} updated {key}: {value}")

async def start_sniping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = user_data_store.get(user_id)

    if not data or not all(k in data for k in ("set_api_id", "set_api_hash", "set_sniper_bot", "set_channels")):
        await query.edit_message_text("Please set all required information first.")
        return

    await query.edit_message_text("Sniper bot is starting...")
    asyncio.create_task(run_sniper(user_id, data))

async def run_sniper(user_id, data):
    api_id = int(data['set_api_id'])
    api_hash = data['set_api_hash']
    sniper_bot = data['set_sniper_bot']
    channels = data['set_channels']

    client = TelegramClient(f"session_{user_id}", api_id, api_hash)
    await client.start()

    @client.on(events.NewMessage(chats=channels))
    async def forward(event):
        if event.message:
            await client.send_message(sniper_bot, event.message)

    print(f"[User {user_id}] Sniper bot is running...")
    await client.run_until_disconnected()

# --- Main ---
if __name__ == "__main__":
    app = Application.builder().token("7788084298:AAENvKOA2P_5BFE9_QmenlNTtY5Zj2idqP4").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(set_api_id|set_api_hash|set_sniper_bot|set_channels)$"))
    app.add_handler(CallbackQueryHandler(start_sniping, pattern="^start_sniping$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("Bot is running...")
    app.run_polling()
