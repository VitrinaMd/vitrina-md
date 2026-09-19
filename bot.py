import time
import telebot
from telebot import types

# Твой свежий токен от BotFather
TOKEN = '8724559334:AAGu2ncPaICSI2rDQvMs1HTTBgOXBD-gArE'
ADMIN_ID = 7419021481  # Твой подтвержденный ID администратора

bot = telebot.TeleBot(TOKEN)

# Временное хранилище для анкет пользователей
user_data = {}


def safe_send_to_admin(text, parse_mode=None, reply_markup=None):
  """Надежная отправка сообщений администратору с попыткой восстановления связи"""
  for attempt in range(3):
    try:
      bot.send_message(
          ADMIN_ID, text, parse_mode=parse_mode, reply_markup=reply_markup
      )
      return True
    except Exception as e:
      print(f'Попытка отправки администратору {attempt + 1} не удалась: {e}')
      time.sleep(1)
  return False


@bot.message_handler(commands=['start'])
def send_welcome(message):
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
  markup.add(types.KeyboardButton('📝 Разместить заказ / резюме'))
  bot.send_message(
      message.chat.id,
      'Привет! Добро пожаловать в маркетплейс фриланса.\nНажми кнопку'
      ' ниже, чтобы создать объявление.',
      reply_markup=markup,
  )


@bot.message_handler(
    func=lambda message: message.text == '📝 Разместить заказ / резюме'
)
def start_form(message):
  user_data[message.from_user.id] = {}
  msg = bot.send_message(
      message.chat.id,
      'Опиши подробно, что нужно сделать или какое у тебя предложение:',
      reply_markup=types.ReplyKeyboardRemove(),
  )
  bot.register_next_step_handler(msg, process_description)


def process_description(message):
  user_id = message.from_user.id
  user_data[user_id] = {'text': message.text, 'user': message.from_user}

  markup = types.InlineKeyboardMarkup()
  markup.add(
      types.InlineKeyboardButton(
          '✅ Отправить администратору', callback_data='confirm_send'
      ),
      types.InlineKeyboardButton('❌ Отменить', callback_data='cancel_send'),
  )

  bot.send_message(
      message.chat.id,
      f'Вот твое объявление:\n\n{message.text}\n\nВсё верно?',
      reply_markup=markup,
  )


@bot.callback_query_handler(
    func=lambda call: call.data in ['confirm_send', 'cancel_send']
)
def callback_handler(call):
  user_id = call.from_user.id

  if call.data == 'cancel_send':
    bot.edit_message_text(
        '❌ Публикация отменена.', call.message.chat.id, call.message.message_id
    )
    if user_id in user_data:
      del user_data[user_id]
    return

  if call.data == 'confirm_send':
    if user_id not in user_data:
      bot.answer_callback_query(call.id, 'Сессия устарела. Начни заново /start')
      return

    data = user_data[user_id]
    user_info = data['user']
    username_str = (
        f'@{user_info.username}'
        if user_info.username
        else f'ID: {user_info.id}'
    )

    admin_text = (
        f'🚨 **Новая заявка на публикацию!**\n\n'
        f'От: {user_info.first_name} ({username_str})\n\n'
        f'{data["text"]}'
    )

    # Пытаемся отправить админу через защищенную функцию
    success = safe_send_to_admin(admin_text, parse_mode='Markdown')

    if success:
      bot.edit_message_text(
          '✅ Заявка успешно отправлена администратору на модерацию!',
          call.message.chat.id,
          call.message.message_id,
      )
    else:
      # Если админу не дошло (например, нет диалога со старта)
      bot.edit_message_text(
          '⚠️ На сервере временная задержка связи. Пожалуйста, нажмите /start и'
          ' отправьте заказ еще раз.',
          call.message.chat.id,
          call.message.message_id,
      )

    # Сохраняем в локальную базу
    try:
      with open('database.txt', 'a', encoding='utf-8') as f:
        f.write(
            f'User: {user_info.id} | Text: {data["text"].replace(chr(10), " ")}\n'
        )
    except Exception as e:
      print(f'Ошибка записи в базу: {e}')

    if user_id in user_data:
      del user_data[user_id]


if __name__ == '__main__':
  print('Бот запущен...')
  bot.infinity_polling(skip_pending=True)
