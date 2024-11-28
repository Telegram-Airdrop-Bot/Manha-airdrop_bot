import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from pymongo import MongoClient

# Load environment variables
API_TOKEN =("7570326283:AAE1Eg_zDJTVy8og1mRq7ADlGUVjCoXtSgY")
MONGO_URI = os.getenv("MONGO_URI")

# Database Setup
client = MongoClient(MONGO_URI)
db = client["airdrop_bot"]
users = db["users"]

# Pause Bot Flag
PAUSED = False

# Replace with actual admin username
ADMIN_USERNAME = "https://t.me/mushfiqmoon"

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not users.find_one({"user_id": user.id}):
        users.insert_one({
            "user_id": user.id,
            "username": user.username or "unknown",
            "wallet": None,
            "tasks_completed": False,
            "balance": 0,
            "referrals": [],
            "joined": False
        })

    await update.message.reply_text(
        "Welcome to the Airdrop Bot!\n\n"
        "👉 Join our [Telegram Channel](https://t.me/successcrypto2)\n"
        "👉 Join our [Telegram Group](https://t.me/successcryptoboss)\n\n"
        "Once done, click the button below to verify.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Verify Joined", callback_data="check_joined")]
        ])
    )

# Verify Join
async def check_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user

    channel_id = "@successcryptoboss"
    group_id = "@successcrypto2"

    try:
        channel_status = await context.bot.get_chat_member(chat_id=channel_id, user_id=user.id)
        group_status = await context.bot.get_chat_member(chat_id=group_id, user_id=user.id)

        if channel_status.status in ["member", "administrator"] and group_status.status in ["member", "administrator"]:
            users.update_one({"user_id": user.id}, {"$set": {"joined": True}})
            await query.edit_message_text("You’ve been verified! Let’s proceed to the tasks.")
            await send_tasklist(query)
        else:
            await query.edit_message_text("Please join both the channel and group first!")
    except Exception as e:
        await query.edit_message_text("❌ An error occurred while checking your membership.")

# Send Tasklist
async def send_tasklist(query):
    await query.message.reply_text(
        "🔹 Complete the following tasks:\n"
        "1️⃣ Subscribe to [YouTube](https://www.youtube.com/@BDMusicfest)\n"
        "2️⃣ Like and share on [Facebook](https://www.facebook.com/Risingsportsbd02)\n"
        "3️⃣ Retweet our [Twitter](https://twitter.com/your_twitter)\n\n"
        "Reply with your BEP-20 Wallet Address to continue.",
        parse_mode="Markdown"
    )

# Wallet Address Collection
async def wallet_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    wallet = update.message.text.strip()

    if len(wallet) < 20:  # Basic validation
        await update.message.reply_text("❌ Invalid wallet address. Please try again.")
    else:
        users.update_one({"user_id": user.id}, {"$set": {"wallet": wallet}})
        await update.message.reply_text(
            "✅ Wallet address saved! Did you complete all the tasks?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Yes, I completed", callback_data="tasks_done")]
            ])
        )

# Task Completion
async def tasks_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user

    users.update_one({"user_id": user.id}, {"$set": {"tasks_completed": True}})
    referral_link = f"https://t.me/{context.bot.username}?start={user.id}"

    await query.edit_message_text(
        f"🎉 Tasks verified! Here's your referral link:\n{referral_link}\n\n"
        "Invite friends to earn more rewards!"
    )

# Bonus Feature
async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users.update_one({"user_id": user.id}, {"$inc": {"balance": 10}})
    await update.message.reply_text("🎁 You’ve received a 10 token bonus! 💰")

# Withdraw Feature
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = users.find_one({"user_id": user.id})

    if user_data and user_data["balance"] >= 50:  # Minimum withdraw threshold
        await update.message.reply_text("✅ Withdrawal request received. Processing soon!")
        users.update_one({"user_id": user.id}, {"$set": {"balance": 0}})
    else:
        balance = user_data["balance"] if user_data else 0
        await update.message.reply_text(f"❌ Insufficient balance. Minimum 50 tokens required. Current: {balance}.")

# Admin Broadcast
async def admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username == ADMIN_USERNAME:
        message = update.message.text.split("/admin ", 1)[1]
        for user in users.find():
            await context.bot.send_message(chat_id=user["user_id"], text=message)

# View Stats
async def view_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username == ADMIN_USERNAME:
        total_users = users.count_documents({})
        tasks_completed = users.count_documents({"tasks_completed": True})
        await update.message.reply_text(
            f"📊 Bot Stats:\n\n"
            f"Total Users: {total_users}\n"
            f"Tasks Completed: {tasks_completed}\n"
        )

# Pause/Unpause Bot
async def toggle_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global PAUSED
    if update.effective_user.username == ADMIN_USERNAME:
        PAUSED = not PAUSED
        status = "paused" if PAUSED else "active"
        await update.message.reply_text(f"Bot is now {status}.")

# Middleware for Pause Check
async def check_paused(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PAUSED:
        await update.message.reply_text("🚫 The bot is currently paused. Please try again later.")
        return False
    return True

# Main Function
def main():
    app = Application.builder().token(API_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_joined, pattern="check_joined"))
    app.add_handler(CallbackQueryHandler(tasks_done, pattern="tasks_done"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wallet_address))
    app.add_handler(CommandHandler("bonus", bonus))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("admin", admin_message))
    app.add_handler(CommandHandler("stats", view_stats))
    app.add_handler(CommandHandler("toggle", toggle_bot))

    # Middleware
    app.add_handler(MessageHandler(filters.ALL, check_paused))

    # Drop pending updates to prevent conflicts
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
