import os
import re
import html
import sqlite3
import logging
from datetime import datetime

import telebot
from telebot import types


# ============================================================
# НАСТРОЙКИ
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

ADMIN_ID = int(os.getenv("ADMIN_ID", "7419021481"))

GROUP_ID_RAW = os.getenv(
    "GROUP_ID",
    "-1004362264263"
).strip()

GROUP_ID = int(GROUP_ID_RAW) if GROUP_ID_RAW else None

SUPPORT_USERNAME = os.getenv(
    "SUPPORT_USERNAME",
    ""
).strip().lstrip("@")

BOT_USERNAME = os.getenv(
    "BOT_USERNAME",
    ""
).strip().lstrip("@")

CHANNEL_USERNAME = os.getenv(
    "CHANNEL_USERNAME",
    "vitrina_freelance_md"
).strip().lstrip("@")

DB_PATH = os.getenv(
    "DB_PATH",
    "vitrina.db"
)

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN не установлен в Environment Variables Render."
    )


# ============================================================
# ЛОГИ
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# TELEGRAM
# ============================================================

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)


# ============================================================
# СОСТОЯНИЯ
# ============================================================

states = {}

# Ответ администратора на обращение поддержки
support_replies = {}


# ============================================================
# ТЕКСТЫ
# ============================================================

TEXT = {
    "ru": {
        "welcome":
            "👋 <b>Добро пожаловать в Vitrina Freelance MD!</b>\n\n"
            "Здесь заказчики находят специалистов, "
            "а фрилансеры — новые заказы.",

        "choose": "Выберите действие:",

        "order": "📝 Разместить заказ",
        "service": "👨‍💻 Предложить свои услуги",

        "submit_ad": "➕ Подать объявление",

        "find": "🔎 Найти",
        "orders": "🔎 Найти заказ",
        "services": "👨‍💻 Найти услуги",

        "mine": "📋 Мои объявления",
        "about": "ℹ️ О проекте",
        "support": "🆘 Поддержка",
        "language": "🌐 Язык / Limba",

        "cancel": "❌ Отмена",

        "saved":
            "✅ Объявление отправлено на модерацию.\n\n"
            "После проверки администратора оно будет опубликовано.",

        "rejected":
            "❌ Ваше объявление было отклонено модератором.",

        "approved":
            "✅ Ваше объявление одобрено и опубликовано.",

        "published":
            "📢 Объявление опубликовано в группе/канале.",

        "need_title":
            "Введите <b>название</b> объявления:",

        "need_category":
            "Выберите <b>категорию</b>:",

        "need_budget":
            "Укажите <b>бюджет</b>.\n\n"
            "Например:\n"
            "• 500 €\n"
            "• 1000–1500 MDL\n"
            "• По договорённости",

        "need_price":
            "Укажите <b>цену</b>.\n\n"
            "Например:\n"
            "• От 200 €\n"
            "• 500 MDL/час\n"
            "• По договорённости",

        "need_city":
            "Укажите <b>город</b> или напишите <b>Удалённо</b>:",

        "need_deadline":
            "Укажите <b>срок выполнения</b> "
            "или напишите «не установлен»:",

        "need_description":
            "Опишите задачу или свои услуги как можно подробнее:",

        "need_experience":
            "Напишите о своём <b>опыте</b>:",

        "need_portfolio":
            "Отправьте <b>ссылку на портфолио</b> "
            "или его описание.\n\n"
            "Можно также отправить фотографию.\n\n"
            "Если портфолио нет — напишите «нет».",

        "need_contact":
            "Укажите, как с вами связаться.\n\n"
            "Например: @username или номер телефона.",

        "preview":
            "🔎 <b>Проверьте объявление</b>\n\n",

        "send":
            "📤 Отправить на модерацию",

        "edit":
            "✏️ Изменить",

        "empty":
            "Пока здесь ничего нет.",

        "choose_language":
            "Выберите язык:",

        "no_results":
            "По вашему запросу ничего не найдено.",

        "ask_search":
            "Введите слово для поиска.\n\n"
            "Например: дизайн, ремонт, перевод, "
            "программист или название города.\n\n"
            "Или нажмите «Все».",

        "all": "📋 Все",

        "my_title": "📋 <b>Ваши объявления</b>",

        "invalid":
            "Пожалуйста, введите текст или используйте кнопку.",

        "contact_author":
            "💬 Связаться с продавцом",

        "comment":
            "💬 Комментировать",

        "choose_ad_type":
            "📢 <b>Какое объявление вы хотите разместить?</b>",

        "need_one_message":
            "✍️ <b>Напишите всё об объявлении одним сообщением.</b>\n\n"
            "Например:\n\n"
            "<i>Ищу фотографа на свадьбу в Кишинёве "
            "15 октября. Бюджет до 3000 леев. "
            "Нужна съёмка с 14:00 до 22:00.</i>\n\n"
            "Я автоматически попробую определить "
            "категорию, город, бюджет и срок.",

        "photo_optional":
            "📷 Если хотите, после этого можно будет добавить фото.",

        "edit_choose":
            "✏️ <b>Что хотите изменить?</b>",

        "add_photo":
            "📷 Добавить фото",

        "replace_photo":
            "📷 Заменить фото",

        "delete_photo":
            "🗑 Удалить фото",

        "no_value":
            "Не указан",

        "support_prompt":
            "🆘 <b>Поддержка</b>\n\n"
            "Напишите вашу проблему одним сообщением.\n\n"
            "Если вопрос связан с объявлением, "
            "можете указать его номер, например <b>#125</b>.\n\n"
            "Сообщение будет передано администратору.",

        "support_sent":
            "✅ Ваше обращение отправлено администратору.\n\n"
            "Ответ придёт сюда через бота.",

        "support_answer":
            "💬 <b>Ответ поддержки</b>\n\n",

        "support_no_user":
            "Пользователь недоступен.",

        "form_closed":
            "Форма уже закрыта."
    },

    "ro": {
        "welcome":
            "👋 <b>Bine ai venit pe Vitrina Freelance MD!</b>\n\n"
            "Aici clienții găsesc specialiști, "
            "iar freelancerii găsesc proiecte noi.",

        "choose": "Alege o acțiune:",

        "order": "📝 Publică o comandă",
        "service": "👨‍💻 Oferă servicii",

        "submit_ad": "➕ Publică un anunț",

        "find": "🔎 Caută",
        "orders": "🔎 Caută comenzi",
        "services": "👨‍💻 Caută servicii",

        "mine": "📋 Anunțurile mele",
        "about": "ℹ️ Despre proiect",
        "support": "🆘 Suport",
        "language": "🌐 Limbă / Язык",

        "cancel": "❌ Anulează",

        "saved":
            "✅ Anunțul a fost trimis pentru moderare.\n\n"
            "După verificare, acesta va fi publicat.",

        "rejected":
            "❌ Anunțul tău a fost respins de moderator.",

        "approved":
            "✅ Anunțul tău a fost aprobat și publicat.",

        "published":
            "📢 Anunțul a fost publicat în grup/canal.",

        "need_title":
            "Introdu <b>titlul</b> anunțului:",

        "need_category":
            "Alege <b>categoria</b>:",

        "need_budget":
            "Indică <b>bugetul</b>.\n\n"
            "De exemplu:\n"
            "• 500 €\n"
            "• 1000–1500 MDL\n"
            "• Negociabil",

        "need_price":
            "Indică <b>prețul</b>.\n\n"
            "De exemplu:\n"
            "• De la 200 €\n"
            "• 500 MDL/oră\n"
            "• Negociabil",

        "need_city":
            "Indică <b>orașul</b> sau scrie <b>La distanță</b>:",

        "need_deadline":
            "Indică <b>termenul</b> sau scrie "
            "„nu este stabilit”:",

        "need_description":
            "Descrie proiectul sau serviciile tale "
            "cât mai detaliat:",

        "need_experience":
            "Scrie despre <b>experiența</b> ta:",

        "need_portfolio":
            "Trimite <b>linkul portofoliului</b> "
            "sau o descriere.\n\n"
            "Poți trimite și o fotografie.\n\n"
            "Dacă nu ai portofoliu — scrie „nu”.",

        "need_contact":
            "Indică modul de contact.\n\n"
            "De exemplu: @username sau număr de telefon.",

        "preview":
            "🔎 <b>Verifică anunțul</b>\n\n",

        "send":
            "📤 Trimite pentru moderare",

        "edit":
            "✏️ Modifică",

        "empty":
            "Încă nu există anunțuri aici.",

        "choose_language":
            "Alege limba:",

        "no_results":
            "Nu au fost găsite rezultate.",

        "ask_search":
            "Introdu un cuvânt pentru căutare.\n\n"
            "De exemplu: design, reparații, traduceri, "
            "programator sau un oraș.\n\n"
            "Sau apasă „Toate”.",

        "all": "📋 Toate",

        "my_title": "📋 <b>Anunțurile tale</b>",

        "invalid":
            "Te rugăm să introduci text sau să folosești butonul.",

        "contact_author":
            "💬 Contactează vânzătorul",

        "comment":
            "💬 Comentează",

        "choose_ad_type":
            "📢 <b>Ce tip de anunț vrei să publici?</b>",

        "need_one_message":
            "✍️ <b>Scrie totul despre anunț într-un singur mesaj.</b>\n\n"
            "De exemplu:\n\n"
            "<i>Caut fotograf pentru nuntă în Chișinău "
            "pe 15 octombrie. Buget până la 3000 lei.</i>\n\n"
            "Voi încerca automat să identific "
            "categoria, orașul, bugetul și termenul.",

        "photo_optional":
            "📷 După aceea poți adăuga o fotografie.",

        "edit_choose":
            "✏️ <b>Ce vrei să modifici?</b>",

        "add_photo":
            "📷 Adaugă fotografie",

        "replace_photo":
            "📷 Înlocuiește fotografia",

        "delete_photo":
            "🗑 Șterge fotografia",

        "no_value":
            "Nu este indicat",

        "support_prompt":
            "🆘 <b>Suport</b>\n\n"
            "Scrie problema într-un singur mesaj.\n\n"
            "Dacă este legată de un anunț, "
            "poți indica numărul, de exemplu <b>#125</b>.\n\n"
            "Mesajul va fi transmis administratorului.",

        "support_sent":
            "✅ Mesajul tău a fost transmis administratorului.\n\n"
            "Răspunsul va veni aici prin bot.",

        "support_answer":
            "💬 <b>Răspunsul suportului</b>\n\n",

        "support_no_user":
            "Utilizatorul nu este disponibil.",

        "form_closed":
            "Formularul este deja închis."
    }
}


