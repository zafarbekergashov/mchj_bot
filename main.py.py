import os
import logging
import telebot
import google.generativeai as genai
from telebot import types

# ─── SOZLAMALAR ───────────────────────────────────────────────
# Render Environment Variables bo'limida ushbu nomlar bilan saqlang
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini-ni sozlash
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # Tejamkor va tezkor model

# Log yuritish
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ─── TIZIM PROMPTI (YURIDIK MANTIQ) ───────────────────────────
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
    bot.reply_to(message, "⚖️ *MChJ Ustav Tekshiruvchi Bot*\n\nUstav matnini yuboring yoki PDF fayl yuklang. Men uni O'zbekiston qonunchiligiga muvofiqligini tekshiraman.", parse_mode="Markdown")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if len(message.text) < 100:
        bot.reply_to(message, "⚠️ Ustav matni juda qisqa. Iltimos, to'liqroq matn yuboring.")
        return
    
    msg = bot.reply_to(message, "⏳ Tahlil qilinmoqda, iltimos kuting...")
    
    try:
        response = model.generate_content(f"{SYSTEM_PROMPT}\n\nUstav matni:\n{message.text}")
        bot.edit_message_text(response.text, message.chat.id, msg.message_id)
    except Exception as e:
        logging.error(e)
        bot.edit_message_text("❌ Xato yuz berdi. API kalitini tekshiring.", message.chat.id, msg.message_id)

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'application/pdf':
        msg = bot.reply_to(message, "📥 PDF qabul qilindi. Gemini orqali tahlil qilinmoqda...")
        
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # Gemini 1.5 PDF-ni matn ko'rinishida tahlil qilish uchun yuborish
            # (Eslatma: Murakkab PDFlar uchun matnni ajratib olish tavsiya etiladi)
            response = model.generate_content([
                SYSTEM_PROMPT,
                {"mime_type": "application/pdf", "data": downloaded_file}
            ])
            
            bot.edit_message_text(response.text, message.chat.id, msg.message_id)
        except Exception as e:
            logging.error(e)
            bot.edit_message_text("❌ PDFni tahlil qilishda xato. Matnni o'zini yuborib ko'ring.", message.chat.id, msg.message_id)
    else:
        bot.reply_to(message, "❌ Faqat PDF fayl yuboring.")

# ─── ISHGA TUSHIRISH ─────────────────────────────────────────
if __name__ == "__main__":
    print("🤖 Bot ishga tushdi...")
    bot.infinity_polling()
