import os
import re
import random
import threading
from collections import defaultdict
import telebot
from telebot import types

from hangman import hangman

token = os.environ.get('TOKEN')
bot = telebot.TeleBot(token)

# Список символов кириллицы для буквенной клавиатуры "Лингвиселицы"
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

# Загрузка словаря и генерация сочетаний для ХОМО
cleaned_words_set = set()
combo_freq = defaultdict(int)
try:
    with open('russian.txt', 'r', encoding='windows-1251') as f:
        for line in f:
            word = line.strip()
            if re.match(r'^[а-яё]+$', word):
                cleaned_words_set.add(word)
                subs = set()
                wlen = len(word)
                for length in (2, 3):
                    for i in range(wlen - length + 1):
                        subs.add(word[i:i + length])
                for s in subs:
                    combo_freq[s] += 1
except FileNotFoundError:
    print("[WARNING] russian.txt не найден.")

homo_combos = {
    'easy': [s for s, count in combo_freq.items() if 500 <= count <= 999],
    'medium': [s for s, count in combo_freq.items() if 100 <= count <= 499],
    'hard': [s for s, count in combo_freq.items() if 10 <= count <= 99]
}

GAMES = {
    'lingviselica': {'name': 'Лингвиселица 🪓', 'desc': 'Угадай лингвистический термин или фразеологизм по буквам.'},
    'homo': {'name': 'ХОМО 💡', 'desc': 'Придумай слово, содержащее заданное буквосочетание (чем больше сложность, тем более редкие попадаются). На придумывание даётся 10 секунд. Слово нужно писать ЗАГЛАВНЫМИ буквами.'}
}

USER_MEMORY = {}
chats = {}


def init_user(user_id):
    if user_id not in USER_MEMORY:
        USER_MEMORY[user_id] = {'active_game': None}


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
            bot.edit_message_text(chat_id=chat_id, message_id=chat['msg'].id, text=text, parse_mode='HTML')
    except Exception as e:
        print(f"[Error in upd]: {e}")


def start_hangman_game(chat_id, user_id, mode):
    source_dict = words if mode == 'terms' else frazeos
    if not source_dict:
        bot.send_message(chat_id, "⚠️ Словарь пуст или не найден.")
        return

    word = random.choice(list(source_dict.keys()))
    info = source_dict[word]
    view = ''.join(i + ' ' if i == ' ' else '_ ' for i in word)

    bot.send_message(chat_id, "(Нажимайте на кнопки с буквами или введите догадку целиком)", reply_markup=keyboard)

    chats[chat_id] = {
        'game': 'lingviselica',
        'w': word,
        'view': view,
        'mis': 0,
        'abc': {c: 7 for c in cyr},
        'info': info,
        'msg': None
    }

    msg = bot.send_message(chat_id, text=f"<code>{hangman[0]}</code>\n{view}", parse_mode='HTML')
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


# Функции игры ХОМО
def start_homo_game(chat_id, user_id, lvl):
    init_user(user_id)
    USER_MEMORY[user_id]['active_game'] = 'homo'
    chats[chat_id] = {
        'game': 'homo',
        'lvl': lvl,
        'score': 0,
        'active': True,
        'timer': None,
        'combo': None
    }
    send_next_homo_combo(chat_id)


def send_next_homo_combo(chat_id):
    session = chats.get(chat_id)
    if not session or not session['active']:
        return

    combos = homo_combos.get(session['lvl'], [])
    if not combos:
        bot.send_message(chat_id, "⚠️ Нет доступных сочетаний.")
        return

    combo = random.choice(combos).upper()
    session['combo'] = combo

    bot.send_message(chat_id, f"⏱ Напишите слово, содержащее: **{combo}**", parse_mode="Markdown")

    if session['timer']:
        session['timer'].cancel()

    timer = threading.Timer(10.0, homo_timeout, args=[chat_id])
    session['timer'] = timer
    timer.start()


def homo_timeout(chat_id):
    session = chats.get(chat_id)
    if session and session['active'] and session['game'] == 'homo':
        session['active'] = False
        score = session['score']
        session['timer'] = None

        bot.send_message(chat_id, f"⏱ Время вышло!\nИгра окончена. Вы успели назвать слов: **{score}**",
                         parse_mode="Markdown")

        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🟢 Легкий режим", callback_data="play_homo_easy"),
            types.InlineKeyboardButton("⚙️ Непростой режим", callback_data="play_homo_medium"),
            types.InlineKeyboardButton("🔥 Невозможный режим", callback_data="play_homo_hard"),
            types.InlineKeyboardButton("🔙 Главное меню", callback_data="to_menu")
        )
        bot.send_message(chat_id, "Попробуем снова?", reply_markup=markup)


