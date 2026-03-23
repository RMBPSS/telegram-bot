from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, CallbackQueryHandler
)
import os

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TOKEN")   # IMPORTANT for Render
ADMIN_ID = 7749940784

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =========================
# USER STORAGE
# =========================
users = set()

# =========================
# PROJECTS
# =========================
PROJECTS = {
    "agriculture": {
        "name": "Agriculture Business Project",
        "price": "300 ETB",
        "file": os.path.join(BASE_DIR, "files", "agriculture.pdf"),
        "preview": os.path.join(BASE_DIR, "files", "agriculture_preview.pdf")
    },
    "software": {
        "name": "Software Project Proposal",
        "price": "250 ETB",
        "file": os.path.join(BASE_DIR, "files", "software.pdf"),
        "preview": os.path.join(BASE_DIR, "files", "software_preview.pdf")
    }
}

# =========================
# MAIN MENU
# =========================
def main_menu():
    keyboard = [
        ["📂 Projects", "💳 Buy"],
        ["📤 Order"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    users.add(user_id)

    await update.message.reply_text(
        "👋 Welcome to RMBPSS Bot!\n\nChoose an option 👇",
        reply_markup=main_menu()
    )

# =========================
# MENU HANDLER
# =========================
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📂 Projects":
        await show_projects(update, context)
    elif text == "💳 Buy":
        await buy(update, context)
    elif text == "📤 Order":
        await order(update, context)

# =========================
# SHOW PROJECTS
# =========================
async def show_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []

    for key, project in PROJECTS.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{project['name']} ({project['price']})",
                callback_data=f"view_{key}"
            )
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📂 Available Projects:\nSelect one 👇",
        reply_markup=reply_markup
    )

# =========================
# VIEW PROJECT (PREVIEW)
# =========================
async def view_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    key = query.data.split("_")[1]
    project = PROJECTS[key]

    context.user_data["selected_project"] = key

    try:
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=open(project["preview"], "rb"),
            caption=f"""
🎓 {project['name']}

✨ What you get:
✔ Complete project proposal
✔ Ready to submit
✔ Editable format
✔ High quality content

💰 Price: {project['price']}

👉 After payment click 📤 Order
"""
        )
    except FileNotFoundError:
        await query.message.reply_text("❌ Preview file not found.")

# =========================
# BUY INFO
# =========================
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💳 Payment Methods:\n\n"
        "Telebirr: 09XXXXXXXX\n"
        "CBE Bank: 1000XXXXXX\n\n"
        "After payment → click 📤 Order"
    )

# =========================
# ORDER
# =========================
async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("selected_project"):
        await update.message.reply_text("❌ Please select a project first using 📂 Projects")
        return

    await update.message.reply_text("📤 Send your payment receipt now.")

# =========================
# HANDLE RECEIPT
# =========================
async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    project_key = context.user_data.get("selected_project")

    if not project_key:
        await update.message.reply_text("❌ Please select a project first")
        return

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}_{project_key}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}_{project_key}")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📥 New Order\n\nUser: @{user.username}\nUser ID: {user.id}\nProject: {project_key}",
        reply_markup=reply_markup
    )

    await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=update.message.chat_id,
        message_id=update.message.message_id
    )

    await update.message.reply_text("✅ Receipt sent. Wait for approval.")

# =========================
# APPROVE / REJECT
# =========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    action = data[0]
    user_id = int(data[1])
    project_key = data[2]

    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("❌ Not admin")
        return

    project = PROJECTS[project_key]

    if action == "approve":
        try:
            await context.bot.send_document(
                chat_id=user_id,
                document=open(project["file"], "rb"),
                caption=f"✅ Approved!\nHere is your {project['name']}"
            )
            await query.edit_message_text("✅ Approved and file sent!")
        except FileNotFoundError:
            await query.edit_message_text("❌ File not found!")

    elif action == "reject":
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Payment not approved."
        )
        await query.edit_message_text("❌ Rejected")

# =========================
# BROADCAST (BONUS)
# =========================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("❌ Usage: /broadcast your message")
        return

    message = " ".join(context.args)

    count = 0
    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
            count += 1
        except:
            pass

    await update.message.reply_text(f"✅ Sent to {count} users")

# =========================
# MAIN
# =========================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("broadcast", broadcast))

app.add_handler(CallbackQueryHandler(view_project, pattern="^view_"))
app.add_handler(CallbackQueryHandler(button_handler, pattern="^(approve|reject)_"))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_receipt))

print("🤖 Bot running...")
app.run_polling()