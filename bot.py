import os
import re
import html
import sqlite3
import logging
from urllib.parse import quote
from datetime import datetime

import telebot
from telebot import types

from news_module import (
    init_news_db,
    handle_listing_published,
    start_news_worker,
)


# ============================================================
# НАСТРОЙКИ
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

ADMIN_ID = int(os.getenv("ADMIN_ID", "7419021481"))

GROUP_ID_RAW = os.getenv("GROUP_ID", "-1004362264263").strip()
GROUP_ID = int(GROUP_ID_RAW) if GROUP_ID_RAW else None

CHANNEL_ID_RAW = os.getenv("CHANNEL_ID", "").strip()
CHANNEL_ID = int(CHANNEL_ID_RAW) if CHANNEL_ID_RAW else None

CHANNEL_USERNAME = os.getenv(
    "CHANNEL_USERNAME",
    "VFM_D"
).strip().lstrip("@")

BOT_USERNAME = os.getenv(
    "BOT_USERNAME",
    ""
).strip().lstrip("@")

SUPPORT_USERNAME = os.getenv(
    "SUPPORT_USERNAME",
    ""
).strip().lstrip("@")

DB_PATH = os.getenv("DB_PATH", "vitrina.db")


if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN не установлен в Environment Variables Render."
    )


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# BOT
# ============================================================

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)


# ============================================================
# STATES
# ============================================================

states = {}
support_replies = {}


# ============================================================
# TEXT
# ============================================================

TEXT = {
    "ru": {
        "welcome": (
            "👋 <b>Добро пожаловать в Vitrina Freelance MD!</b>\n\n"
            "Здесь можно найти специалиста или предложить свои услуги."
        ),

        "choose_ad_type": "Выберите тип объявления:",

        "need_specialist": "🔎 Мне нужен специалист",
        "offer_service": "👨‍💻 Предлагаю свои услуги",

        "need_one_message": (
            "📝 <b>Напишите объявление одним сообщением.</b>\n\n"
            "Просто расскажите:\n"
            "• что нужно сделать;\n"
            "• город;\n"
            "• бюджет;\n"
            "• сроки;\n"
            "• опыт или требования;\n"
            "• дополнительную информацию.\n\n"
            "Я автоматически определю категорию и основные данные."
        ),

        "offer_one_message": (
            "📝 <b>Напишите о своей услуге одним сообщением.</b>\n\n"
            "Например:\n"
            "• какую услугу предлагаете;\n"
            "• город;\n"
            "• цена;\n"
            "• опыт;\n"
            "• портфолио;\n"
            "• дополнительные условия.\n\n"
            "Я автоматически подготовлю объявление."
        ),

        "preview": "👀 <b>Предпросмотр объявления</b>\n\n",

        "edit": "✏️ Изменить",
        "add_photo": "📷 Добавить фото",
        "delete_photo": "🗑 Удалить фото",
        "publish": "✅ Отправить на модерацию",
        "cancel": "❌ Отменить",

        "choose_edit": "Что хотите изменить?",

        "edit_title": "Введите новый заголовок:",
        "edit_description": "Введите новое описание:",
        "edit_budget": "Введите новый бюджет:",
        "edit_city": "Введите новый город:",
        "edit_deadline": "Введите новый срок:",
        "edit_experience": "Введите информацию об опыте:",
        "edit_portfolio": "Введите ссылку на портфолио:",
        "edit_contact": (
            "Введите Telegram username для связи.\n"
            "Например: @username"
        ),

        "choose_category": "Выберите категорию:",

        "send_photo": "Отправьте фотографию объявления.",
        "photo_added": "📷 Фото добавлено.",
        "photo_deleted": "Фото удалено.",

        "cancelled": "❌ Создание объявления отменено.",

        "sent_moderation": (
            "✅ Объявление отправлено на модерацию.\n\n"
            "После проверки оно появится в канале."
        ),

        "published": (
            "📢 <b>Объявление опубликовано в канале!</b>"
        ),

        "rejected": (
            "❌ Ваше объявление не прошло модерацию."
        ),

        "find": "🔎 Найти объявление",
        "mine": "📋 Мои объявления",
        "about": "ℹ️ О проекте",
        "support": "🆘 Поддержка",
        "language": "🌐 Язык",

        "submit_ad": "➕ Подать объявление",
        "invite": "👥 Пригласить друзей",

        "search_prompt": (
            "🔎 Напишите, что вы ищете.\n\n"
            "Например:\n"
            "<i>дизайнер</i>\n"
            "<i>монтажник Кишинёв</i>\n"
            "<i>создание сайта</i>"
        ),

        "nothing_found": "Ничего подходящего не найдено.",

        "my_empty": "У вас пока нет объявлений.",

        "support_prompt": (
            "🆘 Напишите свой вопрос одним сообщением."
        ),

        "support_sent": (
            "✅ Сообщение отправлено администратору."
        ),

        "admin_new": "🆕 <b>Новое объявление на модерации</b>",

        "approve": "✅ Одобрить",
        "reject": "❌ Отклонить",

        "approved_admin": "✅ Опубликовано",
        "rejected_admin": "❌ Отклонено",

        "contact_seller": "💬 Связаться с продавцом",

        "submit_again": "➕ Подать объявление",

        "contact_request": (
            "📩 <b>Новый запрос по вашему объявлению!</b>\n\n"
            "Пользователь хочет связаться с вами."
        ),

        "no_contact": (
            "У вас не указан Telegram username.\n"
            "Пожалуйста, укажите его для связи."
        ),

        "invalid_photo": "Пожалуйста, отправьте фотографию.",

        "invalid_text": "Пожалуйста, отправьте текст.",

        "language_changed": "Язык изменён.",

        "about_text": (
            "ℹ️ <b>Vitrina Freelance MD</b>\n\n"
            "Площадка для поиска специалистов и размещения услуг "
            "в Молдове."
        ),
    },

    "ro": {
        "welcome": (
            "👋 <b>Bun venit la Vitrina Freelance MD!</b>\n\n"
            "Aici poți găsi un specialist sau îți poți oferi serviciile."
        ),

        "choose_ad_type": "Alege tipul anunțului:",

        "need_specialist": "🔎 Am nevoie de un specialist",
        "offer_service": "👨‍💻 Ofer servicii",

        "need_one_message": (
            "📝 <b>Scrie anunțul într-un singur mesaj.</b>\n\n"
            "Spune ce trebuie făcut, orașul, bugetul și termenul."
        ),

        "offer_one_message": (
            "📝 <b>Scrie despre serviciul tău într-un singur mesaj.</b>\n\n"
            "Spune ce serviciu oferi, orașul, prețul și experiența."
        ),

        "preview": "👀 <b>Previzualizarea anunțului</b>\n\n",

        "edit": "✏️ Modifică",
        "add_photo": "📷 Adaugă fotografie",
        "delete_photo": "🗑 Șterge fotografia",
        "publish": "✅ Trimite pentru moderare",
        "cancel": "❌ Anulează",

        "choose_edit": "Ce dorești să modifici?",

        "edit_title": "Introdu noul titlu:",
        "edit_description": "Introdu noua descriere:",
        "edit_budget": "Introdu noul buget:",
        "edit_city": "Introdu noul oraș:",
        "edit_deadline": "Introdu noul termen:",
        "edit_experience": "Introdu experiența:",
        "edit_portfolio": "Introdu linkul portofoliului:",
        "edit_contact": "Introdu username-ul Telegram:",

        "choose_category": "Alege categoria:",

        "send_photo": "Trimite fotografia anunțului.",
        "photo_added": "📷 Fotografia a fost adăugată.",
        "photo_deleted": "Fotografia a fost ștearsă.",

        "cancelled": "❌ Crearea anunțului a fost anulată.",

        "sent_moderation": (
            "✅ Anunțul a fost trimis pentru moderare."
        ),

        "published": (
            "📢 <b>Anunțul a fost publicat pe canal!</b>"
        ),

        "rejected": "❌ Anunțul nu a trecut moderarea.",

        "find": "🔎 Găsește un anunț",
        "mine": "📋 Anunțurile mele",
        "about": "ℹ️ Despre proiect",
        "support": "🆘 Suport",
        "language": "🌐 Limbă",

        "submit_ad": "➕ Publică un anunț",
        "invite": "👥 Invită prieteni",

        "search_prompt": "🔎 Scrie ce cauți.",

        "nothing_found": "Nu au fost găsite rezultate.",

        "my_empty": "Nu ai încă anunțuri.",

        "support_prompt": "🆘 Scrie întrebarea ta.",

        "support_sent": "✅ Mesajul a fost trimis administratorului.",

        "admin_new": "🆕 <b>Anunț nou pentru moderare</b>",

        "approve": "✅ Aprobă",
        "reject": "❌ Respinge",

        "approved_admin": "✅ Publicat",
        "rejected_admin": "❌ Respins",

        "contact_seller": "💬 Contactează vânzătorul",

        "submit_again": "➕ Publică un anunț",

        "contact_request": (
            "📩 <b>Cerere nouă pentru anunțul tău!</b>"
        ),

        "no_contact": (
            "Nu ai username Telegram. "
            "Introdu-l pentru contact."
        ),

        "invalid_photo": "Trimite o fotografie.",

        "invalid_text": "Trimite un text.",

        "language_changed": "Limba a fost schimbată.",

        "about_text": (
            "ℹ️ <b>Vitrina Freelance MD</b>\n\n"
            "Platformă pentru găsirea specialiștilor și "
            "promovarea serviciilor în Moldova."
        ),
    }
}


