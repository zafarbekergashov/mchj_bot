"""
MChJ Ustav Tekshiruvchi Telegram Bot — Render Web Service
Fayl nomi: main2.py
Start Command: gunicorn main2:flask_app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120
"""

import os
import logging
import asyncio
import base64
import io
import threading
import time

from flask import Flask, request, Response
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import anthropic
from docx import Document as DocxDocument

# ─── Sozlamalar ───────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ANTHROPIC_KEY  = os.environ["ANTHROPIC_API_KEY"]
RENDER_URL     = os.environ.get("RENDER_URL", "").rstrip("/")
WEBHOOK_PATH   = f"/webhook/{TELEGRAM_TOKEN}"
PORT           = int(os.environ.get("PORT", 8080))
MAX_FILE_SIZE  = 20 * 1024 * 1024

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
log = logging.getLogger(__name__)

ai_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
flask_app = Flask(__name__)
ptb_app   = None
loop      = None

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

## Javob formati:

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
- Taklif etiladigan tuzatma: "[To'g'ri yuridik formulirovka]"

---
⚠️ TAVSIYA ETILADIGAN QO'SHIMCHALAR:
[Tavsiya etiladigan qo'shimchalar]

---
📊 UMUMIY BAHO:
- Muvofiqlik darajasi: [foizda]
- Xavf darajasi: [Yuqori / O'rta / Past]
- Xulosa: [1-2 jumla]

---
⚖️ Diqqat: Ushbu tahlil dastlabki huquqiy baholash bo'lib, yuridik ahamiyatga ega qarorlar uchun litsenziyalangan advokat maslahati talab etiladi.

Til: Rasmiy O'zbek yuridik tili (lex.uz uslubida). Moddalarga aniq havola bering.
"""


# ─── Word (.docx) dan matn olish ──────────────────────────────
def extract_docx_text(file_bytes: bytes) -> str:
    doc   = DocxDocument(io.BytesIO(file_bytes))
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    parts.append(cell.text.strip())
    return "\n".join(parts)


# ─── Claude API ───────────────────────────────────────────────
def call_claude_text(ustav_text: str) -> str:
    r = ai_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content":
            f"Quyidagi MChJ ustavini O'zbekiston qonunchiligiga muvofiqligini tekshiring:\n\n"
            f"---USTAV MATNI---\n{ustav_text}\n---USTAV MATNI TUGADI---"
        }]
    )
    return r.content[0].text


def call_claude_pdf(pdf_b64: str) -> str:
    r = ai_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": [
            {"type": "document", "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": pdf_b64
            }},
            {"type": "text", "text":
                "Ushbu PDF fayldagi MChJ ustavini O'zbekiston qonunchiligiga muvofiqligini tekshiring."
            }
        ]}]
    )
    return r.content[0].text


# ─── Uzun xabar yuborish ──────────────────────────────────────
async def send_long(update: Update, text: str):
    MAX_LEN = 4000
    if len(text) <= MAX_LEN:
        await update.message.reply_text(text)
        return
    chunks, current = [], ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > MAX_LEN:
            chunks.append(current)
            current = line
        else:
            current += ("\n" if current else "") + line
    if current:
        chunks.append(current)
    for i, chunk in enumerate(chunks):
        await update.message.reply_text(("(davomi)\n\n" if i else "") + chunk)


# ─── Handlerlar ───────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚖️ MChJ Ustav Tekshiruvchi Bot\n\n"
        "Assalomu alaykum! O'zbekiston qonunchiligi asosida MChJ ustavlarini tahlil qilaman.\n\n"
        "📎 Qabul qilinadigan formatlar:\n"
        "• Oddiy matn — to'g'ridan-to'g'ri yuboring\n"
        "• PDF fayl (.pdf)\n"
        "• Word fayl (.docx, .doc)\n"
        "• Matn fayli (.txt)\n\n"
        "Ustav matnini yoki faylini yuboring ⬇️"
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
        "⚠️ Bot dastlabki baholash uchun. Muhim qarorlar uchun advokat tavsiya etiladi."
    )


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if len(text) < 100:
        await update.message.reply_text("⚠️ Matn juda qisqa. To'liq ustav matnini yuboring.")
        return
    wait_msg = await update.message.reply_text(
        "⚖️ Ustav tahlil qilinmoqda...\n"
        "📚 Qonunchilik bilan solishtirish...\n"
        "🔍 Bir necha daqiqa kuting."
    )
    try:
        result = call_claude_text(text)
        await wait_msg.delete()
        await send_long(update, result)
    except Exception as e:
        log.error(f"Matn xatosi: {e}")
        await wait_msg.edit_text("❌ Xato yuz berdi. Qayta urinib ko'ring.")


async def handle_file(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc:
        return
    if doc.file_size and doc.file_size > MAX_FILE_SIZE:
        await update.message.reply_text("❌ Fayl 20 MB dan kichik bo'lishi kerak.")
        return

    mime  = doc.mime_type or ""
    fname = (doc.file_name or "").lower()

    is_pdf  = mime == "application/pdf" or fname.endswith(".pdf")
    is_docx = (mime in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword"
    ] or fname.endswith(".docx") or fname.endswith(".doc"))
    is_txt  = mime == "text/plain" or fname.endswith(".txt")

    if not (is_pdf or is_docx or is_txt):
        await update.message.reply_text(
            "❌ Qo'llab-quvvatlanmaydigan format.\n"
            "Qabul qilinadigan: PDF, Word (.docx/.doc), TXT"
        )
        return

    tur = "📄 PDF" if is_pdf else ("📝 Word" if is_docx else "📃 TXT")
    wait_msg = await update.message.reply_text(
        f"{tur} fayl qabul qilindi...\n"
        "⚖️ Tahlil boshlanmoqda...\n"
        "🔍 Bir necha daqiqa kuting."
    )
    try:
        file       = await doc.get_file()
        file_bytes = bytes(await file.download_as_bytearray())

        if is_pdf:
            result = call_claude_pdf(base64.b64encode(file_bytes).decode())
        elif is_docx:
            try:
                ustav_text = extract_docx_text(file_bytes)
            except Exception as e:
                log.error(f"Word xatosi: {e}")
                await wait_msg.edit_text("❌ Word faylni o'qishda xato. PDF formatida yuboring.")
                return
            if len(ustav_text.strip()) < 50:
                await wait_msg.edit_text("❌ Word fayldan matn olib bo'lmadi. PDF formatida yuboring.")
                return
            result = call_claude_text(ustav_text)
        else:
            try:
                ustav_text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                ustav_text = file_bytes.decode("latin-1", errors="replace")
            result = call_claude_text(ustav_text)

        await wait_msg.delete()
        await send_long(update, result)

    except Exception as e:
        log.error(f"Fayl xatosi: {e}")
        await wait_msg.edit_text(
            "❌ Fayl qayta ishlashda xato.\n"
            "Ustav matnini to'g'ridan-to'g'ri xabar sifatida yuboring."
        )


# ─── Bot thread da ishga tushirish ────────────────────────────
def start_bot_in_thread():
    global ptb_app, loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def _setup():
        global ptb_app
        app = (
            Application.builder()
            .token(TELEGRAM_TOKEN)
            .updater(None)
            .build()
        )
        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CommandHandler("help",  cmd_help))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

        await app.initialize()
        await app.start()

        if RENDER_URL:
            webhook_url = f"{RENDER_URL}{WEBHOOK_PATH}"
            await app.bot.delete_webhook(drop_pending_updates=True)
            await asyncio.sleep(1)
            await app.bot.set_webhook(
                url=webhook_url,
                allowed_updates=["message"]
            )
            log.info(f"✅ Webhook o'rnatildi: {webhook_url}")
        else:
            log.warning("⚠️ RENDER_URL yo'q!")

        ptb_app = app

    loop.run_until_complete(_setup())
    loop.run_forever()


# ─── Flask endpointlar ────────────────────────────────────────
@flask_app.route(WEBHOOK_PATH, methods=["POST"])
def webhook_handler():
    global ptb_app, loop
    if ptb_app is None or loop is None:
        return Response("Bot tayyor emas", status=503)
    data   = request.get_json(force=True)
    update = Update.de_json(data, ptb_app.bot)
    future = asyncio.run_coroutine_threadsafe(
        ptb_app.process_update(update), loop
    )
    try:
        future.result(timeout=55)
    except Exception as e:
        log.error(f"Update xatosi: {e}")
    return Response("OK", status=200)


@flask_app.route("/", methods=["GET"])
@flask_app.route("/health", methods=["GET"])
def health():
    status = "✅ ishlayapti" if ptb_app else "⏳ yuklanmoqda"
    return Response(f"MChJ Ustav Bot {status}", status=200)


# ─── Gunicorn uchun thread avtomatik boshlanadi ───────────────
_bot_thread = threading.Thread(target=start_bot_in_thread, daemon=True)
_bot_thread.start()
time.sleep(5)

if __name__ == "__main__":
    log.info(f"🚀 Flask {PORT} portda ishlamoqda...")
    flask_app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)