# ============================================================
# КАТЕГОРИИ
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
        "дизайн", "designer", "design", "логотип", "лого",
        "баннер", "банер", "визитк", "фирменн", "ui", "ux",
        "photoshop", "figma", "illustrator"
    ],
    "programming": [
        "программист", "программирование", "сайт", "бот",
        "telegram bot", "python", "php", "javascript",
        "js", "html", "css", "it", "разработчик", "developer"
    ],
    "marketing": [
        "маркетинг", "реклама", "таргет", "smm", "seo",
        "продвижен", "instagram", "facebook", "контент"
    ],
    "photo_video": [
        "фотограф", "фото", "фотосъем", "фотосъём",
        "видео", "видеограф", "монтаж", "свадебн"
    ],
    "text": [
        "текст", "копирайт", "копирайтер", "статья",
        "описание", "рерайт", "пост", "писать"
    ],
    "translation": [
        "перевод", "перевести", "переводчик", "translation",
        "română", "румын", "русский", "английский", "англ"
    ],
    "construction": [
        "ремонт", "строитель", "строительство", "маляр",
        "штукатур", "плитк", "электрик", "сантехник",
        "гипсокартон", "бетон", "отделк"
    ],
    "transport": [
        "перевоз", "водитель", "транспорт", "доставка",
        "груз", "такси", "машина", "авто", "курьер"
    ],
    "beauty": [
        "парикмах", "маникюр", "педикюр", "макияж",
        "визаж", "косметолог", "бров", "ресниц", "beauty"
    ]
}

CITY_ALIASES = {
    "Кишинёв": [
        "кишинев", "кишинёв", "chisinau", "chișinău"
    ],
    "Бельцы": [
        "бельцы", "бэлць", "balti", "bălți"
    ],
    "Бендеры": [
        "бендер", "bender"
    ],
    "Тирасполь": [
        "тирас", "tiraspol"
    ],
    "Комрат": [
        "комрат", "comrat"
    ],
    "Кагул": [
        "кагул", "cahul"
    ],
    "Оргеев": [
        "оргеев", "orhei"
    ],
    "Сороки": [
        "сороки", "soroca"
    ],
    "Унгены": [
        "унген", "ungheni"
    ],
    "Дрокия": [
        "дрок", "drochia"
    ],
    "Рыбница": [
        "рыбниц", "rybnitsa", "rybnița"
    ]
}


# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT NOT NULL,
                username TEXT,
                language TEXT NOT NULL DEFAULT 'ru',
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                budget TEXT,
                city TEXT,
                deadline TEXT,
                description TEXT NOT NULL,
                experience TEXT,
                portfolio TEXT,
                photo_id TEXT,
                contact TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                published_message_id INTEGER
            )
        """)

        conn.commit()


def current_time():
    return datetime.utcnow().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# ============================================================
# USERS
# ============================================================

def detect_language(user):
    language = (user.language_code or "").lower()

    if language.startswith("ro"):
        return "ro"

    return "ru"


def save_user(user):
    language = detect_language(user)

    with get_db() as conn:
        conn.execute("""
            INSERT INTO users
            (
                user_id,
                first_name,
                username,
                language,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)

            ON CONFLICT(user_id)

            DO UPDATE SET
                first_name = excluded.first_name,
                username = excluded.username
        """, (
            user.id,
            user.first_name or "",
            user.username,
            language,
            current_time()
        ))

        conn.commit()


def get_language(user_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT language FROM users WHERE user_id=?",
            (user_id,)
        ).fetchone()

    if row:
        return row["language"]

    return "ru"


def set_language(user_id, language):
    if language not in ("ru", "ro"):
        return

    with get_db() as conn:
        conn.execute(
            "UPDATE users SET language=? WHERE user_id=?",
            (language, user_id)
        )
        conn.commit()


def tr(user_id, key):
    language = get_language(user_id)

    return TEXT[language].get(
        key,
        TEXT["ru"].get(key, key)
    )


# ============================================================
# HELPERS
# ============================================================

def escape(value):
    return html.escape(str(value or ""))


def main_menu(user_id):
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2
    )

    keyboard.add(
        types.KeyboardButton(
            tr(user_id, "submit_ad")
        )
    )

    keyboard.add(
        types.KeyboardButton(
            tr(user_id, "order")
        ),
        types.KeyboardButton(
            tr(user_id, "service")
        )
    )

    keyboard.add(
        types.KeyboardButton(
            tr(user_id, "find")
        ),
        types.KeyboardButton(
            tr(user_id, "mine")
        )
    )

    keyboard.add(
        types.KeyboardButton(
            tr(user_id, "about")
        ),
        types.KeyboardButton(
            tr(user_id, "support")
        )
    )

    keyboard.add(
        types.KeyboardButton(
            tr(user_id, "language")
        )
    )

    return keyboard


def cancel_keyboard(user_id):
    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            tr(user_id, "cancel"),
            callback_data="cancel_form"
        )
    )

    return keyboard


def category_keyboard(kind):
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    prefix = "order" if kind == "order" else "service"

    for key, title in CATEGORIES:
        keyboard.add(
            types.InlineKeyboardButton(
                title,
                callback_data=f"{prefix}_category:{key}"
            )
        )

    return keyboard


def find_keyboard(user_id):
    keyboard = types.InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        types.InlineKeyboardButton(
            tr(user_id, "orders"),
            callback_data="find_orders"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            tr(user_id, "services"),
            callback_data="find_services"
        )
    )

    return keyboard


# ============================================================
# НОВЫЙ РЕЖИМ ПОДАЧИ ОБЪЯВЛЕНИЯ
# ============================================================

def ad_type_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        types.InlineKeyboardButton(
            "🔴 Нужен специалист",
            callback_data="quick_kind:order"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🟢 Предлагаю услугу",
            callback_data="quick_kind:service"
        )
    )

    return keyboard


def edit_keyboard(user_id):
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    fields = [
        ("title", "📝 Название"),
        ("category", "🏷 Категория"),
        ("budget", "💰 Бюджет"),
        ("city", "📍 Город"),
        ("deadline", "📅 Срок"),
        ("description", "📄 Описание"),
        ("experience", "⭐ Опыт"),
        ("portfolio", "🔗 Портфолио"),
        ("contact", "📞 Контакт"),
    ]

    for key, label in fields:
        keyboard.add(
            types.InlineKeyboardButton(
                label,
                callback_data=f"edit_field:{key}"
            )
        )

    data = states.get(user_id, {}).get("data", {})

    if data.get("photo_id"):
        keyboard.add(
            types.InlineKeyboardButton(
                tr(user_id, "replace_photo"),
                callback_data="edit_field:photo"
            ),
            types.InlineKeyboardButton(
                tr(user_id, "delete_photo"),
                callback_data="delete_photo"
            )
        )
    else:
        keyboard.add(
            types.InlineKeyboardButton(
                tr(user_id, "add_photo"),
                callback_data="edit_field:photo"
            )
        )

    keyboard.add(
        types.InlineKeyboardButton(
            tr(user_id, "cancel"),
            callback_data="cancel_form"
        )
    )

    return keyboard


def preview_keyboard(user_id):
    keyboard = types.InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        types.InlineKeyboardButton(
            tr(user_id, "send"),
            callback_data="submit_form"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            tr(user_id, "edit"),
            callback_data="edit_form"
        )
    )

    if states.get(user_id, {}).get("data", {}).get("photo_id"):
        keyboard.add(
            types.InlineKeyboardButton(
                tr(user_id, "replace_photo"),
                callback_data="edit_field:photo"
            )
        )
    else:
        keyboard.add(
            types.InlineKeyboardButton(
                tr(user_id, "add_photo"),
                callback_data="edit_field:photo"
            )
        )

    keyboard.add(
        types.InlineKeyboardButton(
            tr(user_id, "cancel"),
            callback_data="cancel_form"
        )
    )

    return keyboard


# ============================================================
# PARSER
# ============================================================

def detect_category(text):
    lower = text.lower()

    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0

        for keyword in keywords:
            if keyword.lower() in lower:
                score += 1

        if score:
            scores[category] = score

    if not scores:
        return "other"

    return max(
        scores,
        key=scores.get
    )


def category_label(category):
    return dict(CATEGORIES).get(
        category,
        "📦 Другое / Altele"
    )


def extract_city(text):
    lower = text.lower()

    for city, aliases in CITY_ALIASES.items():
        for alias in aliases:
            if alias.lower() in lower:
                return city

    if re.search(
        r"\b(удал[её]нно|удал[её]нная работа|remote|online|онлайн)\b",
        lower
    ):
        return "Удалённо"

    return ""


def extract_budget(text):
    # Сначала ищем суммы с валютой.
    patterns = [
        r"(?:бюджет|цена|стоимость|оплата|до|от)\s*"
        r"([0-9][0-9\s.,-]{0,20})\s*"
        r"(€|евро|eur|ле[йи]|lei|mdl|\$|usd|доллар)",
        r"([0-9][0-9\s.,-]{0,20})\s*"
        r"(€|евро|eur|ле[йи]|lei|mdl|\$|usd|доллар)"
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            amount = re.sub(
                r"\s+",
                " ",
                match.group(1)
            ).strip()

            currency = match.group(2)

            return f"{amount} {currency}"

    # Бюджет без валюты
    match = re.search(
        r"(?:бюджет|цена|стоимость|оплата)\s*"
        r"(?:до|от)?\s*"
        r"([0-9][0-9\s.,-]{0,20})",
        text,
        re.IGNORECASE
    )

    if match:
        value = match.group(1).strip()

        # Не считаем датой.
        if not re.fullmatch(
            r"\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?",
            value
        ):
            return value

    if re.search(
        r"\b(по договорённости|по договоренности|договорная|negociabil)\b",
        text,
        re.IGNORECASE
    ):
        return "По договорённости"

    return ""


def extract_deadline(text):
    lower = text.lower()

    explicit = re.search(
        r"(?:срок|до|на|дата|deadline)\s*[:\-]?\s*"
        r"([0-9]{1,2}(?:[./-][0-9]{1,2})?"
        r"(?:[./-][0-9]{2,4})?"
        r"(?:\s+(?:января|февраля|марта|апреля|мая|июня|"
        r"июля|августа|сентября|октября|ноября|декабря|"
        r"октябрь|ноябрь|декабрь|октября))?)",
        lower
    )

    if explicit:
        return explicit.group(1).strip()

    phrases = [
        "сегодня",
        "завтра",
        "послезавтра",
        "на этой неделе",
        "на следующей неделе",
        "в течение недели",
        "в течение месяца",
        "срочно",
        "как можно скорее",
        "срочный заказ"
    ]

    for phrase in phrases:
        if phrase in lower:
            return phrase

    # Дата вроде 15 октября
    months = (
        "января|февраля|марта|апреля|мая|июня|июля|"
        "августа|сентября|октября|ноября|декабря"
    )

    match = re.search(
        rf"\b([0-9]{{1,2}}\s+(?:{months}))\b",
        lower
    )

    if match:
        return match.group(1)

    return ""


def extract_experience(text):
    patterns = [
        r"([0-9]+)\s*(?:лет|года|год)\s*(?:опыта|опыт)",
        r"(?:опыт|стаж)\s*[:\-]?\s*([^.!\n]{1,100})"
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(0).strip()[:300]

    return ""


def extract_portfolio(text):
    match = re.search(
        r"(https?://[^\s<>]+)",
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()[:500]

    return ""


def extract_contact(text, user):
    username = user.username

    if username:
        return f"@{username}"

    match = re.search(
        r"(?:телефон|тел|контакт|whatsapp|viber)\s*[:\-]?\s*"
        r"(\+?[0-9][0-9\s()\-]{6,20})",
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()[:100]

    match = re.search(
        r"(?<!\w)(\+373\s?[0-9]{6,8})(?!\w)",
        text
    )

    if match:
        return match.group(1).strip()

    return ""


def make_title(text, kind):
    clean = re.sub(
        r"https?://\S+",
        "",
        text
    )

    clean = re.sub(
        r"\s+",
        " ",
        clean
    ).strip()

    # Если текст начинается с "Ищу..." — превращаем в более
    # короткий заголовок.
    replacements = [
        (r"^ищу\s+", ""),
        (r"^нужен\s+", ""),
        (r"^нужна\s+", ""),
        (r"^нужно\s+", ""),
        (r"^предлагаю\s+", ""),
        (r"^оказываю\s+", ""),
        (r"^предлагаю услуги\s+", ""),
        (r"^caut\s+", ""),
        (r"^ofer\s+", "")
    ]

    title = clean

    for pattern, replacement in replacements:
        title = re.sub(
            pattern,
            replacement,
            title,
            flags=re.IGNORECASE
        )

    # Берём первое предложение.
    title = re.split(
        r"[.!?\n]",
        title
    )[0].strip()

    if not title:
        title = (
            "Нужен специалист"
            if kind == "order"
            else
            "Предлагаю услугу"
        )

    return title[:120]


def parse_quick_ad(text, kind, user):
    text = text.strip()

    category = detect_category(text)
    city = extract_city(text)
    budget = extract_budget(text)
    deadline = extract_deadline(text)
    experience = extract_experience(text)
    portfolio = extract_portfolio(text)
    contact = extract_contact(text, user)

    title = make_title(
        text,
        kind
    )

    return {
        "kind": kind,
        "title": title,
        "category": category,
        "category_label": category_label(category),
        "budget": budget,
        "city": city,
        "deadline": deadline,
        "description": text[:3000],
        "experience": experience,
        "portfolio": portfolio,
        "photo_id": None,
        "contact": contact
    }


# ============================================================
# PREVIEW
# ============================================================

def preview_text(data):
    kind_text = (
        "📝 Заказ"
        if data["kind"] == "order"
        else
        "👨‍💻 Услуга"
    )

    result = [
        f"<b>{escape(data.get('title'))}</b>",
        f"📌 Тип: {kind_text}",
        f"🏷 Категория: "
        f"{escape(data.get('category_label'))}"
    ]

    result.append(
        f"💰 "
        f"{'Бюджет' if data['kind'] == 'order' else 'Цена'}: "
        f"{escape(data.get('budget') or 'Не указан')}"
    )

    result.append(
        f"📍 {escape(data.get('city') or 'Не указан')}"
    )

    result.append(
        f"📅 Срок: "
        f"{escape(data.get('deadline') or 'Не указан')}"
    )

    if data.get("experience"):
        result.append(
            f"⭐ Опыт: "
            f"{escape(data['experience'])}"
        )

    result.append(
        f"\n📝 {escape(data.get('description'))}"
    )

    if data.get("portfolio"):
        result.append(
            f"\n🔗 Портфолио: "
            f"{escape(data['portfolio'])}"
        )

    if data.get("contact"):
        result.append(
            f"\n📞 Контакт: "
            f"{escape(data['contact'])}"
        )

    if data.get("photo_id"):
        result.append(
            "\n📷 Фото: добавлено"
        )

    return "\n".join(result)


def show_preview(chat_id, user_id):
    if user_id not in states:
        return

    data = states[user_id]["data"]

    bot.send_message(
        chat_id,
        tr(user_id, "preview")
        + preview_text(data),
        reply_markup=preview_keyboard(user_id)
    )


# ============================================================
# QUICK START
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
        reply_markup=ad_type_keyboard()
    )


@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith("quick_kind:")
)
def quick_kind_callback(call):
    user_id = call.from_user.id

    kind = call.data.split(
        ":",
        1
    )[1]

    if kind not in ("order", "service"):
        bot.answer_callback_query(
            call.id,
            "Ошибка.",
            show_alert=True
        )
        return

    states[user_id] = {
        "mode": "quick",
        "step": "quick_text",
        "data": {
            "kind": kind
        }
    }

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        tr(user_id, "need_one_message")
        + "\n\n"
        + tr(user_id, "photo_optional"),
        reply_markup=cancel_keyboard(user_id)
    )


# ============================================================
# START
# ============================================================

@bot.message_handler(commands=["start"])
def start_command(message):
    save_user(message.from_user)

    user_id = message.from_user.id

    parts = message.text.split(
        maxsplit=1
    )

    argument = (
        parts[1]
        if len(parts) > 1
        else ""
    ).strip()

    # --------------------------------------------------------
    # QUICK POST
    # --------------------------------------------------------

    if argument == "post":
        start_quick_form(
            message.chat.id,
            user_id
        )
        return

    # --------------------------------------------------------
    # CONTACT
    # --------------------------------------------------------

    if argument.startswith("contact_"):
        try:
            listing_id = int(
                argument.replace(
                    "contact_",
                    "",
                    1
                )
            )
        except ValueError:
            listing_id = None

        if listing_id:
            with get_db() as conn:
                listing = conn.execute(
                    "SELECT * FROM listings WHERE id=?",
                    (listing_id,)
                ).fetchone()

            if listing and listing["user_id"] != user_id:
                requester = (
                    f"@{message.from_user.username}"
                    if message.from_user.username
                    else
                    message.from_user.first_name
                )

                try:
                    bot.send_message(
                        listing["user_id"],
                        "💬 <b>Новый запрос на связь</b>\n\n"
                        f"Объявление: #{listing_id}\n"
                        f"От: {escape(requester)}\n\n"
                        "Вы можете открыть профиль пользователя "
                        "в Telegram и связаться с ним."
                    )

                    bot.send_message(
                        message.chat.id,
                        "✅ Запрос на связь отправлен автору.",
                        reply_markup=main_menu(user_id)
                    )

                    return

                except Exception:
                    logger.exception(
                        "Contact notification failed"
                    )

    bot.send_message(
        message.chat.id,
        tr(user_id, "welcome")
        + "\n\n"
        + tr(user_id, "choose"),
        reply_markup=main_menu(user_id)
    )


# ============================================================
# CHAT ID
# ============================================================

@bot.message_handler(commands=["id"])
def group_id_command(message):
    bot.send_message(
        message.chat.id,
        "🆔 ID этого чата:\n\n"
        f"<code>{message.chat.id}</code>"
    )


# ============================================================
# MENU
# ============================================================

@bot.message_handler(
    func=lambda message:
        message.text in [
            TEXT["ru"]["submit_ad"],
            TEXT["ro"]["submit_ad"],

            TEXT["ru"]["order"],
            TEXT["ro"]["order"],

            TEXT["ru"]["service"],
            TEXT["ro"]["service"],

            TEXT["ru"]["find"],
            TEXT["ro"]["find"],

            TEXT["ru"]["mine"],
            TEXT["ro"]["mine"],

            TEXT["ru"]["about"],
            TEXT["ro"]["about"],

            TEXT["ru"]["support"],
            TEXT["ro"]["support"],

            TEXT["ru"]["language"],
            TEXT["ro"]["language"]
        ]
)
def menu_handler(message):
    save_user(message.from_user)

    user_id = message.from_user.id
    text = message.text

    # Новый режим
    if text in (
        TEXT["ru"]["submit_ad"],
        TEXT["ro"]["submit_ad"]
    ):
        start_quick_form(
            message.chat.id,
            user_id
        )
        return

    # Старый режим — заказ
    if text in (
        TEXT["ru"]["order"],
        TEXT["ro"]["order"]
    ):
        start_form(
            message.chat.id,
            user_id,
            "order"
        )
        return

    # Старый режим — услуга
    if text in (
        TEXT["ru"]["service"],
        TEXT["ro"]["service"]
    ):
        start_form(
            message.chat.id,
            user_id,
            "service"
        )
        return

    if text in (
        TEXT["ru"]["find"],
        TEXT["ro"]["find"]
    ):
        bot.send_message(
            message.chat.id,
            tr(user_id, "choose"),
            reply_markup=find_keyboard(user_id)
        )
        return

    if text in (
        TEXT["ru"]["mine"],
        TEXT["ro"]["mine"]
    ):
        show_my_listings(
            message.chat.id,
            user_id
        )
        return

    if text in (
        TEXT["ru"]["about"],
        TEXT["ro"]["about"]
    ):
        bot.send_message(
            message.chat.id,
            "<b>Vitrina Freelance MD</b> — "
            "площадка для заказчиков и специалистов.\n\n"
            "Заказчики могут размещать задачи, "
            "а фрилансеры — предлагать свои услуги.\n\n"
            "Все объявления проходят модерацию "
            "перед публикацией.",
            reply_markup=main_menu(user_id)
        )
        return

    if text in (
        TEXT["ru"]["support"],
        TEXT["ro"]["support"]
    ):
        states[user_id] = {
            "mode": "support",
            "step": "support_text",
            "data": {}
        }

        bot.send_message(
            message.chat.id,
            tr(user_id, "support_prompt"),
            reply_markup=cancel_keyboard(user_id)
        )
        return

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton(
            "🇷🇺 Русский",
            callback_data="language:ru"
        ),
        types.InlineKeyboardButton(
            "🇷🇴 Română",
            callback_data="language:ro"
        )
    )

    bot.send_message(
        message.chat.id,
        tr(user_id, "choose_language"),
        reply_markup=keyboard
    )


# ============================================================
# LANGUAGE
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith("language:")
)
def language_callback(call):
    language = call.data.split(
        ":",
        1
    )[1]

    set_language(
        call.from_user.id,
        language
    )

    bot.answer_callback_query(
        call.id,
        "OK"
    )

    user_id = call.from_user.id

    bot.send_message(
        call.message.chat.id,
        tr(user_id, "welcome")
        + "\n\n"
        + tr(user_id, "choose"),
        reply_markup=main_menu(user_id)
    )


# ============================================================
# FIND
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data in (
            "find_orders",
            "find_services"
        )
)
def find_callback(call):
    user_id = call.from_user.id

    kind = (
        "order"
        if call.data == "find_orders"
        else
        "service"
    )

    states[user_id] = {
        "mode": "search",
        "step": "search",
        "data": {
            "kind": kind
        }
    }

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            tr(user_id, "all"),
            callback_data=f"search_all:{kind}"
        )
    )

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        tr(user_id, "ask_search"),
        reply_markup=keyboard
    )


@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith("search_all:")
)
def search_all_callback(call):
    user_id = call.from_user.id

    kind = call.data.split(
        ":",
        1
    )[1]

    states.pop(
        user_id,
        None
    )

    bot.answer_callback_query(call.id)

    show_search_results(
        call.message.chat.id,
        user_id,
        kind,
        ""
    )


def show_search_results(
    chat_id,
    user_id,
    kind,
    query
):
    search = f"%{query.lower()}%"

    with get_db() as conn:
        if query:
            rows = conn.execute("""
                SELECT *
                FROM listings
                WHERE kind=?
                AND status='approved'
                AND (
                    lower(title) LIKE ?
                    OR lower(category) LIKE ?
                    OR lower(description) LIKE ?
                    OR lower(city) LIKE ?
                )
                ORDER BY id DESC
                LIMIT 10
            """, (
                kind,
                search,
                search,
                search,
                search
            )).fetchall()
        else:
            rows = conn.execute("""
                SELECT *
                FROM listings
                WHERE kind=?
                AND status='approved'
                ORDER BY id DESC
                LIMIT 10
            """, (
                kind,
            )).fetchall()

    if not rows:
        bot.send_message(
            chat_id,
            tr(user_id, "no_results"),
            reply_markup=main_menu(user_id)
        )
        return

    for row in rows:
        type_text = (
            "📝 Заказ"
            if kind == "order"
            else
            "👨‍💻 Услуга"
        )

        text = (
            f"<b>{type_text}</b>\n\n"
            f"<b>{escape(row['title'])}</b>\n"
            f"🏷 {escape(row['category'])}\n"
        )

        if row["budget"]:
            text += f"💰 {escape(row['budget'])}\n"

        if row["city"]:
            text += f"📍 {escape(row['city'])}\n"

        text += "\n" + escape(
            row["description"][:900]
        )

        keyboard = types.InlineKeyboardMarkup()

        with get_db() as conn:
            author = conn.execute(
                """
                SELECT username
                FROM users
                WHERE user_id=?
                """,
                (row["user_id"],)
            ).fetchone()

        if author and author["username"]:
            keyboard.add(
                types.InlineKeyboardButton(
                    tr(user_id, "contact_author"),
                    url=(
                        "https://t.me/"
                        + author["username"]
                    )
                )
            )
        elif BOT_USERNAME:
            keyboard.add(
                types.InlineKeyboardButton(
                    tr(user_id, "contact_author"),
                    url=(
                        f"https://t.me/"
                        f"{BOT_USERNAME}"
                        f"?start=contact_{row['id']}"
                    )
                )
            )

        bot.send_message(
            chat_id,
            text,
            reply_markup=keyboard
        )

    bot.send_message(
        chat_id,
        tr(user_id, "choose"),
        reply_markup=main_menu(user_id)
    )


# ============================================================
# MY LISTINGS
# ============================================================

def show_my_listings(chat_id, user_id):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT *
            FROM listings
            WHERE user_id=?
            ORDER BY id DESC
            LIMIT 20
        """, (user_id,)).fetchall()

    if not rows:
        bot.send_message(
            chat_id,
            tr(user_id, "empty"),
            reply_markup=main_menu(user_id)
        )
        return

    status_names = {
        "pending": "🟡 На модерации",
        "approved": "🟢 Одобрено",
        "rejected": "🔴 Отклонено"
    }

    result = [
        tr(user_id, "my_title")
    ]

    for row in rows:
        result.append(
            f"\n#{row['id']} — "
            f"<b>{escape(row['title'])}</b>\n"
            f"{status_names.get(row['status'], row['status'])}"
        )

    bot.send_message(
        chat_id,
        "\n".join(result),
        reply_markup=main_menu(user_id)
    )


