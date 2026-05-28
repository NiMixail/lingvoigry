import os
import re
import random
import threading
import json
from collections import defaultdict
import telebot
from telebot import types

import matplotlib

matplotlib.use('Agg')

from hangman import hangman
from transcribtor import transcribtor
from spectromaker import spectromaker

token = os.environ.get('TOKEN')
bot = telebot.TeleBot(token)

# Список символов кириллицы для буквенной клавиатуры "Лингвиселицы"
cyr = list('АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ-.')
hangman_keyboard = types.ReplyKeyboardMarkup(row_width=5)
buttons = [types.KeyboardButton(text=letter) for letter in cyr]
hangman_keyboard.add(*buttons)

# Список символов для клавиатуры игры "Вордл" (Gramle)
symbols = ['а', 'о', 'у', 'э', 'ы', 'и', 'ь', 'ъ', 'ь°', 'ъ°', "б", "б'", "п", "п'", "г", "г'", "к", "к'", "д", "д'",
           "т", "т'", "з", "з'", "с", "с'", "ж", "ж'", "ш", "ш'", "в", "в'", "ф", "ф'", "х", "х'", "н", "н'", "м", "м'",
           "л", "л'", "р", "р'", "й", "ч'", "ц"]

gramle_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
gramle_buttons = [types.KeyboardButton(text=sym) for sym in symbols]
gramle_buttons.append(types.KeyboardButton(text="⌫"))
gramle_keyboard.add(*gramle_buttons, row_width=12)

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
    with open('russian.txt', 'r', encoding='utf-8') as f:
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
    'easy': [s for s, count in combo_freq.items() if 300 <= count <= 699],
    'medium': [s for s, count in combo_freq.items() if 100 <= count <= 299],
    'hard': [s for s, count in combo_freq.items() if 10 <= count <= 99]
}

GAMES = {
    'lingviselica': {'name': 'Лингвиселица 🪓', 'desc': 'Угадай лингвистический термин или фразеологизм по буквам.'},
    'homo': {'name': 'ХОМО 💡',
             'desc': 'Придумай слово (любой части речи, в любой форме), содержащее заданное буквосочетание. На придумывание даётся 10 секунд. Слово нужно писать ЗАГЛАВНЫМИ буквами.'},
    'gramle': {'name': 'RuGramle 📊',
               'desc': 'Угадайте транскрипцию (6 звуков) русского существительного по его спектрограмме. Игра по правилам Wordle: жирное выделение = жёлтый цвет, жирное с подчёркиванием = зелёный цвет.'},
           'linguesser': {'name': 'Угадай язык 📖', 'desc': 'Угадай язык по фрагменту текста (1 статья всеобщей декларации прав человека). На отгадку дается три попытки. После каждой попытки дается подсказка.'}}

USER_MEMORY = {}
chats = {}
LEADERBOARD_FILE = 'leaderboard.json'
leaderboard = {}


def tokenize(text):
    tokens = []
    modifiers = {"'", "°"}
    for char in text:
        if char in modifiers and tokens:
            tokens[-1] += char
        else:
            tokens.append(char)
    return tokens


def compare_words(guess, target):
    guess_tokens = tokenize(guess)
    target_tokens = tokenize(target)
    length = len(guess_tokens)
    result = [None] * length
    target_chars = list(target_tokens)

    for i in range(length):
        if i < len(target_tokens) and guess_tokens[i] == target_tokens[i]:
            result[i] = f"<b><u>{guess_tokens[i]}</u></b>"
            target_chars[i] = None

    for i in range(length):
        if result[i] is not None:
            continue
        if guess_tokens[i] in target_chars:
            result[i] = f"<b>{guess_tokens[i]}</b>"
            target_chars[target_chars.index(guess_tokens[i])] = None
        else:
            result[i] = f"<s>{guess_tokens[i]}</s>"
    return " ".join(result)


# Функции работы с лидербордом
def load_leaderboard():
    global leaderboard
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                leaderboard = {int(k): v for k, v in data.items()}
        except Exception as e:
            print(f"[Error loading leaderboard]: {e}")
            leaderboard = {}
    else:
        leaderboard = {}


