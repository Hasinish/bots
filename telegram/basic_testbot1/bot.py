import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, ConversationHandler


load_dotenv()
WAITING_NAME, WAITING_EMAIL = range(2)


TOKEN = os.getenv("TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.effective_user.first_name
    

    keyboard = [["hello!", "help!"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"Hey {context.user_data['name']}! Choose and option from bottom:", reply_markup=reply_markup)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I can help you!\nAvailable Commands:\n/help\n/start")


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = context.user_data.get("name", "stranger")
    await update.message.reply_text(f"Hey there {name}!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() == "hi" or update.message.text.lower() == "hello!":
        await update.message.reply_text("Hey!")
    elif update.message.text.lower() == "bye":
        await update.message.reply_text("Goodbye!")
    elif update.message.text.lower() == "help!":
        await help(update, context)
    else:
        await update.message.reply_text("I don't understand")


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("About", callback_data="about")],
                [InlineKeyboardButton("Contact", callback_data="contact")],
                [InlineKeyboardButton("Creator", callback_data="creator")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose an option", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "about":
        await query.edit_message_text("I am a Telegram bot built with Python!")
    elif query.data == "contact":
        await query.edit_message_text("hasin@gmail.com")
    elif query.data == "creator":
        await query.edit_message_text("Hasin 😈")
        
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('''I am Hasin's bot!
Built with Python and python-telegram-bot library.
Version: 1.0''')


async def collect(update, context):
    await update.message.reply_text("What's your name?")
    return WAITING_NAME

async def get_name(update, context):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("What's your email?")
    return WAITING_EMAIL

async def get_email(update, context):
    name = context.user_data["name"]
    email = update.message.text
    await update.message.reply_text(f"Thanks {name}! Got your email: {email}")
    return ConversationHandler.END

async def cancel(update, context):
    await update.message.reply_text("Cancelled!")
    return ConversationHandler.END






app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))
app.add_handler(CommandHandler("about", about))
app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("menu", menu))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(ConversationHandler(entry_points=[CommandHandler("collect", collect)],
                                    states={
                                        WAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
                                        WAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)]

                                    },
                                    fallbacks=[CommandHandler("cancel", cancel)]))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
app.run_polling()

