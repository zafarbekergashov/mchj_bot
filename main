"""
MChJ Ustav Tekshiruvchi Telegram Bot — Render Web Service versiyasi
===================================================================
Render → Web Service → webhook orqali ishlaydi

Kerakli environment variables (Render dashboard > Environment):
  TELEGRAM_TOKEN    — @BotFather dan olingan token
  ANTHROPIC_API_KEY — platform.anthropic.com dan olingan kalit
  RENDER_URL        — https://your-app-name.onrender.com  (Render bergan URL)

O'rnatish (requirements.txt):
  python-telegram-bot==20.7
  anthropic
  flask
  gunicorn
"""

import os
import logging
import asyncio
import base64
import threading
from flask import Flask, request, Response
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import anthropic

# ─── Sozlamalar ───────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ANTHROPIC_KEY  = os.environ["ANTHROPIC_API_KEY"]
RENDER_URL     = os.environ.get("RENDER_URL", "").rstrip("/")
WEBHOOK_PATH   = f"/webhook/{TELEGRAM_TOKEN}"
PORT           = int(os.environ.get("PORT", 8080))
MAX_FILE_SIZE  = 10 * 1024 * 1024   # 10 MB

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
log = logging.getLogger(__name__)

ai_client  = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
flask_app  = Flask(__name__)
ptb_app    = None
event_loop = asyncio.new_event_loop()

# ─── Tizim prompti ────────────────────────────────────────────
SYSTEM_PROMPT = """Siz O'zbekiston Respublikasi qonunchiligi bo'yicha mutaxassis yuridik yordamchisiz.
Vazifangiz — MChJ (Mas'uliyati Cheklangan Jamiyat) ustavlarini O'zbekiston qonunchiligiga muvofiqligini tekshirish.

## Asosiy qonunchilik bazasi:

1. O'RQ-310-II — "Mas'uliyati cheklangan jamiyatlar to'g'risida"gi Qonun (06.12.2001, so'nggi tahrir 2025-yil 8-may, O'RQ-1025)
2. Fuqarolik kodeksi — 49-55, 62-63, 252-255-moddalar
3. O'RQ-1055517 — Yuridik shaxslarni davlat ro'yxatidan o'tkazish to'g'risida
4. O'RQ-2006789 — Tadbirkorlik faoliyati to'g'risida

## Ustavda MAJBURIY bo'limlar (12-modda asosida):

1. Jamiyatning to'liq va qisqartirilgan firma nomi (davlat tilida)
2. Jamiyatning joylashgan manzili va pochta manzili
3. Jamiyat faoliyatining predmeti va maqsadlari
4. Ustav fondi (ustav kapitali) miqdori
5. Har bir ishtirokchining ulushi (foizda yoki kasrda) — 14-modda
6. Ishtirokchilarning huquq va majburiyatlari — 9-10-moddalar
7. Ishtirokchilar tarkibini o'zgartirish tartibi
8. Boshqaruv organlari (umumiy yig'ilish, ijro organi) — 22-29-moddalar
9. Foyda va zararni taqsimlash tartibi
10. Hujjatlarni saqlash va axborot berish tartibi
11. Qayta tashkil etish va tugatish tartibi — 49-51-moddalar

## TAQIQLANGAN yoki XATO holatlar:

- Firma nomida "mas'uliyati cheklangan jamiyat" yoki "MChJ" bo'lmasligi (6-modda)
- Ulushning foiz/kasr o'rniga boshqa ko'rinishda belgilanishi (14-modda)
- Ustav fondini shakllantirishda 1 yildan ortiq muddat belgilanishi (15-modda)
- Umumiy yig'ilish mutlaq vakolatlari to'liq ko'rsatilmasligi (22-modda)
- Direktorning vakolat muddati ko'rsatilmasligi
- Ishtirokchilarning chiqish tartibi ko'rsatilmasligi (25-modda)
- Yirik bitimlar uchun maxsus tartib ko'rsatilmasligi (40-modda)
- Foyda taqsimlash chastotasi ko'rsatilmasligi
- Nizomga o'zgartirish uchun talab etiladigan ovozlar ulushi ko'rsatilmasligi

## Javob formati (har doim shu tuzilmada):

---
📋 USTAV TAHLILI XULOSASI

Tekshirilgan hujjat: [tavsif]
Asosiy qonun: O'RQ-310-II "Mas'uliyati cheklangan jamiyatlar to'g'risida"gi Qonun

---
✅ QONUNCHILIK TALABLARIGA MUVOFIQ BO'LIMLAR:
[Muvofiq bo'lim — qaysi modda asosida]

---
🔴 QONUNCHILIKKA ZID YOKI XAVFLI O'RINLAR:

🔴 XAVF [N]: [Sarlavha]
- Muammo: [nima xato yoki yo'q]
- Qonuniy asos: [modda raqami va qoidasi]
- Taklif etiladigan tuzatma: "[To'g'ri yuridik formulirovka — lex.uz uslubida]"

---
⚠️ TAVSIYA ETILADIGAN QO'SHIMCHALAR:
[Majburiy bo'lmagan, lekin tavsiya etiladigan qo'shimchalar]

---
📊 UMUMIY BAHO:
- Muvofiqlik darajasi: [foizda]
- Xavf darajasi: [Yuqori / O'rta / Past]
- Xulosa: [1-2 jumla]

---
⚖️ Diqqat: Ushbu tahlil dastlabki huquqiy baholash bo'lib, yuridik ahamiyatga ega qarorlar uchun litsenziyalangan advokat maslahati talab etiladi.

## Til va uslub:
- Rasmiy O'zbek yuridik tilidan foydalaning (lex.uz va Vazirlar Mahkamasi uslubida)
- Moddalarga aniq havola bering (masalan: "310-II-son Qonunning 12-moddasining uchinchi qismiga muvofiq")
- Taklif formulirovkalar qonunchilik tilida bo'lsin
- "Jamiyat", "ishtirokchi", "ustav fondi", "ta'sis hujjati" kabi rasmiy terminlardan foydalaning
"""


