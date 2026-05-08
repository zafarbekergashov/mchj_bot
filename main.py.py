import os
import logging
import telebot
import google.generativeai as genai
from telebot import types
from flask import Flask
import threading

# ─── RENDER UCHUN SOXTA SERVER (BEPUL REJIM) ──────────────────
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is alive!"

def run_flask():
    # Render beradigan portni avtomatik aniqlaydi
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ─── SOZLAMALAR ───────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini-ni sozlash
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Log yuritish
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ─── TIZIM PROMPTI (YURIDIK MANTIQ SAQLANDI) ──────────────────
SYSTEM_PROMPT = """Siz O'zbekiston Respublikasi qonunchiligi bo'yicha mutaxassis yuridik yordamchisiz.
MChJ ustavlarini O'RQ-310-II "Mas'uliyati cheklangan jamiyatlar to'g'risida"gi Qonun va Fuqarolik kodeksi asosida tekshirasiz.

Javob formati:
1. 📋 USTAV TAHLILI XULOSASI
2. ✅ QONUNCHILIK TALABLARIGA MUVOFIQ BO'LIMLAR
3. 🔴 QONUNCHILIKKA ZID YOKI XAVFLI O'RINLAR (Har bir xato uchun modda va tuzatish bering)
4. ⚠️ TAVSIYA ETILADIGAN QO'SHIMCHALAR
5. 📊 UMUMIY BAHO (Muvofiqlik % va Xavf darajasi)

Faqat rasmiy O'zbek yuridik tilida javob bering."""

# ─── BOT BUYRUQLARI ───────────────────────────────────────────
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "⚖️ *MChJ Ustav Tekshiruvchi Bot (Bepul)*\n\nUstav matnini yuboring yoki PDF fayl yuklang. O'zbekiston qonunchiligiga muvofiqligini tekshiraman.", parse_mode="Markdown")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if len(message.text) < 100:
        bot.reply_to(message, "⚠️ Ustav matni juda qisqa. Iltimos, to'liqroq matn yuboring.")
        return
    
    msg = bot.reply_to(message, "⏳ Gemini tahlil qilmoqda, kuting...")
    
    try:
        response = model.generate_content(f"{SYSTEM_PROMPT}\n\nUstav matni:\n{message.text}")
        bot.edit_message_text(response.text, message.chat.id, msg.message_id)
    except Exception as e:
        logging.error(e)
        bot.edit_message_text("❌ Xato! API kalit yoki matn hajmi bilan muammo.", message.chat.id, msg.message_id)

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'application/pdf':
        msg = bot.reply_to(message, "📥 PDF tahlil qilinmoqda...")
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            response = model.generate_content([
                SYSTEM_PROMPT,
                {"mime_type": "application/pdf", "data": downloaded_file}
            ])
            bot.edit_message_text(response.text, message.chat.id, msg.message_id)
        except Exception as e:
            logging.error(e)
            bot.edit_message_text("❌ PDF tahlilida xato.", message.chat.id, msg.message_id)
    else:
        bot.reply_to(message, "❌ Faqat PDF yuboring.")

# ─── ISHGA TUSHIRISH (BOG'LANGAN HOLDA) ────────────────────────
if __name__ == "__main__":
    # 1. Flask-ni alohida "oqim"da ishga tushiramiz
    threading.Thread(target=run_flask, daemon=True).start()
    
    # 2. Botni ishga tushiramiz
    print("🤖 Bot bepul Web Service-da ishga tushdi...")
    bot.infinity_polling()