# ============================================================
# CATEGORIES
# ============================================================

CATEGORIES = [
    ("design", "🎨 Дизайн / Design"),
    ("programming", "💻 IT / Programare"),
    ("marketing", "📣 Маркетинг / Marketing"),
    ("photo_video", "📷 Фото / Video"),
    ("text", "✍️ Тексты / Texte"),
    ("translation", "🌍 Переводы / Traduceri"),
    ("construction", "🔨 Ремонт / Construcții"),
    ("transport", "🚚 Транспорт / Transport"),
    ("beauty", "💇 Красота / Frumusețe"),
    ("other", "📦 Другое / Altele"),
]


CATEGORY_KEYWORDS = {
    "design": [
        "дизайн",
        "дизайнер",
        "логотип",
        "баннер",
        "банер",
        "визитка",
        "макет",
        "design",
        "designer",
        "logo",
    ],

    "programming": [
        "программист",
        "программирование",
        "сайт",
        "сайта",
        "бот",
        "telegram bot",
        "python",
        "код",
        "разработка",
        "developer",
        "programare",
        "programator",
    ],

    "marketing": [
        "маркетинг",
        "реклама",
        "таргет",
        "smm",
        "seo",
        "продвижение",
        "рекламная",
        "marketing",
    ],

    "photo_video": [
        "фото",
        "фотограф",
        "видео",
        "видеограф",
        "монтаж видео",
        "съемка",
        "съёмка",
        "photo",
        "video",
    ],

    "text": [
        "копирайтинг",
        "копирайтер",
        "текст",
        "статья",
        "пост",
        "контент",
        "редактор",
        "тексты",
    ],

    "translation": [
        "перевод",
        "перевести",
        "переводчик",
        "русский",
        "румынский",
        "английский",
        "украинский",
        "translation",
        "traducere",
    ],

    "construction": [
        "ремонт",
        "строитель",
        "строительство",
        "маляр",
        "штукатур",
        "плиточник",
        "электрик",
        "сантехник",
        "монтажник",
        "гипсокартон",
        "construcții",
        "zugrav",
    ],

    "transport": [
        "водитель",
        "перевозка",
        "такси",
        "доставка",
        "груз",
        "машина",
        "автомобиль",
        "курьер",
        "transport",
        "șofer",
    ],

    "beauty": [
        "парикмахер",
        "маникюр",
        "педикюр",
        "визажист",
        "косметолог",
        "бровист",
        "ресницы",
        "красота",
        "beauty",
        "маникюра",
        "маникюрист",
        "мастер маникюра",
        "nail",
        "coafor",
        "frumusețe",
        "frumusete",
    ],
}


CITY_ALIASES = {
    "кишинев": "Кишинёв",
    "кишинёв": "Кишинёв",
    "chisinau": "Chișinău",
    "chișinău": "Chișinău",
    "бэлць": "Бельцы",
    "бельцы": "Бельцы",
    "balti": "Bălți",
    "бендеры": "Бендеры",
    "тирасполь": "Тирасполь",
    "tiraspol": "Tiraspol",
    "комрат": "Комрат",
    "comrat": "Comrat",
    "кагул": "Кагул",
    "cahul": "Cahul",
    "оргеев": "Оргеев",
    "orhei": "Orhei",
    "сороки": "Сороки",
    "soroca": "Soroca",
}


# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            language TEXT DEFAULT 'ru',
            created_at TEXT
        )
    """)

    # Growth v1: referral tracking. Safe migration for existing databases.
    user_columns = {row[1] for row in cur.execute("PRAGMA table_info(users)").fetchall()}
    if "referred_by" not in user_columns:
        cur.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            invited_user_id INTEGER PRIMARY KEY,
            referrer_user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            title TEXT,
            category TEXT,
            budget TEXT,
            city TEXT,
            deadline TEXT,
            description TEXT,
            experience TEXT,
            portfolio TEXT,
            photo_id TEXT,
            contact TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            published_message_id INTEGER
        )
    """)

    # Growth v1.1: phone number extracted from listing text.
    listing_columns = {row[1] for row in cur.execute("PRAGMA table_info(listings)").fetchall()}
    if "phone" not in listing_columns:
        cur.execute("ALTER TABLE listings ADD COLUMN phone TEXT")

    conn.commit()
    conn.close()


def current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================================
# USERS / LANGUAGE
# ============================================================

