"""
Общий класс для автоматизации рабочих процессов.
"""

import datetime
from random import randint
from typing import Callable
import logging
import os
import os.path
import time

from plyer import notification
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv()

logging.basicConfig(
    level=logging.ERROR,
    filename="frfx_class.log",
    filemode="a",
    format="%(asctime)s %(levelname)s %(message)s")

def now() -> str:
    return datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")


def log_any_error(any_text):
    """Функция для записи ошибок в файл."""
    with open(rf"{BASE_DIR}\frfx_class_error.txt", "a+") as log:
        print(f"[{now()}] {str(any_text)}", file=log)


def notif(title="Заголовок", message="Сообщение."):
    """Уведомляет о каких-либо событиях."""
    notification.notify(
        title=title,
        message=message)


class SeleniumBrow:
    """Создаем экземляр браузера, задаем ссылку и ожидание."""

    options = webdriver.FirefoxOptions()
    options.add_argument("--start-maximized")
    #options.binary_location = "geckodriver"

    def __init__(self, link: str, main: Callable, time_wait: int = 120, headless: bool = False, is_frk: bool = False):
        self.link: str = link
        self.time_wait: int = time_wait
        self.name_main_func: function = main
        self.resource: str = None
        if headless:
            self.options.add_argument("-headless")
        self.browser: webdriver = webdriver.Firefox(options=self.options)
        self.browser.maximize_window()
        self.actions = ActionChains(self.browser)

        if is_frk:
            # для хрома
            # self.options.add_extension('./cryp/1.2.13_0.zip')
            # self.options.add_extension('./gos/1.2.8_0.zip')
            self.browser.install_addon(rf"{BASE_DIR}/extensions/ru.cryptopro.nmcades@cryptopro.ru.xpi", temporary=True)
            self.browser.install_addon(rf"{BASE_DIR}/extensions/pbafkdcnd@ngodfeigfdgiodgnmbgcfha.ru.xpi", temporary=True)

    def clear_area(self, element):
        """Очищаем текстовое поле в объекте селениума."""
        element.clear()

    def click(self, element):
        """Пробуем кликнуть по элементу до бесконечности. Сохраняет скриншоты, когда не смог."""
        try:
            if not isinstance(element, type(None)):
                element.click()
            else:
                logging.error("Элемента не существует! Невозможно кликнуть.\n")
                raise TypeError("Элемента не существует! Невозможно кликнуть.")
        except TypeError as e:
            log_any_error(f"[ERR] Возникла ошибка TypeError в функции click\n{e}\n{locals()}")
            logging.error("Элемента не существует! Невозможно кликнуть.\n", exc_info=True)
            # input('Проверь на каком этапе возникла ошибка!')
            self.quit()
            return self.name_main_func()

        except Exception as e:
            log_any_error(f"[ERR] Возникла неизвестная ошибка в функции click\n{e.msg}\n{element}\n{type(e)}")
            logging.error("Возникла неизвестная ошибка в функции click.\n", exc_info=True)
            name_file = f'error_click_{randint(1, 10)}.png'
            self.browser.save_screenshot(name_file)
            time.sleep(2)
            self.click(element)

    def click_with_error(self, element):
        """Использует стандартный клик селениума и попускает, если не смог. Сохраняет скриншоты, когда не смог."""
        try:
            if not isinstance(element, type(None)):
                element.click()
            else:
                logging.error("Элемента не существует! Невозможно кликнуть.\n")
                raise TypeError("Элемента не существует! Невозможно кликнуть.")
        except TypeError as e:
            log_any_error(f"[ERR] Возникла ошибка TypeError в функции click\n{e}\n{locals()}")
            logging.error("Элемента не существует! Невозможно кликнуть.\n", exc_info=True)
            # input('Проверь на каком этапе возникла ошибка!')
            self.quit()
            return self.name_main_func()
        except ElementClickInterceptedException as err:
            logging.error("[click_with_error] Ошибка клика по элементу, потому что что-то мешает или вроде того.\n", exc_info=True)
            raise ElementClickInterceptedException("[click_with_error] Не смог кликнуть по элементу")
        except Exception as e:
            log_any_error(f"[ERR] Возникла неизвестная ошибка в функции click_with_error\n{e.msg}\n{element}\n{type(e)}")
            logging.error("Возникла неизвестная ошибка в функции click_with_error.\n", exc_info=True)
            name_file = f'error_click_we_{randint(1, 10)}.png'
            self.browser.save_screenshot(name_file)
            time.sleep(2)

    def ex_sc(self, script_on_element: str):
        """Проверка загрузки элемена в DOM для execute_script по тексту JS элемента."""
        try:
            element = self.browser.execute_script(script_on_element)
            if element is None:
                self.ex_sc(script_on_element)
            else:
                return element
        except Exception as e:
            # log_any_error(f'Ошибка в функции DOM_is_downoading() \n{e}')
            if "Cannot read properties of null" in str(e):
                time.sleep(2)
                logging.info("Нет свойств у несуществуюшего элемента.")
                return self.ex_sc(script_on_element)
            elif "is null" in str(e):
                time.sleep(2)
                logging.info("Элемента не существует.")
                return self.ex_sc(script_on_element)
            elif "no attribute" in str(e):
                logging.info("Нет такого атрибута, возможно элемент еще не прогрузился.")
                time.sleep(2)
                return self.ex_sc(script_on_element)
            else:
                logging.error("Возникла неизвестная ошибка в функции ex_sc.\n", exc_info=True)

    def ex_sc_on_element(self, element, script_on_element: str):
        """Применяет JS скрипт на переданном элементе."""
        try:
            self.browser.execute_script(script_on_element, element)

        except Exception as e:
            # log_any_error(f'Ошибка в функции DOM_is_downoading() \n{e}')
            if "Cannot read properties of null" in str(e):
                time.sleep(2)
                logging.info("Нет свойств у несуществуюшего элемента.")
                return self.ex_sc(script_on_element)
            elif "no attribute" in str(e):
                logging.info("Нет такого атрибута, возможно элемент еще не прогрузился.")
                time.sleep(2)
                return self.ex_sc(script_on_element)
            else:
                logging.error("Возникла неизвестная ошибка в функции DOM_is_downoading.\n", exc_info=True)

    def elem_vis(self, xpath: str):
        """Ожидает элемент на отображение."""
        try:
            element = WebDriverWait(self.browser, self.time_wait).until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
            if element:
                return True
            return False
        except TypeError as e:
            log_any_error(f"[ERR] Элемент не появился. Ошибка TypeError в  elem_vis \n{e}")
            logging.error("Элемент не появился. Ошибка TypeError в  elem_vis \n", exc_info=True)
        except TimeoutException:
            log_any_error("[ERR] Элемент не появился. Ошибка TimeoutException в  elem_vis \n")
            logging.error("Элемент не появился. Ошибка TimeoutException в  elem_vis.\n", exc_info=True)
        except Exception as e:
            log_any_error("[ERR] Элемент не появился. Ошибка Exception в  elem_vis\n")
            logging.error("Элемент не появился. Ошибка Exception в  elem_vis.\n", exc_info=True)
            log_any_error(type(e))
            log_any_error(f"{e.msg}")
            time.sleep(2)

    def elem_vis_with_timeout(self, xpath: str):
        """Ожидает элемент на отображение с ошибкой по таймауту."""
        try:
            WebDriverWait(self.browser, self.time_wait).until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
        except TimeoutException:
            raise TimeoutException
        except Exception as e:
            log_any_error(f"[ERR] Возникла ошибка elem_vis_with_timeout\n{e}")
            logging.error("Возникла ошибка elem_vis_with_timeout.\n", exc_info=True)
            time.sleep(2)

    def elem_invis(self, xpath: str):
        """Ожидает элемент на исчезновение."""
        try:
            WebDriverWait(self.browser, self.time_wait).until(
                EC.invisibility_of_element_located((By.XPATH, xpath))
            )
        except Exception as e:
            log_any_error(f"[ERR] Возникла ошибка elem_invis\n{e}")
            logging.error("Возникла ошибка elem_invis.\n", exc_info=True)
            time.sleep(2)

    def elem_clickable(self, xpath: str):
        """Ожидает элемент на клик."""
        try:
            WebDriverWait(self.browser, self.time_wait).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
        except Exception as e:
            log_any_error(f"[ERR] Возникла ошибка elem_clickable\n{e}")
            logging.error("Возникла ошибка elem_clickable.\n", exc_info=True)
            time.sleep(2)

    def elem_to_be_clickable(self, xpath):
        """Ожидаем элемент на клик и возвращает True если может кликнуть."""
        try:
            WebDriverWait(self.browser, self.time_wait).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            return True
        except Exception as e:
            log_any_error(f"[ERR] Возникла ошибка elem_clickable\n{e}")
            logging.error("Возникла ошибка в elem_to_be_clickable, по элементу нельзя кликнуть.\n", exc_info=True)
            time.sleep(2)
            return False

    def find_id(self, text: str):
        """Находит элемент по id и возвращает его."""
        self.browser.implicitly_wait(15)
        try:
            search = self.browser.find_element("id", text)
            return search
        except Exception as e:
            log_any_error(f"[ERR] Возникла ошибка find_id \n{e}")
            logging.error("Возникла ошибка find_id.\n", exc_info=True)
            time.sleep(2)
            self.quit()

    def find_xpath(self, xpath: str):
        """Ждет пока по элементу можно кликнуть и возвращает его."""
        try:
            search = WebDriverWait(self.browser, self.time_wait).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            if isinstance(search, type(None)):
                time.sleep(1)
                log_any_error(f"[ERR] Объекты None\n{locals()}")
                logging.error("Возникла ошибка Объекты None.\n")
                return self.find_xpa(self, xpath)
            return search
        except Exception as e:
            log_any_error(f"[ERR] Возникла ошибка в фунции find_xpa \n{e.msg}")
            logging.error("Возникла ошибка find_xpa.\n", exc_info=True)
            time.sleep(2)
            return None

    def find_xpath_elements(self, xpath: str):
        """Вернуть список элементов по xpath."""
        try:
            search = self.browser.find_elements(by=By.XPATH, value=xpath)
            return search
        except Exception as e:
            log_any_error(f"[ERR] Возникла ошибка find_xpa_elements\n{e}")
            logging.error("Возникла ошибка find_xpa_elements.\n", exc_info=True)
            time.sleep(2)

    def go_link(self):
        """Метод перехода по ссылке."""
        try:
            self.browser.get(self.link)
        except Exception as e:
            log_any_error(f"[ERR] Возникла ошибка go_link\n{e}")
            logging.error("Возникла ошибка go_link.\n", exc_info=True)
            time.sleep(2)
            self.quit()

    def quit(self):
        """Закрывает браузер."""
        self.browser.quit()

    def scroll(self, obj):
        """Скрол на странице до элемента методом JS arguments[0].scrollIntoView({block: 'center', inline: 'center'})."""
        self.browser.execute_script(
            #"return arguments[0].scrollIntoView(true);",
            "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
            obj
            )

    def send_text(self, element, text: str):
        """Отправляет текст в указанный элемент."""
        element.send_keys(text)
