# Custom Telegram Business Bot (Lead Gen + AI FAQ)

A professional-grade Telegram Business Bot template built in Python. This bot helps businesses automate customer service, answer queries with AI, collect qualified leads, store them in a database, and send instant notification alerts to the owner.

## Key Features

1. **AI FAQ & Fallback**: Automatically answers customer questions using the **Groq SDK** (`llama-3.1-8b-instant`) under a dynamically loaded system prompt.
2. **Interactive Menus**: Sleek inline menus that let users explore services without spamming the chat.
3. **Lead Collection Pipeline**: A secure `ConversationHandler` state machine that captures:
   - Client's Name
   - Email (validated via Regex)
   - Phone Number (validated via Regex)
   - Detailed Project Needs
4. **Local Database**: Instantly saves collected leads in a local **SQLite** database (`leads.db`), completely serverless and self-contained.
5. **Admin Alert System**: Messages the bot owner (admin) directly on Telegram the second a new lead is captured.
6. **Hardened Security**: Protected against prompt injections, rule leaks, and code block leakage.

---

## File Structure

```
business_bot/
│
├── bot.py              # Main Telegram bot configuration and state handlers
├── database.py         # SQLite connection, schema creation, and insert helpers
├── system_prompt.txt   # Hardened AI instruction file (loaded dynamically)
├── requirements.txt    # Python library dependencies
├── .env.template       # Setup environment variables template
└── leads.db            # Local SQLite database file (created automatically)
```

---

## Quick Setup Guide

### 1. Install Dependencies
Run the command below in your project folder to install the required libraries:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.template` to a new file named `.env`:
```bash
cp .env.template .env
```
Fill in the configuration parameters:
- `TOKEN`: Obtain from [@BotFather](https://t.me/BotFather) on Telegram.
- `GROQ_API_KEY`: Obtain from your Groq Console.
- `ADMIN_CHAT_ID`: Get using [@userinfobot](https://t.me/userinfobot) on Telegram.

### 3. Launch the Bot
Start the bot using Python:
```bash
python bot.py
```

### 4. How to Use
- Send `/start` to see the greeting message and the services menu.
- Ask any question about services, pricing, or tech stacks to test the AI.
- Send `/register` to test the validation checks and complete the lead registration form.
- Check your local folder—`leads.db` will have captured the records, and you will receive a direct notification on Telegram!