def save_user(user):
    conn = get_db()

    username = user.username or ""
    first_name = user.first_name or ""

    existing = conn.execute(
        "SELECT user_id FROM users WHERE user_id = ?",
        (user.id,)
    ).fetchone()

    if existing:
        conn.execute(
            """
            UPDATE users
            SET first_name = ?, username = ?
            WHERE user_id = ?
            """,
            (first_name, username, user.id)
        )
    else:
        language = "ru"

        if user.language_code:
            if user.language_code.lower().startswith("ro"):
                language = "ro"

        conn.execute(
            """
            INSERT INTO users
            (user_id, first_name, username, language, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user.id,
                first_name,
                username,
                language,
                current_time()
            )
        )

    conn.commit()
    conn.close()


def get_language(user_id):
    conn = get_db()

    row = conn.execute(
        "SELECT language FROM users WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    conn.close()

    if row and row["language"] in TEXT:
        return row["language"]

    return "ru"


def set_language(user_id, language):
    if language not in TEXT:
        return

    conn = get_db()

    conn.execute(
        "UPDATE users SET language = ? WHERE user_id = ?",
        (language, user_id)
    )

    conn.commit()
    conn.close()


def tr(user_id, key):
    language = get_language(user_id)
    return TEXT.get(language, TEXT["ru"]).get(
        key,
        TEXT["ru"].get(key, key)
    )


# ============================================================
# MAIN MENU
# ============================================================

def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        types.KeyboardButton(tr(user_id, "submit_ad"))
    )

    markup.row(
        types.KeyboardButton(tr(user_id, "find")),
        types.KeyboardButton(tr(user_id, "mine"))
    )

    markup.row(
        types.KeyboardButton(tr(user_id, "about")),
        types.KeyboardButton(tr(user_id, "support"))
    )

    markup.row(
        types.KeyboardButton(tr(user_id, "invite")),
        types.KeyboardButton(tr(user_id, "language"))
    )

    return markup


def cancel_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )

    markup.add(
        types.KeyboardButton(tr(user_id, "cancel"))
    )

    return markup


# ============================================================
# INLINE KEYBOARDS
# ============================================================

def ad_type_keyboard(user_id):
    markup = types.InlineKeyboardMarkup()

    markup.row(
        types.InlineKeyboardButton(
            tr(user_id, "need_specialist"),
            callback_data="quick_kind:order"
        )
    )

    markup.row(
        types.InlineKeyboardButton(
            tr(user_id, "offer_service"),
            callback_data="quick_kind:service"
        )
    )

    return markup


def category_keyboard():
    markup = types.InlineKeyboardMarkup()

    row = []

    for key, label in CATEGORIES:
        row.append(
            types.InlineKeyboardButton(
                label,
                callback_data=f"category:{key}"
            )
        )

        if len(row) == 2:
            markup.row(*row)
            row = []

    if row:
        markup.row(*row)

    return markup


def preview_keyboard(user_id, has_photo=False):
    markup = types.InlineKeyboardMarkup()

    markup.row(
        types.InlineKeyboardButton(
            tr(user_id, "edit"),
            callback_data="edit_menu"
        )
    )

    if has_photo:
        markup.row(
            types.InlineKeyboardButton(
                tr(user_id, "delete_photo"),
                callback_data="delete_photo"
            )
        )
    else:
        markup.row(
            types.InlineKeyboardButton(
                tr(user_id, "add_photo"),
                callback_data="add_photo"
            )
        )

    markup.row(
        types.InlineKeyboardButton(
            tr(user_id, "publish"),
            callback_data="submit_listing"
        )
    )

    markup.row(
        types.InlineKeyboardButton(
            tr(user_id, "cancel"),
            callback_data="cancel_form"
        )
    )

    return markup


def edit_keyboard(user_id):
    markup = types.InlineKeyboardMarkup()

    fields = [
        ("title", "Заголовок"),
        ("description", "Описание"),
        ("category", "Категория"),
        ("budget", "Бюджет"),
        ("city", "Город"),
        ("deadline", "Срок"),
        ("experience", "Опыт"),
        ("portfolio", "Портфолио"),
        ("contact", "Контакт"),
    ]

    for key, label in fields:
        markup.add(
            types.InlineKeyboardButton(
                label,
                callback_data=f"edit_field:{key}"
            )
        )

    markup.add(
        types.InlineKeyboardButton(
            "↩️ Назад",
            callback_data="back_preview"
        )
    )

    return markup


def admin_keyboard(listing_id):
    markup = types.InlineKeyboardMarkup()

    markup.row(
        types.InlineKeyboardButton(
            "✅ Одобрить",
            callback_data=f"admin:approve:{listing_id}"
        ),
        types.InlineKeyboardButton(
            "❌ Отклонить",
            callback_data=f"admin:reject:{listing_id}"
        )
    )

    return markup


# ============================================================
# PARSER
# ============================================================

def detect_category(text):
    """Rule-based Parser v2: phrases + word stems, RU/RO, no external AI."""
    normalized = re.sub(r"\s+", " ", text.lower().replace("ё", "е")).strip()

    # Strong profession/service patterns. They are checked before generic words
    # so phrases such as "мастер массажа" cannot fall into "Другое".
    strong_patterns = {
        "beauty": [
            r"\bмассаж(?:ист|иста|истка|а|ный|истом)?\b", r"\bманикюр\w*\b",
            r"\bпедикюр\w*\b", r"\bпарикмахер\w*\b", r"\bбарбер\w*\b",
            r"\bвизажист\w*\b", r"\bкосметолог\w*\b", r"\bбровист\w*\b",
            r"\bресниц\w*\b", r"\bэпиляц\w*\b", r"\bдепиляц\w*\b",
            r"\bstilist\w*\b", r"\bcoafor\w*\b", r"\bmanichiur\w*\b",
            r"\bpedichiur\w*\b", r"\bmasaj\w*\b", r"\bcosmetolog\w*\b",
        ],
        "construction": [
            r"\bсантех\w*\b", r"\bэлектрик\w*\b", r"\bплиточ\w*\b",
            r"\bстроит\w*\b", r"\bремонт\w*\b", r"\bмаляр\w*\b",
            r"\bштукатур\w*\b", r"\bгипсокартон\w*\b", r"\bсварщик\w*\b",
            r"\bкровел\w*\b", r"\bмебел\w*\b", r"\bzugrav\w*\b",
            r"\belectrician\w*\b", r"\binstalator\w*\b", r"\bconstruct\w*\b",
        ],
        "transport": [
            r"\bводител\w*\b", r"\bкурьер\w*\b", r"\bтакси\w*\b",
            r"\bперевоз\w*\b", r"\bдостав\w*\b", r"\bгрузчик\w*\b",
            r"\bsofer\w*\b", r"\bșofer\w*\b", r"\bcurier\w*\b",
            r"\btransport\w*\b",
        ],
        "programming": [
            r"\bпрограммист\w*\b", r"\bразработчик\w*\b", r"\bdeveloper\w*\b",
            r"\bprogramator\w*\b", r"\bpython\b", r"\bjavascript\b",
            r"\bfrontend\b", r"\bbackend\b", r"\bвеб[- ]?разработ\w*\b",
            r"\btelegram[- ]?бот\w*\b", r"\bсоздан\w* сайта\b",
        ],
        "design": [
            r"\bдизайнер\w*\b", r"\bдизайн\w*\b", r"\blogo\b",
            r"\bлоготип\w*\b", r"\bdesigner\w*\b", r"\bgrafic\w*\b",
        ],
        "marketing": [
            r"\bмаркетолог\w*\b", r"\bмаркетинг\w*\b", r"\bsmm\b",
            r"\bтаргетолог\w*\b", r"\bseo\b", r"\bmarketing\w*\b",
        ],
        "photo_video": [
            r"\bфотограф\w*\b", r"\bвидеограф\w*\b", r"\bфотосъем\w*\b",
            r"\bфотосъём\w*\b", r"\bвидеосъем\w*\b", r"\bvideo\w*\b",
        ],
        "translation": [
            r"\bпереводчик\w*\b", r"\bперевод\w* текст\w*\b",
            r"\btranslator\w*\b", r"\btraducator\w*\b", r"\btraducător\w*\b",
        ],
        "text": [
            r"\bкопирайтер\w*\b", r"\bкопирайтинг\w*\b", r"\bредактор\w*\b",
            r"\bcontent writer\b", r"\bcopywriter\w*\b",
        ],
    }

    for category, patterns in strong_patterns.items():
        if any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in patterns):
            return category

    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            kw = keyword.lower().replace("ё", "е").strip()
            if re.search(rf"(?<!\w){re.escape(kw)}(?!\w)", normalized, flags=re.IGNORECASE):
                score += 2 if " " in kw else 1
        if score:
            scores[category] = score

    return max(scores, key=scores.get) if scores else "other"

def category_label(category):
    for key, label in CATEGORIES:
        if key == category:
            return label

    return category


def extract_city(text):
    """Find known Moldovan cities, including common Russian/Romanian forms."""
    normalized = text.lower().replace("ё", "е")
    city_patterns = [
        (r"\bкишин(?:ев|ева|еве|евом)\b", "Кишинёв"),
        (r"\bchi(?:s|ș)in(?:a|ă)u\b", "Chișinău"),
        (r"\bбельц(?:ы|ах|ами)?\b|\bбэлць\b|\bb(?:a|ă)l(?:t|ț)i\b", "Бельцы"),
        (r"\bбендер(?:ы|ах|ами)?\b|\bbender\w*\b", "Бендеры"),
        (r"\bтираспол(?:ь|я|е|ем)\b|\btiraspol\b", "Тирасполь"),
        (r"\bкомрат(?:а|е|ом)?\b|\bcomrat\b", "Комрат"),
        (r"\bкагул(?:а|е|ом)?\b|\bcahul\b", "Кагул"),
        (r"\bоргеев(?:а|е|ом)?\b|\borhei\b", "Оргеев"),
        (r"\bсорок(?:и|ах|ами)?\b|\bsoroca\b", "Сороки"),
    ]
    for pattern, city in city_patterns:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return city

    # Fallback only for explicitly labelled city; stop at punctuation/field words.
    match = re.search(
        r"(?:город|г\.|oras|oraș)\s*[:\-]?\s*([A-Za-zА-Яа-яȘșȚțĂăÎî-]{3,25})",
        text, flags=re.IGNORECASE
    )
    return match.group(1).strip() if match else ""

def extract_budget(text):
    patterns = [
        r"(?:бюджет|цена|стоимость|оплата)\s*(?:до|от)?\s*([0-9][0-9\s.,]*)\s*(€|евро|лей|леев|mdl|lei|\$|usd)?",
        r"([0-9][0-9\s.,]*)\s*(€|евро|лей|леев|mdl|lei|\$|usd)",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:
            amount = re.sub(
                r"\s+",
                " ",
                match.group(1).strip()
            )

            currency = (
                match.group(2).strip()
                if match.group(2)
                else ""
            )

            if currency:
                return f"{amount} {currency}"

            return amount

    return ""


def extract_deadline(text):
    # ВАЖНО:
    # отдельно слово "до" НЕ считаем дедлайном,
    # иначе "бюджет до 3000 леев" ошибочно станет сроком.

    patterns = [
        r"(?:срок|сроки|дедлайн|deadline|дата)\s*[:\-]?\s*([^,\n.!?]{2,50})",
        r"(?:за|в течение)\s+([0-9]+\s*(?:дн(?:ей|я)?|день|недел(?:ю|и)?|месяц(?:а|ев)?))",
        r"(?:до|к)\s+([0-9]{1,2}[./-][0-9]{1,2}(?:[./-][0-9]{2,4})?)",
        r"(?:до|к)\s+([0-9]{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря))",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:
            value = match.group(1).strip()

            if len(value) > 60:
                value = value[:60]

            return value

    return ""


def extract_experience(text):
    """Extract only the experience value, never the following city/phone text."""
    patterns = [
        r"(?:опыт|стаж)\s*[:\-]?\s*(?:работы\s*)?(\d{1,2}\s*(?:лет|года|год|месяц(?:а|ев)?))",
        r"(\d{1,2}\s*(?:лет|года|год|месяц(?:а|ев)?))\s*(?:опыта|стажа)",
        r"(?:experien(?:t|ț)(?:a|ă)|experienta|experiența)\s*[:\-]?\s*(\d{1,2}\s*(?:ani|an|luni))",
        r"(\d{1,2}\s*(?:ani|an|luni))\s*(?:experien(?:t|ț)(?:a|ă)|experienta|experiența)",
        r"(?:работаю|работает|в профессии)\s+(?:уже\s+)?(\d{1,2}\s*(?:лет|года|год))",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return re.sub(r"\s+", " ", match.group(1).strip())
    return ""

def extract_portfolio(text):
    match = re.search(
        r"(https?://[^\s]+)",
        text,
        flags=re.IGNORECASE
    )

    if match:
        return match.group(1).rstrip(".,)")

    return ""


def extract_phone(text):
    """Extract and normalize a plausible phone number without inventing digits."""
    candidates = re.findall(r"(?<!\d)(?:\+?\d[\d\s().-]{6,}\d)(?!\d)", text)

    for raw in candidates:
        digits = re.sub(r"\D", "", raw)
        if not (8 <= len(digits) <= 15):
            continue

        # Moldova: users often write 373XXXXXXXX without the leading +.
        if digits.startswith("373") and len(digits) == 11:
            return "+" + digits
        if raw.strip().startswith("+"):
            return "+" + digits
        if len(digits) == 9 and digits.startswith("0"):
            return "+373" + digits[1:]
        if len(digits) == 8:
            return "+373" + digits

        return digits

    return ""


def extract_contact(text, user):
    match = re.search(
        r"(?<!\w)@([A-Za-z0-9_]{4,32})",
        text
    )

    if match:
        return f"@{match.group(1)}"

    if user.username:
        return f"@{user.username}"

    return ""


def make_title(text, kind):
    clean = re.sub(
        r"\s+",
        " ",
        text.strip()
    )

    clean = re.sub(
        r"^(ищу|нужен|нужна|нужно|ищем|предлагаю|оказываю|предоставляю)\s+",
        "",
        clean,
        flags=re.IGNORECASE
    )

    first_sentence = re.split(
        r"[.!?\n]",
        clean
    )[0].strip()

    if not first_sentence:
        first_sentence = clean

    if len(first_sentence) > 90:
        first_sentence = first_sentence[:87] + "..."

    return first_sentence


def parse_quick_ad(text, user, kind):
    category = detect_category(text)

    return {
        "kind": kind,
        "title": make_title(text, kind),
        "category": category,
        "budget": extract_budget(text),
        "city": extract_city(text),
        "deadline": extract_deadline(text),
        "description": text.strip(),
        "experience": extract_experience(text),
        "portfolio": extract_portfolio(text),
        "photo_id": None,
        "phone": extract_phone(text),
        "contact": extract_contact(text, user),
    }


# ============================================================
# FORMATTING
# ============================================================

def preview_text(user_id, data):
    kind_text = (
        "🔎 Нужен специалист"
        if data.get("kind") == "order"
        else "👨‍💻 Предлагаю услугу"
    )

    category = data.get("category") or "other"

    lines = [
        tr(user_id, "preview"),
        f"📌 <b>{html.escape(data.get('title') or 'Без названия')}</b>",
        "",
        kind_text,
        f"📂 <b>Категория:</b> {html.escape(category_label(category))}",
    ]

    if data.get("budget"):
        lines.append(
            f"💰 <b>Бюджет:</b> {html.escape(data['budget'])}"
        )

    if data.get("city"):
        lines.append(
            f"📍 <b>Город:</b> {html.escape(data['city'])}"
        )

    if data.get("deadline"):
        lines.append(
            f"⏱ <b>Срок:</b> {html.escape(data['deadline'])}"
        )

    if data.get("experience"):
        lines.append(
            f"⭐ <b>Опыт:</b> {html.escape(data['experience'])}"
        )

    if data.get("phone"):
        lines.append(
            f"📞 <b>Телефон:</b> {html.escape(data['phone'])}"
        )

    lines.extend([
        "",
        "📝 <b>Описание:</b>",
        html.escape(data.get("description") or ""),
    ])

    if data.get("portfolio"):
        lines.extend([
            "",
            f"🔗 <b>Портфолио:</b> "
            f"{html.escape(data['portfolio'])}"
        ])

    if data.get("contact"):
        lines.extend([
            "",
            f"👤 <b>Контакт:</b> "
            f"{html.escape(data['contact'])}"
        ])

    return "\n".join(lines)


CATEGORY_HASHTAGS = {
    "design": "#Дизайн",
    "programming": "#IT",
    "marketing": "#Маркетинг",
    "photo_video": "#ФотоВидео",
    "text": "#Тексты",
    "translation": "#Переводы",
    "construction": "#Ремонт",
    "transport": "#Транспорт",
    "beauty": "#Красота",
    "other": "#Услуги",
}

def listing_hashtags(row):
    tags = [CATEGORY_HASHTAGS.get(row["category"] or "other", "#Услуги")]
    if row["kind"] == "order":
        tags.append("#ИщуСпециалиста")
    else:
        tags.append("#ПредлагаюУслуги")
    city = (row["city"] or "").lower()
    if "кишин" in city or "chișinău" in city or "chisinau" in city:
        tags.append("#Кишинёв")
    tags.append("#VitrinaMD")
    return " ".join(tags)


def render_public_text(row, description=None):
    kind_text = (
        "🔎 Ищу специалиста"
        if row["kind"] == "order"
        else "👨‍💻 Предлагаю услугу"
    )

    title = html.escape(
        row["title"] or "Без названия"
    )

    category = html.escape(
        category_label(row["category"] or "other")
    )

    lines = [
        f"📌 <b>{title}</b>",
        "",
        kind_text,
        f"📂 <b>Категория:</b> {category}",
    ]

    if row["budget"]:
        lines.append(
            f"💰 <b>Бюджет:</b> "
            f"{html.escape(row['budget'])}"
        )

    if row["city"]:
        lines.append(
            f"📍 <b>Город:</b> "
            f"{html.escape(row['city'])}"
        )

    if row["deadline"]:
        lines.append(
            f"⏱ <b>Срок:</b> "
            f"{html.escape(row['deadline'])}"
        )

    if row["experience"]:
        lines.append(
            f"⭐ <b>Опыт:</b> "
            f"{html.escape(row['experience'])}"
        )

    if "phone" in row.keys() and row["phone"]:
        lines.append(
            f"📞 <b>Телефон:</b> {html.escape(row['phone'])}"
        )

    if description:
        lines.extend([
            "",
            "📝 <b>Описание:</b>",
            html.escape(description),
        ])

    if row["portfolio"]:
        lines.extend([
            "",
            f"🔗 <b>Портфолио:</b> "
            f"{html.escape(row['portfolio'])}"
        ])

    lines.extend([
        "",
        listing_hashtags(row),
        "",
        "📢 <b>Vitrina Freelance MD</b>",
        "📤 Знаете подходящего человека? Поделитесь объявлением.",
    ])

    return "\n".join(lines)


def build_public_text(row, limit=4096):
    description = row["description"] or ""

    full = render_public_text(
        row,
        description
    )

    if len(full) <= limit:
        return full

    # Ищем максимальную длину описания,
    # которая помещается в Telegram.
    low = 0
    high = len(description)
    best = render_public_text(row, "")

    while low <= high:
        mid = (low + high) // 2

        candidate_description = description[:mid]

        if mid < len(description):
            candidate_description += "…"

        candidate = render_public_text(
            row,
            candidate_description
        )

        if len(candidate) <= limit:
            best = candidate
            low = mid + 1
        else:
            high = mid - 1

    return best


# ============================================================
# CHANNEL
# ============================================================

def get_channel_target():
    if CHANNEL_ID:
        return CHANNEL_ID

    if CHANNEL_USERNAME:
        return f"@{CHANNEL_USERNAME}"

    return None


def publish_keyboard(row, message_id=None):
    markup = types.InlineKeyboardMarkup()

    username = (
        row["username"]
        if "username" in row.keys()
        else ""
    )

    if username:
        username = username.lstrip("@")

        markup.add(
            types.InlineKeyboardButton(
                "💬 Связаться с продавцом",
                url=f"https://t.me/{username}"
            )
        )

    elif BOT_USERNAME:
        markup.add(
            types.InlineKeyboardButton(
                "💬 Связаться с продавцом",
                url=(
                    f"https://t.me/{BOT_USERNAME}"
                    f"?start=contact_{row['id']}"
                )
            )
        )

    if BOT_USERNAME:
        markup.add(
            types.InlineKeyboardButton(
                "➕ Подать объявление",
                url=f"https://t.me/{BOT_USERNAME}?start=post"
            )
        )

    if message_id and CHANNEL_USERNAME:
        post_url = f"https://t.me/{CHANNEL_USERNAME}/{message_id}"
        share_url = (
            "https://t.me/share/url?url=" + quote(post_url, safe="") +
            "&text=" + quote("Посмотрите это объявление на Vitrina Freelance MD", safe="")
        )
        markup.add(
            types.InlineKeyboardButton(
                "📤 Поделиться",
                url=share_url
            )
        )

    return markup


def publish_listing(listing_id):
    target = get_channel_target()

    if not target:
        raise RuntimeError(
            "CHANNEL_USERNAME или CHANNEL_ID не установлен."
        )

    conn = get_db()

    row = conn.execute(
        """
        SELECT
            listings.*,
            users.username,
            users.first_name
        FROM listings
        LEFT JOIN users
            ON users.user_id = listings.user_id
        WHERE listings.id = ?
        """,
        (listing_id,)
    ).fetchone()

    conn.close()

    if not row:
        raise RuntimeError(
            f"Объявление #{listing_id} не найдено."
        )

    if row["published_message_id"]:
        logger.info(
            "Listing %s already published as message %s",
            listing_id,
            row["published_message_id"]
        )

        return row["published_message_id"]

    keyboard = publish_keyboard(row)

    if row["photo_id"]:
        text = build_public_text(
            row,
            limit=1024
        )

        message = bot.send_photo(
            target,
            row["photo_id"],
            caption=text,
            reply_markup=keyboard
        )

    else:
        text = build_public_text(
            row,
            limit=4096
        )

        message = bot.send_message(
            target,
            text,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )

    # Message id is known only after publication, so now add a real share link.
    try:
        bot.edit_message_reply_markup(
            chat_id=target,
            message_id=message.message_id,
            reply_markup=publish_keyboard(row, message.message_id)
        )
    except Exception as exc:
        logger.warning("Could not add share button to listing %s: %s", listing_id, exc)

    conn = get_db()

    conn.execute(
        """
        UPDATE listings
        SET published_message_id = ?
        WHERE id = ?
        """,
        (
            message.message_id,
            listing_id
        )
    )

    conn.commit()
    conn.close()

    logger.info(
        "Listing %s published to %s, message_id=%s",
        listing_id,
        target,
        message.message_id
    )

    # Учитываем только реально опубликованное объявление.
    # Повторный вызов publish_listing() не увеличит счётчик,
    # потому что выше есть ранний return при published_message_id.
    handle_listing_published(
        bot=bot,
        db_path=DB_PATH,
        channel_target=get_channel_target(),
        bot_username=BOT_USERNAME,
    )

    return message.message_id


# ============================================================
# START QUICK FORM
# ============================================================

def start_quick_form(chat_id, user_id):
    states[user_id] = {
        "mode": "quick",
        "step": "choose_kind",
        "data": {}
    }

    bot.send_message(
        chat_id,
        tr(user_id, "choose_ad_type"),
        reply_markup=ad_type_keyboard(user_id)
    )


def start_quick_form_with_kind(chat_id, user_id, kind):
    states[user_id] = {
        "mode": "quick",
        "step": "quick_text",
        "data": {
            "kind": kind
        }
    }

    key = (
        "need_one_message"
        if kind == "order"
        else "offer_one_message"
    )

    bot.send_message(
        chat_id,
        tr(user_id, key),
        reply_markup=cancel_keyboard(user_id)
    )


# ============================================================
# PREVIEW
# ============================================================

def show_preview(chat_id, user_id):
    state = states.get(user_id)

    if not state:
        return

    data = state.get("data", {})

    text = preview_text(
        user_id,
        data
    )

    has_photo = bool(
        data.get("photo_id")
    )

    if state.get("preview_message_id"):
        try:
            bot.edit_message_text(
                text,
                chat_id,
                state["preview_message_id"],
                reply_markup=preview_keyboard(
                    user_id,
                    has_photo
                )
            )
            return
        except Exception:
            pass

    message = bot.send_message(
        chat_id,
        text,
        reply_markup=preview_keyboard(
            user_id,
            has_photo
        )
    )

    state["preview_message_id"] = message.message_id


# ============================================================
# SAVE LISTING
# ============================================================

def submit_form(chat_id, user_id):
    state = states.get(user_id)

    if not state:
        return

    data = state.get("data", {})

    required = [
        data.get("title"),
        data.get("description"),
        data.get("kind"),
        data.get("category"),
    ]

    if not all(required):
        bot.send_message(
            chat_id,
            "❗ Не хватает данных для объявления."
        )
        return

    if not data.get("contact") and not data.get("phone"):
        state["step"] = "contact"

        bot.send_message(
            chat_id,
            tr(user_id, "no_contact"),
            reply_markup=cancel_keyboard(user_id)
        )

        return

    conn = get_db()

    cursor = conn.execute(
        """
        INSERT INTO listings (
            user_id,
            kind,
            title,
            category,
            budget,
            city,
            deadline,
            description,
            experience,
            portfolio,
            photo_id,
            phone,
            contact,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            data["kind"],
            data["title"],
            data["category"],
            data.get("budget", ""),
            data.get("city", ""),
            data.get("deadline", ""),
            data["description"],
            data.get("experience", ""),
            data.get("portfolio", ""),
            data.get("photo_id"),
            data.get("phone", ""),
            data.get("contact", ""),
            "pending",
            current_time()
        )
    )

    listing_id = cursor.lastrowid

    conn.commit()
    conn.close()

    send_moderation(listing_id)

    states.pop(user_id, None)

    bot.send_message(
        chat_id,
        tr(user_id, "sent_moderation"),
        reply_markup=main_menu(user_id)
    )


