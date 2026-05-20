import os
import random
import telebot
from telebot import types

TOKEN = '8774876949:AAFu1ikXGq1-8t_I_r3Np_8QLIdmJ8y9EQc'
bot = telebot.TeleBot(TOKEN)

# Глобальный словарь для слов «Виселицы»
DICTIONARY = {}

x = 6
HANGMAN_IMAGES = []
for i in range(x):
    img_name = f'img{i}.jpg'  
    HANGMAN_IMAGES.append(img_name)



GAMES = {
    'rugramle': {'name': 'RuGramle 🎵', 'desc': 'Угадай слово из 5 звуков по спектрограмме.', 'levels_count': 3},
    'lingviselica': {'name': 'Лингвиселица 🪓', 'desc': 'Угадай лингвистический термин или фразеологизм по буквам.', 'levels_count': 3},
    'homo': {'name': 'ХОМО 💡', 'desc': 'Придумай слово, содержащее заданное буквосочетание.', 'levels_count': 3},
    'guess_lang': {'name': 'Угадай язык 🌍', 'desc': 'Определи язык по письменному фрагменту текста.', 'levels_count': 3}
}

# текущие сессии игр
USER_MEMORY = {}


def load_dictionary():
    global DICTIONARY
    if not os.path.exists('dictionary.txt'):
        with open('dictionary.txt', 'w', encoding='utf-8') as f:
            f.write("МЕТАФОРА * Оборот речи, состоящий в употреблении слов в переносном значении.\n")
            f.write("ФОНЕМА * Минимальная смыслоразличительная единица языка.\n")
            f.write("ФРАЗЕОЛОГИЗМ * Устойчивое сочетание слов с самостоятельным значением.\n")
    
    DICTIONARY.clear()
    with open('dictionary.txt', 'r', encoding='utf-8') as f:
        for line in f:
            if ' * ' in line:
                parts = line.strip().split(' * ')
                DICTIONARY[parts[0].upper()] = parts[1]

# состояние игрока
def init_user(user_id):
    if user_id not in USER_MEMORY:
        USER_MEMORY[user_id] = {
            'active_game': None  # сессия запущенной игры
        }

def get_main_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, info in GAMES.items():
        markup.add(types.InlineKeyboardButton(text=info['name'], callback_data=f"open_{key}"))
    return markup

# старт
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
        "Выбирай мини-игру из списка ниже, а затем уровень сложности:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")

# обработка кнопок и меню
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    init_user(user_id)

    data = call.data

    # 1. Возврат в главное меню
    if data == "to_menu":
        USER_MEMORY[user_id]['active_game'] = None
        bot.clear_step_handler_by_chat_id(chat_id)
        bot.edit_message_text("Выбирай мини-игру из списка:", chat_id, message_id, reply_markup=get_main_menu_keyboard())
        bot.answer_callback_query(call.id)
        return

    # 2. Открытие меню выбора уровней конкретной игры
    if data.startswith("open_"):
        game_key = data.split("_")[1]
        levels_count = GAMES[game_key]['levels_count']
        
        # генерация кнопок уровней
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

    # 3. Запуск конкретного уровня
    if data.startswith("play_"):
        _, game_key, lvl = data.split("_")
        lvl = int(lvl)
        bot.delete_message(chat_id, message_id) # Удаляем меню, чтобы начать игру
        
        if game_key == 'lingviselica':
            start_hangman_game(chat_id, user_id, lvl)
        else:
            # Симуляция других игр
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

    # 4. Симуляция исходов для других игр
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
            
        bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id, reply_markup=markup, parse_mode="Markdown")
        bot.answer_callback_query(call.id)


