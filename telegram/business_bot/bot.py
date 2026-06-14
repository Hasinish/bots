import os
import re
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler
)

# Load configuration
load_dotenv()
TOKEN = os.getenv("TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Import SQLite database functions
from database import insert_lead, init_db

# Import and initialize Groq client
from groq import Groq
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Define conversation states
WAITING_NAME, WAITING_EMAIL, WAITING_PHONE, WAITING_NEEDS = range(4)

async def get_ai_reply(prompt: str) -> str:
    """Queries Groq with the system prompt and the user's message."""
    if not groq_client:
        return "AI is not configured. Please set GROQ_API_KEY in .env!"
        
    # 1. Read system prompt instructions from file dynamically
    system_instruction = "You are a helpful business assistant."
    base_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(base_dir, "system_prompt.txt")
    
    if os.path.exists(prompt_path):
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_instruction = f.read()
        except Exception as e:
            print(f"Warning: Could not read system_prompt.txt: {e}")
            
    # 2. Call the Groq Chat Completion API
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant"
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error querying Groq API: {e}")
        return "Sorry, I encountered an error while processing that."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    user_name = update.effective_user.first_name
    
    # Create an inline button to open the main menu
    keyboard = [
        [InlineKeyboardButton("Open Menu 📋", callback_data="show_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Hey {user_name}! Welcome to Hasin's Business Bot.\n\n"
        "Click the button below to see what services are available:",
        reply_markup=reply_markup
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for inline button clicks (CallbackQueries)."""
    query = update.callback_query
    await query.answer()  # Tell Telegram we received the click
    
    if query.data == "show_menu":
        await query.edit_message_text(
            "Here are the services Hasin Ishrak offers:\n\n"
            "🤖 Custom Telegram Bots\n"
            "💻 Full-Stack Web Development\n"
            "🧠 AI Agent Integrations\n\n"
            "To register your project details and get a quote, type /register"
        )

# --- LEAD COLLECTION CONVERSATION ---

async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for lead collection: asks for user's name."""
    await update.message.reply_text(
        "Let's get some details about your project so Hasin can give you a quote.\n\n"
        "To start, what is your full name?\n"
        "(Type /cancel at any time to quit)"
    )
    return WAITING_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the name and asks for email."""
    context.user_data["lead_name"] = update.message.text
    await update.message.reply_text(
        f"Nice to meet you, {context.user_data['lead_name']}!\n\n"
        "Now, what is your email address?"
    )
    return WAITING_EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validates the email and asks for phone number."""
    email = update.message.text.strip()
    
    # Simple regex validation
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        await update.message.reply_text(
            "That doesn't look like a valid email. Please try again:\n"
            "(Or type /cancel to quit)"
        )
        return WAITING_EMAIL
        
    context.user_data["lead_email"] = email
    await update.message.reply_text(
        "Got it! Next, what is your phone number?"
    )
    return WAITING_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validates phone number and asks for project needs."""
    phone = update.message.text.strip()
    
    # Validate phone number format (loose check: 7-20 chars, optional +, digits, spaces, hyphens, parens)
    if not re.match(r"^\+?[0-9\s\-\(\)]{7,20}$", phone):
        await update.message.reply_text(
            "That doesn't look like a valid phone number. Please try again:\n"
            "(Or type /cancel to quit)"
        )
        return WAITING_PHONE
        
    context.user_data["lead_phone"] = phone
    await update.message.reply_text(
        "Awesome. Finally, please describe your project needs in a few sentences:\n"
        "(What do you want the bot to do?)"
    )
    return WAITING_NEEDS

async def get_needs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores project needs, saves to DB, alerts admin, and finishes the conversation."""
    context.user_data["lead_needs"] = update.message.text.strip()
    
    name = context.user_data["lead_name"]
    email = context.user_data["lead_email"]
    phone = context.user_data["lead_phone"]
    needs = context.user_data["lead_needs"]
    
    # 1. Save the lead details to SQLite database
    try:
        lead_id = insert_lead(name, email, phone, needs)
    except Exception as e:
        print(f"Error saving lead to database: {e}")
        lead_id = "Error (Not Saved)"

    # 2. Inform the user registration succeeded
    await update.message.reply_text(
        f"Thank you, {name}! We have collected your information:\n\n"
        f"📧 Email: {email}\n"
        f"📞 Phone: {phone}\n"
        f"📋 Needs: {needs}\n\n"
        "Hasin will review this and get back to you shortly!"
    )
    
    # 3. Send instant notification to the admin/owner (Hasin)
    if ADMIN_CHAT_ID:
        try:
            admin_alert = (
                f"🚨 NEW LEAD COLLECTED! 🚨\n\n"
                f"👤 Name: {name}\n"
                f"📧 Email: {email}\n"
                f"📞 Phone: {phone}\n"
                f"📋 Needs: {needs}\n\n"
                f"Database Row ID: {lead_id}"
            )
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_alert)
        except Exception as e:
            print(f"Error sending admin notification: {e}")
            
    return ConversationHandler.END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fallback handler that routes user messages to Groq AI."""
    user_text = update.message.text
    
    # Trigger a 'typing' indicator so the user knows the bot is thinking
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Get reply from Groq
    reply = await get_ai_reply(user_text)
    
    # Send response back to the user
    await update.message.reply_text(reply)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text(
        "Lead registration cancelled. If you change your mind, type /register again!"
    )
    return ConversationHandler.END

if __name__ == "__main__":
    if not TOKEN:
        print("Error: TOKEN not found in environment variables!")
        exit(1)
        
    print("Starting Telegram bot skeleton...")
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Initialize SQLite database table
    init_db()
    
    # Register command and button handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button))
    
    # Register lead collection conversation flow
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            WAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            WAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            WAITING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            WAITING_NEEDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_needs)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv_handler)
    
    # Register fallback message handler for AI replies
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()