# ============================================================
# MODERATION
# ============================================================

def moderation_text(row):
    kind_text = (
        "🔎 Ищу специалиста"
        if row["kind"] == "order"
        else "👨‍💻 Предлагаю услугу"
    )

    lines = [
        "🆕 <b>Новое объявление на модерации</b>",
        "",
        f"🆔 ID: <code>{row['id']}</code>",
        f"👤 User ID: <code>{row['user_id']}</code>",
        "",
        f"📌 <b>{html.escape(row['title'] or '')}</b>",
        "",
        kind_text,
        f"📂 <b>Категория:</b> "
        f"{html.escape(category_label(row['category'] or 'other'))}",
    ]

    if row["budget"]:
        lines.append(
            f"💰 <b>Бюджет:</b> "
            f"{html.escape(row['budget'])}"
        )

    if row["city"]:
        lines.append(
            f"📍 <b>Город:</b> "
            f"{html.escape(row['city'])}"
        )

    if row["deadline"]:
        lines.append(
            f"⏱ <b>Срок:</b> "
            f"{html.escape(row['deadline'])}"
        )

    if row["experience"]:
        lines.append(
            f"⭐ <b>Опыт:</b> "
            f"{html.escape(row['experience'])}"
        )

    if "phone" in row.keys() and row["phone"]:
        lines.append(
            f"📞 <b>Телефон:</b> {html.escape(row['phone'])}"
        )

    lines.extend([
        "",
        "📝 <b>Описание:</b>",
        html.escape(row["description"] or ""),
    ])

    if row["portfolio"]:
        lines.extend([
            "",
            f"🔗 <b>Портфолио:</b> "
            f"{html.escape(row['portfolio'])}"
        ])

    if row["contact"]:
        lines.extend([
            "",
            f"👤 <b>Контакт:</b> "
            f"{html.escape(row['contact'])}"
        ])

    return "\n".join(lines)