def save_leaderboard():
    try:
        with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
            json.dump({str(k): v for k, v in leaderboard.items()}, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[Error saving leaderboard]: {e}")


def update_score(user_id, username, points):
    if not user_id:
        return
    load_leaderboard()
    if user_id not in leaderboard:
        leaderboard[user_id] = {'name': username or f"User {user_id}", 'score': 0}
    if username:
        leaderboard[user_id]['name'] = username
    leaderboard[user_id]['score'] += points
    save_leaderboard()


def get_user_display_name(user):
    if not user:
        return "Аноним"
    if user.username:
        return f"@{user.username}"
    first = user.first_name or ""
    last = user.last_name or ""
    name = f"{first} {last}".strip()
    return name if name else f"User {user.id}"


def init_user(user_id):
    if user_id not in USER_MEMORY:
        USER_MEMORY[user_id] = {'active_game': None}


def get_main_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, info in GAMES.items():
        markup.add(types.InlineKeyboardButton(text=info['name'], callback_data=f"open_{key}", style='primary'))
    markup.add(types.InlineKeyboardButton(text="Справка ℹ️", callback_data="open_help"))
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

    bot.send_message(chat_id, "(Нажимайте на кнопки с буквами или введите догадку целиком)",
                     reply_markup=hangman_keyboard)

    chats[chat_id] = {
        'game': 'lingviselica',
        'mode': mode,
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

#функции игры угадай язык

def linguesser_gameover(chat_id, user_id):
    text = "Попробуем ещё раз?"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖖 Сыграть снова (Режим: простой)", callback_data="play_linguesser_easy"),
        types.InlineKeyboardButton("⚡️ Сыграть снова (Режим: средний)", callback_data="play_linguesser_medium"),
        types.InlineKeyboardButton("🤯 Сыграть снова (Режим: сложный)", callback_data="play_linguesser_hard"),
        types.InlineKeyboardButton("🔙 В главное меню", callback_data="to_menu")
    )
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

def start_linguesser_game(chat_id, user_id, lvl):
    
    if lvl == "easy":
        with open('угадай язык/простой.txt', 'r', encoding='utf-8') as f:
            langs = f.readlines()
            a = (random.randint(0,69))*4
            
            lang, info, text = langs[a].strip(), langs[a+1].strip(), langs[a+2].strip()
    elif lvl == "medium":
        with open('угадай язык/средний.txt', 'r', encoding='utf-8') as f:
            langs = f.readlines()
            a = (random.randint(0,78))*4
            lang, info, text = langs[a].strip(), langs[a+1].strip(), langs[a+2].strip()
    elif lvl == "hard":
        with open('угадай язык/сложный.txt', 'r', encoding='utf-8') as f:
            langs = f.readlines()
            a = (random.randint(0,54))*4
            lang, info, text = langs[a].strip(), langs[a+1].strip(), langs[a+2].strip()
    
    if text[-4:] == ".jpg":
        with open(f"угадай язык/{text}", 'rb') as photo:
            bot.send_photo(chat_id, photo)
    else:

        bot.send_message(chat_id, text)

    init_user(user_id)
    USER_MEMORY[user_id]['active_game'] = 'linguesser'
    chats[chat_id] = {
        'game': 'linguesser',
        'lvl': lvl,
        'score': 0,
        'tries': 3,
        'lang': lang,
        'info': info,
        'text': text,
        'played': []

    }

def send_lang(chat_id, user_id, lvl):
    ch = chats[chat_id]
    while ch["lang"] in ch["played"]:
        if lvl == "easy":
            with open('угадай язык/простой.txt', 'r', encoding='utf-8') as f:
                langs = f.readlines()
                a = (random.randint(0,69))*4
            
                lang, info, text = langs[a].strip(), langs[a+1].strip(), langs[a+2].strip()
        elif lvl == "medium":
            with open('угадай язык/средний.txt', 'r', encoding='utf-8') as f:
                langs = f.readlines()
                a = (random.randint(0,78))*4
                lang, info, text = langs[a].strip(), langs[a+1].strip(), langs[a+2].strip()
        elif lvl == "hard":
            with open('угадай язык/сложный.txt', 'r', encoding='utf-8') as f:
                langs = f.readlines()
                a = (random.randint(0,54))*4
                lang, info, text = langs[a].strip(), langs[a+1].strip(), langs[a+2].strip()
        ch['lang'] = lang
        ch['info'] = info

    if text[-4:] == ".jpg":
        with open(f"угадай язык/{text}", 'rb') as photo:
            bot.send_photo(chat_id, photo)
    else:
        bot.send_message(chat_id, text)


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
        'combo': None,
        'last_guesser_id': None,
        'last_guesser_name': None
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

        last_id = session.get('last_guesser_id')
        last_name = session.get('last_guesser_name')

        if last_id is not None:
            update_score(last_id, last_name, -10)

        bot.send_message(chat_id, f"⏱ Время вышло!\nИгра окончена. Вы успели назвать слов: **{score}**.",
                         parse_mode="Markdown")

        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🟢 Легкий режим", callback_data="play_homo_easy"),
            types.InlineKeyboardButton("⚙️ Непростой режим", callback_data="play_homo_medium"),
            types.InlineKeyboardButton("🔥 Невозможный режим", callback_data="play_homo_hard"),
            types.InlineKeyboardButton("🔙 Главное меню", callback_data="to_menu")
        )
        bot.send_message(chat_id, "Попробуем снова?", reply_markup=markup)