# ============================================================
# CANCEL
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "cancel_form"
)
def cancel_form(call):
    states.pop(
        call.from_user.id,
        None
    )

    support_replies.pop(
        call.from_user.id,
        None
    )

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        tr(
            call.from_user.id,
            "choose"
        ),
        reply_markup=main_menu(
            call.from_user.id
        )
    )


# ============================================================
# OLD FORM
# ============================================================

def start_form(chat_id, user_id, kind):
    states[user_id] = {
        "mode": "old",
        "step": "title",
        "data": {
            "kind": kind
        }
    }

    bot.send_message(
        chat_id,
        tr(user_id, "need_title"),
        reply_markup=cancel_keyboard(user_id)
    )


# ============================================================
# OLD FORM EDIT
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "edit_form"
)
def edit_form(call):
    user_id = call.from_user.id

    if user_id not in states:
        bot.answer_callback_query(
            call.id,
            tr(user_id, "form_closed"),
            show_alert=True
        )
        return

    states[user_id]["step"] = "edit_menu"

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        tr(user_id, "edit_choose"),
        reply_markup=edit_keyboard(user_id)
    )


@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith("edit_field:")
)
def edit_field_callback(call):
    user_id = call.from_user.id

    state = states.get(user_id)

    if not state:
        bot.answer_callback_query(
            call.id,
            tr(user_id, "form_closed"),
            show_alert=True
        )
        return

    field = call.data.split(
        ":",
        1
    )[1]

    data = state["data"]

    bot.answer_callback_query(call.id)

    if field == "category":
        state["step"] = "edit_category"

        bot.send_message(
            call.message.chat.id,
            tr(user_id, "need_category"),
            reply_markup=category_keyboard(
                data["kind"]
            )
        )
        return

    if field == "photo":
        state["step"] = "edit_photo"

        bot.send_message(
            call.message.chat.id,
            "📷 Отправьте фотографию.",
            reply_markup=cancel_keyboard(user_id)
        )
        return

    prompts = {
        "title": "need_title",
        "budget": (
            "need_budget"
            if data["kind"] == "order"
            else "need_price"
        ),
        "city": "need_city",
        "deadline": "need_deadline",
        "description": "need_description",
        "experience": "need_experience",
        "portfolio": "need_portfolio",
        "contact": "need_contact"
    }

    if field not in prompts:
        return

    state["step"] = f"edit_{field}"

    bot.send_message(
        call.message.chat.id,
        tr(user_id, prompts[field]),
        reply_markup=cancel_keyboard(user_id)
    )


