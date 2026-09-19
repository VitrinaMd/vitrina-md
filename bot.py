import os
import sqlite3
import html
import time
import telebot

from telebot import types


# =========================================================
# НАСТРОЙКИ
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "ВСТАВЬ_СЮДА_НОВЫЙ_ТОКЕН")
ADMIN_ID = 7419021481

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
        SELECT id, user_id, first_name, username, text, status
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
    """, (status, application_id))

    conn.commit()
    conn.close()


# =========================================================
# ОТПРАВКА АДМИНИСТРАТОРУ
# =========================================================

def send_to_admin(application_id):

    application = get_application(application_id)

    if not application:
        return False

    app_id, user_id, first_name, username, text, status = application

    username_text = (
        f"@{username}"
        if username
        else f"ID: {user_id}"
    )

    safe_first_name = html.escape(first_name)
    safe_username = html.escape(username_text)
    safe_text = html.escape(text)

    admin_text = (
        f"🚨 <b>Новая заявка №{app_id}</b>\n\n"
        f"👤 <b>Пользователь:</b> {safe_first_name}\n"
        f"🔗 <b>Контакт:</b> {safe_username}\n"
        f"🆔 <b>ID:</b> {user_id}\n\n"
        f"📝 <b>Объявление:</b>\n"
        f"{safe_text}\n\n"
        f"🟡 <b>Статус:</b> На модерации"
    )

    markup = types.InlineKeyboardMarkup(row_width=2)

    approve_button = types.InlineKeyboardButton(
        "✅ Опубликовать",
        callback_data=f"approve:{app_id}"
    )

    reject_button = types.InlineKeyboardButton(
        "❌ Отклонить",
        callback_data=f"reject:{app_id}"
    )

    markup.add(
        approve_button,
        reject_button
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
# /START
# =========================================================

@bot.message_handler(commands=["start"])
def start_command(message):

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    button = types.KeyboardButton(
        "📝 Разместить заказ / резюме"
    )

    markup.add(button)

    bot.send_message(
        message.chat.id,
        "👋 <b>Привет!</b>\n\n"
        "Добро пожаловать в <b>Vitrina.md</b> — "
        "маркетплейс фриланса.\n\n"
        "Здесь можно разместить заказ или предложить "
        "свои услуги.\n\n"
        "Нажми кнопку ниже 👇",
        parse_mode="HTML",
        reply_markup=markup
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

    cancel_button = types.KeyboardButton("❌ Отмена")

    markup.add(cancel_button)

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
# ОБРАБОТКА ОПИСАНИЯ
# =========================================================

def process_description(message):

    if message.text == "❌ Отмена":

        send_main_menu(message.chat.id)

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

    # Ограничение размера
    if len(text) > 3500:

        msg = bot.send_message(
            message.chat.id,
            "❌ Текст слишком длинный.\n\n"
            "Максимальная длина — 3500 символов.\n"
            "Сократи описание и отправь ещё раз."
        )

        bot.register_next_step_handler(
            msg,
            process_description
        )

        return

    safe_text = html.escape(text)

    markup = types.InlineKeyboardMarkup(row_width=2)

    send_button = types.InlineKeyboardButton(
        "✅ Отправить",
        callback_data="confirm"
    )

    edit_button = types.InlineKeyboardButton(
        "✏️ Изменить",
        callback_data="edit"
    )

    cancel_button = types.InlineKeyboardButton(
        "❌ Отмена",
        callback_data="cancel"
    )

    markup.add(
        send_button,
        edit_button,
        cancel_button
    )

    # Временно сохраняем текст в объекте Telegram-сообщения
    # через следующий шаг
    bot.send_message(
        message.chat.id,
        "👀 <b>Предпросмотр объявления:</b>\n\n"
        f"{safe_text}\n\n"
        "Всё правильно?",
        parse_mode="HTML",
        reply_markup=markup
    )

    # Сохраняем временное состояние
    bot.register_next_step_handler_by_chat_id(
        message.chat.id,
        lambda msg: None
    )

    temporary_data[message.from_user.id] = text


# =========================================================
# ВРЕМЕННЫЕ ДАННЫЕ
# =========================================================

temporary_data = {}


# =========================================================
# CALLBACK-КНОПКИ ПОЛЬЗОВАТЕЛЯ
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data in ["confirm", "edit", "cancel"]
)
def user_callback(call):

    user_id = call.from_user.id

    if call.data == "cancel":

        temporary_data.pop(user_id, None)

        bot.edit_message_text(
            "❌ <b>Создание объявления отменено.</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )

        bot.answer_callback_query(call.id)

        send_main_menu(call.message.chat.id)

        return

    if call.data == "edit":

        text = temporary_data.get(user_id)

        if not text:

            bot.answer_callback_query(
                call.id,
                "Сессия устарела. Начни заново через /start",
                show_alert=True
            )

            return

        msg = bot.send_message(
            call.message.chat.id,
            "✏️ Хорошо.\n\n"
            "Отправь исправленный текст объявления:"
        )

        bot.register_next_step_handler(
            msg,
            process_description
        )

        bot.answer_callback_query(call.id)

        return

    if call.data == "confirm":

        text = temporary_data.get(user_id)

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

        sent = send_to_admin(application_id)

        if sent:

            bot.edit_message_text(
                f"✅ <b>Заявка №{application_id} отправлена "
                f"администратору!</b>\n\n"
                "После проверки объявление будет опубликовано.",
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

        temporary_data.pop(user_id, None)

        bot.answer_callback_query(call.id)


# =========================================================
# CALLBACK-КНОПКИ АДМИНИСТРАТОРА
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("approve:")
    or call.data.startswith("reject:")
)
def admin_callback(call):

    # Защита: только администратор
    if call.from_user.id != ADMIN_ID:

        bot.answer_callback_query(
            call.id,
            "⛔ У вас нет доступа.",
            show_alert=True
        )

        return

    action, application_id_text = call.data.split(":")

    application_id = int(application_id_text)

    application = get_application(application_id)

    if not application:

        bot.answer_callback_query(
            call.id,
            "Заявка не найдена.",
            show_alert=True
        )

        return

    app_id, user_id, first_name, username, text, status = application

    if status != "pending":

        bot.answer_callback_query(
            call.id,
            f"Заявка уже обработана: {status}",
            show_alert=True
        )

        return

    if action == "approve":

        update_application_status(
            application_id,
            "approved"
        )

        safe_text = html.escape(text)

        # Сообщение пользователю
        try:

            bot.send_message(
                user_id,
                "🎉 <b>Твоя заявка одобрена!</b>\n\n"
                "Администратор проверил объявление.\n\n"
                f"📝 {safe_text}",
                parse_mode="HTML"
            )

        except Exception as e:

            print(
                f"Не удалось уведомить пользователя: {e}"
            )

        bot.edit_message_text(
            f"✅ <b>Заявка №{application_id} опубликована.</b>\n\n"
            f"👤 {html.escape(first_name)}\n"
            f"📝 {safe_text}",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )

        bot.answer_callback_query(
            call.id,
            "Заявка опубликована!"
        )

    elif action == "reject":

        update_application_status(
            application_id,
            "rejected"
        )

        try:

            bot.send_message(
                user_id,
                "❌ <b>Заявка отклонена.</b>\n\n"
                "К сожалению, объявление не прошло "
                "модерацию.",
                parse_mode="HTML"
            )

        except Exception as e:

            print(
                f"Не удалось уведомить пользователя: {e}"
            )

        bot.edit_message_text(
            f"❌ <b>Заявка №{application_id} отклонена.</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )

        bot.answer_callback_query(
            call.id,
            "Заявка отклонена."
        )


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
# ЗАПУСК
# =========================================================

if __name__ == "__main__":

    init_database()

    print("================================")
    print("Vitrina.md бот запущен")
    print("================================")

    bot.infinity_polling(
        skip_pending=True,
        interval=1,
        timeout=30
    )