# Функции игры ВОРДЛ (Gramle)
def start_gramle_game(chat_id, user_id):
    init_user(user_id)
    USER_MEMORY[user_id]['active_game'] = 'gramle'

    word = ""
    if os.path.exists('wordlist.txt'):
        try:
            with open('wordlist.txt', 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
                if lines:
                    word = random.choice(lines)
        except Exception as e:
            print(f"[Error reading wordlist.txt]: {e}")

    if not word:
        word = "пример"

    target = transcribtor(word)
    word_lower = word.lower()

    wait_msg = bot.send_message(chat_id, "⌛ Генерируем спектрограмму, подождите...")

    filename = f"spectrogram_{chat_id}.png"
    try:
        spectromaker(word_lower, filename)
    except Exception as e:
        bot.edit_message_text(f"⚠️ Ошибка при генерации спектрограммы: {e}", chat_id, wait_msg.message_id)
        return

    try:
        bot.delete_message(chat_id, wait_msg.message_id)
    except Exception:
        pass

    # Отправляем фото спектрограммы с клавиатурой ввода
    try:
        with open(filename, 'rb') as photo:
            bot.send_photo(
                chat_id,
                photo,
                caption="🔍 Спектрограмма загаданного слова:",
                reply_markup=gramle_keyboard
            )
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ Не удалось отправить спектрограмму: {e}")

    try:
        os.remove(filename)
    except Exception:
        pass

    msg = bot.send_message(
        chat_id,
        "📝 <b>Результаты ваших попыток (0/6):</b>\n\n<i>Ожидание первой попытки...</i>",
        parse_mode="HTML"
    )

    chats[chat_id] = {
        'game': 'gramle',
        'word': word,
        'target': target,
        'attempts_history': [],
        'current_guess': [],
        'last_msgs': [],
        'msg_id': msg.message_id,  # сохраняем ID сообщения для редактирования
        'active': True
    }


def show_gramle_game_over_menu(chat_id, user_id, status):
    text = "Продолжим?" if status == 'win' else "Попробуем ещё раз?"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔄 Сыграть снова", callback_data="play_gramle"),
        types.InlineKeyboardButton("🔙 В главное меню", callback_data="to_menu")
    )
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")


