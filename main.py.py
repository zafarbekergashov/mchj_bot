import os
import logging
import telebot
import google.generativeai as genai
import io
import PyPDF2
from flask import Flask
import threading

# ─── RENDER UCHUN SERVER ───
app = Flask(__name__)
@app.route('/')
def health(): return "OK"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ─── SOZLAMALAR ───
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

SYSTEM_PROMPT = """Siz O'zbekiston yuridik mutaxassisiz. MChJ ustavini O'RQ-310-II asosida tahlil qiling. 
Javobni: Xulosa, Muvofiq joylar, Xato va kamchiliklar, Tavsiyalar va Umumiy ball shaklida bering."""

# ─── PDF-DAN MATN AJRATISH FUNKSIYASI ───
def extract_text_from_pdf(pdf_bytes):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "⚖️ MChJ Ustav tahlil botiga xush kelibsiz! Matn yoki PDF yuboring.")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if len(message.text) < 100:
        bot.reply_to(message, "⚠️ Matn juda qisqa.")
        return
    msg = bot.reply_to(message, "⏳ Tahlil qilinmoqda...")
    try:
        response = model.generate_content(f"{SYSTEM_PROMPT}\n\nUstav:\n{message.text}")
        bot.edit_message_text(response.text, message.chat.id, msg.message_id)
    except Exception as e:
        bot.edit_message_text("❌ Xato yuz berdi.", message.chat.id, msg.message_id)

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'application/pdf':
        msg = bot.reply_to(message, "📥 PDF o'qilmoqda...")
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # PDF-dan matnni ajratib olamiz
            pdf_text = extract_text_from_pdf(downloaded_file)
            
            if len(pdf_text.strip()) < 50:
                bot.edit_message_text("❌ PDF ichida matn topilmadi yoki u rasm ko'rinishida.", message.chat.id, msg.message_id)
                return

            bot.edit_message_text("⏳ Gemini tahlil qilmoqda...", message.chat.id, msg.message_id)
            response = model.generate_content(f"{SYSTEM_PROMPT}\n\nUstav matni:\n{pdf_text}")
            bot.edit_message_text(response.text, message.chat.id, msg.message_id)
            
        except Exception as e:
            logging.error(e)
            bot.edit_message_text("❌ PDF tahlilida xato.", message.chat.id, msg.message_id)
    else:
        bot.reply_to(message, "❌ Faqat PDF yuboring.")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.infinity_polling()
