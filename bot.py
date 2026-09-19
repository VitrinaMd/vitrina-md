import os
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

GROUP_ID_RAW = os.getenv("GROUP_ID", "").strip()
GROUP_ID = int(GROUP_ID_RAW) if GROUP_ID_RAW else None

SUPPORT_USERNAME = os.getenv(
    "SUPPORT_USERNAME", ""
).strip().lstrip("@")

BOT_USERNAME = os.getenv(
    "BOT_USERNAME", ""
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
# TELEGRAM BOT
# ============================================================

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)


# ============================================================
# ВРЕМЕННЫЕ СОСТОЯНИЯ ФОРМ
# ============================================================

states = {}


# ============================================================
# ТЕКСТЫ RU / RO
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
        "find": "🔎 Найти",
        "orders": "🔎 Найти заказ",
        "services": "👨‍💻 Найти услуги",
        "mine": "📋 Мои объявления",
        "about": "ℹ️ О проекте",
        "support": "🆘 Поддержка",
        "language": "🌐 Язык / Limba",

        "back": "⬅️ Назад",
        "cancel": "❌ Отмена",

        "saved":
            "✅ Объявление отправлено на модерацию.\n\n"
            "После проверки администратора оно будет опубликовано.",

        "rejected":
            "❌ Ваше объявление было отклонено модератором.",

        "approved":
            "✅ Ваше объявление одобрено и опубликовано.",

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
            "Укажите <b>срок выполнения</b> или напишите "
            "«не установлен»:",

        "need_description":
            "Опишите задачу или свои услуги как можно подробнее:",

        "need_experience":
            "Напишите о своём <b>опыте</b>:",

        "need_portfolio":
            "Отправьте <b>ссылку на портфолио</b> или его описание.\n\n"
            "Можно также отправить одну фотографию.\n\n"
            "Если портфолио нет — напишите «нет».",

        "need_contact":
            "Укажите, как с вами связаться.\n\n"
            "Например: @username или номер телефона.\n\n"
            "Если у вас есть Telegram username, его можно указать.",

        "preview":
            "🔎 <b>Проверьте объявление</b>\n\n",

        "send":
            "📤 Отправить на модерацию",

        "edit":
            "✏️ Изменить",

        "published":
            "📢 Объявление опубликовано в группе.",

        "empty":
            "Пока здесь ничего нет.",

        "about_text":
            "<b>Vitrina Freelance MD</b> — площадка для заказчиков "
            "и специалистов.\n\n"
            "Заказчики могут размещать задачи, "
            "а фрилансеры — предлагать свои услуги.\n\n"
            "Все объявления проходят модерацию перед публикацией "
            "в Telegram-группе.",

        "support_text":
            "Если нужна помощь, напишите администратору проекта.",

        "choose_language":
            "Выберите язык:",

        "no_results":
            "По вашему запросу ничего не найдено.",

        "ask_search":
            "Введите слово для поиска.\n\n"
            "Например: дизайн, ремонт, перевод, программист "
            "или название города.\n\n"
            "Или нажмите «Все».",

        "all":
            "📋 Все",

        "my_title":
            "📋 <b>Ваши объявления</b>",

        "invalid":
            "Пожалуйста, введите текст или используйте кнопку.",
    },


    "ro": {

        "welcome":
            "👋 <b>Bine ai venit pe Vitrina Freelance MD!</b>\n\n"
            "Aici clienții găsesc specialiști, "
            "iar freelancerii găsesc proiecte noi.",

        "choose":
            "Alege o acțiune:",

        "order":
            "📝 Publică o comandă",

        "service":
            "👨‍💻 Oferă servicii",

        "find":
            "🔎 Caută",

        "orders":
            "🔎 Caută comenzi",

        "services":
            "👨‍💻 Caută servicii",

        "mine":
            "📋 Anunțurile mele",

        "about":
            "ℹ️ Despre proiect",

        "support":
            "🆘 Suport",

        "language":
            "🌐 Limbă / Язык",

        "back":
            "⬅️ Înapoi",

        "cancel":
            "❌ Anulează",

        "saved":
            "✅ Anunțul a fost trimis pentru moderare.\n\n"
            "După verificare, acesta va fi publicat.",

        "rejected":
            "❌ Anunțul tău a fost respins de moderator.",

        "approved":
            "✅ Anunțul tău a fost aprobat și publicat.",

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
            "Descrie proiectul sau serviciile tale cât mai detaliat:",

        "need_experience":
            "Scrie despre <b>experiența</b> ta:",

        "need_portfolio":
            "Trimite <b>linkul portofoliului</b> sau o descriere.\n\n"
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

        "published":
            "📢 Anunțul a fost publicat în grup.",

        "empty":
            "Încă nu există anunțuri aici.",

        "about_text":
            "<b>Vitrina Freelance MD</b> este o platformă "
            "pentru clienți și specialiști.\n\n"
            "Clienții pot publica proiecte, "
            "iar freelancerii își pot oferi serviciile.\n\n"
            "Toate anunțurile sunt moderate înainte de publicarea "
            "în grupul Telegram.",

        "support_text":
            "Dacă ai nevoie de ajutor, contactează administratorul proiectului.",

        "choose_language":
            "Alege limba:",

        "no_results":
            "Nu au fost găsite rezultate.",

        "ask_search":
            "Introdu un cuvânt pentru căutare.\n\n"
            "De exemplu: design, reparații, traduceri, programator "
            "sau un oraș.\n\n"
            "Sau apasă „Toate”.",

        "all":
            "📋 Toate",

        "my_title":
            "📋 <b>Anunțurile tale</b>",

        "invalid":
            "Te rugăm să introduci text sau să folosești butonul.",
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
# ПОЛЬЗОВАТЕЛЬ
# ============================================================

def detect_language(user):

    lang = (
        user.language_code or ""
    ).lower()

    if lang.startswith("ro"):
        return "ro"

    if lang.startswith("ru"):
        return "ru"

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
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def escape(value):

    return html.escape(
        str(value or "")
    )


def main_menu(user_id):

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2
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

    keyboard = types.InlineKeyboardMarkup(
        row_width=2
    )

    prefix = (
        "order"
        if kind == "order"
        else
        "service"
    )

    for key, title in CATEGORIES:

        keyboard.add(
            types.InlineKeyboardButton(
                title,
                callback_data=f"{prefix}_category:{key}"
            )
        )

    return keyboard


def find_keyboard(user_id):

    keyboard = types.InlineKeyboardMarkup(
        row_width=1
    )

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
# ФОРМА
# ============================================================

def start_form(chat_id, user_id, kind):

    states[user_id] = {

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


def preview_text(data):

    kind_text = (
        "📝 Заказ"
        if data["kind"] == "order"
        else
        "👨‍💻 Услуга"
    )

    result = [

        f"<b>{escape(data['title'])}</b>",

        f"📌 Тип: {kind_text}",

        f"🏷 Категория: "
        f"{escape(data.get('category_label'))}"

    ]

    if data.get("budget"):

        result.append(
            f"💰 "
            f"{'Бюджет' if data['kind'] == 'order' else 'Цена'}: "
            f"{escape(data['budget'])}"
        )

    if data.get("city"):

        result.append(
            f"📍 {escape(data['city'])}"
        )

    if data.get("deadline"):

        result.append(
            f"📅 Срок: {escape(data['deadline'])}"
        )

    if data.get("experience"):

        result.append(
            f"⭐ Опыт: {escape(data['experience'])}"
        )

    result.append(
        f"\n📝 {escape(data['description'])}"
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

    return "\n".join(result)


def preview_keyboard(user_id):

    keyboard = types.InlineKeyboardMarkup(
        row_width=1
    )

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

    keyboard.add(
        types.InlineKeyboardButton(
            tr(user_id, "cancel"),
            callback_data="cancel_form"
        )
    )

    return keyboard


def show_preview(chat_id, user_id):

    data = states[user_id]["data"]

    bot.send_message(
        chat_id,
        tr(user_id, "preview")
        + preview_text(data),
        reply_markup=preview_keyboard(user_id)
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
    )

    # --------------------------------------------------------
    # КОНТАКТ ЧЕРЕЗ БОТА
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

                listing = conn.execute("""
                    SELECT
                        listings.*,
                        users.username,
                        users.first_name
                    FROM listings
                    JOIN users
                        ON users.user_id = listings.user_id
                    WHERE listings.id=?
                """, (listing_id,)).fetchone()

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
# ID ГРУППЫ
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

            TEXT["ru
