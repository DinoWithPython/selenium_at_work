"""
Скрипт для автоматизации процесса записи пацинетов в МОНИКИ, а так же сбора статистики открытия ячеек расписания МОНИКов.
Делится на несколько частей: собирает специальность и количество свободных ячеек на текущий момент в таблицу БД(по умолчанию SQLite)
"""

import datetime
import logging
import os
import os.path
import time
from typing import Union

from dotenv import load_dotenv
from selenium.common.exceptions import SessionNotCreatedException, TimeoutException
import schedule
from plyer import notification

import moniki_bd as bd

__version__ = "1.0.0"
__author__ = "DinoWithPython"
__copyright__ = "2024, ГБУЗ Мытищинская ОКБ"
__contact__ = "<email: pa.dmi@rambler.ru>"

MAIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

path = MAIN_DIR.split("\\")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIRECTION_FOR_GET_TALONS = os.getenv("DIRECTION_FOR_GET_TALONS")

logging.basicConfig(
    level=logging.INFO,
    filename="moniki_class.log",
    filemode="w",
    format="%(asctime)s %(levelname)s %(message)s")

def notif(title="Заголовок", message="Сообщение."):
    """Уведомляет о каких-либо событиях."""
    notification.notify(
        title=title,
        message=message)

def now():
    return datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")

def check_html(sel):
    html = sel.browser.page_source
    file = open("foo.html", "w", encoding='UTF-8')
    file.write(html)
    file.close()