@bot.callback_query_handler(
    func=lambda call:
        call.data == "delete_photo"
)
def delete_photo_callback(call):
    user_id = call.from_user.id

    if user_id not in states:
        bot.answer_callback_query(
            call.id,
            tr(user_id, "form_closed"),
            show_alert=True
        )
        return

    states[user_id]["data"]["photo_id"] = None

    bot.answer_callback_query(
        call.id,
        "Фото удалено."
    )

    show_preview(
        call.message.chat.id,
        user_id
    )


# ============================================================
# CATEGORY
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith("order_category:")
        or call.data.startswith("service_category:")
)
def category_callback(call):
    user_id = call.from_user.id

    if user_id not in states:
        bot.answer_callback_query(
            call.id,
            "Форма устарела.",
            show_alert=True
        )
        return

    category_key = call.data.split(
        ":",
        1
    )[1]

    category_label_value = dict(
        CATEGORIES
    ).get(
        category_key,
        category_key
    )

    data = states[user_id]["data"]

    data["category"] = category_key
    data["category_label"] = category_label_value

    # Если редактируем категорию — сразу назад к preview.
    if states[user_id]["step"] == "edit_category":
        states[user_id]["step"] = "preview"

        bot.answer_callback_query(call.id)

        show_preview(
            call.message.chat.id,
            user_id
        )
        return

    states[user_id]["step"] = "budget"

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        tr(
            user_id,
            "need_budget"
            if data["kind"] == "order"
            else "need_price"
        ),
        reply_markup=cancel_keyboard(user_id)
    )