# Команды
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    init_user(user_id)
    USER_MEMORY[user_id]['active_game'] = None

    bot.send_message(message.chat.id, "👋 **Добро пожаловать в лингвистический игровой бот!**\n\nВыбирай мини-игру:",
                     reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")


@bot.message_handler(commands=['leaderboard'])
def leaderboard_command(message):
    load_leaderboard()
    if not leaderboard:
        bot.reply_to(message, "🏆 Лидерборд пока пуст. Будьте первыми!")
        return

    sorted_users = sorted(leaderboard.items(), key=lambda x: x[1]['score'], reverse=True)
    top_10 = sorted_users[:10]

    text = "🏆 **ТОП-10 ИГРОКОВ** 🏆\n\n"
    for i, (uid, data) in enumerate(top_10, 1):
        safe_name = data['name'].replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
        text += f"{i}. {safe_name} — **{data['score']}** баллов\n"

    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(commands=['removekeyboard'])
def remove_keyboard_command(message):
    remove_markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Скрываю клавиатуру...", reply_markup=remove_markup)


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

    if data == "open_help":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🔙 В главное меню", callback_data="to_menu"))
        bot.edit_message_text("""Бот создан @nimixail, @usenkoam, @autopsied, @cizzef в мае 2026 года в рамках проекта по программированию первого курса ФиКЛ ВШЭ. Если есть предложения или нашли ошибки, пишите @nimixail.

*Доступные команды:*
/start — главное меню
/leaderboard — топ лучших игроков бота 🏆
/removekeyboard — удалить клавиатуру с кнопками, если почему-то не убралась сама
""", chat_id, message_id, reply_markup=markup, parse_mode="Markdown")
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
        elif game_key == 'gramle':
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("🎮 Начать игру", callback_data="play_gramle"),
                types.InlineKeyboardButton("🔙 В главное меню", callback_data="to_menu")
            )
            text = f"🎮 **Игра:** {GAMES[game_key]['name']}\n\nℹ️ {GAMES[game_key]['desc']}"
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="Markdown")
        elif game_key == "linguesser":
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("🖖 Простой 🖖", callback_data="play_linguesser_easy"),
                types.InlineKeyboardButton("⚡️ Средний ⚡️", callback_data="play_linguesser_medium"),
                types.InlineKeyboardButton("🤯 Сложный 🤯", callback_data="play_linguesser_hard")
            )
            markup.add(types.InlineKeyboardButton("🔙 В главное меню", callback_data="to_menu"))
            text = f"🎮 **Игра:** {GAMES[game_key]['name']}\n\nℹ️ {GAMES[game_key]['desc']}\n\n**Выберите сложность:**"
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="Markdown")

        bot.answer_callback_query(call.id)
        return

    if data.startswith("play_"):
        parts = data.split("_")
        game_key = parts[1]
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass

        if game_key == 'lingviselica':
            start_hangman_game(chat_id, user_id, parts[2])
        elif game_key == 'homo':
            start_homo_game(chat_id, user_id, parts[2])
        elif game_key == 'gramle':
            start_gramle_game(chat_id, user_id)
        elif game_key == "linguesser":
            start_linguesser_game(chat_id, user_id, parts[2])

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

    is_alphabetic = bool(re.match(r'^[А-ЯЁа-яё]+$', text))
    is_all_caps = text.isupper() if is_alphabetic else False
    contains_combo = (session['combo'] in text) if is_all_caps else False
    in_dict = (text.lower() in cleaned_words_set) if contains_combo else False

    if is_all_caps and contains_combo and in_dict:
        if session['timer']:
            session['timer'].cancel()
            session['timer'] = None
        session['score'] += 1

        points = 1 if session['lvl'] == 'easy' else (2 if session['lvl'] == 'medium' else 3)
        username = get_user_display_name(message.from_user)
        update_score(message.from_user.id, username, points)

        session['last_guesser_id'] = message.from_user.id
        session['last_guesser_name'] = username

        send_next_homo_combo(chat_id)
    elif is_all_caps:
        try:
            bot.set_message_reaction(chat_id, message.message_id, [types.ReactionTypeEmoji("👎")])
        except Exception:
            pass

# Игровой процесс угадай язык
@bot.message_handler(
    func=lambda msg: msg.chat.id in chats and chats[msg.chat.id].get('game') == 'linguesser' and chats[
        msg.chat.id].get('lang') is not None)
