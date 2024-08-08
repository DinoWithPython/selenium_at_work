"""Файлик для замены xpath на шаблон. Мало ли еще пригодится :)"""

import re

with open('moniki_tets.py','r') as f:
    a = f.readlines()
    for text in range(len(a)):
        a[text] = re.sub(r"'.*//.*'", 'нет ссылкам', a[text]) 