# ============================================================
# PUBLIC CHANNEL URL
# ============================================================

def channel_post_url(message_id):
    if not CHANNEL_USERNAME:
        return None

    return (
        f"https://t.me/"
        f"{CHANNEL_USERNAME}/"
        f"{message_id}"
        f"?comment={message_id}"
    )


# ============================================================
# PUBLICATION
# ============================================================

def publish_listing(listing_id):
    if not GROUP_ID:
        raise RuntimeError(
            "GROUP_ID не установлен в Render."
        )

    with get_db() as conn:
        row = conn.execute("""
            SELECT
                listings.*,
                users.username
            FROM listings
            JOIN users
                ON users.user_id = listings.user_id
            WHERE listings.id=?
        """, (listing_id,)).fetchone()

    if not row:
        raise RuntimeError(
            "Объявление не найдено."
        )

    type_title = (
        "📝 ЗАКАЗ"
        if row["kind"] == "order"
        else
        "👨‍💻 УСЛУГА"
    )

    text = (
        f"<b>{type_title}</b>\n\n"
        f"<b>{escape(row['title'])}</b>\n"
        f"🏷 {escape(row['category'])}\n"
    )

    if row["budget"]:
        label = (
            "Бюджет"
            if row["kind"] == "order"
            else
            "Цена"
        )

        text += (
            f"💰 {label}: "
            f"{escape(row['budget'])}\n"
        )

    if row["city"]:
        text += (
            f"📍 {escape(row['city'])}\n"
        )

    if row["deadline"]:
        text += (
            f"📅 Срок: "
            f"{escape(row['deadline'])}\n"
        )

    if row["experience"]:
        text += (
            f"⭐ Опыт: "
            f"{escape(row['experience'])}\n"
        )

    text += (
        "\n"
        f"{escape(row['description'])}\n"
    )

    if row["portfolio"]:
        text += (
            "\n🔗 Портфолио: "
            f"{escape(row['portfolio'])}\n"
        )

    text += (
        "\n━━━━━━━━━━━━━━━━━━\n"
        "🚀 <b>Хотите разместить своё объявление?</b>\n"
        "Подайте его через нашего бота."
    )

    # Telegram ограничивает caption фото.
    # Если текст слишком большой — публикуем текст отдельно.
    if row["photo_id"] and len(text) <= 1000:
        post_message = bot.send_photo(
            GROUP_ID,
            row["photo_id"],
            caption=text
        )
    elif row["photo_id"]:
        post_message = bot.send_photo(
            GROUP_ID,
            row["photo_id"],
            caption=(
                f"<b>{escape(row['title'])}</b>\n"
                f"🏷 {escape(row['category'])}"
            )
        )

        bot.send_message(
            GROUP_ID,
            text
        )
    else:
        post_message = bot.send_message(
            GROUP_ID,
            text
        )

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    if row["username"]:
        keyboard.add(
            types.InlineKeyboardButton(
                "💬 Связаться с продавцом",
                url=(
                    "https://t.me/"
                    + row["username"]
                )
            )
        )
    elif BOT_USERNAME:
        keyboard.add(
            types.InlineKeyboardButton(
                "💬 Связаться с продавцом",
                url=(
                    f"https://t.me/"
                    f"{BOT_USERNAME}"
                    f"?start=contact_{listing_id}"
                )
            )
        )

    post_url = channel_post_url(
        post_message.message_id
    )

    if post_url:
        keyboard.add(
            types.InlineKeyboardButton(
                "💬 Комментировать",
                url=post_url
            )
        )

    if BOT_USERNAME:
        keyboard.add(
            types.InlineKeyboardButton(
                "➕ Подать объявление",
                url=(
                    f"https://t.me/"
                    f"{BOT_USERNAME}"
                    f"?start=post"
                )
            )
        )

    # Для сообщения с фото клавиатура ставится на само фото.
    try:
        bot.edit_message_reply_markup(
            GROUP_ID,
            post_message.message_id,
            reply_markup=keyboard
        )
    except Exception:
        logger.exception(
            "Could not add publication buttons"
        )

    with get_db() as conn:
        conn.execute(
            """
            UPDATE listings
            SET published_message_id=?
            WHERE id=?
            """,
            (
                post_message.message_id,
                listing_id
            )
        )
        conn.commit()

    return post_message.message_id


# ============================================================
# USER NOTIFICATION
# ============================================================

def notify_user(user_id, text):
    try:
        bot.send_message(
            user_id,
            text,
            reply_markup=main_menu(user_id)
        )
    except Exception:
        logger.exception(
            "Could not notify user %s",
            user_id
        )


# ============================================================
# ADMIN MODERATION
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith("admin_approve:")
        or
        call.data.startswith("admin_reject:")
)
def admin_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(
            call.id,
            "Нет доступа.",
            show_alert=True
        )
        return

    action, id_text = call.data.split(
        ":",
        1
    )

    try:
        listing_id = int(id_text)
    except ValueError:
        bot.answer_callback_query(
            call.id,
            "Неверный ID.",
            show_alert=True
        )
        return

    with get_db() as conn:
        listing = conn.execute(
            "SELECT * FROM listings WHERE id=?",
            (listing_id,)
        ).fetchone()

    if not listing:
        bot.answer_callback_query(
            call.id,
            "Объявление не найдено.",
            show_alert=True
        )
        return

    if listing["status"] != "pending":
        bot.answer_callback_query(
            call.id,
            "Это объявление уже обработано.",
            show_alert=True
        )
        return

    # REJECT
    if action == "admin_reject":
        with get_db() as conn:
            conn.execute(
                """
                UPDATE listings
                SET status='rejected'
                WHERE id=?
                """,
                (listing_id,)
            )
            conn.commit()

        bot.answer_callback_query(
            call.id,
            "Отклонено."
        )

        try:
            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )
        except Exception:
            logger.exception(
                "Could not remove admin buttons"
            )

        notify_user(
            listing["user_id"],
            tr(
                listing["user_id"],
                "rejected"
            )
        )
        return

    # APPROVE
    try:
        message_id = publish_listing(
            listing_id
        )

        with get_db() as conn:
            conn.execute(
                """
                UPDATE listings
                SET status='approved'
                WHERE id=?
                """,
                (listing_id,)
            )
            conn.commit()

        bot.answer_callback_query(
            call.id,
            "Опубликовано."
        )

        try:
            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )
        except Exception:
            logger.exception(
                "Could not remove admin buttons"
            )

        notify_user(
            listing["user_id"],
            tr(
                listing["user_id"],
                "approved"
            )
            + "\n"
            + tr(
                listing["user_id"],
                "published"
            )
        )

        logger.info(
            "Listing #%s published as message %s",
            listing_id,
            message_id
        )

    except Exception as error:
        logger.exception(
            "Publication failed"
        )

        bot.answer_callback_query(
            call.id,
            "Ошибка публикации.",
            show_alert=True
        )

        try:
            bot.send_message(
                ADMIN_ID,
                "⚠️ <b>Ошибка публикации</b>\n\n"
                f"Объявление: #{listing_id}\n"
                f"<code>{escape(error)}</code>"
            )
        except Exception:
            logger.exception(
                "Could not send publication error to admin"
            )