# ─── Telegram handlerlar ──────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚖️ MChJ Ustav Tekshiruvchi Bot\n\n"
        "Assalomu alaykum! Ushbu bot O'zbekiston Respublikasi qonunchiligiga "
        "muvofiq MChJ ustavlarini tahlil qiladi.\n\n"
        "📚 Asosiy qonunchilik:\n"
        "• O'RQ-310-II — MChJ to'g'risidagi Qonun (2025 tahriri)\n"
        "• Fuqarolik kodeksi (49-55, 252-255-moddalar)\n"
        "• Davlat ro'yxatidan o'tkazish to'g'risidagi Qonun\n\n"
        "📄 Qanday foydalanish:\n"
        "1. Ustav matnini to'g'ridan-to'g'ri yuboring\n"
        "2. Yoki PDF / TXT fayl yuklang\n"
        "3. Bot 🔴 xavfli o'rinlarni belgilaydi va tuzatma taklif qiladi\n\n"
        "/help — Yordam  |  /about — Bot haqida\n\n"
        "Ustav matnini yuboring ⬇️"
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Yordam\n\n"
        "Nima tekshiriladi?\n"
        "• Firma nomi to'g'riligi (6-modda)\n"
        "• Ustav fondi va ulush tartibi (14-15-moddalar)\n"
        "• Majburiy bo'limlar mavjudligi (12-modda)\n"
        "• Boshqaruv organlari vakolatlari (22-29-moddalar)\n"
        "• Ishtirokchilar huquq va majburiyatlari (9-10-moddalar)\n"
        "• Yirik bitimlar tartibi (40-modda)\n"
        "• Qayta tashkil etish va tugatish (49-51-moddalar)\n\n"
        "Formatlar: Matn, PDF, TXT\n\n"
        "⚠️ Bot dastlabki baholash uchun. Muhim qarorlar uchun advokat tavsiya etiladi."
    )


async def cmd_about(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ Bot haqida\n\n"
        "MChJ ustavlarini O'zbekiston qonunchiligi asosida tahlil qiluvchi bot.\n\n"
        "Texnologiya: Claude AI (Anthropic)\n"
        "Qonunchilik bazasi: lex.uz\n\n"
        "⚖️ Bot yuridik maslahat bermaydi."
    )


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if len(text) < 100:
        await update.message.reply_text(
            "⚠️ Ustav matni juda qisqa.\n"
            "Iltimos, to'liq ustav matnini yuboring."
        )
        return
    wait_msg = await update.message.reply_text(
        "⚖️ Ustav tahlil qilinmoqda...\n"
        "📚 Qonunchilik bilan solishtirish...\n"
        "🔍 Bir necha daqiqa kuting."
    )
    try:
        result = ai_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": (
                    "Quyidagi MChJ ustav matnini O'zbekiston Respublikasi qonunchiligiga "
                    "muvofiqligini batafsil tekshiring:\n\n"
                    "---USTAV MATNI---\n"
                    f"{text}\n"
                    "---USTAV MATNI TUGADI---"
                )
            }]
        ).content[0].text
        await wait_msg.delete()
        await send_long(update, result)
    except Exception as e:
        log.error(f"Tahlil xatosi: {e}")
        await wait_msg.edit_text("❌ Tahlilda xato yuz berdi. Qayta urinib ko'ring.")


