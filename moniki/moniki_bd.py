"""
Работает с БД для скрипта по МОНИКИ. Для работы с БД используется sqlite3.
Содержит несколько таблиц:
- moniki_specialties - специальности МОНИКИ, их наименование и количество свободных ячеек на текущий момент;
- moniki_data - то есть таблица для анализа даты и времени открытия некоторого количества ячеек по определенным специальностям.
- moniki_records - основная таблица для работы с направлениями и записью к врачам в МОНИКИ.

Записывает информацию об открытии ячеек, а также направлений пациентов. Основной скрипт для работы с БД.
"""

import sqlite3
from datetime import datetime as d
import os
import sys

__version__ = "1.0.0"
__author__ = "DinoWithPython"
__copyright__ = "2024, ГБУЗ Мытищинская ОКБ"
__contact__ = "<Telegram: @pa_dmi>"

MAIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(MAIN_DIR))

PATH_DB = rf'{MAIN_DIR}\moniki\data.db'


def __create_table_specialties():
    """
    Создание таблицы специальностей МОНИКИ.
        * name - название специальности;
        * count_talons - количество ячеек, которые свободны сейчас.
    Является по сути основной таблицей для скрипта, если в ней есть свободные ячейки, то скрипт будет пытаться
    записать на них. Так же является проверочным значением для добавления направлений по специальностям.
    Если в этой таблице нет такой специальности, то добавить направление с ней не получится.
    """
    con = sqlite3.connect(PATH_DB)
    cur = con.cursor()
    cur.execute("""CREATE TABLE moniki_specialties(
        name TEXT NOT NULL PRIMARY KEY,
        count_talons INTEGER
    );
    """)
    con.commit()
    con.close()


def __create_table_data():
    """
    Таблица для учета времени открытия расписания.
        * date_adding - дата открытия расписания для специальности;
        * name - название специальности, для которой открыли ячейки;
        * count_talons - количество ячеек, которые были открыты.
    То есть таблица для анализа даты и времени открытия некоторого количества ячеек по определенным специальностям.
    """
    con = sqlite3.connect(PATH_DB)
    cur = con.cursor()
    cur.execute("""CREATE TABLE moniki_data(
        date_adding TEXT NOT NULL,
        name TEXT NOT NULL,
        count_talons INTEGER,
        FOREIGN KEY (name) REFERENCES moniki_specialties(name)
    );
    """)
    con.commit()
    con.close()


def __add_column_in_table(name_table, name_column, type_column):
    """Добавление столбца в таблицу."""
    con = sqlite3.connect(PATH_DB)
    cur = con.cursor()
    cur.execute(f"""ALTER TABLE {name_table} ADD COLUMN {name_column} {type_column}""")
    con.commit()
    con.close()


def __create_table_records():
    """
    Таблица для хранения направлений, по которым нужно записать пациента и учет таких записей.
        * date_adding - дата создания записи;
        * number_direct - номер направления;
        * name - название специальности;
        * is_recorded - записан пациент или нет;
        * date_direct - дата записи по направлению;
        * time_direct - время записи по направлению;
        * date_changes - дата изменения записи, то есть когда скрипт записал пациента(нужно для анализа работы скрипта);
        * specific - специфика, то есть требования врачей(определенная подспециальность, конкретный врач и т.п.);
        * comment - комментарий, обычно в нем указывается тот, кого после записи нужно оповестить;
        * notified - уведомил ли я сотрудника из поля comment о том, что записал пациента;
    Основная таблица для работы с направлениями и записью к врачам в МОНИКИ.
    """
    con = sqlite3.connect(PATH_DB)
    cur = con.cursor()
    cur.execute("""CREATE TABLE moniki_records(
        date_adding TIMESTAMP NOT NULL,
        number_direct TEXT NOT NULL,
        name TEXT NOT NULL,
        is_recorded BOOLEAN NOT NULL,
        date_direct TEXT,
        time_direct TEXT,
        date_changes TIMESTAMP,
        specific TEXT,
        comment TEXT,
        notified BOOLEAN NOT NULL,
        FOREIGN KEY (name) REFERENCES moniki_specialties(name)
    );
    """)
    con.commit()
    con.close()


def sql_operation(func):
    """Декоратор для открытия и закрытия соединения с БД с сохранением данных."""
    def wrapper(*args, **kwargs):
        try:
            con = sqlite3.connect(PATH_DB)
            con.execute("PRAGMA foreign_keys = 1")
            cur = con.cursor()
            func(cur, *args, **kwargs)
            con.commit()
        finally:
            con.close()
    return wrapper


