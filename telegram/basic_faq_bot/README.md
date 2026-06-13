# Custom Telegram AI FAQ Bot

A production-ready, lightweight Telegram AI Assistant designed to answer customer queries automatically using Groq's high-speed Llama models. Perfect for small businesses, freelancers, agency owners, or communities looking for an automated FAQ & support assistant.

---

## Features
- **AI-Powered Replies**: Uses Groq API (`llama-3.1-8b-instant`) for lightning-fast, high-quality responses.
- **Dynamic Training**: Easily configure or update the bot's knowledge base and tone by editing a plain-text file (`system_prompt.txt`) without writing or changing Python code.
- **Robust Error Handling**: Handles network, API, and token issues gracefully without crashing.

---

## Setup Instructions

### 1. Prerequisites
Make sure you have Python (version 3.8 or higher) installed on your system.

### 2. Install Dependencies
Navigate into the bot's directory and install the required dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configure API Credentials
Create a `.env` file in the root of the bot's directory (or edit the template `.env` file) and fill in your details:
```env
TOKEN=your_telegram_bot_token_here
GROQ_API_KEY=your_groq_api_key_here
```
- **TOKEN**: Get this by messaging [@BotFather](https://t.me/BotFather) on Telegram and creating a new bot.
- **GROQ_API_KEY**: Get this for free by creating an account on the [Groq Console](https://console.groq.com/).

### 4. Teach the Bot (Customizing the FAQ)
Open `system_prompt.txt` and fill in your business details:
- What services do you offer?
- What are your packages and pricing?
- How can clients contact you?
- What rules/tone should the AI follow?

*Tip: You can edit `system_prompt.txt` while the bot is running, and the AI will update its responses immediately!*

### 5. Run the Bot
Start your bot by executing the script:
```bash
python bot.py
```

---

## How it Works
1. **`/start` & `/help`**: Welcomes users and tells them what commands are available.
2. **Text message fallback**: When a user types a question, the bot reads the business description from `system_prompt.txt`, appends the user's message, and queries the Groq API to generate an accurate, context-aware answer.
