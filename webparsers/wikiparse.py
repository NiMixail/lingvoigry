from bs4 import BeautifulSoup
import requests
import re

# Текущие проблемы: если у слова несколько определений с пометкой лингв., берётся только первое

with open('dictionary.txt', 'w', encoding='utf-8') as out:
    with open('wiktionary_terms.txt', 'r', encoding='utf-8') as inp:
        for line in inp:
            try:
                response = requests.get(f"https://ru.wiktionary.org/w/index.php?title={line.strip()}")
                soup = BeautifulSoup(response.text, features="html.parser")
                print(line)
                wordef = None
                for word in soup.find_all(id=re.compile("^Семантические_свойства")):
                    definition_text = word.find_next("ol")
                    for item in definition_text.find_all("li"):
                        text = item.get_text()
                        if text:
                            text = "".join(re.findall("[-◆А-яё.,! ]+", text))
                            defn = text.split('◆')[0].strip()
                            if 'лингв.' in defn:
                                defn = defn.replace('лингв.', '').strip().strip(', ')
                                if wordef is None:
                                    wordef = line.strip().upper(), defn
                if wordef:
                    out.write(wordef[0] + ' * ' + wordef[1] + '\n')
                else:
                    print('Определение с пометкой лингв. не нашлось!!')
            except Exception:
                print('Что-то пошло не так!!!!! Игнорим')