def handle_linguesser_message(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    ch = chats[chat_id]
    t = message.text
    
    if ch["lang"].lower() == t.lower():
        bot.reply_to(message, "Верно!")
        ch["played"].append(ch["lang"])
        ch["tries"] = 3
        if ch['lvl'] == "easy":
            ch['score'] += 2
        elif ch['lvl'] == "medium":
            ch['score'] += 5
        elif ch['lvl'] == "hard":
            ch['score'] += 10
        
        send_lang(chat_id, user_id, ch["lvl"])
    else:
        ch["tries"] -= 1
        try:
            bot.set_message_reaction(chat_id, message.message_id, [types.ReactionTypeEmoji("👎")])
        except Exception:
            pass
        if ch["tries"] == 2:
            bot.send_message(message.chat.id, f"Подсказка: первая буква в названии языка {ch["lang"][0]}.")
        elif ch['tries'] == 1:
            bot.send_message(message.chat.id, f"Подсказка: язык относится к таксонам {ch["info"]}.")
        elif ch['tries'] == 0:
            bot.send_message(message.chat.id, f"Вы проиграли! Это {ch["lang"].lower()}.")
            username = get_user_display_name(message.from_user)
            update_score(message.from_user.id, username, ch['score'])
            linguesser_gameover(chat_id, user_id)


# Игровой процесс ВОРДЛ (Gramle)
@bot.message_handler(
    func=lambda msg: msg.chat.id in chats and chats[msg.chat.id].get('game') == 'gramle' and chats[msg.chat.id].get(
        'active'))
def handle_gramle_message(message):
    chat_id = message.chat.id
    session = chats[chat_id]
    text = message.text.strip()

    if text == "⌫":
        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass

        if session['current_guess']:
            session['current_guess'].pop()
            if session['last_msgs']:
                last_msg_id = session['last_msgs'].pop()
                try:
                    bot.delete_message(chat_id, last_msg_id)
                except Exception:
                    pass
        return

    if text in symbols:
        session['current_guess'].append(text)
        session['last_msgs'].append(message.message_id)

        if len(session['current_guess']) == 6:
            result_string = "".join(session['current_guess'])

            for msg_id in session['last_msgs']:
                try:
                    bot.delete_message(chat_id, msg_id)
                except Exception:
                    pass
            session['last_msgs'].clear()

            result_formatted = compare_words(result_string, session['target'])
            session['attempts_history'].append(result_formatted)

            guess_tokens = tokenize(result_string)
            target_tokens = tokenize(session['target'])
            is_win = (guess_tokens == target_tokens)

            history_text = "\n".join(
                [f"Попытка {idx + 1}: {attempt}" for idx, attempt in enumerate(session['attempts_history'])])

            if is_win:
                session['active'] = False
                username = get_user_display_name(message.from_user)
                update_score(message.from_user.id, username, 20)

                final_text = f"🎉 <b>ПОБЕДА!</b>\nВы правильно угадали транскрипцию!\n\n{history_text}\n\nСлово: <b>{session['word']}</b> [{session['target']}]"
                try:
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=session['msg_id'],
                        text=final_text,
                        parse_mode="HTML"
                    )
                except Exception:
                    bot.send_message(chat_id, final_text, parse_mode="HTML")

                # Скрываем виртуальную клавиатуру
                try:
                    rem_msg = bot.send_message(chat_id, "Выход из игрового режима...",
                                               reply_markup=types.ReplyKeyboardRemove())
                    bot.delete_message(chat_id, rem_msg.message_id)
                except Exception:
                    pass

                show_gramle_game_over_menu(chat_id, message.from_user.id, 'win')
            else:
                if len(session['attempts_history']) >= 6:
                    session['active'] = False
                    username = get_user_display_name(message.from_user)
                    update_score(message.from_user.id, username, -10)

                    final_text = f"💀 <b>ИГРА ОКОНЧЕНА!</b> Попытки исчерпаны.\n\n{history_text}\n\nБыло загадано слово: <b>{session['word']}</b> [{session['target']}]"
                    try:
                        bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=session['msg_id'],
                            text=final_text,
                            parse_mode="HTML"
                        )
                    except Exception:
                        bot.send_message(chat_id, final_text, parse_mode="HTML")

                    # Скрываем виртуальную клавиатуру
                    try:
                        rem_msg = bot.send_message(chat_id, "Выход из игрового режима...",
                                                   reply_markup=types.ReplyKeyboardRemove())
                        bot.delete_message(chat_id, rem_msg.message_id)
                    except Exception:
                        pass

                    show_gramle_game_over_menu(chat_id, message.from_user.id, 'lose')
                else:
                    updated_text = f"📝 <b>Результаты ваших попыток ({len(session['attempts_history'])}/6):</b>\n\n{history_text}\n\nПродолжайте вводить символы:"
                    try:
                        bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=session['msg_id'],
                            text=updated_text,
                            parse_mode="HTML"
                        )
                    except Exception:
                        # В случае ошибки редактирования отправляем новое и сохраняем его ID
                        new_msg = bot.send_message(chat_id, updated_text, parse_mode="HTML")
                        session['msg_id'] = new_msg.message_id

                    session['current_guess'].clear()


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
                points = 20 if ch['mode'] == 'terms' else 10
                username = get_user_display_name(message.from_user)
                update_score(message.from_user.id, username, points)

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
                points = -20 if ch['mode'] == 'terms' else -10
                username = get_user_display_name(message.from_user)
                update_score(message.from_user.id, username, points)

                bot.reply_to(message,
                             text=f'🥀💀 ВЫ ПРОИГРАЛИ! 💀🥀 \nБыло загадано <b>{ch["w"]}</b> — {ch["info"]}',
                             parse_mode='HTML', reply_markup=types.ReplyKeyboardRemove())
                ch['w'] = None
                show_game_over_menu(chat_id, user_id, 'lose')


if __name__ == '__main__':
    load_leaderboard()
    print("[INFO] Бот успешно запущен...")
    bot.infinity_polling()