def send_moderation(listing_id):
    conn = get_db()

    row = conn.execute(
        """
        SELECT
            listings.*,
            users.username,
            users.first_name
        FROM listings
        LEFT JOIN users
            ON users.user_id = listings.user_id
        WHERE listings.id = ?
        """,
        (listing_id,)
    ).fetchone()

    conn.close()

    if not row:
        return

    text = moderation_text(row)
    keyboard = admin_keyboard(listing_id)

    if row["photo_id"]:
        caption = text[:1024]

        bot.send_photo(
            ADMIN_ID,
            row["photo_id"],
            caption=caption,
            reply_markup=keyboard
        )

        if len(text) > 1024:
            bot.send_message(
                ADMIN_ID,
                text[1024:]
            )

    else:
        bot.send_message(
            ADMIN_ID,
            text[:4096],
            reply_markup=keyboard
        )


# ============================================================
# GROWTH: REFERRALS / STATS
# ============================================================

def register_referral(invited_user_id, referrer_user_id):
    if invited_user_id == referrer_user_id:
        return False
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT 1 FROM referrals WHERE invited_user_id = ?",
            (invited_user_id,)
        ).fetchone()
        if existing:
            return False
        conn.execute(
            "INSERT INTO referrals (invited_user_id, referrer_user_id, created_at) VALUES (?, ?, ?)",
            (invited_user_id, referrer_user_id, current_time())
        )
        conn.execute(
            "UPDATE users SET referred_by = ? WHERE user_id = ? AND referred_by IS NULL",
            (referrer_user_id, invited_user_id)
        )
        conn.commit()
        logger.info("Referral registered: %s -> %s", referrer_user_id, invited_user_id)
        return True
    finally:
        conn.close()

