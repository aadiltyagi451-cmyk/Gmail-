import requests
import sqlite3
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

BOT_TOKEN = "8376225941:AAHvhTSl5OEMCO1hLvyFau3XI2O3Xn4k6c0"

# ---------------- DATABASE ----------------
db = sqlite3.connect("data.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS logs(
email TEXT,
status TEXT,
time TEXT
)
""")
db.commit()

# ---------------- CHECK FUNCTION ----------------
def check_email(email):
    url = "https://accounts.google.com/_/lookup/accountlookup"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }

    data = {
        "f.req": f'["{email}",null,null,null,"en"]'
    }

    try:
        r = requests.post(url, headers=headers, data=data, timeout=10)
        text = r.text.lower()

        if "password" in text or "challenge" in text:
            return "✅ Created"

        elif "couldn" in text or "not found" in text:
            return "❌ Not Created"

        else:
            return "⚠️ Unknown"

    except:
        return "⚠️ Error"

# ---------------- HANDLE ----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()

    if "@" not in email:
        await update.message.reply_text("❌ Invalid email")
        return

    await update.message.reply_text("⏳ Checking...")

    result = check_email(email)

    cur.execute("INSERT INTO logs VALUES (?,?,datetime('now'))", (email, result))
    db.commit()

    await update.message.reply_text(f"{email}\n{result}")

# ---------------- STATS ----------------
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cur.execute("SELECT status, COUNT(*) FROM logs GROUP BY status")
    rows = cur.fetchall()

    msg = "📊 Stats:\n"
    for status, count in rows:
        msg += f"{status} → {count}\n"

    await update.message.reply_text(msg)

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Send Gmail to check (No Selenium Mode)")

# ---------------- APP ----------------
app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("🚀 Bot Running (No Selenium)...")
app.run_polling()
