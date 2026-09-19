import datetime
import telebot
from telebot import types

# Твой токен от BotFather
TOKEN = '8724559334:AAEpp2ABawjVc8qZ1xOaqoYVTmWo97yKtGc'

# Твой Telegram ID администратора
ADMIN_ID = 7419021481

# Юзернейм твоего публичного канала
CHANNEL_ID = '@vitrina_freelance_md' 

bot = telebot.TeleBot(TOKEN)

# Словарь для отслеживания шагов пользователей
user_states = {}

def save_to_database(record_type, user_info, text):
    try:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"[{current_time}] TYPE: {record_type} | USER: {user_info}\nCONTENT: {text}\n" + "-"*40 + "\n"
        with open("database.txt", "a", encoding="utf-8") as f:
            f.write(record)
    except Exception as e:
        print(f"Ошибка сохранения в базу: {e}")

def get_latest_trends():
    trends_text = (
        "📰 **Тренды и советы для фрилансеров и заказчиков:**\n\n"
        "1. **Для специалистов:** Указывайте в резюме конкретные примеры работ и реальные контакты для быстрой связи.\n"
        "2. **Для заказчиков:** Четкое ТЗ (техническое задание) экономит время и гарантирует лучший результат.\n"
        "3. **Местный рынок:** Прямое сотрудничество без посредников — залог быстрой работы и честных цен.\n\n"
        "_Следите за обновлениями на платформе!_"
    )
    return trends_text

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user_states[user_id] = None
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    item_designer = types.KeyboardButton('🎨 Разместить резюме (Найти работу)')
    item_seller = types.KeyboardButton('🛍 Разместить заказ (Найти исполнителя)')
    item_news = types.KeyboardButton('📰 Новости и советы')
    item_about = types.KeyboardButton('ℹ️ О проекте')
    
    markup.add(item_designer, item_seller, item_news, item_about)
    
    welcome_text = (
        "Привет! 👋 Добро пожаловать на местную биржу фриланса.\n\n"
        "Здесь специалисты находят проекты, а работодатели — исполнителей.\n\n"
        "Выберите нужное действие в меню ниже:"
    )
    
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else f"ID: {user_id}"
    text = message.text
    current_state = user_states.get(user_id)

    if text == '🎨 Разместить резюме (Найти работу)':
        user_states[user_id] = 'waiting_for_designer_portfolio'
        bot.send_message(
            message.chat.id, 
            "👤 **Создание резюме специалиста:**\n\n"
            "Пожалуйста, отправьте одним сообщением:\n"
            "• Ваше имя / направление\n"
            "• Опыт работы и навыки\n"
            "• Ссылку на портфолио\n"
            "• Способ связи (Telegram / Телефон)",
            parse_mode='Markdown'
        )
    elif text == '🛍 Разместить заказ (Найти исполнителя)':
        user_states[user_id] = 'waiting_for_seller_task'
        bot.send_message(
            message.chat.id, 
            "📋 **Создание заказа:**\n\n"
            "Пожалуйста, опишите вашу задачу:\n"
            "• Что нужно сделать\n"
            "• Требования к исполнителю\n"
            "• Бюджет / Сроки\n"
            "• Как с вами связаться",
            parse_mode='Markdown'
        )
    elif text == '📰 Новости и советы':
        news_message = get_latest_trends()
        bot.send_message(message.chat.id, news_message, parse_mode='Markdown')
        
    elif text == 'ℹ️ О проекте':
        bot.send_message(
            message.chat.id, 
            "ℹ️ **О платформе:**\n\n"
            "Это независимая площадка для быстрой связи локальных специалистов и заказчиков.\n"
            "Все заявки проходят модерацию для защиты от спама.",
            parse_mode='Markdown'
        )
    
    else:
        if current_state == 'waiting_for_designer_portfolio':
            save_to_database("RESUME / SPECIALIST", username, text)
            
            admin_text = f"🎨 **Новое резюме!**\nОт: {username} (ID: `{user_id}`)\n\n{text}"
            
            admin_markup = types.InlineKeyboardMarkup(row_width=2)
            admin_markup.add(
                types.InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_des_{user_id}"),
                types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_des_{user_id}")
            )
            
            try:
                print(f"Пытаюсь отправить резюме админу {ADMIN_ID}...")
                bot.send_message(ADMIN_ID, admin_text, parse_mode='Markdown', reply_markup=admin_markup)
                print("Уведомление админу успешно отправлено!")
            except Exception as e:
                print(f"ОШИБКА отправки администратору: {e}")
            
            bot.send_message(
                message.chat.id, 
                "✅ Ваше резюме успешно отправлено администратору на модерацию!"
            )
            user_states[user_id] = None
            
        elif current_state == 'waiting_for_seller_task':
            save_to_database("ORDER / CLIENT", username, text)
            
            admin_text = f"🛍 **Новый заказ!**\nОт: {username} (ID: `{user_id}`)\n\n{text}"
            
            admin_markup = types.InlineKeyboardMarkup(row_width=2)
            admin_markup.add(
                types.InlineKeyboardButton("✅ Опубликовать", callback_data=f"approve_sel_{user_id}"),
                types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_sel_{user_id}")
            )
            
            try:
                print(f"Пытаюсь отправить заказ админу {ADMIN_ID}...")
                bot.send_message(ADMIN_ID, admin_text, parse_mode='Markdown', reply_markup=admin_markup)
                print("Уведомление админу успешно отправлено!")
            except Exception as e:
                print(f"ОШИБКА отправки администратору: {e}")
            
            bot.send_message(
                message.chat.id, 
                "✅ Ваш заказ успешно отправлен администратору на проверку!"
            )
            user_states[user_id] = None
            
        else:
            bot.send_message(
                message.chat.id, 
                "Пожалуйста, используйте кнопки меню или отправьте /start для перезапуска."
            )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    parts = data.split('_')
    action = parts[0]
    target_type = parts[1]
    target_user_id = int(parts[2])
    
    if action == 'approve':
        if target_type == 'des':
            bot.send_message(target_user_id, "🎉 Ваше резюме одобрено и опубликовано!")
            channel_post = f"📢 **Новое резюме на бирже!**\n\n{call.message.text.replace('🎨 **Новое резюме!**', '').strip()}"
        elif target_type == 'sel':
            bot.send_message(target_user_id, "🎉 Ваш заказ одобрен и опубликован!")
            channel_post = f"📢 **Новый заказ на бирже!**\n\n{call.message.text.replace('🛍 **Новый заказ!**', '').strip()}"
        
        # Отправка в публичный канал
        try:
            bot.send_message(CHANNEL_ID, channel_post, parse_mode='Markdown')
            print("Заявка успешно опубликована в канале!")
        except Exception as e:
            print(f"Ошибка публикации в канал: {e}")
            
        bot.edit_message_text(text=call.message.text + "\n\n**[СТАТУС: ОДОБРЕНО И ОПУБЛИКОВАНО ✅]**", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='Markdown')
        
    elif action == 'reject':
        if target_type == 'des':
            bot.send_message(target_user_id, "⚠️ Ваше резюме отклонено модератором.")
        else:
            bot.send_message(target_user_id, "⚠️ Ваш заказ отклонен модератором.")
            
        bot.edit_message_text(text=call.message.text + "\n\n**[СТАТУС: ОТКЛОНЕНО ❌]**", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='Markdown')

if __name__ == '__main__':
    print("Биржа фриланса запущена...")
    bot.infinity_polling()