def referral_count(user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM referrals WHERE referrer_user_id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    return int(row["c"] if row else 0)

def send_referral_link(chat_id, user_id):
    if not BOT_USERNAME:
        bot.send_message(chat_id, "Ссылка приглашения временно недоступна.")
        return
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
    count = referral_count(user_id)
    bot.send_message(
        chat_id,
        "👥 <b>Пригласить друзей</b>\n\n"
        f"Ваша персональная ссылка:\n{html.escape(link)}\n\n"
        f"Приглашено: <b>{count}</b>\n\n"
        "Отправьте ссылку знакомым, которым нужны работа, клиенты или специалисты."
    )


# ============================================================
# COMMAND / START
# ============================================================

@bot.message_handler(commands=["start"])
def start_handler(message):
    save_user(message.from_user)

    user_id = message.from_user.id

    args = message.text.split(maxsplit=1)

    if len(args) > 1:
        payload = args[1].strip()

        if payload.startswith("ref_"):
            try:
                referrer_id = int(payload.split("_", 1)[1])
                register_referral(user_id, referrer_id)
            except (ValueError, TypeError):
                pass

        if payload == "post":
            start_quick_form(
                message.chat.id,
                user_id
            )
            return

        if payload.startswith("contact_"):
            try:
                listing_id = int(
                    payload.split("_", 1)[1]
                )

                handle_contact_request(
                    user_id,
                    listing_id
                )

            except Exception:
                bot.send_message(
                    message.chat.id,
                    "Не удалось открыть объявление."
                )

            return

    bot.send_message(
        message.chat.id,
        tr(user_id, "welcome"),
        reply_markup=main_menu(user_id)
    )


# ============================================================
# CONTACT REQUEST
# ============================================================

def handle_contact_request(user_id, listing_id):
    conn = get_db()

    row = conn.execute(
        """
        SELECT
            listings.*,
            users.username,
            users.first_name
        FROM listings
        LEFT JOIN users
            ON users.user_id = listings.user_id
        WHERE listings.id = ?
          AND listings.status = 'approved'
        """,
        (listing_id,)
    ).fetchone()

    requester = conn.execute(
        """
        SELECT first_name, username
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()

    conn.close()

    if not row:
        return

    seller_id = row["user_id"]

    if seller_id == user_id:
        return

    requester_name = (
        requester["first_name"]
        if requester
        else "Пользователь"
    )

    requester_username = (
        requester["username"]
        if requester and requester["username"]
        else ""
    )

    message_text = (
        "📩 <b>Новый запрос по вашему объявлению!</b>\n\n"
        f"📌 <b>{html.escape(row['title'])}</b>\n\n"
        f"👤 Имя: {html.escape(requester_name)}"
    )

    if requester_username:
        message_text += (
            f"\n🔗 Telegram: "
            f"@{html.escape(requester_username)}"
        )

    try:
        bot.send_message(
            seller_id,
            message_text
        )
    except Exception as exc:
        logger.warning(
            "Could not notify seller %s: %s",
            seller_id,
            exc
        )

    bot.send_message(
        user_id,
        "✅ Продавцу отправлено уведомление. "
        "Он сможет связаться с вами в Telegram."
    )


# ============================================================
# CALLBACK: AD TYPE
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("quick_kind:")
)
def quick_kind_callback(call):
    user_id = call.from_user.id

    save_user(call.from_user)

    kind = call.data.split(":", 1)[1]

    if kind not in ("order", "service"):
        bot.answer_callback_query(call.id)
        return

    states[user_id] = {
        "mode": "quick",
        "step": "quick_text",
        "data": {
            "kind": kind
        }
    }

    key = (
        "need_one_message"
        if kind == "order"
        else "offer_one_message"
    )

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        tr(user_id, key),
        call.message.chat.id,
        call.message.message_id
    )


# ============================================================
# CALLBACK: EDIT MENU
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "edit_menu"
)
def edit_menu_callback(call):
    user_id = call.from_user.id

    state = states.get(user_id)

    if not state:
        bot.answer_callback_query(call.id)
        return

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        tr(user_id, "choose_edit"),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=edit_keyboard(user_id)
    )


# ============================================================
# CALLBACK: EDIT FIELD
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("edit_field:")
)
def edit_field_callback(call):
    user_id = call.from_user.id

    state = states.get(user_id)

    if not state:
        bot.answer_callback_query(call.id)
        return

    field = call.data.split(":", 1)[1]

    if field == "category":
        state["step"] = "edit_category"

        bot.answer_callback_query(call.id)

        bot.edit_message_text(
            tr(user_id, "choose_category"),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=category_keyboard()
        )

        return

    if field == "photo":
        state["step"] = "edit_photo"

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            tr(user_id, "send_photo"),
            reply_markup=cancel_keyboard(user_id)
        )

        return

    valid_fields = {
        "title": "edit_title",
        "description": "edit_description",
        "budget": "edit_budget",
        "city": "edit_city",
        "deadline": "edit_deadline",
        "experience": "edit_experience",
        "portfolio": "edit_portfolio",
        "contact": "edit_contact",
    }

    if field not in valid_fields:
        bot.answer_callback_query(call.id)
        return

    state["step"] = f"edit_{field}"

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        tr(user_id, valid_fields[field]),
        reply_markup=cancel_keyboard(user_id)
    )


# ============================================================
# CALLBACK: CATEGORY
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("category:")
)
def category_callback(call):
    user_id = call.from_user.id

    state = states.get(user_id)

    if not state:
        bot.answer_callback_query(call.id)
        return

    category = call.data.split(":", 1)[1]

    valid = {
        key
        for key, _ in CATEGORIES
    }

    if category not in valid:
        bot.answer_callback_query(call.id)
        return

    state["data"]["category"] = category
    state["step"] = "preview"

    bot.answer_callback_query(call.id)

    show_preview(
        call.message.chat.id,
        user_id
    )


# ============================================================
# CALLBACK: BACK PREVIEW
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "back_preview"
)
def back_preview_callback(call):
    user_id = call.from_user.id

    if user_id not in states:
        bot.answer_callback_query(call.id)
        return

    bot.answer_callback_query(call.id)

    show_preview(
        call.message.chat.id,
        user_id
    )


# ============================================================
# CALLBACK: ADD PHOTO
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "add_photo"
)
def add_photo_callback(call):
    user_id = call.from_user.id

    state = states.get(user_id)

    if not state:
        bot.answer_callback_query(call.id)
        return

    state["step"] = "edit_photo"

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        tr(user_id, "send_photo"),
        reply_markup=cancel_keyboard(user_id)
    )


# ============================================================
# CALLBACK: DELETE PHOTO
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "delete_photo"
)
def delete_photo_callback(call):
    user_id = call.from_user.id

    state = states.get(user_id)

    if not state:
        bot.answer_callback_query(call.id)
        return

    state["data"]["photo_id"] = None

    bot.answer_callback_query(
        call.id,
        tr(user_id, "photo_deleted")
    )

    show_preview(
        call.message.chat.id,
        user_id
    )


# ============================================================
# CALLBACK: CANCEL
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "cancel_form"
)
def cancel_form_callback(call):
    user_id = call.from_user.id

    states.pop(user_id, None)

    bot.answer_callback_query(call.id)

    try:
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
        )
    except Exception:
        pass

    bot.send_message(
        call.message.chat.id,
        tr(user_id, "cancelled"),
        reply_markup=main_menu(user_id)
    )


# ============================================================
# CALLBACK: SUBMIT LISTING
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "submit_listing"
)
def submit_listing_callback(call):
    user_id = call.from_user.id

    state = states.get(user_id)

    if not state:
        bot.answer_callback_query(call.id)
        return

    bot.answer_callback_query(call.id)

    submit_form(
        call.message.chat.id,
        user_id
    )


# ============================================================
# ADMIN MODERATION
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("admin:")
)
def admin_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(
            call.id,
            "Нет доступа.",
            show_alert=True
        )
        return

    parts = call.data.split(":")

    if len(parts) != 3:
        bot.answer_callback_query(call.id)
        return

    action = parts[1]

    try:
        listing_id = int(parts[2])
    except ValueError:
        bot.answer_callback_query(call.id)
        return

    conn = get_db()

    row = conn.execute(
        """
        SELECT *
        FROM listings
        WHERE id = ?
        """,
        (listing_id,)
    ).fetchone()

    conn.close()

    if not row:
        bot.answer_callback_query(
            call.id,
            "Объявление не найдено.",
            show_alert=True
        )
        return

    if row["status"] != "pending":
        bot.answer_callback_query(
            call.id,
            "Это объявление уже обработано.",
            show_alert=True
        )
        return

    if action == "reject":
        conn = get_db()

        conn.execute(
            """
            UPDATE listings
            SET status = 'rejected'
            WHERE id = ?
            """,
            (listing_id,)
        )

        conn.commit()
        conn.close()

        try:
            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )
        except Exception:
            pass

        try:
            bot.send_message(
                row["user_id"],
                TEXT[
                    get_language(row["user_id"])
                ]["rejected"]
            )
        except Exception:
            pass

        bot.answer_callback_query(
            call.id,
            "Объявление отклонено."
        )

        return

    if action == "approve":
        try:
            message_id = publish_listing(
                listing_id
            )

            conn = get_db()

            conn.execute(
                """
                UPDATE listings
                SET status = 'approved',
                    published_message_id = ?
                WHERE id = ?
                """,
                (
                    message_id,
                    listing_id
                )
            )

            conn.commit()
            conn.close()

            try:
                bot.edit_message_reply_markup(
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=None
                )
            except Exception:
                pass

            try:
                bot.send_message(
                    row["user_id"],
                    TEXT[
                        get_language(row["user_id"])
                    ]["published"]
                )
            except Exception:
                pass

            bot.answer_callback_query(
                call.id,
                "Опубликовано."
            )

        except Exception as exc:
            logger.exception(
                "Publication error for listing %s",
                listing_id
            )

            bot.answer_callback_query(
                call.id,
                "Ошибка публикации. Проверь канал и права бота.",
                show_alert=True
            )

        return


# ============================================================
# TEXT / PHOTO INPUT
# ============================================================

@bot.message_handler(
    content_types=["text", "photo"]
)
def form_input(message):
    save_user(message.from_user)

    user_id = message.from_user.id
    chat_id = message.chat.id

    text = (
        message.text.strip()
        if message.content_type == "text"
        else ""
    )

    # --------------------------------------------------------
    # CANCEL
    # --------------------------------------------------------

    if text == tr(user_id, "cancel"):
        states.pop(user_id, None)

        bot.send_message(
            chat_id,
            tr(user_id, "cancelled"),
            reply_markup=main_menu(user_id)
        )

        return

    state = states.get(user_id)

    if not state:
        handle_menu_text(message)
        return

    # --------------------------------------------------------
    # SUPPORT
    # --------------------------------------------------------

    if state.get("mode") == "support":
        if message.content_type != "text":
            bot.send_message(
                chat_id,
                tr(user_id, "invalid_text")
            )
            return

        support_replies[user_id] = text

        bot.send_message(
            ADMIN_ID,
            (
                "🆘 <b>Новое сообщение в поддержку</b>\n\n"
                f"👤 User ID: <code>{user_id}</code>\n"
                f"💬 {html.escape(text)}"
            )
        )

        states.pop(user_id, None)

        bot.send_message(
            chat_id,
            tr(user_id, "support_sent"),
            reply_markup=main_menu(user_id)
        )

        return

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if state.get("mode") == "search":
        if message.content_type != "text":
            return

        states.pop(user_id, None)

        show_search_results(
            chat_id,
            user_id,
            text
        )

        return

    # --------------------------------------------------------
    # QUICK AD
    # --------------------------------------------------------

    if state.get("mode") != "quick":
        return

    step = state.get("step")
    data = state.get("data", {})

    # --------------------------------------------------------
    # QUICK TEXT
    # --------------------------------------------------------

    if step == "quick_text":
        if message.content_type != "text":
            bot.send_message(
                chat_id,
                tr(user_id, "invalid_text")
            )
            return

        parsed = parse_quick_ad(
            text,
            message.from_user,
            data.get("kind", "order")
        )

        state["data"] = parsed
        state["step"] = "preview"

        show_preview(
            chat_id,
            user_id
        )

        return

    # --------------------------------------------------------
    # CONTACT
    # --------------------------------------------------------

    if step == "contact":
        if message.content_type != "text":
            bot.send_message(
                chat_id,
                tr(user_id, "invalid_text")
            )
            return

        contact = text.strip()

        if contact and not contact.startswith("@"):
            if re.fullmatch(
                r"[A-Za-z0-9_]{4,32}",
                contact
            ):
                contact = "@" + contact

        data["contact"] = contact
        state["step"] = "preview"

        show_preview(
            chat_id,
            user_id
        )

        return

    # --------------------------------------------------------
    # EDIT PHOTO
    # --------------------------------------------------------

    if step == "edit_photo":
        if message.content_type != "photo":
            bot.send_message(
                chat_id,
                tr(user_id, "invalid_photo")
            )
            return

        data["photo_id"] = (
            message.photo[-1].file_id
        )

        state["step"] = "preview"

        bot.send_message(
            chat_id,
            tr(user_id, "photo_added")
        )

        show_preview(
            chat_id,
            user_id
        )

        return

    # --------------------------------------------------------
    # EDIT CATEGORY
    # --------------------------------------------------------

    if step == "edit_category":
        return

    # --------------------------------------------------------
    # EDIT FIELDS
    # --------------------------------------------------------

    if step.startswith("edit_"):
        field = step.replace(
            "edit_",
            "",
            1
        )

        if message.content_type != "text":
            bot.send_message(
                chat_id,
                tr(user_id, "invalid_text")
            )
            return

        if field in {
            "title",
            "description",
            "budget",
            "city",
            "deadline",
            "experience",
            "portfolio",
            "contact",
        }:
            data[field] = text.strip()

            state["step"] = "preview"

            show_preview(
                chat_id,
                user_id
            )

        return


# ============================================================
# MENU HANDLER
# ============================================================

def handle_menu_text(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip()

    if text == tr(user_id, "submit_ad"):
        start_quick_form(
            chat_id,
            user_id
        )
        return

    if text == tr(user_id, "find"):
        states[user_id] = {
            "mode": "search",
            "step": "search",
            "data": {}
        }

        bot.send_message(
            chat_id,
            tr(user_id, "search_prompt"),
            reply_markup=cancel_keyboard(user_id)
        )

        return

    if text == tr(user_id, "mine"):
        show_my_listings(
            chat_id,
            user_id
        )
        return

    if text == tr(user_id, "about"):
        bot.send_message(
            chat_id,
            tr(user_id, "about_text"),
            reply_markup=main_menu(user_id)
        )
        return

    if text == tr(user_id, "support"):
        states[user_id] = {
            "mode": "support",
            "step": "support",
            "data": {}
        }

        bot.send_message(
            chat_id,
            tr(user_id, "support_prompt"),
            reply_markup=cancel_keyboard(user_id)
        )

        return

    if text == tr(user_id, "invite"):
        send_referral_link(chat_id, user_id)
        return

    if text == tr(user_id, "language"):
        markup = types.InlineKeyboardMarkup()

        markup.row(
            types.InlineKeyboardButton(
                "🇷🇺 Русский",
                callback_data="lang:ru"
            ),
            types.InlineKeyboardButton(
                "🇷🇴 Română",
                callback_data="lang:ro"
            )
        )

        bot.send_message(
            chat_id,
            "🌐 Выберите язык / Alege limba:",
            reply_markup=markup
        )

        return


# ============================================================
# LANGUAGE CALLBACK
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("lang:")
)
def language_callback(call):
    language = call.data.split(":", 1)[1]

    if language not in TEXT:
        bot.answer_callback_query(call.id)
        return

    set_language(
        call.from_user.id,
        language
    )

    bot.answer_callback_query(
        call.id,
        TEXT[language]["language_changed"]
    )

    bot.send_message(
        call.message.chat.id,
        TEXT[language]["welcome"],
        reply_markup=main_menu(call.from_user.id)
    )


# ============================================================
# SEARCH
# ============================================================

def show_search_results(chat_id, user_id, query):
    query_lower = query.lower().strip()

    conn = get_db()

    rows = conn.execute(
        """
        SELECT
            listings.*,
            users.username,
            users.first_name
        FROM listings
        LEFT JOIN users
            ON users.user_id = listings.user_id
        WHERE listings.status = 'approved'
        ORDER BY listings.id DESC
        LIMIT 100
        """
    ).fetchall()

    conn.close()

    results = []

    for row in rows:
        haystack = " ".join([
            row["title"] or "",
            row["category"] or "",
            row["description"] or "",
            row["city"] or "",
            row["budget"] or "",
        ]).lower()

        words = [
            word
            for word in re.findall(
                r"\w+",
                query_lower,
                flags=re.UNICODE
            )
            if len(word) >= 2
        ]

        if not words:
            continue

        if all(word in haystack for word in words):
            results.append(row)

    if not results:
        bot.send_message(
            chat_id,
            tr(user_id, "nothing_found"),
            reply_markup=main_menu(user_id)
        )
        return

    for row in results[:10]:
        text = build_public_text(
            row,
            limit=3500
        )

        keyboard = types.InlineKeyboardMarkup()

        if row["username"]:
            username = row["username"].lstrip("@")

            keyboard.add(
                types.InlineKeyboardButton(
                    "💬 Связаться с продавцом",
                    url=f"https://t.me/{username}"
                )
            )

        elif BOT_USERNAME:
            keyboard.add(
                types.InlineKeyboardButton(
                    "💬 Связаться с продавцом",
                    url=(
                        f"https://t.me/{BOT_USERNAME}"
                        f"?start=contact_{row['id']}"
                    )
                )
            )

        try:
            if row["photo_id"]:
                bot.send_photo(
                    chat_id,
                    row["photo_id"],
                    caption=text[:1024],
                    reply_markup=keyboard
                )
            else:
                bot.send_message(
                    chat_id,
                    text,
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )
        except Exception as exc:
            logger.warning(
                "Search result send error: %s",
                exc
            )

    bot.send_message(
        chat_id,
        "🔎 Поиск завершён.",
        reply_markup=main_menu(user_id)
    )


# ============================================================
# MY LISTINGS
# ============================================================

def show_my_listings(chat_id, user_id):
    conn = get_db()

    rows = conn.execute(
        """
        SELECT *
        FROM listings
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 20
        """,
        (user_id,)
    ).fetchall()

    conn.close()

    if not rows:
        bot.send_message(
            chat_id,
            tr(user_id, "my_empty"),
            reply_markup=main_menu(user_id)
        )
        return

    for row in rows:
        status_map = {
            "pending": "⏳ На модерации",
            "approved": "✅ Опубликовано",
            "rejected": "❌ Отклонено",
        }

        status = status_map.get(
            row["status"],
            row["status"]
        )

        text = (
            f"📌 <b>{html.escape(row['title'] or '')}</b>\n"
            f"{status}\n"
            f"📂 {html.escape(category_label(row['category'] or 'other'))}"
        )

        bot.send_message(
            chat_id,
            text
        )

    bot.send_message(
        chat_id,
        "📋 Готово.",
        reply_markup=main_menu(user_id)
    )


# ============================================================
# GROWTH COMMANDS
# ============================================================

@bot.message_handler(commands=["invite"])
def invite_handler(message):
    save_user(message.from_user)
    send_referral_link(message.chat.id, message.from_user.id)


@bot.message_handler(commands=["stats"])
def stats_handler(message):
    if message.from_user.id != ADMIN_ID:
        return
    conn = get_db()
    total_users = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    users_7d = conn.execute(
        "SELECT COUNT(*) AS c FROM users WHERE datetime(created_at) >= datetime('now', '-7 days')"
    ).fetchone()["c"]
    total_listings = conn.execute("SELECT COUNT(*) AS c FROM listings").fetchone()["c"]
    published = conn.execute("SELECT COUNT(*) AS c FROM listings WHERE status = 'approved'").fetchone()["c"]
    referrals = conn.execute("SELECT COUNT(*) AS c FROM referrals").fetchone()["c"]
    top = conn.execute(
        "SELECT category, COUNT(*) AS c FROM listings WHERE status='approved' GROUP BY category ORDER BY c DESC LIMIT 3"
    ).fetchall()
    conn.close()
    top_text = ", ".join(f"{category_label(r['category'])}: {r['c']}" for r in top) or "пока нет данных"
    bot.send_message(
        message.chat.id,
        "📊 <b>Vitrina — статистика</b>\n\n"
        f"👥 Пользователей: <b>{total_users}</b>\n"
        f"🆕 Новых за 7 дней: <b>{users_7d}</b>\n"
        f"📝 Объявлений всего: <b>{total_listings}</b>\n"
        f"✅ Опубликовано: <b>{published}</b>\n"
        f"🔗 Приглашений: <b>{referrals}</b>\n\n"
        f"🔥 Популярные категории: {top_text}"
    )


# ============================================================
# ERROR HANDLER
# ============================================================

@bot.message_handler(
    commands=["id"]
)
def id_handler(message):
    bot.send_message(
        message.chat.id,
        (
            f"Chat ID: <code>{message.chat.id}</code>\n"
            f"User ID: <code>{message.from_user.id}</code>"
        )
    )


# ============================================================
# STARTUP
# ============================================================

if __name__ == "__main__":
    init_db()

    # Если BOT_USERNAME не указан в Render,
    # определяем его автоматически.
    if not BOT_USERNAME:
        try:
            me = bot.get_me()

            if me.username:
                BOT_USERNAME = me.username

                logger.info(
                    "BOT_USERNAME detected automatically: @%s",
                    BOT_USERNAME
                )

        except Exception:
            logger.exception(
                "Не удалось автоматически определить BOT_USERNAME."
            )

    channel_target = get_channel_target()

    logger.info(
        "Vitrina Freelance MD started"
    )

    logger.info(
        "GROUP_ID = %s",
        GROUP_ID
    )

    logger.info(
        "CHANNEL_USERNAME = @%s",
        CHANNEL_USERNAME
    )

    logger.info(
        "CHANNEL_TARGET = %s",
        channel_target
    )

    logger.info(
        "BOT_USERNAME = @%s",
        BOT_USERNAME
    )

    logger.info(
        "ADMIN_ID = %s",
        ADMIN_ID
    )

    # Новостной модуль работает фоновым потоком внутри этого же процесса.
    # Второй infinity_polling() не создаётся.
    init_news_db(DB_PATH)

    start_news_worker(
        bot=bot,
        db_path=DB_PATH,
        channel_target_getter=get_channel_target,
        bot_username_getter=lambda: BOT_USERNAME,
    )

    bot.infinity_polling(
        skip_pending=True,
        allowed_updates=[
            "message",
            "callback_query"
        ]
    )
