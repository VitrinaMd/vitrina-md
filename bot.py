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

ADMIN_ID = int(
    os.getenv("ADMIN_ID", "7419021481")
)

GROUP_ID_RAW = os.getenv(
    "GROUP_ID",
    "-1004362264263"
).strip()

GROUP_ID = (
    int(GROUP_ID_RAW)
    if GROUP_ID_RAW
    else None
)

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
# TELEGRAM BOT
# ============================================================

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)


# ============================================================
# СОСТОЯНИЯ
# ============================================================

states = {}


# ============================================================
# ТЕКСТЫ
# ============================================================

TEXT = {

    "ru": {

        "welcome":
            "👋 <b>Добро пожаловать в Vitrina Freelance MD!</b>\n\n"
            "Здесь заказчики находят специалистов, "
            "а фрилансеры — новые заказы.",

        "choose":
            "Выберите действие:",

        "order":
            "📝 Разместить заказ",

        "service":
            "👨‍💻 Предложить свои услуги",

        "find":
            "🔎 Найти",

        "orders":
            "🔎 Найти заказ",

        "services":
            "👨‍💻 Найти услуги",

        "mine":
            "📋 Мои объявления",

        "about":
            "ℹ️ О проекте",

        "support":
            "🆘 Поддержка",

        "language":
            "🌐 Язык / Limba",

        "cancel":
            "❌ Отмена",

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
            "Можно также отправить одну фотографию.\n\n"
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

        "all":
            "📋 Все",

        "my_title":
            "📋 <b>Ваши объявления</b>",

        "invalid":
            "Пожалуйста, введите текст или используйте кнопку.",

        "contact_author":
            "💬 Связаться с продавцом",

        "comment":
            "💬 Комментировать",

        "submit_ad":
            "➕ Подать объявление",
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

        "cancel":
            "❌ Anulează",

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
            "Indică <b>orașul</b> sau scrie "
            "<b>La distanță</b>:",

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

        "all":
            "📋 Toate",

        "my_title":
            "📋 <b>Anunțurile tale</b>",

        "invalid":
            "Te rugăm să introduci text sau să folosești butonul.",

        "contact_author":
            "💬 Contactează vânzătorul",

        "comment":
            "💬 Comentează",

        "submit_ad":
            "➕ Publică un anunț",
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
# USERS
# ============================================================

def detect_language(user):

    language = (
        user.language_code or ""
    ).lower()

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
# FORM
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
            f"⭐ Опыт: "
            f"{escape(data['experience'])}"
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

        support_text = (
            "Если нужна помощь, напишите "
            "администратору проекта."
            if get_language(user_id) == "ru"
            else
            "Dacă ai nevoie de ajutor, contactează "
            "administratorul proiectului."
        )

        if SUPPORT_USERNAME:

            support_text += (
                f"\n\n👉 @{escape(SUPPORT_USERNAME)}"
            )

        bot.send_message(
            message.chat.id,
            support_text,
            reply_markup=main_menu(user_id)
        )

        return

    keyboard = types.InlineKeyboardMarkup(
        row_width=2
    )

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

    bot.answer_callback_query(
        call.id
    )

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

    bot.answer_callback_query(
        call.id
    )

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

            text += (
                f"💰 {escape(row['budget'])}\n"
            )

        if row["city"]:

            text += (
                f"📍 {escape(row['city'])}\n"
            )

        text += (
            "\n"
            + escape(
                row["description"][:900]
            )
        )

        keyboard = types.InlineKeyboardMarkup()

        with get_db() as conn:

            author = conn.execute(
                """
                SELECT username
                FROM users
                WHERE user_id=?
                """,
                (
                    row["user_id"],
                )
            ).fetchone()

        if author and author["username"]:

            keyboard.add(
                types.InlineKeyboardButton(
                    tr(
                        user_id,
                        "contact_author"
                    ),
                    url=(
                        "https://t.me/"
                        + author["username"]
                    )
                )
            )

        else:

            keyboard.add(
                types.InlineKeyboardButton(
                    tr(
                        user_id,
                        "contact_author"
                    ),
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

def show_my_listings(
    chat_id,
    user_id
):

    with get_db() as conn:

        rows = conn.execute("""
            SELECT *
            FROM listings
            WHERE user_id=?
            ORDER BY id DESC
            LIMIT 20
        """, (
            user_id,
        )).fetchall()

    if not rows:

        bot.send_message(
            chat_id,
            tr(user_id, "empty"),
            reply_markup=main_menu(user_id)
        )

        return

    status_names = {

        "pending":
            "🟡 На модерации",

        "approved":
            "🟢 Одобрено",

        "rejected":
            "🔴 Отклонено"
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

    bot.answer_callback_query(
        call.id
    )

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
# EDIT
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
            "Форма уже закрыта.",
            show_alert=True
        )

        return

    states[user_id]["step"] = "title"

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        call.message.chat.id,
        tr(
            user_id,
            "need_title"
        ),
        reply_markup=cancel_keyboard(
            user_id
        )
    )


# ============================================================
# CATEGORY
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith("order_category:")
        or
        call.data.startswith("service_category:")
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

    category_label = dict(
        CATEGORIES
    ).get(
        category_key,
        category_key
    )

    data = states[user_id]["data"]

    data["category"] = category_key

    data["category_label"] = category_label

    states[user_id]["step"] = "budget"

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        call.message.chat.id,
        tr(
            user_id,
            "need_budget"
            if data["kind"] == "order"
            else "need_price"
        ),
        reply_markup=cancel_keyboard(
            user_id
        )
    )


# ============================================================
# PUBLIC CHANNEL POST URL
# ============================================================

def channel_post_url(message_id):

    if not CHANNEL_USERNAME:

        return None

    return (
        f"https://t.me/"
        f"{CHANNEL_USERNAME}/"
        f"{message_id}"
    )


# ============================================================
# PUBLICATION
# ============================================================

def publish_listing(listing_id):

    if not GROUP_ID:

        raise RuntimeError(
            "GROUP_ID не установлен в Render."
        )

    if not BOT_USERNAME:

        raise RuntimeError(
            "BOT_USERNAME не установлен в Render."
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
        """, (
            listing_id,
        )).fetchone()

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

    # --------------------------------------------------------
    # Сначала публикуем сообщение
    # --------------------------------------------------------

    if row["photo_id"]:

        post_message = bot.send_photo(
            GROUP_ID,
            row["photo_id"],
            caption=text
        )

    else:

        post_message = bot.send_message(
            GROUP_ID,
            text
        )

    # --------------------------------------------------------
    # КНОПКИ
    # --------------------------------------------------------

    keyboard = types.InlineKeyboardMarkup(
        row_width=1
    )

    # Связаться с продавцом
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

    else:

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

    # Комментарии
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

    # Подать объявление
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

    # --------------------------------------------------------
    # Добавляем клавиатуру
    # --------------------------------------------------------

    bot.edit_message_reply_markup(
        GROUP_ID,
        post_message.message_id,
        reply_markup=keyboard
    )

    # --------------------------------------------------------
    # Сохраняем ID публикации
    # --------------------------------------------------------

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

def notify_user(
    user_id,
    text
):

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

        listing_id = int(
            id_text
        )

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

    # --------------------------------------------------------
    # REJECT
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # APPROVE
    # --------------------------------------------------------

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

        bot.send_message(
            ADMIN_ID,
            "⚠️ <b>Ошибка публикации</b>\n\n"
            f"Объявление: #{listing_id}\n"
            f"<code>{escape(error)}</code>"
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

    state = states.get(
        user_id
    )

    if not state:

        bot.answer_callback_query(
            call.id,
            "Форма уже закрыта.",
            show_alert=True
        )

        return

    data = state["data"]

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
        """, (
            listing_id,
        )).fetchone()

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
        "\n👤 "
        f"{escape(row['first_name'])}"
    )

    if row["username"]:

        admin_text += (
            f" (@{escape(row['username'])})"
        )

    keyboard = types.InlineKeyboardMarkup(
        row_width=2
    )

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
                caption=admin_text,
                reply_markup=keyboard
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

    if user_id not in states:

        return

    state = states[user_id]

    step = state["step"]

    data = state["data"]

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if step == "search":

        if not message.text:

            bot.send_message(
                message.chat.id,
                tr(
                    user_id,
                    "invalid"
                )
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
    # TITLE
    # --------------------------------------------------------

    if step == "title":

        if not message.text:

            bot.send_message(
                message.chat.id,
                tr(
                    user_id,
                    "invalid"
                )
            )

            return

        data["title"] = (
            message.text.strip()[:120]
        )

        state["step"] = "category"

        bot.send_message(
            message.chat.id,
            tr(
                user_id,
                "need_category"
            ),
            reply_markup=category_keyboard(
                data["kind"]
            )
        )

        return

    # --------------------------------------------------------
    # BUDGET
    # --------------------------------------------------------

    if step == "budget":

        if not message.text:

            bot.send_message(
                message.chat.id,
                tr(
                    user_id,
                    "invalid"
                )
            )

            return

        data["budget"] = (
            message.text.strip()[:100]
        )

        state["step"] = "city"

        bot.send_message(
            message.chat.id,
            tr(
                user_id,
                "need_city"
            ),
            reply_markup=cancel_keyboard(
                user_id
            )
        )

        return

    # --------------------------------------------------------
    # CITY
    # --------------------------------------------------------

    if step == "city":

        if not message.text:

            bot.send_message(
                message.chat.id,
                tr(
                    user_id,
                    "invalid"
                )
            )

            return

        data["city"] = (
            message.text.strip()[:100]
        )

        if data["kind"] == "order":

            state["step"] = "deadline"

            bot.send_message(
                message.chat.id,
                tr(
                    user_id,
                    "need_deadline"
                ),
                reply_markup=cancel_keyboard(
                    user_id
                )
            )

        else:

            state["step"] = "experience"

            bot.send_message(
                message.chat.id,
                tr(
                    user_id,
                    "need_experience"
                ),
                reply_markup=cancel_keyboard(
                    user_id
                )
            )

        return

    # --------------------------------------------------------
    # DEADLINE
    # --------------------------------------------------------

    if step == "deadline":

        if not message.text:

            bot.send_message(
                message.chat.id,
                tr(
                    user_id,
                    "invalid"
                )
            )

            return

        data["deadline"] = (
            message.text.strip()[:100]
        )

        state["step"] = "description"

        bot.send_message(
            message.chat.id,
            tr(
                user_id,
                "need_description"
            ),
            reply_markup=cancel_keyboard(
                user_id
            )
        )

        return

    # --------------------------------------------------------
    # EXPERIENCE
    # --------------------------------------------------------

    if step == "experience":

        if not message.text:

            bot.send_message(
                message.chat.id,
                tr(
                    user_id,
                    "invalid"
                )
            )

            return

        data["experience"] = (
            message.text.strip()[:500]
        )

        state["step"] = "description"

        bot.send_message(
            message.chat.id,
            tr(
                user_id,
                "need_description"
            ),
            reply_markup=cancel_keyboard(
                user_id
            )
        )

        return

    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    if step == "description":

        if not message.text:

            bot.send_message(
                message.chat.id,
                tr(
                    user_id,
                    "invalid"
                )
            )

            return

        data["description"] = (
            message.text.strip()[:2500]
        )

        state["step"] = "portfolio"

        bot.send_message(
            message.chat.id,
            tr(
                user_id,
                "need_portfolio"
            ),
            reply_markup=cancel_keyboard(
                user_id
            )
        )

        return

    # --------------------------------------------------------
    # PORTFOLIO
    # --------------------------------------------------------

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
                tr(
                    user_id,
                    "invalid"
                )
            )

            return

        state["step"] = "contact"

        bot.send_message(
            message.chat.id,
            tr(
                user_id,
                "need_contact"
            ),
            reply_markup=cancel_keyboard(
                user_id
            )
        )

        return

    # --------------------------------------------------------
    # CONTACT
    # --------------------------------------------------------

    if step == "contact":

        if not message.text:

            bot.send_message(
                message.chat.id,
                tr(
                    user_id,
                    "invalid"
                )
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

@bot.message_handler(
    commands=["menu"]
)
def menu_command(message):

    save_user(
        message.from_user
    )

    user_id = message.from_user.id

    bot.send_message(
        message.chat.id,
        tr(
            user_id,
            "choose"
        ),
        reply_markup=main_menu(
            user_id
        )
    )


# ============================================================
# CANCEL COMMAND
# ============================================================

@bot.message_handler(
    commands=["cancel"]
)
def cancel_command(message):

    user_id = message.from_user.id

    states.pop(
        user_id,
        None
    )

    save_user(
        message.from_user
    )

    bot.send_message(
        message.chat.id,
        tr(
            user_id,
            "choose"
        ),
        reply_markup=main_menu(
            user_id
        )
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
        "===================================="
    )

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
                             )