# Команды
@bot.message_handler(commands=['start'])
def start_command(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "❌ Бот работает только в личных сообщениях.")
        return

    user_id = message.from_user.id
    init_user(user_id)
    USER_MEMORY[user_id]['active_game'] = None

    bot.send_message(message.chat.id, "👋 **Добро пожаловать в лингвистический игровой бот!**\n\nВыбирай мини-игру:",
                     reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")


@bot.message_handler(commands=['jajemdedov'])
def jajemdedov(message):
    remove_markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Скрываю клавиатуру букв...", reply_markup=remove_markup)


@bot.message_handler(commands=['test'])
def test(message):
    if frazeos:
        ch = random.choice(list(frazeos.keys()))
        bot.reply_to(message, text=f"**Пример:** {ch} — {frazeos[ch]}", parse_mode='Markdown')
    else:
        bot.reply_to(message, text="Словарь пуст.")


# Обработка колбэков меню
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    init_user(user_id)

    data = call.data

    if data == "to_menu":
        USER_MEMORY[user_id]['active_game'] = None
        if chat_id in chats:
            if chats[chat_id].get('timer'):
                chats[chat_id]['timer'].cancel()
            chats[chat_id]['active'] = False
            chats[chat_id]['w'] = None
        bot.clear_step_handler_by_chat_id(chat_id)
        bot.edit_message_text("Выбирай мини-игру из списка:", chat_id, message_id,
                              reply_markup=get_main_menu_keyboard())
        bot.answer_callback_query(call.id)
        return

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
        elif game_key == 'homo':
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("🟢 Легкий", callback_data="play_homo_easy"),
                types.InlineKeyboardButton("⚙️ Непростой", callback_data="play_homo_medium"),
                types.InlineKeyboardButton("🔥 Невозможный", callback_data="play_homo_hard")
            )
            markup.add(types.InlineKeyboardButton("🔙 В главное меню", callback_data="to_menu"))
            text = f"🎮 **Игра:** {GAMES[game_key]['name']}\n\nℹ️ {GAMES[game_key]['desc']}\n\n**Выберите сложность:**"
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="Markdown")

        bot.answer_callback_query(call.id)
        return

    if data.startswith("play_"):
        parts = data.split("_")
        game_key = parts[1]
        bot.delete_message(chat_id, message_id)

        if game_key == 'lingviselica':
            start_hangman_game(chat_id, user_id, parts[2])
        elif game_key == 'homo':
            start_homo_game(chat_id, user_id, parts[2])

        bot.answer_callback_query(call.id)
        return


# Игровой процесс ХОМО
@bot.message_handler(
    func=lambda msg: msg.chat.id in chats and chats[msg.chat.id].get('game') == 'homo' and chats[msg.chat.id].get(
        'active'))
def handle_homo_message(message):
    chat_id = message.chat.id
    session = chats[chat_id]
    text = message.text.strip()

    is_alphabetic = re.match(r'^[А-ЯЁа-яё]+$', text)
    is_all_caps = text.isupper() if is_alphabetic else False
    contains_combo = session['combo'] in text if is_all_caps else False
    in_dict = text.lower() in cleaned_words_set if contains_combo else False

    if is_all_caps and contains_combo and in_dict:
        if session['timer']:
            session['timer'].cancel()
            session['timer'] = None
        session['score'] += 1
        send_next_homo_combo(chat_id)
    elif is_all_caps:
        try:
            bot.set_message_reaction(chat_id, message.message_id, [types.ReactionTypeEmoji("👎")])
        except Exception:
            pass


# Игровой процесс Лингвиселицы
@bot.message_handler(
    func=lambda msg: msg.chat.id in chats and chats[msg.chat.id].get('game') == 'lingviselica' and chats[
        msg.chat.id].get('w') is not None)
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
                bot.set_message_reaction(chat_id, message.message_id, [types.ReactionTypeEmoji("👎")])
            except Exception:
                pass
            upd(chat_id)
            if ch['mis'] >= len(hangman) - 1:
                bot.reply_to(message,
                             text=f'🥀💀 ВЫ ПРОИГРАЛИ! 💀🥀 \nБыло загадано <b>{ch["w"]}</b> — {ch["info"]}',
                             parse_mode='HTML', reply_markup=types.ReplyKeyboardRemove())
                ch['w'] = None
                show_game_over_menu(chat_id, user_id, 'lose')


if __name__ == '__main__':
    print("[INFO] Бот успешно запущен...")
    bot.infinity_polling()
