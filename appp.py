import time
import os
import sqlite3
import random

from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# 🔐 CHANGE THIS TOKEN
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

# ---------------- DRIVER ----------------
def create_driver():
    options = Options()

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,720")

    options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")

    driver = webdriver.Chrome(service=service, options=options)
    return driver

driver = create_driver()

# ---------------- MAIN PROCESS ----------------
def record_process(email):
    images = []

    driver.get("https://accounts.google.com/")
    time.sleep(random.randint(3, 5))

    # Enter email
    email_input = driver.find_element(By.ID, "identifierId")
    email_input.clear()

    for char in email:
        email_input.send_keys(char)
        time.sleep(0.05)

    time.sleep(random.randint(1, 2))

    # 📸 Screenshot BEFORE ENTER
    img1 = f"{email}_{int(time.time())}_before.png"
    driver.save_screenshot(img1)
    images.append(img1)

    # ENTER
    email_input.send_keys(Keys.ENTER)

    time.sleep(random.randint(4, 6))

    # 📸 Screenshot AFTER ENTER
    img2 = f"{email}_{int(time.time())}_after.png"
    driver.save_screenshot(img2)
    images.append(img2)

    page = driver.page_source.lower()

    # RESULT DETECTION
    if "couldn't find your google account" in page or "couldn’t find your google account" in page:
        result = "❌ Not Created"

    elif "enter your password" in page or "welcome" in page or "password" in page:
        result = "✅ Created"

    elif "try again later" in page or "unusual traffic" in page or "not be secure" in page:
        result = "⚠️ BLOCKED"

    else:
        result = "⚠️ Unknown"

    # SAVE DB
    cur.execute("INSERT INTO logs VALUES (?,?,datetime('now'))", (email, result))
    db.commit()

    time.sleep(random.randint(5, 8))

    return result, images

# ---------------- HANDLE MESSAGE ----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()

    if "@" not in email:
        await update.message.reply_text("❌ Invalid email")
        return

    await update.message.reply_text("⏳ Checking...")

    try:
        result, images = record_process(email)

        # Send screenshots
        for img in images:
            with open(img, "rb") as photo:
                await update.message.reply_photo(photo)
            os.remove(img)

        await update.message.reply_text(f"{email}\n{result}")

    except Exception as e:
        await update.message.reply_text("⚠️ Error / Blocked")

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
    await update.message.reply_text("🤖 Send Gmail to check status")

# ---------------- APP ----------------
app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("🚀 Bot Running...")
app.run_polling()    
