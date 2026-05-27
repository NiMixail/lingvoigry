import os
import random
import re
import telebot
from telebot import types

from hangman import hangman

token = os.environ.get('TOKEN')
bot = telebot.TeleBot(token)

# Список символов кириллицы для буквенной клавиатуры
cyr = list('АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ-.')
keyboard = types.ReplyKeyboardMarkup(row_width=5)
buttons = [types.KeyboardButton(text=letter) for letter in cyr]
keyboard.add(*buttons)

# Загрузка словарей терминов и фразеологизмов
words = {}
try:
    with open('dictionary.txt', 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.split(' * ')
            if len(parts) >= 2:
                words[parts[0]] = parts[1].strip()
except FileNotFoundError:
    print("[WARNING] dictionary.txt не найден.")

frazeos = {}
try:
    with open('dictionary_f_.txt', 'r', encoding='utf-8') as f:
        for line in f:
            cleaned_line = re.sub(r'</?div.*?>|<br.*?>|a href.*?.htm»', '', line
                                  ).replace('&amp;LT;', '⟨').replace('&amp;GT;', '⟩')
            parts = cleaned_line.split(' ###### ')
            if len(parts) >= 2:
                frazeo = re.sub(r'\(.*?\)', '', parts[0]).upper()
                frazeos[frazeo] = parts[1].strip()
except FileNotFoundError:
    print("[WARNING] dictionary_f_.txt не найден.")

# Доступные мини-игры в боте
GAMES = {
    'rugramle': {'name': 'RuGramle 🎵', 'desc': 'Угадай слово из 5 звуков по спектрограмме.', 'levels_count': 3},
    'lingviselica': {'name': 'Лингвиселица 🪓', 'desc': 'Угадай лингвистический термин или фразеологизм по буквам.',
                     'levels_count': 0},
    'homo': {'name': 'ХОМО 💡', 'desc': 'Придумай слово, содержащее заданное буквосочетание.', 'levels_count': 3},
    'guess_lang': {'name': 'Угадай язык 🌍', 'desc': 'Определи язык по письменному фрагменту текста.', 'levels_count': 3}
}

# Память активных сессий и состояний
USER_MEMORY = {}
chats = {}


def init_user(user_id):
    if user_id not in USER_MEMORY:
        USER_MEMORY[user_id] = {
            'active_game': None
        }


def get_main_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, info in GAMES.items():
        markup.add(types.InlineKeyboardButton(text=info['name'], callback_data=f"open_{key}"))
    return markup


def upd(chat_id):
    try:
        chat = chats[chat_id]
        text = f"<code>{hangman[chat['mis']]}</code>\n{chat['view']}"
        if text != chat['msg'].text:
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=chat['msg'].id,
                                  text=text,
                                  parse_mode='HTML')
    except Exception as e:
        print(f"[Error in upd]: {e}")


def start_hangman_game(chat_id, user_id, mode):
    # Метод запускает игру Лингвиселица на основе выбранного режима (terms / idioms)
    source_dict = words if mode == 'terms' else frazeos
    if not source_dict:
        bot.send_message(chat_id, "⚠️ Словарь пуст или не найден. Проверьте файлы словарей.")
        return

    word = random.choice(list(source_dict.keys()))
    info = source_dict[word]
    view = ''.join(i + ' ' if i == ' ' else '_ ' for i in word)

    # Принудительно вызываем клавиатуру букв
    bot.send_message(chat_id, "(Нажимайте на кнопки с буквами или введите догадку целиком)", reply_markup=keyboard)

    chats[chat_id] = {
        'w': word,
        'view': view,
        'mis': 0,
        'abc': {c: 7 for c in cyr},
        'info': info,
        'msg': None
    }

    msg = bot.send_message(chat_id,
                           text=f"<code>{hangman[0]}</code>\n{view}",
                           parse_mode='HTML')
    chats[chat_id]['msg'] = msg

    init_user(user_id)
    USER_MEMORY[user_id]['active_game'] = 'lingviselica'


def show_game_over_menu(chat_id, user_id, status):

    text = "Продолжим?" if status == 'win' else "Попробуем ещё раз?"

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔄 Сыграть снова (Термины)", callback_data="play_lingviselica_terms"),
        types.InlineKeyboardButton("💬 Сыграть снова (Фразеологизмы)", callback_data="play_lingviselica_idioms"),
        types.InlineKeyboardButton("🔙 В главное меню", callback_data="to_menu")
    )
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")