# -логика виселицы
def start_hangman_game(chat_id, user_id, lvl):
    if not DICTIONARY:
        bot.send_message(chat_id, "❌ Словарь пуст или не загружен.")
        return

    w = random.choice(list(DICTIONARY.keys()))
    view = ''.join(i if i == ' ' else '_' for i in w)
    mistakes = 0
    letters = {c: 7 for c in 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ-.'}

    USER_MEMORY[user_id]['active_game'] = {
        'game': 'lingviselica',
        'word': w,
        'view': view,
        'mistakes': mistakes,
        'letters': letters,
        'level': lvl
    }

    bot.send_message(chat_id, "🎬 **Игра началась!** Вводите буквы по одной в чат.", parse_mode="Markdown")
    render_hangman_step(chat_id, user_id)

def render_hangman_step(chat_id, user_id):
    game_state = USER_MEMORY[user_id]['active_game']
    if not game_state:
        return

    mistakes = game_state['mistakes']
    view = game_state['view']
    letters = game_state['letters']
    
    used_letters_str = ""
    for le in sorted(letters):
        if letters[le] == 7:     
            used_letters_str += f"{le} "
        elif letters[le] == 2:   
            used_letters_str += f"<b>{le}</b> "
        elif letters[le] == 1:   
            used_letters_str += f"<s>{le}</s> "

    caption = (
        f"📈 **Уровень {game_state['level']}**\n\n"
        f"<b>Слово:</b>  {view.replace('_', ' _ ')}\n\n"
        f"<b>Использованные буквы:</b>\n{used_letters_str}\n\n"
        f"✏️ <i>Вводите букву:</i>"
    )

    # Защита от ошибок, если картинки нет на жестком диске
    try:
        img_path = HANGMAN_IMAGES[mistakes]
        with open(img_path, 'rb') as photo:
            msg = bot.send_photo(chat_id, photo, caption=caption, parse_mode="HTML")
    except Exception as e:
        # Если картинки нет, отправляем просто текст, чтобы бот не падал
        fallback_text = f"🖼 *[Тут должна быть картинка {mistakes}]*\n\n" + caption.replace("<b>", "**").replace("</b>", "**").replace("<s>", "~").replace("</s>", "~").replace("<i>", "_").replace("</i>", "_")
        msg = bot.send_message(chat_id, fallback_text, parse_mode="Markdown")

    bot.register_next_step_handler(msg, process_hangman_letter)

def process_hangman_letter(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    init_user(user_id)
    
    game_state = USER_MEMORY[user_id]['active_game']
    
    if message.text and message.text.startswith('/'):
        start_command(message)
        return

    if not game_state or game_state['game'] != 'lingviselica':
        return

    letter = message.text.strip().upper() if message.text else ""

    if len(letter) != 1 or letter not in game_state['letters']:
        msg = bot.send_message(chat_id, "❌ Введите одну русскую букву, дефис или точку.")
        bot.register_next_step_handler(msg, process_hangman_letter)
        return

    w = game_state['word']
    view = game_state['view']
    letters = game_state['letters']
    mistakes = game_state['mistakes']
    lvl = game_state['level']

    if letter in w:
        if letter in letters:
            letters[letter] = 2
        for i in range(len(w)):
            if w[i] == letter:
                view = view[:i] + letter + view[i + 1:]
        game_state['view'] = view
    else:
        mistakes += 1
        if letter in letters:
            letters[letter] = 1
        game_state['mistakes'] = mistakes

    # Проверка ВЫИГРЫША / ПРОИГРЫША
    is_game_over = False
    
    if mistakes >= len(HANGMAN_IMAGES) - 1:
        result_title = "💀 **Вы проиграли!**"
        is_game_over = True
    elif view == w:
        result_title = "🎉 **Верно! Победа!**"
        is_game_over = True

    if is_game_over:
        text = (
            f"{result_title}\n\n"
            f"Слово: **{w}**\n"
            f"📖 **Толкование:** {DICTIONARY.get(w, 'Нет описания')}\n\n"
            f"Уровень: {lvl}"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🔄 Повторить этот уровень", callback_data=f"play_lingviselica_{lvl}"),
            types.InlineKeyboardButton("🎛 Выбрать другой уровень", callback_data="open_lingviselica"),
            types.InlineKeyboardButton("🔙 Главное меню", callback_data="to_menu")
        )
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
        USER_MEMORY[user_id]['active_game'] = None
        return

    # Продолжаем игру
    render_hangman_step(chat_id, user_id)

# запуск
if __name__ == '__main__':
    print("[INFO] Загрузка словарей...")
    load_dictionary()
    print("[INFO] Бот успешно запущен...")
    bot.infinity_polling()