class Sel:
    """Создан для помощи врачам в целях оптимизации процесса записи в МОНИКИ."""

    def __init__(self):
        import os
        import sys

        # Добавляем путь к директории проекта в sys.path
        project_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        sys.path.append(project_directory)
        from frfx_hlss_sel_cls import SeleniumBrow as SB

        self.sel = SB(link="нет ссылок", main=main, headless=True)
    
    def open_emias(self):
        """Открывает сайт ЕМИАСА."""
        try:
            logging.info("Открывается сайт ЕМИАСА")
            self.sel.go_link()
        except Exception as err:
            logging.error(f"Ошибка при открытии сайта ЕМИАСА\n{err}", exc_info=True)
    
    def input_login_and_pass(self):
        """Находит поля для ввода логина и пароля и вводит их."""
        try:
            login, passw = os.getenv("EMIPLOG"), os.getenv("EMIPPASS")
            logging.info("Находит по id поле для ввода логина")
            input_login = self.sel.find_id('Login')
            logging.info("Вводит логин")
            self.sel.send_text(input_login, login)
            logging.info("Находит по id поле для ввода пароля")
            input_password = self.sel.find_id('Password')
            logging.info("Вводит пароль")
            self.sel.send_text(input_password, passw)
        except Exception as err:
            logging.error(f"Ошибка при вводе логина и пароля в методе input_login_and_pass\n{err}", exc_info=True)
    
    def log_in(self):
        """
        Находит кнопку войти и входит в систему.
        Если не может войти, то выводит ошибку.
        """
        try:
            logging.info("Находит кнопку 'войти' по xpath.")
            button_in = self.sel.find_xpath(нет ссылкам)
            logging.info("Кликает по кнопке 'войти'")
            self.sel.click(button_in)
        except Exception as err:
            logging.error(f"Ошибка при клике по кнопку 'войти' в методе log_in\n{err}", exc_info=True)
    
    def open_section_directs(self):
        """Находит раздел с направлениями на госпитализацию и кликает по элементу меню."""
        try:
            logging.info("Находит раздел с направлениями")
            click_section = self.sel.find_xpath(нет ссылкам)
            logging.info("Кликает по разделу с направлениями")
            self.sel.click(click_section)
        except Exception as err:
            logging.error(f"Ошибка при клике по разделу с направлениями в методе open_section_directs\n{err}", exc_info=True)
    
    def switch_to_another_window(self):
        """Переключает на окно с направлениями."""
        try:
            logging.info("Ожидает пока окон не станет больше одного")
            while len(self.sel.browser.window_handles) == 1:
                time.sleep(2)

            logging.info("Открывается новое окно и переходим в него")
            new_window = self.sel.browser.window_handles[1]
            self.sel.browser.switch_to.window(new_window)
        except Exception as err:
            logging.error(f"Ошибка при переключении на окно с направлениями в методе switch_to_another_window\n{err}", exc_info=True)


    def open_filters(self):
        """Раскрывает панель фильтров при поиске направления."""
        try:
            logging.info("Находит кнопку с фильтрами.")
            button_filter = self.sel.find_xpath(нет ссылкам)
            logging.info("Кликает по кнопке с текстом поиск.")
            self.sel.click(button_filter)
        except Exception as err:
            logging.error(f"Ошибка при раскрытии панели фильтров в методе open_filters\n{err}", exc_info=True)
                            


    def del_doctor_filter(self):
        """Удаляет врача из фильтров на странице поиска направлений."""
        try:
            logging.info("Находит крест рядом с фио врача.")
            clear_doctor = self.sel.find_xpath(нет ссылкам)
            logging.info("Кликает по кресту рядом с фио врача")
            self.sel.click(clear_doctor)
        except Exception as err:
            logging.error(f"Ошибка при удалении врача из фильтров в методе del_doctor_filter\n{err}", exc_info=True)
            
    def clear_direct_and_search(self, direction_number=DIRECTION_FOR_GET_TALONS):
        """
        Очищает поле для поиска направлений и вводит туда номер.
        По умолчанию используется моё направление для поиска доступных ячеек.
        """
        try:
            logging.info("Находит поле для поиска направлений.")
            input_direction_number = self.sel.find_xpath(нет ссылкам)
            logging.info("Очищает поле для поиска направлений")
            self.sel.clear_area(input_direction_number)
            logging.info("Кликает по полю направлений, чтобы внести туда номер.")
            self.sel.click(input_direction_number)
            logging.info("Вводит номер направления")
            self.sel.send_text(input_direction_number, direction_number)
        except Exception as err:
            logging.error(f"Ошибка при очистке поля для поиска направлений в методе clear_direct_and_search, направление номер: {direction_number}\n{err}", exc_info=True)

    def find_direct(self):
        """Нажимает кнопку найти, считая, что номер направления уже введен."""
        try:
            logging.info("Находит кнопку 'Найти'")
            click_find = self.sel.find_xpath(нет ссылкам)
            logging.info("Ждем пока крутилка не исчезнет.")
            self.sel.elem_invis(нет ссылкам)
            logging.info("Кликает по кнопке 'Найти'")
            self.sel.click(click_find)
            time.sleep(2)
        except Exception as err:
            logging.error(f"Ошибка при нажатии кнопки 'Найти' в методе find_direct\n{err}", exc_info=True)

    def get_in_directon(self, direction_number=DIRECTION_FOR_GET_TALONS):
        """Ждет загрузки направления и переходит в него."""
        try:
            logging.info("Задаю неявные ожидания в секунду.")
            self.sel.browser.implicitly_wait(1)
            logging.info("Жду, пока исчезнет элемент загрузки.")
            self.sel.elem_invis(нет ссылкам)
            logging.info("Жду, пока появится строка с номером направления.")
            self.sel.elem_vis(fнет ссылкам)
            time.sleep(1)
            logging.info("Ищу кнопку просмотра направления (глаз или карандаш).")
            button_eye_or_pencil = self.sel.find_xpath(
                нет ссылкам
                'or @class="mat-mdc-tooltip-trigger icon-button icon-edit-icon"]'
                )
            logging.info("Кликает по кнопке 'Просмотреть направление'")
            self.sel.click_with_error(button_eye_or_pencil)
        except Exception as err:
            logging.error(f"Ошибка при нажатии кнопки 'Просмотреть направление' в методе get_in_directon, направление {direction_number}\n{err}", exc_info=True)

    def check_write_button(self, direction_number=DIRECTION_FOR_GET_TALONS):
        """"Проверяет, что кнопка записи направления находится на странице и кликает по ней."""
        try:
            logging.info("Жду, что по кнопке можно кликнуть.")
            self.sel.elem_clickable(нет ссылкам)
            logging.info("Нахожу кнопку 'Записать на прием'")
            click_appoiment = self.sel.find_xpath(нет ссылкам)
            logging.info("Кликает по кнопке 'Записать на прием'")
            self.sel.click_with_error(click_appoiment)
        except Exception as err:
            logging.error(f"Ошибка при нажатии кнопки 'Записать на прием' в методе check_write_button, направление: {direction_number}\n{err}", exc_info=True)
    
    def click_step_2(self):
        """Ждет, когда можно будет кликнуть по шагу 2 и кликает."""
        try:
            logging.info("Жду, что можно кликнуть по следующей неделе, по идее тогда все подгрузилось.")
            self.sel.elem_clickable(нет ссылкам)
            logging.info("Ищу элемент 'шаг 2'")
            step_2 = self.sel.find_xpath(нет ссылкам)
            logging.info("Кликает по шагу 2")
            self.sel.click(step_2)
            logging.info("Жду, пока появится специальность 'Акушерство и гинекология'")
            self.sel.elem_vis(нет ссылкам)
        except Exception as err:
            logging.error(f"Ошибка при клике по шагу 2 в методе click_step_2\n{err}", exc_info=True)

    def get_talons(self):
        """
        Находит специальности и количество таланов для них, сохраняет в бд, заменяет данные о свободных талонах в таблице
        moniki_specialties."""
        try:
            logging.info("Прохожу в цикле специальности и количество свободных талонов с шагом 2(вторая строка это число направлений).")
            for speacialty in range(0, len(self.sel.find_xpath_elements(нет ссылкам))*2, 2):
                logging.info("Нахожу специальность от первой строки и вниз.")
                spec = self.sel.find_xpath(fнет ссылкам)
                logging.info("Нахожу количество свободныхталонов для текущей строки специальности.")
                count_spec = self.sel.find_xpath(fнет ссылкам)
                logging.info("Проверка что специальность и количество ячеек не None.")
                # Проверка, что специальность и число ячеек не ноль, так бывает)
                if spec is not None and count_spec is not None:
                    spec = spec.text
                    count_spec = count_spec.text
                else:
                    logging.info(f"Специальности с None: {speacialty+1} по номеру. Жду и пробую еще раз")
                    logging.info("На первом проходе специальность и количество талонов было None, пробую еще раз.")
                    spec = self.sel.find_xpath(fнет ссылкам).text
                    count_spec = self.sel.find_xpath(fнет ссылкам).text
                logging.info("Определяю число талонов как второй элемент строки с текстом ': '.")
                count_spec = count_spec.split(': ')[1]
                logging.info("Подгружаю в переменную текущее количество талонов по специальностям.")
                specialty = bd.get_data_all_specialty()
                logging.info("Проверяю, что специальность есть в БД, а если нет, то устанавливаю 0 талонов.")
                if specialty.get(spec, 'Not') != 'Not':
                    logging.info("Вычисляю разницу между талонами в БД и текущим количество(отриц.значение хорошо).")
                    # Такая строка необходима, для некоторых специальностей count_spec сразу число, а не строка.
                    change = specialty[spec] - int(count_spec) if isinstance(count_spec, str) else count_spec
                    logging.info("Проверяю разницу между ячейками, если она не ноль, иду дальше.")
                    if change != 0:
                        logging.info(f"Специальность {spec} стало талонов {count_spec} изменилась на {change}")
                        logging.info("Если разница талонов меньше -1, то добавляю в БД для аналитики. Не трогаю одиночные талоны - отмена других больниц.")
                        if change < -1:
                            logging.info("Добавляет информацию об открытии талонов для специальности в таблицу moniki_data.")
                            bd.put_change_data(spec, int(change))
                        logging.info("Меняет количество талонов в БД доступных для записи.")
                        bd.change_value_specialty(spec, int(count_spec))
                else:
                    logging.info(f"Специальности {spec} не было в словаре ранее. Добавляю специальность и текущее кол-во талонов.")
                    bd.put_specialty(spec, int(count_spec))

            logging.info("Нахожу элемент кнопки 'Закрыть'")
            close_button = self.sel.find_xpath(нет ссылкам)
            logging.info("Кликаю по кнопке 'Закрыть'")
            self.sel.click(close_button)
            print('Обновил информацию о талонах в:', now())
        except Exception as err:
            logging.error(f"Ошибка при получении талонов в методе get_talons\n{err}", exc_info=True)

    def get_specialty_from_bd(self) -> dict:
        """Берет информацию из БД по текущему количеству талонов для специальностей."""
        try:
            logging.info("Обращаюсь к таблице moniki_specialities и получаю информацию о специальностях и талонах на текущий момент.")
            data = bd.get_data_all_specialty()
            logging.info("Возвращаю словарь с данными специальностей и талонов для них из БД.")
            return data
        except Exception as err:
            logging.error(f"Ошибка при получении талонов в методе get_specialty_from_bd\n{err}", exc_info=True)
                                
    def get_need_record(self) -> list:
        """Запрос к БД и получение данных направлений не записанных."""
        try:
            logging.info("Обращаюсь к таблице moniki_records и получаю список направлений с данными без записи.")
            need_record = bd.get_not_recorder()
            logging.info("Возвращаю список списков с данными по направлениям не записанных.")
            return need_record
        except Exception as err:
            logging.error(f"Ошибка при получении талонов в методе get_need_record\n{err}", exc_info=True)

    def check_next_week_button(self):
        """Проверяет, что появилась кнопка 'Следующая неделя' и по ней можно кликнуть."""
        try:
            logging.info("Жду, что кнопка 'Следующая неделя' появилась и отображается.")
            self.sel.time_wait = 30
            self.sel.elem_vis(нет ссылкам)
            logging.info("Проверяю что нет спинера при клике по следующей неделе")
            self.sel.elem_invis(нет ссылкам)
            logging.info("Проверяю, что кнопка 'Следующая неделя' кликабельна.")
            self.sel.elem_clickable(нет ссылкам)
            self.sel.time_wait = 60
        except Exception as err:
            self.sel.time_wait = 60
            logging.error(f"Ошибка при получении талонов в методе check_next_week_button\n{err}", exc_info=True)

    def check_visit_shedules(self) -> bool:
        """Проверяет, что сетка с расписанием есть и возвращает bool элемент."""
        try:
            logging.info("Если есть сетка с расписанием на этой неделе, то возвращает True")
            self.sel.time_wait = 1
            self.sel.elem_vis_with_timeout(нет ссылкам)
            self.sel.time_wait = 60
            return True
        except TimeoutException:
            self.sel.time_wait = 60
            logging.info("Расписания нет на этой неделе.")
            return False
        except Exception as err:
            logging.error(f"Ошибка при получении талонов в методе check_visit_shedules\n{err}", exc_info=True)
                                
    def correct_specific(self, specific: str) -> Union[None, str]:
        """Проверяет специфику и возвращает None или строку"""
        logging.info("Проверяю, что специфика есть и не пустая строка или None.")
        if specific is None or specific == '':
            logging.info("Специфики нет, возвращаю None.")
            return None
        logging.info("Специфика существует, возвращаю изначальную строку с ней.")
        return specific

    def check_specific_fio(self, specific: str) -> Union[str, list]:
        """Проверяет фио в специфике и возвращает строку или список."""
        logging.info("Проверяю есть ли запятая с пробелом в специфике.")
        if ',' in specific:
            logging.info("В специфике есть запятая, значит разделяю на несколько имен и возвращают список.")
            names = specific.split(', ')
            return names
        else:
            logging.info("В специфике нет запятой, значит фамилия одна и возвращаю переданную специфику.")
            return specific
                                
    def get_locator_for_search(self, specific: str) -> str:
        """
        Проверяет специфику, если она пуста, то возвращает локатор для поиска свободных ячеек.
        Если в специфике есть специальность, то возвращает локатор для поиска ячеек по специфике.
        Если в специфике есть 'ФИО', то возвращает локатор для поиска ячеек по фио.
        """
        logging.info("Проверяю, что специфика есть.")
        if specific is None:
            logging.info("Специфика пуста, возвращаю локатор для поиска свободных ячеек.")
            return нет ссылкам
        logging.info("Проверяю, что в специфике есть ФИО.")
        if 'ФИО: ' in specific:
            logging.info("Обнаружил 'ФИО' в специфике. Оставляю только часть строки с фио.")
            specific = specific.split("ФИО: ")[1]
            logging.info("Проверяю, есть ли другие фамилии в специфике. Если есть, то делаю списком, если нет, то оставляю строкой.")
            specific = specific if ',' not in specific else specific.split(',')
            logging.info("Если специфика в итоге строка, то ФИО одно. Возвращаю локатор для одного фио.")
            if isinstance(specific, str):
                return fнет ссылкам
            logging.info("Если специфика в итоге список, то ФИО много. Возвращаю локатор для поиска многих фио.")
            many_names_on_str = ''.join([f'contains(text(), "{x}") or ' for x in specific])
            locator = (
                нет ссылкам
                f'{many_names_on_str[:-4]}'
                нет ссылкам
                )
            return locator
        logging.info("В специфике специальность, возвращаю локатор для поиска специальности в разном регистре.")
        locator = (
            fнет ссылкам
            f' or contains(text(), "{specific.upper()}")'
            fнет ссылкам
        )
        return locator

    def click_next_week(self):
        """Находит элемент "Шаг 2", скроллит до него и затем кликает на кнопку "Следующая неделя"."""
        try:
            self.sel.time_wait = 60 
            logging.info("Проверяю что нет спинера при клике по следующей неделе")
            self.sel.elem_invis(нет ссылкам)
            logging.info("Нахожу элемент с надписью 'шаг 2'.")
            step_2 = self.sel.find_xpath(нет ссылкам)
            time.sleep(2)
            logging.info("Скроллю до элемнета 'Шаг 2'.")
            self.sel.scroll(step_2)
            time.sleep(1)

            logging.info("Ищу кнопку 'Следующая неделя'.")
            next_week = self.sel.find_xpath(нет ссылкам)
            logging.info("Кликаю на кнопку 'Следующая неделя'.")
            self.sel.click(next_week)
            logging.info("Ждем пока крутилка не исчезнет после клика по следующей неделе.")
            self.sel.elem_invis(нет ссылкам)
        except Exception as err:
            logging.error(f"Ошибка при клике на кнопку 'Следующая неделя' в методе click_next_week: {err}", exc_info=True)

    def finding_free_cells(self, locator: str):
        """Находит все элементы на странице по переданному локатору и возвращает их."""
        try:
            logging.info("Нахожу все элементы с указанным локатором и возвращаю их.")
            return self.sel.find_xpath_elements(locator)
        except Exception as err:
            logging.error(f"Ошибка при поиске элементов по локатору в методе finding_free_cells: {err}", exc_info=True)

    def scroll_step_2(self):
        """Скроллит страницу до элемента 'Шаг 2'."""
        try:
            logging.info("Ищу элемент 'Шаг 2'.")
            step_2 = self.sel.find_xpath(нет ссылкам)
            time.sleep(1)
            logging.info("Скроллю до элемента 'Шаг 2'.")
            self.sel.scroll(step_2)
            time.sleep(1)
        except Exception as err:
            logging.error(f"Ошибка при скроллинге до элемента 'Шаг 2' в методе scroll_step_2: {err}", exc_info=True)

    def create_forbitten_dates(self) -> list:
        """Создает список с исключениями: сегодня, завтра, и возвращает его."""
        logging.info("Создаю список с датами, который надо исключать.")
        forbidden_dates = [(
                datetime.datetime.now() + datetime.timedelta(days=0+x)
                ).strftime("%d.%m.%Y") for x in range(3)
                ]
        logging.info("Дополняю список дат текстовыми 'сегодня', 'завтра', 'послезавтра', ведь емиас их включает.")
        forbidden_dates.extend(['сегодня', 'завтра', 'послезавтра'])
        logging.info("Возвращаю список дат для исключения.")
        return forbidden_dates

    def search_free_cell_and_click(self, number_cell: int, locator: str):
        """Находит свободную ячейку в неделе и кликает по ней."""
        try:
            logging.info("Нахожу первую ячейку врача с расписанием.")
            free_cell = self.sel.find_xpath(f'({locator})[{number_cell+1}]')
            self.sel.time_wait = 3
            logging.info("Проверка могу ли кликнуть по ячейке сейчас, видна ли она.")
            if not self.sel.elem_to_be_clickable(free_cell):
                logging.info("Ячейка не видна, скролю до неё.")
                self.sel.scroll(free_cell)
                # sel.browser.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", free_cells)
                # close_button = sel.find_xpa(нет ссылкам)
                # close_button.location_once_scrolled_into_view
                # # ActionChains(sel.browser).move_to_element(free_cells).perform()
                #ActionChains(sel.browser).move_by_offset(0, -60).perform()
            self.sel.time_wait = 60
            time.sleep(1)
            logging.info("Кликаю по ячейке.")
            self.sel.click_with_error(free_cell)
        except Exception as err:
            logging.error(f"Ошибка при поиске свободной ячейки в методе search_free_cell_and_click: {err}", exc_info=True)

    def get_date_cell(self) -> str:
        """После кликая по свободной ячейке врача, проверяет дату записи и возвращает её."""
        try:
            logging.info("Жду, что поле с датой появилось.")
            self.sel.elem_vis(нет ссылкам)
            logging.info("Получаю текст из поля с датой записи и возвращаю его.")
            data_record = self.sel.find_xpath(нет ссылкам).text
            return data_record
        except Exception as err:
            logging.error(f"Ошибка при получении даты записи в методе get_date_cell {data_record=}: {err}", exc_info=True)
                                
    def check_data_record(self, data_record: str, forbidden_dates: list) -> bool:
        """Проверяет, что дата не входит в запрещенные и возвращает True если дата запрещена, False не запрещена."""
        logging.info("Проверяю, что дата не входит в запрещенный диапазон.")
        for word in forbidden_dates:
            if word in data_record:
                logging.info(f"Дата входит в запрещенный диапазон {word} присутсвует в {data_record=}.")
                return True
        logging.info("Дата не входит в запрещенный диапазон.")
        return False

    def click_on_active_cell(self):
        """Если дата не подошла, то нужно клинкуть по текущей активной ячейке, чтобы вернулись предыдущие."""
        try:
            self.sel.time_wait = 60
            logging.info("Нахожу теперь уже активную ячейку.")
            active_cell = self.sel.find_xpath(нет ссылкам)
            logging.info("Кликаю по активной ячейке, чтобы вернуться ко всем ячейкам")
            self.sel.click_with_error(active_cell)
            time.sleep(1)
        except Exception as err:
            logging.error(f"Ошибка при клике на активную ячейку в методе click_on_active_cell: {err}", exc_info=True)

    def find_times_in_cell(self) -> list:
        """Находит время с возможностью для записи."""
        try:
            logging.info("Нахожу и возвращаю список со временем, на которое можно записать.")
            self.sel.wait_time = 1
            self.sel.browser.implicitly_wait(3)
            times = self.sel.find_xpath_elements(нет ссылкам)
            self.sel.wait_time = 60
            return times
        except Exception as err:
            logging.error(f"Ошибка при поиске времени в методе find_times_in_cell: {err}", exc_info=True)

    def select_last_time(self) -> str:
        """Выбирает последнюю ячейку со временем из доступных и возвращает время."""
        try:
            logging.info("задаю ожидания.")
            self.sel.browser.implicitly_wait(5)
            self.sel.time_wait = 60
            logging.info("Ожидаю, что по последней ячейке можно кликнуть")
            self.sel.elem_clickable(нет ссылкам)
            #notif(title="МОНИКИ спец", message=f"Обнаружены талоны для {specific}")
            logging.info("Нахожу элемент с последней ячейкой.")
            cell_time = self.sel.find_xpath(нет ссылкам)
            logging.info("Скроллю до последней ячейки со временем.")
            self.sel.scroll(cell_time)
            time.sleep(1)
            logging.info("Сохраняю информацию о времени записи в переменную, чтобы ей вернуть.")
            time_record = cell_time.text
            logging.info("Кликаю по ячейке со временем.")
            self.sel.click_with_error(cell_time)
            return time_record
        except Exception as err:
            logging.error(f"Ошибка при выборе последней ячейки со временем в методе select_last_times: {err}", exc_info=True)
                                
    def click_write_button_on_time(self):
        """Нажимаю на кнопку "записать" для времени."""
        try:
            logging.info("Нахожу кнопку для записи для ячейки со временем.")
            click_write = self.sel.find_xpath(нет ссылкам)
            logging.info("Скроллю до кнопки 'записать', бывает, что её не видно.")
            self.sel.scroll(click_write)
            logging.info("Пытаюсь кликнуть по кнопке записи.")
            self.sel.click(click_write)
            time.sleep(1)
        except Exception as err:
            logging.error(f"Ошибка при нажатии на кнопку 'записать' в методе click_write_button_on_time: {err}", exc_info=True)
                                
    def click_close_after_write(self):
        """Нажимаю на кнопку 'закрыть' после записи."""
        try:
            logging.info("Ищу кнопку 'закрыть' после записи на время.")
            close_button = self.sel.find_xpath(нет ссылкам)
            logging.info("Пробую кликнуть по кнопке 'закрыть'.")
            self.sel.click(close_button)
        except Exception as err:
            logging.error(f"Ошибка при нажатии на кнопку 'закрыть' в методе click_close_after_write: {err}", exc_info=True)

    def click_close_after_search_all_weeks(self):
        """Нажимаю на кнопку 'закрыть' после поиска."""
        try:
            logging.info("Ищу кнопку 'закрыть' после безрезультатного поиска.")
            close_button = self.sel.find_xpath(нет ссылкам)
            logging.info("Пробую кликнуть по кнопке 'закрыть'.")
            self.sel.click(close_button)
        except Exception as err:
            logging.error(f"Ошибка при нажатии на кнопку 'закрыть' в методе click_close_after_search_all_weeks: {err}", exc_info=True)

    def save_data_of_writing_in_bd(self, date_record: str, time_record: str, direction_number: str):
        """Сохраняет в базу данных информацию о том, что пациент успешно записан."""
        logging.info(f"Записываю в базу данных факт записи пациента по направлению: {date_record} {time_record} {direction_number}")
        bd.change_datetime_record(
            is_recorded=1,
            date_direct=date_record,
            time_direct=time_record,
            number_direct=direction_number)