# Команда СТАРТ
@bot.message_handler(commands=['start'])
def start_command(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "❌ Бот работает только в личных сообщениях.")
        return

    user_id = message.from_user.id
    init_user(user_id)
    USER_MEMORY[user_id]['active_game'] = None

    welcome_text = (
        "👋 **Привет! Добро пожаловать в лингвистический игровой бот!**\n\n"
        "Выбирай мини-игру из списка ниже!"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")

@bot.message_handler(commands=['jajemdedov'])
def jajemdedov(message):
    remove_markup = types.ReplyKeyboardRemove()


@bot.message_handler(commands=['test'])
def test(message):
    if frazeos:
        ch = random.choice(list(frazeos.keys()))
        bot.reply_to(message, text=f"**Пример:** {ch} — {frazeos[ch]}", parse_mode='Markdown')
    else:
        bot.reply_to(message, text="Словарь фразеологизмов пуст или не загружен.")


# Обработка колбэков меню
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    init_user(user_id)

    data = call.data

    # Возврат в главное меню
    if data == "to_menu":
        USER_MEMORY[user_id]['active_game'] = None
        if chat_id in chats:
            chats[chat_id]['w'] = None
        bot.clear_step_handler_by_chat_id(chat_id)
        bot.edit_message_text("Выбирай мини-игру из списка:", chat_id, message_id,
                              reply_markup=get_main_menu_keyboard())
        bot.answer_callback_query(call.id)
        return

    # Открытие меню выбора режимов/уровней игры
    if data.startswith("open_"):
        game_key = data.split("_")[1]

        if game_key == 'lingviselica':
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("Термины 📖", callback_data="play_lingviselica_terms"),
                types.InlineKeyboardButton("Фразеологизмы 💬", callback_data="play_lingviselica_idioms")
            )
            markup.add(types.InlineKeyboardButton("🔙 В главное меню", callback_data="to_menu"))
            text = f"🎮 **Игра:** {GAMES[game_key]['name']}\n\nℹ️ {GAMES[game_key]['desc']}\n\n**Выберите категорию:**"
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            levels_count = GAMES[game_key]['levels_count']
            markup = types.InlineKeyboardMarkup(row_width=3)
            buttons = []
            for i in range(1, levels_count + 1):
                buttons.append(types.InlineKeyboardButton(f"Ур. {i}", callback_data=f"play_{game_key}_{i}"))
            markup.add(*buttons)
            markup.add(types.InlineKeyboardButton("🔙 В главное меню", callback_data="to_menu"))

            text = f"🎮 **Игра:** {GAMES[game_key]['name']}\n\nℹ️ {GAMES[game_key]['desc']}\n\n**Выберите уровень:**"
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="Markdown")

        bot.answer_callback_query(call.id)
        return

    # Запуск конкретного уровня / режима
    if data.startswith("play_"):
        parts = data.split("_")
        game_key = parts[1]
        bot.delete_message(chat_id, message_id)

        if game_key == 'lingviselica':
            mode = parts[2]  # 'terms' или 'idioms'
            start_hangman_game(chat_id, user_id, mode)
        else:
            lvl = int(parts[2])
            game_text = f"🎮 **Игра:** {GAMES[game_key]['name']}\n📈 **Уровень:** {lvl}\n\nТут процесс игры..."
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🟢 Симулировать Победу", callback_data=f"sim_win_{game_key}_{lvl}"),
                types.InlineKeyboardButton("🔴 Симулировать Поражение", callback_data=f"sim_lose_{game_key}_{lvl}")
            )
            markup.add(types.InlineKeyboardButton("🔙 Прервать игру", callback_data=f"open_{game_key}"))
            bot.send_message(chat_id, game_text, reply_markup=markup, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return

    # Симуляция исходов сторонних игр
    if data.startswith("sim_"):
        _, status, game_key, lvl = data.split("_")

        if status == "win":
            text = f"🎉 **ПОБЕДА в {GAMES[game_key]['name']} (Уровень {lvl})!**\nЧто делаем дальше?"
        else:
            text = f"😢 **ПОРАЖЕНИЕ в {GAMES[game_key]['name']} (Уровень {lvl})**\nПопробуем снова?"

        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🔄 Повторить уровень", callback_data=f"play_{game_key}_{lvl}"),
            types.InlineKeyboardButton("🎛 Выбрать другой уровень", callback_data=f"open_{game_key}"),
            types.InlineKeyboardButton("🔙 Главное меню", callback_data="to_menu")
        )

        bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id, reply_markup=markup,
                              parse_mode="Markdown")
        bot.answer_callback_query(call.id)


# Обработка игрового процесса Лингвиселицы (проверяем наличие активного слова у пользователя)
@bot.message_handler(func=lambda message: message.chat.id in chats and chats[message.chat.id].get('w') is not None)
def handle_hangman_message(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    ch = chats[chat_id]
    text = message.text

    if (ch['w'] and (len(text) == 1 or text == ch['w'])
            and (text.isupper() or not text.isalpha())):
        c = text
        if c in ch['w']:
            if c == ch['w']:
                ch['view'] = ''.join(i + ' ' for i in ch['w'])
            if c in ch['abc']:
                if ch['abc'][c] != 2:
                    ch['abc'][c] = 2
                    for i in range(len(ch['w'])):
                        if ch['w'][i] == c:
                            ch['view'] = ch['view'][:i * 2] + c + ' ' + ch['view'][(i + 1) * 2:]
                    upd(chat_id)
            if ch['view'] == ''.join(i + ' ' for i in ch['w']):
                bot.reply_to(message,
                             f"🎊🌟 ПОБЕДА! 🌟🎊 \nБыло действительно загадано <b>{ch['w']}</b> — {ch['info']}",
                             parse_mode='HTML', reply_markup=types.ReplyKeyboardRemove())
                ch['w'] = None
                show_game_over_menu(chat_id, user_id, 'win')
        else:
            if c in ch['abc']:
                ch['abc'][c] = 1
            ch['mis'] += 1
            try:
                bot.set_message_reaction(chat_id, message.message_id,
                                         [types.ReactionTypeEmoji("👎")])
            except Exception:
                pass
            upd(chat_id)
            if ch['mis'] >= len(hangman) - 1:
                bot.reply_to(message,
                             text=f'🥀💀 ВЫ ПРОИГРАЛИ! 💀🥀 \nБыло загадано <b>{ch["w"]}</b> — {ch["info"]}',
                             parse_mode='HTML', reply_markup=types.ReplyKeyboardRemove())
                ch['w'] = None
                show_game_over_menu(chat_id, user_id, 'lose')


# Запуск бота
if __name__ == '__main__':
    print("[INFO] Бот успешно запущен...")
    bot.infinity_polling()