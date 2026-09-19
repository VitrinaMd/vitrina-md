import os
import sqlite3
import html
import time
import telebot

from telebot import types


# =========================================================
# НАСТРОЙКИ
# =========================================================

BOT_TOKEN = "8724559334:AAGGHuWXx2wjrWTYbvLTSUbJRsFGbaFwF3g"

# Твой Telegram ID администратора
ADMIN_ID = 7419021481

# Пока оставляем пустым.
# После получения ID группы вставим его сюда.
GROUP_ID = None

DB_NAME = "vitrina.db"


bot = telebot.TeleBot(BOT_TOKEN)


# =========================================================
# БАЗА ДАННЫХ
# =========================================================

def init_database():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            first_name TEXT,
            username TEXT,
            text TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# СОХРАНЕНИЕ ЗАЯВКИ
# =========================================================

def create_application(user, text):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO applications
        (user_id, first_name, username, text, status)
        VALUES (?, ?, ?, ?, 'pending')
    """, (
        user.id,
        user.first_name or "",
        user.username or "",
        text
    ))

    application_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return application_id


# =========================================================
# ПОЛУЧЕНИЕ ЗАЯВКИ
# =========================================================

def get_application(application_id):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            user_id,
            first_name,
            username,
            text,
            status
        FROM applications
        WHERE id = ?
    """, (application_id,))

    result = cursor.fetchone()

    conn.close()

    return result


# =========================================================
# ИЗМЕНЕНИЕ СТАТУСА
# =========================================================

