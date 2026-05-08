"""
O'zbekiston MChJ Ustav Tekshiruvchi Telegram Bot
================================================
Talablar:
  pip install python-telegram-bot==20.7 anthropic httpx

Ishga tushirish:
  1. TELEGRAM_TOKEN va ANTHROPIC_API_KEY ni o'rnating
  2. python mchj_ustav_bot.py
"""

import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
import anthropic

# ─── Sozlamalar ───────────────────────────────────────────────
TELEGRAM_TOKEN  = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_TOKEN")
ANTHROPIC_KEY   = os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_KEY")
MAX_FILE_SIZE   = 10 * 1024 * 1024   # 10 MB

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
log = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

# ─── Tizim prompti (MCHJ qonunchiligiga asoslangan) ──────────
SYSTEM_PROMPT = """Siz O'zbekiston Respublikasi qonunchiligi bo'yicha mutaxassis yuridik yordamchisiz.
Sizning vazifangiz — MChJ (Mas'uliyati Cheklangan Jamiyat) ustavlarini O'zbekiston qonunchiligiga muvofiqligini tekshirish.

## Siz tayanadigan asosiy qonunchilik:

1. **O'RQ-310-II** — "Mas'uliyati cheklangan jamiyatlar to'g'risida"gi Qonun (06.12.2001, so'nggi tahrir 2025-yil 8-may, O'RQ-1025)
2. **O'RQ-3111347** — Fuqarolik kodeksi (tegishli moddalar: 49-55, 62-63, 252-255)
3. **O'RQ-1055517** — Yuridik shaxslarni davlat ro'yxatidan o'tkazish to'g'risidagi qonun
4. **O'RQ-2006789** — Tadbirkorlik faoliyati to'g'risidagi qonun

## Ustavda MAJBURIY bo'lishi kerak bo'lgan bo'limlar (12-modda asosida):

1. Jamiyatning to'liq va qisqartirilgan firma nomi (davlat tilida)
2. Jamiyatning joylashgan manzili (pochta manzili bilan birga)
3. Jamiyat faoliyatining predmeti va maqsadlari
4. Ustav fondi (ustav kapitali) miqdori
5. Har bir ishtirokchining ulushi miqdori (foizda yoki kasrda)
6. Ishtirokchilarning huquq va majburiyatlari
7. Ishtirokchilar tarkibini o'zgartirish tartibi
8. Boshqaruv organlari (umumiy yig'ilish, ijro organi)
9. Foyda va zararni taqsimlash tartibi
10. Hujjatlarni saqlash va axborot berish tartibi
11. Qayta tashkil etish va tugatish tartibi

## TAQIQLANGAN yoki XATO bo'lgan holatlar:

- "Mas'uliyati cheklangan jamiyat" so'zlari yoki "MChJ" abbreviaturasi firma nomida bo'lmasligi (6-modda)
- Ishtirokchi ulushining foiz/kasr o'rniga boshqa ko'rinishda belgilanishi (14-modda)  
- Ustav fondining toʻliq shakllantirilish muddati 1 yildan oshishi (15-modda)
- Umumiy yig'ilish vakolatlari to'liq ko'rsatilmasligi (22-modda)
- Direktorning vakolat muddati ko'rsatilmasligi
- Ishtirokchilarning chiqish tartibi ko'rsatilmasligi (25-modda)
- Kredit berish, garov berish bo'yicha yirik bitimlar uchun maxsus tartib ko'rsatilmasligi (40-modda)
- Foyda taqsimlash chastotasi (har qancha oyda bir marta) ko'rsatilmasligi
- Nizomga o'zgartirish kiritish uchun talab etiladigan ovozlar ulushi ko'rsatilmasligi

## Javob formati:

Har doim quyidagi tuzilmada javob bering (O'zbek tilida, rasmiy yuridik uslubda):

---
📋 **USTAV TAHLILI XULOSASI**

**Tekshirilgan hujjat:** [hujjat nomi yoki tavsifi]
**Tahlil sanasi:** [sana]
**Asosiy qonun:** O'RQ-310-II "Mas'uliyati cheklangan jamiyatlar to'g'risida"gi Qonun

---
✅ **QONUNCHILIK TALABLARIGA MUVOFIQ BO'LIMLAR:**
[Har bir muvofiq bo'lim uchun: Bo'lim nomi — qaysi modda asosida muvofiq]

---
🔴 **QONUNCHILIKKA ZID YOKI XAVFLI O'RINLAR:**

[Har bir muammo uchun:]
🔴 **XAVF [raqam]: [Sarlavha]**
- **Muammo:** [aniq nima xato yoki yo'q]
- **Qonuniy asos:** [modda raqami va matni]
- **Taklif etiladigan tuzatma:** "[To'g'ri yuridik formulirovka — lex.uz uslubida]"

---
⚠️ **TAVSIYA ETILADIGAN QUSHIMCHALAR:**
[Majburiy bo'lmagan, lekin tavsiya etiladigan qo'shimchalar]

---
📊 **UMUMIY BAHO:**
- Muvofiqlik darajasi: [foizda]
- Xavf darajasi: [Yuqori / O'rta / Past]
- Xulosa: [1-2 jumla]

---
⚖️ *Diqqat: Ushbu tahlil dastlabki huquqiy baholash bo'lib, yuridik ahamiyatga ega qarorlar uchun litsenziyalangan advokat maslahati talab etiladi.*

## Til va uslub talablari:

- Faqat rasmiy O'zbek yuridik tilidan foydalaning (lex.uz va Vazirlar Mahkamasi qarorlari uslubida)
- Qonun moddalariga aniq havola bering (masalan: "310-II-son Qonunning 12-moddasining uchinchi qismiga muvofiq")
- Taklif etiladigan formulirovkalar qonunchilik tilida bo'lsin
- "Jamiyat", "ishtirokchi", "ustav fondi", "ta'sis hujjati" kabi rasmiy terminlardan foydalaning
"""