def get_data_all_records() -> dict:
    """Берет информацию из тыблица по записям из moniki_records."""
    try:
        con = sqlite3.connect(PATH_DB)
        cur = con.cursor()
        cur.execute("""SELECT * FROM moniki_records""")
        data = cur.fetchall()
    finally:
        con.close()
        return data


def get_data_all_specialty() -> dict:
    """Берет информацию из базы по специальностям и количеству ячеек из moniki_specialties."""
    try:
        con = sqlite3.connect(PATH_DB)
        cur = con.cursor()
        cur.execute("""SELECT * FROM moniki_specialties""")
        data = {name: value for name, value in cur.fetchall()}
    finally:
        con.close()
        return data


@sql_operation
def put_specialty(cur, specialty: str, value: int):
    """Добавляет специальность и количество ячеек в moniki_specialties."""
    cur.execute("""INSERT INTO moniki_specialties VALUES(?, ?)""", (specialty, value))


@sql_operation
def change_value_specialty(cur, specialty: str, value: int):
    """Меняет количество свободных ячеек на текущее в moniki_specialties."""
    cur.execute(
        """UPDATE moniki_specialties SET count_talons = (?) WHERE name = (?)""",
        (value, specialty)
    )


@sql_operation
def _change_status_record(cur, number_direct: str, value: int):
    """Меняет статус записи is_recorded в moniki_records."""
    value = value.strip()
    if value in ('0', '1'):
        cur.execute(
            """UPDATE moniki_records SET is_recorded = (?) WHERE number_direct = (?)""",
            (value, number_direct)
        )
    else:
        print('Вы передали не верный статус. Передайте "1" или "0". Передано <{value}>')


@sql_operation
def put_change_data(cur, specialty: str, value: int):
    """Добавляет в таблицу moniki_data отметку о времени появления более 2 ячеек."""
    record = (d.now(), specialty, value)
    cur.execute("""INSERT INTO moniki_data VALUES(?, ?, ?)""", record)