async def handle_file(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc:
        return
    if doc.file_size and doc.file_size > MAX_FILE_SIZE:
        await update.message.reply_text("❌ Fayl 10 MB dan kichik bo'lishi kerak.")
        return
    allowed = ["application/pdf", "text/plain", "application/msword",
               "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if doc.mime_type not in allowed:
        await update.message.reply_text("❌ Faqat PDF, TXT yoki Word fayllari.")
        return

    wait_msg = await update.message.reply_text(
        "📥 Fayl qabul qilindi...\n"
        "⚖️ Qonunchilik bilan solishtirish...\n"
        "🔍 Bir necha daqiqa kuting."
    )
    try:
        file = await doc.get_file()
        file_bytes = bytes(await file.download_as_bytearray())

        if doc.mime_type == "application/pdf":
            pdf_b64 = base64.b64encode(file_bytes).decode()
            result = ai_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                system=SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_b64
                            }
                        },
                        {
                            "type": "text",
                            "text": (
                                "Ushbu PDF fayldagi MChJ ustavini O'zbekiston qonunchiligiga "
                                "muvofiqligini batafsil tekshiring."
                            )
                        }
                    ]
                }]
            ).content[0].text
        else:
            try:
                ustav_text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                ustav_text = file_bytes.decode("latin-1", errors="replace")
            result = ai_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                system=SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": (
                        "Quyidagi MChJ ustavini O'zbekiston qonunchiligiga "
                        "muvofiqligini batafsil tekshiring:\n\n"
                        f"{ustav_text}"
                    )
                }]
            ).content[0].text

        await wait_msg.delete()
        await send_long(update, result)
    except Exception as e:
        log.error(f"Fayl xatosi: {e}")
        await wait_msg.edit_text(
            "❌ Fayl qayta ishlashda xato.\n"
            "Ustav matnini to'g'ridan-to'g'ri xabar sifatida yuboring."
        )


async def send_long(update: Update, text: str):
    MAX_LEN = 4000
    if len(text) <= MAX_LEN:
        await update.message.reply_text(text)
        return
    chunks, current = [], ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > MAX_LEN:
            if current:
                chunks.append(current)
            current = line
        else:
            current += ("\n" if current else "") + line
    if current:
        chunks.append(current)
    for i, chunk in enumerate(chunks):
        await update.message.reply_text(("(davomi)\n\n" if i else "") + chunk)


# ─── PTB app ni sozlash ───────────────────────────────────────
async def setup_bot():
    global ptb_app
    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .updater(None)
        .build()
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CommandHandler("about", cmd_about))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    await app.initialize()
    await app.start()

    if RENDER_URL:
        webhook_url = f"{RENDER_URL}{WEBHOOK_PATH}"
        await app.bot.set_webhook(url=webhook_url, allowed_updates=["message"])
        log.info(f"✅ Webhook o'rnatildi: {webhook_url}")
    else:
        log.warning("⚠️  RENDER_URL yo'q — webhook o'rnatilmadi")

    ptb_app = app


# ─── Flask endpointlar ────────────────────────────────────────
@flask_app.route(WEBHOOK_PATH, methods=["POST"])
def webhook_handler():
    if ptb_app is None:
        return Response("Bot tayyor emas", status=503)
    data = request.get_json(force=True)
    update = Update.de_json(data, ptb_app.bot)
    future = asyncio.run_coroutine_threadsafe(
        ptb_app.process_update(update), event_loop
    )
    future.result(timeout=60)
    return Response("OK", status=200)


@flask_app.route("/", methods=["GET"])
@flask_app.route("/health", methods=["GET"])
def health():
    return Response("MChJ Ustav Bot ishlayapti ✅", status=200)


# ─── Ishga tushirish ──────────────────────────────────────────
def run_event_loop():
    asyncio.set_event_loop(event_loop)
    event_loop.run_until_complete(setup_bot())
    event_loop.run_forever()


if __name__ == "__main__":
    # Async loop ni alohida threadda ishga tushirish
    bot_thread = threading.Thread(target=run_event_loop, daemon=True)
    bot_thread.start()
    # Webhook setup tugashini kutish
    import time; time.sleep(3)

    log.info(f"🚀 Flask {PORT} portda ishlamoqda...")
    flask_app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)