# ─── /start komandasi ─────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "⚖️ *MChJ Ustav Tekshiruvchi Bot*\n\n"
        "Assalomu alaykum\\! Ushbu bot O'zbekiston Respublikasi qonunchiligiga muvofiq "
        "Mas'uliyati Cheklangan Jamiyat \\(MChJ\\) ustavlarini tahlil qiladi\\.\n\n"
        "*Asosiy qonunchilik asoslari:*\n"
        "• O'RQ\\-310\\-II — MChJ to'g'risidagi Qonun\n"
        "• Fuqarolik kodeksi \\(tegishli moddalar\\)\n"
        "• Davlat ro'yxatidan o'tkazish to'g'risidagi Qonun\n\n"
        "*Qanday foydalanish:*\n"
        "1\\. Ustav matnini *to'g'ridan\\-to'g'ri yuboring* \\(matn sifatida\\)\n"
        "2\\. Yoki *PDF/Word fayl* yuklang\n"
        "3\\. Bot qonunchilikka muvofiqligini tekshiradi va 🔴 xavfli o'rinlarni belgilaydi\n\n"
        "*Buyruqlar:*\n"
        "/start — Botni ishga tushirish\n"
        "/help — Yordam\n"
        "/about — Bot haqida\n\n"
        "📄 Ustav matnini yuboring\\!"
    )
    await update.message.reply_text(text, parse_mode="MarkdownV2")


# ─── /help komandasi ──────────────────────────────────────────
async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *Yordam*\n\n"
        "*Nima tekshiriladi?*\n"
        "• Firma nomi to'g'riligi \\(6\\-modda\\)\n"
        "• Ustav fondi miqdori va ulush tartibi \\(14\\-15\\-moddalar\\)\n"
        "• Majburiy bo'limlarning mavjudligi \\(12\\-modda\\)\n"
        "• Boshqaruv organlari vakolatlari \\(22\\-29\\-moddalar\\)\n"
        "• Ishtirokchilar huquq va majburiyatlari \\(9\\-10\\-moddalar\\)\n"
        "• Yirik bitimlar tartibi \\(40\\-modda\\)\n"
        "• Qayta tashkil etish va tugatish \\(49\\-51\\-moddalar\\)\n\n"
        "*Qo'llab\\-quvvatlanadigan formatlar:*\n"
        "• Oddiy matn \\(xabar sifatida\\)\n"
        "• PDF fayl\n"
        "• TXT fayl\n\n"
        "*Eslatma:* Bot dastlabki huquqiy baholash uchun mo'ljallangan\\. "
        "Muhim qarorlar uchun litsenziyalangan advokatga murojaat qiling\\."
    )
    await update.message.reply_text(text, parse_mode="MarkdownV2")


