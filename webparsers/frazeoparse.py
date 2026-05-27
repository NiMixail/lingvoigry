import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import unquote
import re

scraper = cloudscraper.create_scraper()
# print(scraper.get("https://rus-phraseology-dict.slovaronline.com/2-Ёлки-моталки").text)

N = 14333


def first():
    with (open('dictionary_f.txt', 'w', encoding='utf-8') as out):
        for i in range(1, N + 1):
            try:
                response = scraper.get(f"https://rus-phraseology-dict.slovaronline.com/{str(i).zfill(2)}")
                fraz = unquote(response.url.split('.com/')[1].split('-', 1)[1])
                soup = BeautifulSoup(response.text, features="html.parser")
                info = str(soup.find(class_="blockquote"))
                if info.startswith('<div class="blockquote" itemprop="content">') and info.endswith("</div>"):
                    info = info[43: -6]
                print(fraz)
                out.write(f"{fraz} ###### {info}\n")
            except Exception:
                print('Что-то пошло не так!!!!! Игнорим')


def second():
    with (open('dictionary_f_.txt', 'w', encoding='utf-8') as out):
        with (open('dictionary_f.txt', 'r', encoding='utf-8') as inp):
            c = ''
            for line in inp:
                if " ###### " in line:
                    out.write(c + '\n')
                    c = line.strip('\n')
                else:
                    c += line.strip('\n') + ' '
            out.write(c + '\n')

second()