def update_application_status(application_id, status):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE applications
        SET status = ?
        WHERE id = ?
    """, (
        status,
        application_id
    ))

    conn.commit()
    conn.close()


# =========================================================
# ГЛАВНОЕ МЕНЮ
# =========================================================

def send_main_menu(chat_id):

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.add(
        types.KeyboardButton(
            "📝 Разместить заказ / резюме"
        )
    )

    bot.send_message(
        chat_id,
        "Главное меню 👇",
        reply_markup=markup
    )


# =========================================================
# /START
# =========================================================

@bot.message_handler(commands=["start"])
def start_command(message):

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.add(
        types.KeyboardButton(
            "📝 Разместить заказ / резюме"
        )
    )

    bot.send_message(
        message.chat.id,
        "👋 <b>Привет!</b>\n\n"
        "Добро пожаловать в <b>Vitrina.md</b> — "
        "маркетплейс фриланса.\n\n"
        "Здесь можно разместить заказ "
        "или предложить свои услуги.\n\n"
        "Нажми кнопку ниже 👇",
        parse_mode="HTML",
        reply_markup=markup
    )


# =========================================================
# ПОЛУЧЕНИЕ ID ГРУППЫ
# =========================================================

@bot.message_handler(commands=["id"])
def get_group_id(message):

    bot.send_message(
        message.chat.id,
        f"🆔 ID этого чата:\n{message.chat.id}"
    )


# =========================================================
# НАЧАЛО СОЗДАНИЯ ОБЪЯВЛЕНИЯ
# =========================================================

@bot.message_handler(
    func=lambda message:
    message.text == "📝 Разместить заказ / резюме"
)
def start_application(message):

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.add(
        types.KeyboardButton("❌ Отмена")
    )

    msg = bot.send_message(
        message.chat.id,
        "📝 <b>Создание объявления</b>\n\n"
        "Напиши подробно, что тебе нужно сделать "
        "или какие услуги ты предлагаешь.\n\n"
        "Например:\n"
        "• Нужно сделать сайт\n"
        "• Ищу электрика\n"
        "• Предлагаю услуги дизайнера\n\n"
        "Отправь описание одним сообщением.",
        parse_mode="HTML",
        reply_markup=markup
    )

    bot.register_next_step_handler(
        msg,
        process_description
    )


# =========================================================
# ВРЕМЕННЫЕ ДАННЫЕ
# =========================================================

temporary_data = {}


# =========================================================
# ОБРАБОТКА ОПИСАНИЯ
# =========================================================

def process_description(message):

    user_id = message.from_user.id

    if message.text == "❌ Отмена":

        temporary_data.pop(user_id, None)

        send_main_menu(
            message.chat.id
        )

        return

    text = message.text.strip() if message.text else ""

    if not text:

        msg = bot.send_message(
            message.chat.id,
            "❌ Объявление не может быть пустым.\n\n"
            "Напиши описание ещё раз."
        )

        bot.register_next_step_handler(
            msg,
            process_description
        )

        return

    if len(text) > 3500:

        msg = bot.send_message(
            message.chat.id,
            "❌ Текст слишком длинный.\n\n"
            "Максимальная длина — 3500 символов."
        )

        bot.register_next_step_handler(
            msg,
            process_description
        )

        return

    temporary_data[user_id] = text

    safe_text = html.escape(text)

    markup = types.InlineKeyboardMarkup(
        row_width=2
    )

    markup.add(
        types.InlineKeyboardButton(
            "✅ Отправить",
            callback_data="confirm"
        ),
        types.InlineKeyboardButton(
            "✏️ Изменить",
            callback_data="edit"
        ),
        types.InlineKeyboardButton(
            "❌ Отмена",
            callback_data="cancel"
        )
    )

    bot.send_message(
        message.chat.id,
        "👀 <b>Предпросмотр объявления:</b>\n\n"
        f"{safe_text}\n\n"
        "Всё правильно?",
        parse_mode="HTML",
        reply_markup=markup
    )


# =========================================================
# КНОПКИ ПОЛЬЗОВАТЕЛЯ
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data in [
        "confirm",
        "edit",
        "cancel"
    ]
)
def user_callback(call):

    user_id = call.from_user.id

    # -----------------------------------------------------
    # ОТМЕНА
    # -----------------------------------------------------

    if call.data == "cancel":

        temporary_data.pop(
            user_id,
            None
        )

        bot.edit_message_text(
            "❌ <b>Создание объявления отменено.</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )

        bot.answer_callback_query(
            call.id
        )

        send_main_menu(
            call.message.chat.id
        )

        return

    # -----------------------------------------------------
    # ИЗМЕНЕНИЕ
    # -----------------------------------------------------

    if call.data == "edit":

        if user_id not in temporary_data:

            bot.answer_callback_query(
                call.id,
                "Сессия устарела. Начни заново через /start",
                show_alert=True
            )

            return

        msg = bot.send_message(
            call.message.chat.id,
            "✏️ Отправь исправленный текст объявления:"
        )

        bot.register_next_step_handler(
            msg,
            process_description
        )

        bot.answer_callback_query(
            call.id
        )

        return

    # -----------------------------------------------------
    # ОТПРАВКА
    # -----------------------------------------------------

    if call.data == "confirm":

        text = temporary_data.get(
            user_id
        )

        if not text:

            bot.answer_callback_query(
                call.id,
                "Сессия устарела. Начни заново через /start",
                show_alert=True
            )

            return

        application_id = create_application(
            call.from_user,
            text
        )

        sent = send_application_to_admin(
            application_id
        )

        if sent:

            bot.edit_message_text(
                f"✅ <b>Заявка №{application_id} "
                f"отправлена администратору!</b>\n\n"
                "После проверки она может быть опубликована.",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML"
            )

        else:

            update_application_status(
                application_id,
                "send_error"
            )

            bot.edit_message_text(
                "⚠️ Не удалось отправить заявку "
                "администратору.\n\n"
                "Попробуй ещё раз через /start.",
                call.message.chat.id,
                call.message.message_id
            )

        temporary_data.pop(
            user_id,
            None
        )

        bot.answer_callback_query(
            call.id
        )


# =========================================================
# ОТПРАВКА ЗАЯВКИ АДМИНИСТРАТОРУ
# =========================================================

def send_application_to_admin(
    application_id
):

    application = get_application(
        application_id
    )

    if not application:

        return False

    (
        app_id,
        user_id,
        first_name,
        username,
        text,
        status
    ) = application

    username_text = (
        f"@{username}"
        if username
        else f"ID: {user_id}"
    )

    safe_first_name = html.escape(
        first_name
    )

    safe_username = html.escape(
        username_text
    )

    safe_text = html.escape(
        text
    )

    admin_text = (
        f"🚨 <b>Новая заявка №{app_id}</b>\n\n"
        f"👤 <b>Пользователь:</b> "
        f"{safe_first_name}\n"
        f"🔗 <b>Контакт:</b> "
        f"{safe_username}\n"
        f"🆔 <b>ID:</b> {user_id}\n\n"
        f"📝 <b>Объявление:</b>\n"
        f"{safe_text}\n\n"
        f"🟡 <b>Статус:</b> На модерации"
    )

    markup = types.InlineKeyboardMarkup(
        row_width=2
    )

    markup.add(
        types.InlineKeyboardButton(
            "✅ Опубликовать",
            callback_data=f"approve:{app_id}"
        ),
        types.InlineKeyboardButton(
            "❌ Отклонить",
            callback_data=f"reject:{app_id}"
        )
    )

    for attempt in range(3):

        try:

            bot.send_message(
                ADMIN_ID,
                admin_text,
                parse_mode="HTML",
                reply_markup=markup
            )

            return True

        except Exception as e:

            print(
                f"Ошибка отправки админу "
                f"(попытка {attempt + 1}): {e}"
            )

            time.sleep(1)

    return False


# =========================================================
# МОДЕРАЦИЯ АДМИНИСТРАТОРОМ
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("approve:")
    or call.data.startswith("reject:")
)
def admin_callback(call):

    # Только администратор
    if call.from_user.id != ADMIN_ID:

        bot.answer_callback_query(
            call.id,
            "⛔ У вас нет доступа.",
            show_alert=True
        )

        return

    action, application_id_text = (
        call.data.split(":")
    )

    application_id = int(
        application_id_text
    )

    application = get_application(
        application_id
    )

    if not application:

        bot.answer_callback_query(
            call.id,
            "Заявка не найдена.",
            show_alert=True
        )

        return

    (
        app_id,
        user_id,
        first_name,
        username,
        text,
        status
    ) = application

    if status != "pending":

        bot.answer_callback_query(
            call.id,
            f"Заявка уже обработана: {status}",
            show_alert=True
        )

        return

    # =====================================================
    # ОДОБРЕНИЕ
    # =====================================================

    if action == "approve":

        update_application_status(
            application_id,
            "approved"
        )

        safe_text = html.escape(
            text
        )

        # Отправляем пользователю
        try:

            bot.send_message(
                user_id,
                "🎉 <b>Твоя заявка одобрена!</b>\n\n"
                "Объявление прошло модерацию.",
                parse_mode="HTML"
            )

        except Exception as e:

            print(
                f"Не удалось уведомить пользователя: {e}"
            )

        # Если GROUP_ID указан,
        # публикуем в группе
        if GROUP_ID:

            try:

                username_text = (
                    f"@{username}"
                    if username
                    else "Связь через Telegram"
                )

                publication = (
                    f"📢 <b>Новое объявление "
                    f"Vitrina.md</b>\n\n"
                    f"📝 {safe_text}\n\n"
                    f"👤 Автор: "
                    f"{html.escape(first_name)}\n"
                    f"📩 {html.escape(username_text)}\n\n"
                    f"🆔 Объявление №{app_id}"
                )

                bot.send_message(
                    GROUP_ID,
                    publication,
                    parse_mode="HTML"
                )

            except Exception as e:

                print(
                    f"Ошибка публикации в группе: {e}"
                )

        bot.edit_message_text(
            f"✅ <b>Заявка №{application_id} "
            f"опубликована.</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )

        bot.answer_callback_query(
            call.id,
            "Заявка опубликована!"
        )

    # =====================================================
    # ОТКЛОНЕНИЕ
    # =====================================================

    elif action == "reject":

        update_application_status(
            application_id,
            "rejected"
        )

        try:

            bot.send_message(
                user_id,
                "❌ <b>Заявка отклонена.</b>\n\n"
                "Объявление не прошло модерацию.",
                parse_mode="HTML"
            )

        except Exception as e:

            print(
                f"Не удалось уведомить пользователя: {e}"
            )

        bot.edit_message_text(
            f"❌ <b>Заявка №{application_id} "
            f"отклонена.</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )

        bot.answer_callback_query(
            call.id,
            "Заявка отклонена."
        )


# =========================================================
# ЗАПУСК БОТА
# =========================================================

if __name__ == "__main__":

    init_database()

    print("--------------------------------")
    print("Vitrina.md бот запущен")
    print("--------------------------------")

    bot.infinity_polling(
        skip_pending=True,
        interval=1,
        timeout=30
    )