# ─── /about komandasi ─────────────────────────────────────────
async def cmd_about(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "ℹ️ *Bot haqida*\n\n"
        "Ushbu bot O'zbekiston Respublikasi qonunchiligi asosida MChJ ustavlarini "
        "tahlil qilish uchun yaratilgan\\.\n\n"
        "*Texnologiya:* Claude AI \\(Anthropic\\)\n"
        "*Qonunchilik bazasi:* lex\\.uz rasmiy qonunchilik ma'lumotlari bazasi\n\n"
        "⚖️ *Muhim:* Bot yuridik maslahat bermaydi\\. "
        "Natijalar faqat ma'lumot maqsadida taqdim etiladi\\."
    )
    await update.message.reply_text(text, parse_mode="MarkdownV2")


# ─── Matn xabari kelganda ─────────────────────────────────────
async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ustav_text = update.message.text.strip()

    if len(ustav_text) < 100:
        await update.message.reply_text(
            "⚠️ Ustav matni juda qisqa. Iltimos, to'liq ustav matnini yuboring "
            "(kamida bir necha paragraf)."
        )
        return

    await analyse_ustav(update, ctx, ustav_text)


# ─── Fayl kelganda ────────────────────────────────────────────
async def handle_file(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc:
        return

    # Fayl hajmini tekshirish
    if doc.file_size and doc.file_size > MAX_FILE_SIZE:
        await update.message.reply_text("❌ Fayl hajmi 10 MB dan oshmasligi kerak.")
        return

    # Fayl turini tekshirish
    allowed = ["application/pdf", "text/plain",
               "application/msword",
               "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if doc.mime_type not in allowed:
        await update.message.reply_text(
            "❌ Faqat PDF, TXT yoki Word fayllari qabul qilinadi."
        )
        return

    wait_msg = await update.message.reply_text(
        "📥 Fayl qabul qilindi. Tahlil boshlanmoqda, iltimos kuting..."
    )

    try:
        file = await doc.get_file()
        file_bytes = await file.download_as_bytearray()

        # PDF bo'lsa base64 orqali Claude ga yuborish
        if doc.mime_type == "application/pdf":
            import base64
            pdf_b64 = base64.b64encode(bytes(file_bytes)).decode()
            await analyse_ustav_pdf(update, ctx, pdf_b64, wait_msg)
        else:
            # TXT yoki boshqa matn fayli
            try:
                text = bytes(file_bytes).decode("utf-8")
            except UnicodeDecodeError:
                text = bytes(file_bytes).decode("latin-1", errors="replace")
            await wait_msg.delete()
            await analyse_ustav(update, ctx, text)

    except Exception as e:
        log.error(f"Fayl qayta ishlashda xato: {e}")
        await wait_msg.edit_text("❌ Faylni o'qishda xato yuz berdi. Iltimos qayta urinib ko'ring.")


# ─── Asosiy tahlil funksiyasi (matn uchun) ───────────────────
async def analyse_ustav(update: Update, ctx: ContextTypes.DEFAULT_TYPE, ustav_text: str):
    wait_msg = await update.message.reply_text(
        "⚖️ Ustav tahlil qilinmoqda...\n"
        "📚 O'zbekiston qonunchiligi bilan solishtirish amalga oshirilmoqda...\n"
        "🔍 Xavfli o'rinlar aniqlanmoqda...\n\n"
        "Bu bir necha daqiqa vaqt olishi mumkin."
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Quyidagi MChJ ustav matnini O'zbekiston Respublikasi "
                        f"qonunchiligiga muvofiqligini batafsil tekshiring va "
                        f"ko'rsatilgan format bo'yicha tahlil natijasini bering:\n\n"
                        f"---USTAV MATNI BOSHLANADI---\n"
                        f"{ustav_text}\n"
                        f"---USTAV MATNI TUGADI---"
                    )
                }
            ]
        )

        result = response.content[0].text
        await wait_msg.delete()
        await send_long_message(update, result)

    except anthropic.APIError as e:
        log.error(f"Anthropic API xatosi: {e}")
        await wait_msg.edit_text(
            "❌ Tahlil amalga oshirilmadi (API xatosi). Iltimos bir oz kutib qayta urinib ko'ring."
        )
    except Exception as e:
        log.error(f"Kutilmagan xato: {e}")
        await wait_msg.edit_text("❌ Xato yuz berdi. Iltimos qayta urinib ko'ring.")