def main():
    """Главная функция для создания класса и запуска методов."""
    try:
        s = Sel()
        s.open_emias()
        s.input_login_and_pass()
        s.log_in()
        s.open_section_directs()
        s.switch_to_another_window()
        # окно с направление, очистка фильтра и поиск направлений
        s.open_filters()
        s.del_doctor_filter()
        s.clear_direct_and_search()
        s.find_direct()
        s.get_in_directon()
        s.check_write_button()
        s.scroll_step_2()
        s.click_step_2()
        s.get_talons()
        # запрос к БД и получение номеров направлений не записанных
        specialty_info = s.get_specialty_from_bd()
        need_record = s.get_need_record()
        logging.info("Если количество направлений, по которым нужно записать больше нуля, то начинаю их отработку.")
        if len(need_record) > 0:
            logging.info("Цикл по направлениям.")
            for record in need_record:
                logging.info("Задаю переменные из направлений: номер, специальность, специфика.")
                number_direct = record[0]
                spec = record[1]
                specific = s.correct_specific(record[2])
                if specialty_info[spec] > 0:
                    logging.info(f"Номер направления: {number_direct} специальность: {spec} специфика: {specific}")
                    logging.info("Если есть талоны для данной специальности, осуществляю запись.")
                    s.clear_direct_and_search(direction_number=number_direct)
                    s.find_direct()
                    s.get_in_directon(direction_number=number_direct)
                    s.check_write_button(direction_number=number_direct)
                    s.scroll_step_2()
                    locator = s.get_locator_for_search(specific=specific)
                    forbidden_dates = s.create_forbitten_dates()
                    logging.info("Цикл для проверки недель и ячеек на них. По умолчанию проверяем 3 недели.")
                    for _ in range(3):
                        s.check_next_week_button()
                        if not s.check_visit_shedules():
                            s.click_next_week()
                            continue
                        # далее в поиске ячеек смотрим на количество элементов
                        logging.info("Задаю ожидание в секунду, чтобы не ждать слишком долго ячеек с расписанием.")
                        s.sel.time_wait = 1
                        free_cells = s.finding_free_cells(locator=locator)
                        if len(free_cells) == 0:
                            s.click_next_week()
                            continue
                        s.scroll_step_2()
                        s.sel.time_wait = 60
                        logging.info("Цикл для прохода по доступным ячейкам для записи.")
                        is_not_writing = True
                        for number_cell in range(len(free_cells)):
                            time.sleep(1)
                            s.search_free_cell_and_click(number_cell=number_cell, locator=locator) 
                            data_record = s.get_date_cell()
                            if s.check_data_record(data_record=data_record, forbidden_dates=forbidden_dates):
                                s.click_on_active_cell()
                                continue
                            times = s.find_times_in_cell()
                            if len(times) == 0:
                                s.click_on_active_cell()
                                continue
                            time_record = s.select_last_time()
                            s.click_write_button_on_time()
                            s.click_close_after_write()
                            is_not_writing = False
                            print('Запуск был в:', now(), f'Пациент записан. {specific=}.')
                            s.save_data_of_writing_in_bd(
                                date_record=data_record,
                                time_record=time_record,
                                direction_number=number_direct)
                            logging.info("Если пациента записан, то рвем цикл прохода по ячейкам времени")
                            break
                        if is_not_writing:
                            s.click_next_week()
                        else:
                            logging.info("Если пациент записан, то рвем переходы по неделям.")
                            break
                    logging.info("Нажимаю на кнопку закрыть, если не получилось записать.")
                    s.click_close_after_search_all_weeks()
                        
                    time.sleep(1)
        s.sel.quit()
    except SessionNotCreatedException as e:
        print("\n---------------" f"\n{e}")
        print(
            "---------------"
            "\nВерсия chromedriver не поддерживает текущую версию"
            " браузера Chrome."
            "\nОбновите версию chromedriver"
            "\n---------------"
        )
        input("Для продолжения нажмитие Enter...")
    except Exception as e:
        logging.error(f"__! Возникла ошибка в функции main\n{e}")
        time.sleep(2)
        if "because another element" in str(e):
            s.sel.quit()
            return main()
        s.sel.quit()
        return main()


if __name__ == "__main__":
    main()
    schedule.every(4).minutes.do(main)
    while True:
        schedule.run_pending()
