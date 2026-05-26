import re

def transcribtor(word): 
    
    word = word.replace('тс', 'ц')
    word = word.replace('тьс', 'ц')
    word = word.replace('стн', 'сн')
    word = word.replace('сч', 'щ')
    word = word.replace('сш', 'шш')
    word = word.replace('сж', 'жж')
    word = word.replace('сщ', 'щщ')
    word = word.replace('ьо', 'ьйо')

    if re.findall(r'\b[яёюеЯЁЮЕ]', word):
        word = re.sub(r'\b([яёюеЯЁЮЕ])', lambda m: "й" + {'Я':'А','Ё':'О','Ю':'У','Е':'Э','я':'а','ё':'о','ю':'у','е':'э'}[m.group(1)], word)    
    if re.findall(r'ь[яёюеЯЁЮЕ]', word):
        word = re.sub(r'ь([яёюеЯЁЮЕ])', lambda m: "'й" + {'Я':'А','Ё':'О','Ю':'У','Е':'Э','я':'а','ё':'о','ю':'у','е':'э'}[m.group(1)], word)
    if re.findall(r'ъ[яёюеЯЁЮЕ]', word):
        word = re.sub(r'ъ([яёюеЯЁЮЕ])', lambda m: "й" + {'Я':'А','Ё':'О','Ю':'У','Е':'Э','я':'а','ё':'о','ю':'у','е':'э'}[m.group(1)], word)
    if re.findall(r'[аоиыэуйАОИЫЭУ][яёюеЯЁЮЕ]', word):
        word = re.sub(r'([аоиыэуйАОИЫЭУ])([яёюеЯЁЮЕ])', lambda m: m.group(1) + "й" + {'Я':'А','Ё':'О','Ю':'У','Е':'Э','я':'а','ё':'о','ю':'у','е':'э'}[m.group(2)], word)
    if re.findall(r'[жцш][яёюеиЯЁЮЕИ]', word):
        word = re.sub(r'([жшц])([яёюеиЯЁЮЕИ])', lambda m: m.group(1) + {'Я':'А','Ё':'О','Ю':'У','Е':'Э','И':'Ы','я':'а','ё':'о','ю':'у','е':'э','и':'ы'}[m.group(2)], word)
    if re.findall(r'[яёюеЯЁЮЕ]', word):
        word = re.sub(r'([яёюеЯЁЮЕ])', lambda m: "'" + {'Я':'А','Ё':'О','Ю':'У','Е':'Э','я':'а','ё':'о','ю':'у','е':'э'}[m.group(1)], word)
        
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
        
        
    if re.findall(r'[аоиыэу]', word): #редукция
        word = re.sub(r"('|й|ч|\b)([аиэ])", r'\1ь', word)
        word = re.sub(r"('|й|ч|\b)([оу])", r'\1ь°', word)
        word = re.sub(r"([^'йч]|\b)([аыэ])", r'\1ъ', word)
        word = re.sub(r"([^'йч]|\b)([оу])", r'\1ъ°', word)
        
    if re.findall(r"[гдбвжз]'?$", word): #оглушение
        word = re.sub(r"([гдбвжз]'?$)", lambda m: {'г':'к','д':'т','б':'п','в':'ф','ж':'ш','з':'с'}[m.group(1)], word)

    
    while re.findall(r"([гдбвжз])('?)([ктпшщсф])('?)", word): #оглушение
        word = re.sub(r"([гдбвжз])('?)([ктпшщсф])('?)", lambda m: {'г':'к','д':'т','б':'п','в':'ф','ж':'ш','з':'с'}[m.group(1)] + m.group(2) + m.group(3) + m.group(4), word)
           
    
    while re.findall(r"([ктпшщсф])('?)([гдбвжз])('?)", word): #озвончение
        word = re.sub(r"([ктпшщсф])('?)([гдбвжз])('?)", lambda m: {'к':'г','т':'д','п':'б','ф':'в','ш':'ж','щ':"ж'",'с':'з'}[m.group(1)] + m.group(2) + m.group(3) + m.group(4), word)    
    
    if re.findall(r"([бвгджзклмнпрстфхцш])([бвгджзклмнпрстфхцш]'|[йчщ])", word):
        word = re.sub(r"([бвгджзклмнпрстфхцш])([бвгджзклмнпрстфхцш]'|[йчщ])", r"\1'\2", word)
    word = word.replace("щ'", "ш'")
    word = word.replace("щ", "ш'")
    return word.lower()