# ─── PDF tahlili (base64 orqali) ─────────────────────────────
async def analyse_ustav_pdf(update: Update, ctx, pdf_b64: str, wait_msg):
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            messages=[
                {
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
                                "Ushbu PDF fayldagi MChJ ustav matnini O'zbekiston Respublikasi "
                                "qonunchiligiga muvofiqligini batafsil tekshiring va "
                                "ko'rsatilgan format bo'yicha tahlil natijasini bering."
                            )
                        }
                    ]
                }
            ]
        )

        result = response.content[0].text
        await wait_msg.delete()
        await send_long_message(update, result)

    except anthropic.APIError as e:
        log.error(f"Anthropic API xatosi (PDF): {e}")
        await wait_msg.edit_text(
            "❌ PDF tahlil amalga oshirilmadi. "
            "Iltimos ustav matnini to'g'ridan-to'g'ri xabar sifatida yuboring."
        )
    except Exception as e:
        log.error(f"PDF tahlilida xato: {e}")
        await wait_msg.edit_text("❌ Xato yuz berdi. Matnni to'g'ridan-to'g'ri yuboring.")


# ─── Uzun xabarni bo'lib yuborish ────────────────────────────
async def send_long_message(update: Update, text: str):
    """Telegram 4096 belgi chegarasi bo'lgani uchun uzun xabarlarni bo'lib yuboradi."""
    MAX_LEN = 4000

    # Markdown formatlashni tozalash (Telegram MarkdownV2 uchun)
    # Oddiy Markdown ishlatamiz
    if len(text) <= MAX_LEN:
        await update.message.reply_text(text)
    else:
        # Bo'lib yuborish — yangi satr bo'yicha
        chunks = []
        current = ""
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
            if i == 0:
                await update.message.reply_text(chunk)
            else:
                await update.message.reply_text(f"_(davomi)_\n\n{chunk}")


# ─── Noma'lum xabar ───────────────────────────────────────────
async def handle_unknown(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ Tushunarsiz xabar. Iltimos:\n"
        "• Ustav matnini to'g'ridan-to'g'ri yuboring\n"
        "• Yoki PDF/TXT fayl yuklang\n\n"
        "/help — Yordam uchun"
    )


# ─── Asosiy ishga tushirish ───────────────────────────────────
def main():
    if TELEGRAM_TOKEN == "YOUR_TELEGRAM_TOKEN":
        print("❌ XATO: TELEGRAM_TOKEN o'rnatilmagan!")
        print("   export TELEGRAM_TOKEN='your_bot_token'")
        return
    if ANTHROPIC_KEY == "YOUR_ANTHROPIC_KEY":
        print("❌ XATO: ANTHROPIC_API_KEY o'rnatilmagan!")
        print("   export ANTHROPIC_API_KEY='your_api_key'")
        return

    print("✅ MChJ Ustav Tekshiruvchi Bot ishga tushmoqda...")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Handlerlar
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CommandHandler("about", cmd_about))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.ALL, handle_unknown))

    print("🤖 Bot tayyor! Telegram'da /start bosing.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
