import os
import telebot
import random
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

bot = telebot.TeleBot('8850874673:AAFNCF8uBohHutgg7X2pDwgYuSufSZOtCLM')

import re


def transcribtor(word):
    word = word.replace('тс', 'ц')
    word = word.replace('тьс', 'ц')
    word = word.replace('стн', 'сн')
    word = word.replace('здн', 'зн')
    word = word.replace('сч', 'щ')
    word = word.replace('сш', 'шш')
    word = word.replace('сж', 'жж')
    word = word.replace('сщ', 'щщ')
    word = word.replace('ьо', 'ьйо')

    if re.findall(r'\b[яёюеЯЁЮЕ]', word):
        word = re.sub(r'\b([яёюеЯЁЮЕ])',
                      lambda m: "й" + {'Я': 'А', 'Ё': 'О', 'Ю': 'У', 'Е': 'Э', 'я': 'а', 'ё': 'о', 'ю': 'у', 'е': 'э'}[
                          m.group(1)], word)
    if re.findall(r'ь[яёюеЯЁЮЕ]', word):
        word = re.sub(r'ь([яёюеЯЁЮЕ])',
                      lambda m: "'й" + {'Я': 'А', 'Ё': 'О', 'Ю': 'У', 'Е': 'Э', 'я': 'а', 'ё': 'о', 'ю': 'у', 'е': 'э'}[
                          m.group(1)], word)
    if re.findall(r'ъ[яёюеЯЁЮЕ]', word):
        word = re.sub(r'ъ([яёюеЯЁЮЕ])',
                      lambda m: "й" + {'Я': 'А', 'Ё': 'О', 'Ю': 'У', 'Е': 'Э', 'я': 'а', 'ё': 'о', 'ю': 'у', 'е': 'э'}[
                          m.group(1)], word)
    if re.findall(r'[аоиыэуйАОИЫЭУ][яёюеЯЁЮЕ]', word):
        word = re.sub(r'([аоиыэуйАОИЫЭУ])([яёюеЯЁЮЕ])', lambda m: m.group(1) + "й" +
                                                                  {'Я': 'А', 'Ё': 'О', 'Ю': 'У', 'Е': 'Э', 'я': 'а',
                                                                   'ё': 'о', 'ю': 'у', 'е': 'э'}[m.group(2)], word)
    if re.findall(r'[жцш][яёюеиЯЁЮЕИ]', word):
        word = re.sub(r'([жшц])([яёюеиЯЁЮЕИ])', lambda m: m.group(1) +
                                                          {'Я': 'А', 'Ё': 'О', 'Ю': 'У', 'Е': 'Э', 'И': 'Ы', 'я': 'а',
                                                           'ё': 'о', 'ю': 'у', 'е': 'э', 'и': 'ы'}[m.group(2)], word)
    if re.findall(r'[яёюеЯЁЮЕ]', word):
        word = re.sub(r'([яёюеЯЁЮЕ])',
                      lambda m: "'" + {'Я': 'А', 'Ё': 'О', 'Ю': 'У', 'Е': 'Э', 'я': 'а', 'ё': 'о', 'ю': 'у', 'е': 'э'}[
                          m.group(1)], word)

    if re.findall(r'([^аоиыэу]*)и', word):
        word = re.sub(r'([^аоиыэу]*)(и)', r"\1'\2", word)

    if re.findall(r'([^аоиыэу]*)ь', word):
        word = re.sub(r'([^аоиыэу]*)ь', r"\1'", word)

    if re.findall(r'([жшц]*)ь', word):
        word = re.sub(r'([^жшц]*)ь', r"\1", word)

    if re.findall(r'[аоиыэу][^аоиыэу]*[АОИЫЭУ]', word):
        word = re.sub(r'[оа]([^аоиыэу]*[АОИЫЭУ])', r'А\1', word)
        word = re.sub(r'[эи]([^аоиыэу]*[АОИЫЭУ])', r'И\1', word)
        word = re.sub(r'[ы]([^аоиыэу]*[АОИЫЭУ])', r'Ы\1', word)
        word = re.sub(r'[у]([^аоиыэу]*[АОИЫЭУ])', r'У\1', word)

    if re.findall(r'[аоиыэу]', word):  # редукция
        word = re.sub(r"('|й|ч|\b)([аиэ])", r'\1ь', word)
        word = re.sub(r"('|й|ч|\b)([оу])", r'\1ь°', word)
        word = re.sub(r"([^'йч]|\b)([аыэ])", r'\1ъ', word)
        word = re.sub(r"([^'йч]|\b)([оу])", r'\1ъ°', word)
    if re.findall(r"[гдбвжз]'?$", word):  # оглушение
        word = re.sub(r"([гдбвжз])('?)$",
                      lambda m: {'г': 'к', 'д': 'т', 'б': 'п', 'в': 'ф', 'ж': 'ш', 'з': 'с'}[m.group(1)] + m.group(2),
                      word)

    while re.findall(r"([гдбвжз])('?)([ктпшщсф])('?)", word):  # оглушение
        word = re.sub(r"([гдбвжз])('?)([ктпшщсф])('?)",
                      lambda m: {'г': 'к', 'д': 'т', 'б': 'п', 'в': 'ф', 'ж': 'ш', 'з': 'с'}[m.group(1)] + m.group(
                          2) + m.group(3) + m.group(4), word)

    while re.findall(r"([ктпшщсф])('?)([гдбвжз])('?)", word):  # озвончение
        word = re.sub(r"([ктпшщсф])('?)([гдбвжз])('?)",
                      lambda m: {'к': 'г', 'т': 'д', 'п': 'б', 'ф': 'в', 'ш': 'ж', 'щ': "ж'", 'с': 'з'}[
                                    m.group(1)] + m.group(2) + m.group(3) + m.group(4), word)

    if re.findall(r"([бвгджзклмнпрстфхцш])([бвгджзклмнпрстфхцш]'|[йчщ])", word):
        word = re.sub(r"([бвгджзклмнпрстфхцш])([бвгджзклмнпрстфхцш]'|[йчщ])", r"\1'\2", word)
    word = word.replace("щ'", "ш'")
    word = word.replace("щ", "ш'")
    word = word.replace('ч', "ч'")
    return word.lower()


