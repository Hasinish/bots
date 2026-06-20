import os
import re
import httpx
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

# Load configuration from .env file
load_dotenv()
TOKEN = os.getenv("TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Import database module and language functions
from database import init_db, set_user_language, get_user_language, insert_lead, get_all_leads

# Import and initialize Groq client
from groq import Groq
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Define conversation states for registration
WAITING_NAME, WAITING_EMAIL, WAITING_PHONE, WAITING_NEEDS = range(4)

# Localized strings for English, Spanish, and Bengali
STRINGS = {
    'en': {
        'welcome': "Hey {name}! Welcome to Hasin's Business Bot.\n\nClick the buttons below to see options or change language:",
        'btn_menu': "Open Menu 📋",
        'btn_lang': "Change Language 🌐",
        'menu_text': "Here are the services Hasin Ishrak offers:\n\n🤖 Custom Telegram Bots\n💻 Full-Stack Web Development\n🧠 AI Agent Integrations\n\nTo register your project details and get a quote, type /register",
        'choose_lang': "Please choose your preferred language:",
        'lang_set': "Language set to English! 👍",
        'ask_name': "Let's get some details about your project so Hasin can give you a quote.\n\nTo start, what is your full name?\n(Type /cancel at any time to quit)",
        'ask_email': "Nice to meet you, {name}!\n\nNow, what is your email address?",
        'invalid_email': "That doesn't look like a valid email. Please try again:\n(Or type /cancel to quit)",
        'ask_phone': "Got it! Next, what is your phone number?",
        'invalid_phone': "That doesn't look like a valid phone number. Please try again:\n(Or type /cancel to quit)",
        'ask_needs': "Awesome. Finally, please describe your project needs in a few sentences:\n(What do you want the bot to do?)",
        'success': "Thank you, {name}! We have collected your information:\n\n📧 Email: {email}\n📞 Phone: {phone}\n📋 Needs: {needs}\n\nHasin will review this and get back to you shortly!",
        'cancel': "Lead registration cancelled. If you change your mind, type /register again!",
        'auth_denied': "Unauthorized. You are not allowed to use this command."
    },
    'es': {
        'welcome': "¡Hola, {name}! Bienvenido al Bot de Negocios de Hasin.\n\nHaz clic en los botones de abajo para ver las opciones o cambiar de idioma:",
        'btn_menu': "Abrir Menú 📋",
        'btn_lang': "Cambiar Idioma 🌐",
        'menu_text': "Aquí están los servicios que ofrece Hasin Ishrak:\n\n🤖 Bots de Telegram personalizados\n💻 Desarrollo web Full-Stack\n🧠 Integraciones de agentes de IA\n\nPara registrar los detalles de tu proyecto y obtener una cotización, escribe /register",
        'choose_lang': "Por favor, elige tu idioma de preferencia:",
        'lang_set': "¡Idioma configurado en Español! 👍",
        'ask_name': "Vamos a recopilar algunos detalles sobre tu proyecto para que Hasin pueda darte una cotización.\n\nPara empezar, ¿cuál es tu nombre completo?\n(Escribe /cancel en cualquier momento para salir)",
        'ask_email': "¡Mucho gusto, {name}!\n\nAhora, ¿cuál es tu dirección de correo electrónico?",
        'invalid_email': "Eso no parece un correo electrónico válido. Inténtalo de nuevo:\n(O escribe /cancel para salir)",
        'ask_phone': "¡Entendido! A continuación, ¿cuál es tu número de teléfono?",
        'invalid_phone': "Eso no parece un número de teléfono válido. Inténtalo de nuevo:\n(O escribe /cancel para salir)",
        'ask_needs': "Excelente. Finalmente, describe las necesidades de tu proyecto en unas pocas frases:\n(¿Qué quieres que haga el bot?)",
        'success': "¡Gracias, {name}! Hemos recopilado tu información:\n\n📧 Correo: {email}\n📞 Teléfono: {phone}\n📋 Necesidades: {needs}\n\n¡Hasin revisará esto y se pondrá en contacto contigo pronto!",
        'cancel': "Registro de prospecto cancelado. Si cambias de opinión, ¡escribe /register de nuevo!",
        'auth_denied': "No autorizado. No tienes permiso para usar este comando."
    },
    'bn': {
        'welcome': "হে {name}! হাসিনের বিজনেস বটের পক্ষ থেকে স্বাগতম।\n\nঅপশন দেখতে বা ভাষা পরিবর্তন করতে নিচের বোতামগুলোতে ক্লিক করুন:",
        'btn_menu': "মেনু খুলুন 📋",
        'btn_lang': "ভাষা পরিবর্তন করুন 🌐",
        'menu_text': "হাসিন ইশরাক যেসব সেবা প্রদান করেন:\n\n🤖 কাস্টম টেলিগ্রাম বট\n💻 ফুল-স্ট্যাক ওয়েব ডেভেলপমেন্ট\n🧠 এআই এজেন্ট ইন্টিগ্রেশন\n\nআপনার প্রজেক্টের বিবরণ রেজিস্টার করতে এবং একটি কোটেশন পেতে, /register টাইপ করুন",
        'choose_lang': "দয়া করে আপনার পছন্দসই ভাষা নির্বাচন করুন:",
        'lang_set': "ভাষা পরিবর্তন করে বাংলা করা হয়েছে! 👍",
        'ask_name': "চলুন আপনার প্রজেক্টের কিছু বিবরণ সংগ্রহ করি যাতে হাসিন আপনাকে একটি কোটেশন দিতে পারেন।\n\nশুরু করতে, আপনার সম্পূর্ণ নাম কী?\n(যেকোনো সময় বাতিল করতে /cancel টাইপ করুন)",
        'ask_email': "আপনার সাথে পরিচিত হয়ে ভালো লাগলো, {name}!\n\nএখন, আপনার ইমেল ঠিকানাটি কী?",
        'invalid_email': "এটি একটি সঠিক ইমেল বলে মনে হচ্ছে না। অনুগ্রহ করে আবার চেষ্টা করুন:\n(অথবা বাতিল করতে /cancel টাইপ করুন)",
        'ask_phone': "বুঝেছি! এরপর, আপনার ফোন নম্বরটি কী?",
        'invalid_phone': "এটি একটি সঠিক ফোন নম্বর বলে মনে হচ্ছে না। অনুগ্রহ করে আবার চেষ্টা করুন:\n(অথবা বাতিল করতে /cancel টাইপ করুন)",
        'ask_needs': "দারুণ। অবশেষে, আপনার প্রজেক্টের প্রয়োজনীয়তা সংক্ষেপে বর্ণনা করুন:\n(বটটি ঠিক কী কাজ করবে?)",
        'success': "ধন্যবাদ, {name}! আমরা আপনার তথ্য সংগ্রহ করেছি:\n\n📧 ইমেল: {email}\n📞 ফোন: {phone}\n📋 প্রয়োজনীয়তা: {needs}\n\nহাসিন শীঘ্রই এটি পর্যালোচনা করে আপনার সাথে যোগাযোগ করবেন!",
        'cancel': "রেজিস্ট্রেশন বাতিল করা হয়েছে। যদি মত পরিবর্তন করেন, আবার /register টাইপ করুন!",
        'auth_denied': "অননুমোদিত। এই কমান্ডটি ব্যবহার করার অনুমতি আপনার নেই।"
    }
}

async def send_webhook_lead(name: str, email: str, phone: str, needs: str, language: str) -> bool:
    """Sends lead details to the configured n8n Webhook URL."""
    if not WEBHOOK_URL:
        print("Webhook URL is not configured.")
        return False
        
    payload = {
        "event": "new_lead",
        "name": name,
        "email": email,
        "phone": phone,
        "needs": needs,
        "language": language
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(WEBHOOK_URL, json=payload, timeout=10.0)
            if response.status_code in [200, 201, 202]:
                print("Lead data sent to webhook successfully!")
                return True
            else:
                print(f"Webhook failed with status code {response.status_code}")
                return False
    except Exception as e:
        print(f"Error sending webhook: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    user_name = update.effective_user.first_name
    chat_id = update.effective_chat.id
    lang = get_user_language(chat_id)
    
    keyboard = [
        [InlineKeyboardButton(STRINGS[lang]['btn_menu'], callback_data="show_menu")],
        [InlineKeyboardButton(STRINGS[lang]['btn_lang'], callback_data="change_lang")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        STRINGS[lang]['welcome'].format(name=user_name),
        reply_markup=reply_markup
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for inline button clicks (CallbackQueries)."""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    lang = get_user_language(chat_id)
    
    if query.data == "show_menu":
        await query.edit_message_text(STRINGS[lang]['menu_text'])
    elif query.data == "change_lang":
        keyboard = [
            [
                InlineKeyboardButton("English 🇬🇧", callback_data="set_lang_en"),
                InlineKeyboardButton("Español 🇪🇸", callback_data="set_lang_es")
            ],
            [
                InlineKeyboardButton("বাংলা 🇧🇩", callback_data="set_lang_bn")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            STRINGS[lang]['choose_lang'],
            reply_markup=reply_markup
        )
    elif query.data.startswith("set_lang_"):
        new_lang = query.data.split("_")[-1]
        set_user_language(chat_id, new_lang)
        
        confirm_text = STRINGS[new_lang]['lang_set']
        
        keyboard = [
            [InlineKeyboardButton(STRINGS[new_lang]['btn_menu'], callback_data="show_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(confirm_text, reply_markup=reply_markup)

# --- LEAD COLLECTION CONVERSATION ---

async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for lead collection: asks for user's name."""
    lang = get_user_language(update.effective_chat.id)
    await update.message.reply_text(STRINGS[lang]['ask_name'])
    return WAITING_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the name and asks for email."""
    context.user_data["lead_name"] = update.message.text
    lang = get_user_language(update.effective_chat.id)
    await update.message.reply_text(
        STRINGS[lang]['ask_email'].format(name=context.user_data["lead_name"])
    )
    return WAITING_EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validates the email and asks for phone number."""
    email = update.message.text.strip()
    lang = get_user_language(update.effective_chat.id)
    
    # Simple regex validation
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        await update.message.reply_text(STRINGS[lang]['invalid_email'])
        return WAITING_EMAIL
        
    context.user_data["lead_email"] = email
    await update.message.reply_text(STRINGS[lang]['ask_phone'])
    return WAITING_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validates phone number and asks for project needs."""
    phone = update.message.text.strip()
    lang = get_user_language(update.effective_chat.id)
    
    # Validate phone number format (loose check: 7-20 chars)
    if not re.match(r"^\+?[0-9\s\-\(\)]{7,20}$", phone):
        await update.message.reply_text(STRINGS[lang]['invalid_phone'])
        return WAITING_PHONE
        
    context.user_data["lead_phone"] = phone
    await update.message.reply_text(STRINGS[lang]['ask_needs'])
    return WAITING_NEEDS

async def get_needs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores project needs, saves to DB, alerts admin, and finishes."""
    context.user_data["lead_needs"] = update.message.text.strip()
    chat_id = update.effective_chat.id
    lang = get_user_language(chat_id)
    
    name = context.user_data["lead_name"]
    email = context.user_data["lead_email"]
    phone = context.user_data["lead_phone"]
    needs = context.user_data["lead_needs"]
    
    # 1. Save the lead details to SQLite database
    try:
        lead_id = insert_lead(name, email, phone, needs, lang)
    except Exception as e:
        print(f"Error saving lead to database: {e}")
        lead_id = "Error (Not Saved)"

    # 2. Trigger webhook POST asynchronously (non-blocking)
    context.application.create_task(send_webhook_lead(name, email, phone, needs, lang))

    # 3. Inform the user registration succeeded
    await update.message.reply_text(
        STRINGS[lang]['success'].format(name=name, email=email, phone=phone, needs=needs)
    )
    
    # 3. Send instant notification to the admin/owner (Hasin)
    if ADMIN_CHAT_ID:
        try:
            admin_alert = (
                f"🚨 NEW LEAD COLLECTED! 🚨\n\n"
                f"👤 Name: {name}\n"
                f"📧 Email: {email}\n"
                f"📞 Phone: {phone}\n"
                f"🌐 Lang: {lang}\n"
                f"📋 Needs: {needs}\n\n"
                f"Database Row ID: {lead_id}"
            )
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_alert)
        except Exception as e:
            print(f"Error sending admin notification: {e}")
            
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    lang = get_user_language(update.effective_chat.id)
    await update.message.reply_text(STRINGS[lang]['cancel'])
    return ConversationHandler.END

async def admin_leads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command `/leads` to view all collected leads."""
    chat_id = str(update.effective_chat.id)
    if not ADMIN_CHAT_ID or chat_id != str(ADMIN_CHAT_ID):
        lang = get_user_language(update.effective_chat.id)
        await update.message.reply_text(STRINGS[lang]['auth_denied'])
        return
        
    leads = get_all_leads()
    if not leads:
        await update.message.reply_text("No leads collected yet. 📋")
        return
        
    report = "📋 **COLLECTED LEADS REPORT** 📋\n\n"
    for lead in leads:
        # id, name, email, phone, needs, language, created_at
        lead_id, name, email, phone, needs, lang, created_at = lead
        report += (
            f"🔹 **Lead #{lead_id}**\n"
            f"👤 Name: {name}\n"
            f"📧 Email: {email}\n"
            f"📞 Phone: {phone}\n"
            f"🌐 Lang: {lang}\n"
            f"📋 Needs: {needs}\n"
            f"📅 Date: {created_at}\n\n"
        )
        
    if len(report) > 4000:
        chunks = [report[i:i+4000] for i in range(0, len(report), 4000)]
        for chunk in chunks:
            await update.message.reply_text(chunk, parse_mode="Markdown")
    else:
        await update.message.reply_text(report, parse_mode="Markdown")

async def get_ai_reply(prompt: str, language: str) -> str:
    """Queries Groq with the system prompt and the user's message, instructing it on language."""
    if not groq_client:
        return "AI is not configured. Please set GROQ_API_KEY in .env!"
        
    system_instruction = "You are a helpful business assistant."
    base_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(base_dir, "system_prompt.txt")
    
    if os.path.exists(prompt_path):
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_instruction = f.read()
                
            lang_names = {'en': 'English', 'es': 'Spanish', 'bn': 'Bengali'}
            lang_name = lang_names.get(language, 'English')
            system_instruction = system_instruction.replace("{LANGUAGE}", lang_name)
        except Exception as e:
            print(f"Warning: Could not read system_prompt.txt: {e}")
            
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fallback handler that routes user messages to Groq AI."""
    user_text = update.message.text
    chat_id = update.effective_chat.id
    lang = get_user_language(chat_id)
    
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    reply = await get_ai_reply(user_text, lang)
    await update.message.reply_text(reply)

if __name__ == "__main__":
    if not TOKEN:
        print("Error: TOKEN not found in environment variables!")
        exit(1)
        
    print("Starting basic bot skeleton (Premium)...")
    
    # Initialize database
    init_db()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leads", admin_leads))
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Run the bot
    app.run_polling()