# ============================================================
# SUBMIT FORM
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "submit_form"
)
def submit_form(call):
    user_id = call.from_user.id

    state = states.get(user_id)

    if not state:
        bot.answer_callback_query(
            call.id,
            tr(user_id, "form_closed"),
            show_alert=True
        )
        return

    data = state["data"]

    # Для нового режима категория может быть не определена.
    if not data.get("category_label"):
        data["category"] = data.get(
            "category",
            "other"
        )
        data["category_label"] = category_label(
            data["category"]
        )

    # Контакт автоматически берём из Telegram.
    if not data.get("contact"):
        username = call.from_user.username

        if username:
            data["contact"] = f"@{username}"

    # Если вообще нет контакта — просим указать.
    if not data.get("contact"):
        state["step"] = "contact"

        bot.answer_callback_query(
            call.id,
            "Нужен контакт.",
            show_alert=True
        )

        bot.send_message(
            call.message.chat.id,
            tr(user_id, "need_contact"),
            reply_markup=cancel_keyboard(user_id)
        )
        return

    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO listings
            (
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
                contact,
                status,
                created_at
            )
            VALUES
            (
                ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?
            )
            """,
            (
                user_id,
                data["kind"],
                data["title"],
                data["category_label"],
                data.get("budget"),
                data.get("city"),
                data.get("deadline"),
                data["description"],
                data.get("experience"),
                data.get("portfolio"),
                data.get("photo_id"),
                data.get("contact"),
                "pending",
                current_time()
            )
        )

        listing_id = cursor.lastrowid
        conn.commit()

    states.pop(
        user_id,
        None
    )

    with get_db() as conn:
        row = conn.execute("""
            SELECT
                listings.*,
                users.first_name,
                users.username
            FROM listings
            JOIN users
                ON users.user_id = listings.user_id
            WHERE listings.id=?
        """, (listing_id,)).fetchone()

    type_title = (
        "📝 ЗАКАЗ"
        if row["kind"] == "order"
        else
        "👨‍💻 УСЛУГА"
    )

    admin_text = (
        f"<b>🆕 Новое объявление #{listing_id}</b>\n\n"
        f"{type_title}\n"
        f"<b>{escape(row['title'])}</b>\n"
        f"🏷 {escape(row['category'])}\n"
    )

    if row["budget"]:
        admin_text += (
            f"💰 {escape(row['budget'])}\n"
        )

    if row["city"]:
        admin_text += (
            f"📍 {escape(row['city'])}\n"
        )

    if row["deadline"]:
        admin_text += (
            f"📅 {escape(row['deadline'])}\n"
        )

    if row["experience"]:
        admin_text += (
            f"⭐ {escape(row['experience'])}\n"
        )

    admin_text += (
        "\n"
        f"📝 {escape(row['description'])}\n"
    )

    if row["portfolio"]:
        admin_text += (
            "\n🔗 "
            f"{escape(row['portfolio'])}\n"
        )

    admin_text += (
        "\n📞 "
        f"{escape(row['contact'] or 'Не указан')}"
    )

    admin_text += (
        "\n\n👤 "
        f"{escape(row['first_name'])}"
    )

    if row["username"]:
        admin_text += (
            f" (@{escape(row['username'])})"
        )

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton(
            "✅ Одобрить",
            callback_data=(
                f"admin_approve:{listing_id}"
            )
        ),
        types.InlineKeyboardButton(
            "❌ Отклонить",
            callback_data=(
                f"admin_reject:{listing_id}"
            )
        )
    )

    try:
        if row["photo_id"]:
            bot.send_photo(
                ADMIN_ID,
                row["photo_id"],
                caption=admin_text[:1000],
                reply_markup=keyboard
            )

            if len(admin_text) > 1000:
                bot.send_message(
                    ADMIN_ID,
                    admin_text[1000:]
                )
        else:
            bot.send_message(
                ADMIN_ID,
                admin_text,
                reply_markup=keyboard
            )

    except Exception:
        logger.exception(
            "Could not send listing to admin"
        )

        bot.send_message(
            call.message.chat.id,
            "⚠️ Объявление сохранено, "
            "но возникла ошибка отправки админу."
        )

        bot.answer_callback_query(
            call.id,
            "Ошибка отправки админу.",
            show_alert=True
        )

        return

    bot.answer_callback_query(
        call.id,
        "Отправлено."
    )

    bot.send_message(
        call.message.chat.id,
        tr(user_id, "saved"),
        reply_markup=main_menu(user_id)
    )


# ============================================================
# SUPPORT ADMIN
# ============================================================

def extract_listing_number(text):
    match = re.search(
        r"(?:#|№)\s*(\d+)",
        text
    )

    if match:
        return int(match.group(1))

    return None


def support_admin_keyboard(user_id):
    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "💬 Ответить",
            callback_data=f"support_reply:{user_id}"
        )
    )

    return keyboard


@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith("support_reply:")
)
def support_reply_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(
            call.id,
            "Нет доступа.",
            show_alert=True
        )
        return

    try:
        target_user_id = int(
            call.data.split(
                ":",
                1
            )[1]
        )
    except ValueError:
        bot.answer_callback_query(
            call.id,
            "Ошибка.",
            show_alert=True
        )
        return

    support_replies[ADMIN_ID] = target_user_id

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        "💬 Напишите ответ пользователю одним сообщением.",
        reply_markup=cancel_keyboard(ADMIN_ID)
    )


# ============================================================
# FORM INPUT
# ============================================================

@bot.message_handler(
    content_types=[
        "text",
        "photo"
    ]
)
def form_input(message):
    user_id = message.from_user.id

    save_user(
        message.from_user
    )

    # --------------------------------------------------------
    # ADMIN SUPPORT REPLY
    # --------------------------------------------------------

    if user_id == ADMIN_ID and user_id in support_replies:
        target_user_id = support_replies.pop(
            user_id
        )

        if not message.text:
            bot.send_message(
                message.chat.id,
                "Пожалуйста, отправьте ответ текстом."
            )
            support_replies[user_id] = target_user_id
            return

        try:
            bot.send_message(
                target_user_id,
                tr(
                    target_user_id,
                    "support_answer"
                )
                + escape(message.text.strip()),
                reply_markup=main_menu(target_user_id)
            )

            bot.send_message(
                message.chat.id,
                "✅ Ответ отправлен пользователю.",
                reply_markup=main_menu(ADMIN_ID)
            )

        except Exception:
            logger.exception(
                "Support reply failed"
            )

            bot.send_message(
                message.chat.id,
                "⚠️ Не удалось отправить ответ пользователю."
            )

        return

    state = states.get(user_id)

    if not state:
        return

    step = state["step"]
    data = state["data"]

    # --------------------------------------------------------
    # SUPPORT
    # --------------------------------------------------------

    if state.get("mode") == "support" and step == "support_text":
        if not message.text:
            bot.send_message(
                message.chat.id,
                tr(user_id, "invalid")
            )
            return

        support_message = message.text.strip()[:3000]

        listing_id = extract_listing_number(
            support_message
        )

        listing_info = None

        if listing_id:
            with get_db() as conn:
                listing_info = conn.execute(
                    """
                    SELECT id, title
                    FROM listings
                    WHERE id=? AND user_id=?
                    """,
                    (
                        listing_id,
                        user_id
                    )
                ).fetchone()

        admin_text = (
            "🆘 <b>НОВОЕ ОБРАЩЕНИЕ В ПОДДЕРЖКУ</b>\n\n"
            f"👤 Пользователь: "
            f"{escape(message.from_user.first_name)}\n"
        )

        if message.from_user.username:
            admin_text += (
                f"📱 Username: "
                f"@{escape(message.from_user.username)}\n"
            )

        admin_text += (
            f"🆔 ID: <code>{user_id}</code>\n"
        )

        if listing_info:
            admin_text += (
                f"📋 Объявление: #{listing_info['id']}\n"
                f"Название: "
                f"<b>{escape(listing_info['title'])}</b>\n"
            )

        admin_text += (
            "\n💬 <b>Сообщение:</b>\n"
            f"{escape(support_message)}"
        )

        try:
            bot.send_message(
                ADMIN_ID,
                admin_text,
                reply_markup=support_admin_keyboard(user_id)
            )

            states.pop(
                user_id,
                None
            )

            bot.send_message(
                message.chat.id,
                tr(user_id, "support_sent"),
                reply_markup=main_menu(user_id)
            )

        except Exception:
            logger.exception(
                "Support message failed"
            )

            bot.send_message(
                message.chat.id,
                "⚠️ Не удалось отправить обращение. "
                "Попробуйте ещё раз."
            )

        return

    # --------------------------------------------------------
    # QUICK MODE
    # --------------------------------------------------------

    if state.get("mode") == "quick":

        if step == "quick_text":

            if not message.text:
                bot.send_message(
                    message.chat.id,
                    tr(user_id, "invalid")
                )
                return

            parsed = parse_quick_ad(
                message.text,
                data["kind"],
                message.from_user
            )

            state["data"] = parsed
            state["step"] = "preview"

            show_preview(
                message.chat.id,
                user_id
            )

            return

        # ----------------------------------------------------
        # EDIT QUICK FIELDS
        # ----------------------------------------------------

        if step.startswith("edit_"):

            field = step.replace(
                "edit_",
                "",
                1
            )

            # Категория обрабатывается callback.
            if field == "category":
                return

            if field == "photo":

                if not message.photo:
                    bot.send_message(
                        message.chat.id,
                        "📷 Отправьте фотографию.",
                        reply_markup=cancel_keyboard(user_id)
                    )
                    return

                data["photo_id"] = (
                    message.photo[-1].file_id
                )

                state["step"] = "preview"

                show_preview(
                    message.chat.id,
                    user_id
                )

                return

            if not message.text:
                bot.send_message(
                    message.chat.id,
                    tr(user_id, "invalid")
                )
                return

            value = message.text.strip()

            if field == "title":
                data["title"] = value[:120]

            elif field == "budget":
                data["budget"] = value[:100]

            elif field == "city":
                data["city"] = value[:100]

            elif field == "deadline":
                data["deadline"] = value[:100]

            elif field == "description":
                data["description"] = value[:3000]

            elif field == "experience":
                data["experience"] = value[:500]

            elif field == "portfolio":
                if value.lower() in (
                    "нет",
                    "no",
                    "nu",
                    "нету"
                ):
                    data["portfolio"] = ""
                else:
                    data["portfolio"] = value[:1000]

            elif field == "contact":
                data["contact"] = value[:200]

            state["step"] = "preview"

            show_preview(
                message.chat.id,
                user_id
            )

            return

        return

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if step == "search":
        if not message.text:
            bot.send_message(
                message.chat.id,
                tr(user_id, "invalid")
            )
            return

        kind = data.get(
            "kind",
            "order"
        )

        states.pop(
            user_id,
            None
        )

        show_search_results(
            message.chat.id,
            user_id,
            kind,
            message.text.strip()
        )

        return

    # --------------------------------------------------------
    # OLD FORM
    # --------------------------------------------------------

    if step == "title":
        if not message.text:
            bot.send_message(
                message.chat.id,
                tr(user_id, "invalid")
            )
            return

        data["title"] = (
            message.text.strip()[:120]
        )

        state["step"] = "category"

        bot.send_message(
            message.chat.id,
            tr(user_id, "need_category"),
            reply_markup=category_keyboard(
                data["kind"]
            )
        )

        return

    if step == "budget":
        if not message.text:
            bot.send_message(
                message.chat.id,
                tr(user_id, "invalid")
            )
            return

        data["budget"] = (
            message.text.strip()[:100]
        )

        state["step"] = "city"

        bot.send_message(
            message.chat.id,
            tr(user_id, "need_city"),
            reply_markup=cancel_keyboard(user_id)
        )

        return

    if step == "city":
        if not message.text:
            bot.send_message(
                message.chat.id,
                tr(user_id, "invalid")
            )
            return

        data["city"] = (
            message.text.strip()[:100]
        )

        if data["kind"] == "order":
            state["step"] = "deadline"

            bot.send_message(
                message.chat.id,
                tr(user_id, "need_deadline"),
                reply_markup=cancel_keyboard(user_id)
            )
        else:
            state["step"] = "experience"

            bot.send_message(
                message.chat.id,
                tr(user_id, "need_experience"),
                reply_markup=cancel_keyboard(user_id)
            )

        return

    if step == "deadline":
        if not message.text:
            bot.send_message(
                message.chat.id,
                tr(user_id, "invalid")
            )
            return

        data["deadline"] = (
            message.text.strip()[:100]
        )

        state["step"] = "description"

        bot.send_message(
            message.chat.id,
            tr(user_id, "need_description"),
            reply_markup=cancel_keyboard(user_id)
        )

        return

    if step == "experience":
        if not message.text:
            bot.send_message(
                message.chat.id,
                tr(user_id, "invalid")
            )
            return

        data["experience"] = (
            message.text.strip()[:500]
        )

        state["step"] = "description"

        bot.send_message(
            message.chat.id,
            tr(user_id, "need_description"),
            reply_markup=cancel_keyboard(user_id)
        )

        return

    if step == "description":
        if not message.text:
            bot.send_message(
                message.chat.id,
                tr(user_id, "invalid")
            )
            return

        data["description"] = (
            message.text.strip()[:2500]
        )

        state["step"] = "portfolio"

        bot.send_message(
            message.chat.id,
            tr(user_id, "need_portfolio"),
            reply_markup=cancel_keyboard(user_id)
        )

        return

    if step == "portfolio":
        if message.photo:
            data["photo_id"] = (
                message.photo[-1].file_id
            )

            data["portfolio"] = (
                message.caption.strip()[:1000]
                if message.caption
                else
                "Фото портфолио"
            )

        elif message.text:
            data["portfolio"] = (
                message.text.strip()[:1000]
            )

        else:
            bot.send_message(
                message.chat.id,
                tr(user_id, "invalid")
            )
            return

        state["step"] = "contact"

        bot.send_message(
            message.chat.id,
            tr(user_id, "need_contact"),
            reply_markup=cancel_keyboard(user_id)
        )

        return

    if step == "contact":
        if not message.text:
            bot.send_message(
                message.chat.id,
                tr(user_id, "invalid")
            )
            return

        data["contact"] = (
            message.text.strip()[:200]
        )

        state["step"] = "preview"

        show_preview(
            message.chat.id,
            user_id
        )


# ============================================================
# MENU COMMAND
# ============================================================

@bot.message_handler(commands=["menu"])
def menu_command(message):
    save_user(
        message.from_user
    )

    user_id = message.from_user.id

    bot.send_message(
        message.chat.id,
        tr(user_id, "choose"),
        reply_markup=main_menu(user_id)
    )


# ============================================================
# CANCEL COMMAND
# ============================================================

@bot.message_handler(commands=["cancel"])
def cancel_command(message):
    user_id = message.from_user.id

    states.pop(
        user_id,
        None
    )

    support_replies.pop(
        user_id,
        None
    )

    save_user(
        message.from_user
    )

    bot.send_message(
        message.chat.id,
        tr(user_id, "choose"),
        reply_markup=main_menu(user_id)
    )


# ============================================================
# START BOT
# ============================================================

if __name__ == "__main__":

    init_db()

    logger.info(
        "===================================="
    )

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
        "ADMIN_ID = %s",
        ADMIN_ID
    )

    logger.info(
        "BOT_USERNAME = @%s",
        BOT_USERNAME
    )

    logger.info(
        "DB_PATH = %s",
        DB_PATH
    )

    logger.info(
        "===================================="
    )

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
)