def spectromaker(text):
    from gtts import gTTS
    import miniaudio
    import numpy as np
    import io

    target_sample_rate = 48000

    tts = gTTS(text=text, lang='ru')
    mp3_buffer = io.BytesIO()
    tts.write_to_fp(mp3_buffer)
    mp3_buffer.seek(0)

    decoded = miniaudio.decode(mp3_buffer.read(), nchannels=1, sample_rate=target_sample_rate,
                               output_format=miniaudio.SampleFormat.SIGNED16)
    audio_numpy = np.frombuffer(decoded.samples, dtype=np.int16)

    audio_float = audio_numpy.astype(np.float32) / 32768.0

    import parselmouth
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set()

    snd = parselmouth.Sound(audio_float, sampling_frequency=target_sample_rate)

    def draw_spectrogram(spectrogram, dynamic_range=70):
        X, Y = spectrogram.x_grid(), spectrogram.y_grid()
        with np.errstate(divide='ignore'):
            sg_db = 10 * np.log10(spectrogram.values)
        plt.pcolormesh(X, Y, sg_db, vmin=sg_db.max() - dynamic_range, cmap='Greys')
        plt.ylim([spectrogram.ymin, spectrogram.ymax])
        plt.xlabel("time [s]")
        plt.ylabel("frequency [Hz]")

    def draw_intensity(intensity):
        plt.plot(intensity.xs(), intensity.values.T, linewidth=3, color='w')
        plt.plot(intensity.xs(), intensity.values.T, linewidth=1, color='Red')
        plt.grid(False)
        plt.ylim(0)
        plt.ylabel("intensity [dB]")

    intensity = snd.to_intensity()
    spectrogram = snd.to_spectrogram()

    plt.figure()
    draw_spectrogram(spectrogram)
    plt.twinx()
    draw_intensity(intensity)
    plt.xlim([snd.xmin, snd.xmax])
    plt.savefig('image.png', dpi=300)


with open('wordlist.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    word = random.choice(lines).strip()
target = transcribtor(word)
word = word.lower()
spectromaker(word)
user_arrays = {}
user_last_msgs = {}

symbols = ['а', 'о', 'у', 'э', 'ы', 'и', 'ь', 'ъ', 'ь°', 'ъ°', "б", "б'", "п", "п'", "г", "г'", "к", "к'", "д", "д'",
           "т", "т'", "з", "з'", "с", "с'", "ж", "ж'", "ш", "ш'", "в", "в'", "ф", "ф'", "х", "х'", "н", "н'", "м", "м'",
           "л", "л'", "р", "р'", "й", "ч'", "ц"]


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


@bot.message_handler(commands=['start'])
def send_image_and_start(message):
    chat_id = message.chat.id

    user_arrays[chat_id] = []
    user_last_msgs[chat_id] = []

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [KeyboardButton(sym) for sym in symbols]
    buttons.append(KeyboardButton("⌫"))
    markup.add(*buttons, row_width=12)
    with open('image.png', 'rb') as photo:
        bot.send_photo(
            chat_id,
            photo,
            caption="_ _ _ _ _ _",
            reply_markup=markup
        )


@bot.message_handler(func=lambda message: message.text in symbols)
def handle_char(message):
    chat_id = message.chat.id

    if chat_id not in user_arrays:
        return

    user_arrays[chat_id].append(message.text)

    user_last_msgs[chat_id].append(message.message_id)

    if len(user_arrays[chat_id]) == 6:
        result_string = "".join(user_arrays[chat_id])

        for msg_id in user_last_msgs[chat_id]:
            try:
                bot.delete_message(chat_id, msg_id)
            except Exception as e:
                print(f"Не удалось удалить сообщение {msg_id}: {e}")

        bot.send_message(
            chat_id,
            compare_words(result_string, target),
            parse_mode="HTML"
        )

        user_arrays[chat_id].clear()
        user_last_msgs[chat_id].clear()


@bot.message_handler(func=lambda message: message.text == "⌫")
def handle_backspace(message):
    chat_id = message.chat.id

    try:
        bot.delete_message(chat_id, message.message_id)
    except:
        pass

    if chat_id in user_arrays and user_arrays[chat_id]:
        user_arrays[chat_id].pop()

        if chat_id in user_last_msgs and user_last_msgs[chat_id]:
            last_msg_id = user_last_msgs[chat_id].pop()
            try:
                bot.delete_message(chat_id, last_msg_id)
            except:
                pass


if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling(none_stop=True)
