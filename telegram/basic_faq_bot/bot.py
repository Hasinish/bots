import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize the Groq client
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here" else None

async def get_ai_reply(prompt: str) -> str:
    if not groq_client:
        return "AI is not configured. Please set GROQ_API_KEY in .env!"
    
    # 1. Load system prompt from file dynamically (relative to this script's directory)
    system_instruction = "You are a helpful business assistant."
    base_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(base_dir, "system_prompt.txt")
    
    if os.path.exists(prompt_path):
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_instruction = f.read()
        except Exception as e:
            print(f"Warning: Could not read system_prompt.txt: {e}")
            
    # 2. Query Groq with loaded instructions safely
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
        return f"Sorry, I encountered an error while generating a response. Details: {str(e)}"


# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hello {user_name}! I am your Business Assistant.\n\n"
        "Ask me anything, or type /help to see what I can do."
    )

# /help command handler
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Start the conversation\n"
        "/help - Show this help message\n\n"
        "Or simply type any question, and I will answer it!"
    )

# Route incoming user messages to the AI reply function
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # 1. Ask the AI for a reply
    reply = await get_ai_reply(user_text)
    
    # 2. Reply to the Telegram user with the AI response
    await update.message.reply_text(reply)


# Main execution block
if __name__ == "__main__":
    if not TOKEN or TOKEN == "your_telegram_bot_token_here":
        print("ERROR: Please set a valid TOKEN in your .env file!")
        exit(1)

    print("Starting bot...")
    app = ApplicationBuilder().token(TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run polling loop
    app.run_polling()