@sql_operation
def put_record(
        cur,
        number_direct: str,
        specialty: str,
        is_recorded: int,
        date_direct: str = None,
        time_direct: str = None,
        date_changes: str = None,
        specific: str = None,
        comment: str = None,
        notified: bool = False
        ):
    """
    Добавляет в таблицу moniki_records новое направление для отслеживания.
    Если нужно искать по конкретной specific, то вводим её часть для явного поиска.
    Для поиска по фамилии вводим 'ФИО: ', по такому шаблону скрипт далее разделяет специфику(регистр специфики не важен, но важен для фио).
    Помимо этого, если нужно искать несколько ФИО, то следует их вводить через запятую с пробелом:
    "Ахмат, Сидор, Иванов", при этом регистр ФИО имеет значения.
    """
    record = (d.now(), number_direct, specialty, is_recorded, date_direct, time_direct, date_changes, specific, comment, notified)
    cur.execute("""
        INSERT INTO moniki_records VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", record)


@sql_operation
def change_datetime_record(cur, is_recorded: int, date_direct: str, time_direct: str, number_direct: str):
    """После записи пациента меняет статус, дату и время строки в moniki_records."""
    cur.execute(
        """ UPDATE moniki_records
            SET is_recorded = (?),
                date_direct = (?),
                time_direct = (?),
                date_changes = (?)
            WHERE number_direct = (?)""",
        (is_recorded, date_direct, time_direct, d.now(), number_direct)
    )


def get_not_recorder() -> list:
    """Возвращает список кортежей номера не записанных направлений и специальности из moniki_records.
        [(номер направления, специальность, специфика), (номер направления, специальность, специфика), ...]
    """
    try:
        con = sqlite3.connect(PATH_DB)
        cur = con.cursor()
        cur.execute("""SELECT number_direct, name, specific FROM moniki_records WHERE is_recorded = 0""")
        data = cur.fetchall()
    finally:
        con.close()
        return data


def _adding_record_in_bd():
    """Функция для добавления новых записей через консоль."""
    nmr_direction = input('Введите номер направления:\n')
    spec = input('Введите специальность:\n')
    specific = input('Введите специфику, если нет, нажмите Enter:\n')
    comment = input('Введите кого после записи оповестить: \n')
    if specific == '':
        put_record(nmr_direction, spec, 0, comment=comment.strip())
    else:
        put_record(nmr_direction, spec, 0, specific=specific.strip(), comment=comment.strip())


@sql_operation
def _delete_data_over_30_days(cur):
    """Удаляет из таблицы moniki_data информацию о добавлении записей старше 30 дней."""
    cur.execute("""DELETE FROM moniki_data WHERE date_adding < datetime('now', '-30 days')""")


@sql_operation
def _delete_row_record(cur, number_record: str):
    """Удаляет из таблицы moniki_records строку с переданным номером направления."""
    cur.execute("""DELETE FROM moniki_records WHERE number_direct = (?)""", (number_record,))


@sql_operation
def change_notified_status(cur, number_direct: str):
    """После записи пациента меняет статус, дату и время строки в moniki_records."""
    cur.execute(
        """ UPDATE moniki_records
            SET notified = (?)
            WHERE number_direct = (?)""",
        (True, number_direct)
    )


if __name__ == "__main__":
    # __create_table_specialties()
    # __create_table_data()
    # specialty = {
    #     "Акушерство и гинекология": 0,
    #     "Аллергология и иммунология": 0,
    #     "Гастроэнтерология": 0,
    #     "Гематология": 0,
    #     "Инфекционные болезни": 0,
    #     "Кардиология": 0,
    #     "Колопроктология": 0,
    #     "Лабораторная диагностика": 0,
    #     "Неврология": 0,
    #     "Нейрохирургия": 0,
    #     "Нефрология": 0,
    #     "Онкология": 0,
    #     "Оториноларингология": 0,
    #     "Офтальмология": 0,
    #     "Психотерапия": 0,
    #     "Пульмонология": 0,
    #     "Ревматология": 0,
    #     "Сердечно-сосудистая хирургия": 0,
    #     "Стоматология общей практики": 0,
    #     "Стоматология терапевтическая": 0,
    #     "Стоматология хирургическая": 0,
    #     "Сурдология-оториноларингология": 0,
    #     "Терапия": 0,
    #     "Торакальная хирургия": 0,
    #     "Травматология и ортопедия": 0,
    #     "Ультразвуковая диагностика": 0,
    #     "Урология": 0,
    #     "Функциональная диагностика": 0,
    #     "Хирургия": 0,
    #     "Челюстно-лицевая хирургия": 0,
    #     "Эндокринология": 0,
    # }
    # for key, value in specialty.items():
    #     put_specialty(key, value)
    # print(get_data_all_specialty())

    # put_record('2134', 'Сурдология-оториноларингология', 0)
    # change_datetime_record(1, '15.11.2023', '17:15', '213')

    # print(get_not_recorder())

    # По сути это нужно для взаимодействия с БД через терминал/консоль. По умолчанию используется приложение на Flask.
    args = sys.argv
    if len(args) == 1:
        print('Не передан ни один аргумент, передайте help.')
    if args[1] == 'help':
        print(
            '-- Для добавления записи в БД передайте аргумент add.\n'
            '-- Для удаления записей открытия расписания более 30 дней передайте аргумент del\n'
            '-- Для получения списка пациентов, ожидающих записи передайте need_recorder\n'
            '-- Для поулчения списка всех записей в таблице необходимых для записи передайте all_recorder\n'
            '-- Изменить статус записи по номеру направления передайте chg_status\n'
            '-- Для удаления строки с направлением передайте del_record\n'
            '-- Для смены статуса оповещения ntf\n'
            )
    elif args[1] == 'add':
        _adding_record_in_bd()
    elif args[1] == 'del':
        _delete_data_over_30_days()
        print('Записи о добавлении расписания датой добавления более 30 дней - удалены.')
    elif args[1] == 'need_recorder':
        for num, elem in enumerate(get_not_recorder()):
            print(f'{num}. Номер направления: {elem[0]}.\n Специальность: {elem[1]}.\n Специфика: {elem[2]}')
    elif args[1] == 'all_recorder':
        for num, elem in enumerate(get_data_all_records()):
            print(num, *elem)
    elif args[1] == 'chg_status':
        number_direct = input('Введите номер направления:\n').strip()
        status = input('Введите статус (0 - не записан, 1 - записан):\n').strip()
        _change_status_record(number_direct=number_direct, value=status)
        print(f'Статус направления {number_direct} изменён.')
    elif args[1] == 'del_record':
        number_direct = input('Введите номер направления:\n').strip()
        _delete_row_record(number_direct)
        print(f'Направление с номером {number_direct} успешно удалено!')
    elif args[1] == 'ntf':
        number_direct = input('Введите номер направления:\n').strip()
        change_notified_status(number_direct)
        print('По данному направлению статус изменен на оповещены.')
