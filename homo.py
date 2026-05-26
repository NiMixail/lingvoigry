import os
from collections import defaultdict

def sl_wind(text, k):
    if k > len(text):
        return []
    return [text[i:i + k] for i in range(len(text) - k + 1)]

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "russian.txt")

with open(file_path, 'r', encoding='utf-8') as file:
    combinations = defaultdict(int)
    for word in file:
        word = word.strip()
        if not word.isalpha():
            continue 
        for j in range(2, 4):
            for item in sl_wind(word, j):
                combinations[item] += 1 

    sorted_combs = dict(sorted(combinations.items(), key=lambda item: item[1]))
    print(sorted_combs)