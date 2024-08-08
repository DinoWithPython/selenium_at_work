import datetime
from typing import Callable
import os
import os.path
import platform
# import sys
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def now():
    return datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")


def log_any_error(any_text):
    """Функция для записи ошибок в файл."""
    with open(rf"{BASE_DIR}\log_any_error.txt", "a+") as log:
        print(f"[{now()}] {str(any_text)}", file=log)


class SeleniumBrow:
    """Создаем экземляр браузера, задаем ссылку и ожидание."""

    if platform.system() == "Windows":
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
    #     options.headless = True
    #     options.add_argument('log-level=2')
    #     # options.add_argument("--headless=new")
    #     options.add_experimental_option(
    #         "excludeSwitches",
    #         ["enable-automation"]
    #         )
    #     options.add_experimental_option('useAutomationExtension', False)

    def __init__(self, link: str, main: Callable, time_wait: int = 120):
        self.link = link
        self.time_wait = time_wait
        self.name_main_func = main
        if platform.system() == "Windows":
            self.browser = webdriver.Chrome(options=self.options)
        elif platform.system() == "Linux":
            self.browser = webdriver.Firefox()  # options=self.options

    def go_link(self):
        """Метод перехода по ссылке."""
        try:
            self.browser.get(self.link)
        except Exception as e:
            log_any_error(f"[ERR] Возникла ошибка go_link\n{e}")
            time.sleep(2)
            self.quit()

    def clear_area(self, element):
        """Очищаем поле в объекте."""
        element.clear()

    def find_id(self, text):
        """Находит элемент по id и возвращает его."""
        self.browser.implicitly_wait(15)
        try:
            search = self.browser.find_element("id", text)
            return search
        except Exception as e:
            log_any_error(f"[ERR] Возникла ошибка find_id в стационаре\n{e}")
            time.sleep(2)
            self.quit()

    def find_xpa(self, xpath):
        """Ждет пока по элементу можно кликнуть и возвращает его."""
        try:
            search = WebDriverWait(self.browser, self.time_wait).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            if isinstance(search, type(None)):
                time.sleep(1)
                log_any_error(f"[ERR] Объекты None\n{locals()}")
                return self.find_xpa(self, xpath)
            return search
        except Exception as e:
            log_any_error(f"[ERR] Возникла ошибка в фунции find_xpa в стационаре \n{e.msg}")
            time.sleep(2)
            return None

    def find_xpa_elements(self, xpath):
        """Вернуть список элементов по xpath."""
        try:
            search = self.browser.find_elements(by=By.XPATH, value=xpath)
            return search
        except Exception as e:
            log_any_error(f"[ERR] Возникла ошибка find_xpa_elements\n{e}")
            time.sleep(2)

    def click(self, element):
        """Клик по элементу."""
        try:
            if not isinstance(element, type(None)):
                element.click()
            else:
                raise TypeError("Элемента не существует! Невозможно кликнуть.")
        except TypeError as e:
            log_any_error(f"[ERR] Возникла ошибка в функции click\n{e}\n{locals()}")
            # input('Проверь на каком этапе возникла ошибка!')
            self.quit()
            return self.name_main_func()

        except Exception as e:
            log_any_error(f"[ERR] Возникла ошибка в функции click\n{e.msg}\n{element}")
            time.sleep(2)
            self.click(element)

    def scroll(self, obj):
        """Скрол на странице до элемента."""
        self.browser.execute_script(
            "return arguments[0].scrollIntoView(true);",
            obj
            )

    def send_text(self, element, text: str):
        """Отправляет текст в указанный элемент."""
        element.send_keys(text)

    def elem_vis(self, xpath):
        """Ожидаем элемент на отображение."""
        try:
            element = WebDriverWait(self.browser, self.time_wait).until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
            if element:
                return True
            return False
        except TypeError as e:
            log_any_error(f"[ERR] Элемент не появился. Ошибка TypeError в  elem_vis \n{e}")
        except TimeoutException:
            log_any_error("[ERR] Элемент не появился. Ошибка TimeoutException в  elem_vis \n")
        except Exception as e:
            log_any_error("[ERR] Элемент не появился. Ошибка Exception в  elem_vis\n")
            log_any_error(type(e))
            log_any_error(f"{e.msg}")
            time.sleep(2)

    def elem_vis_with_timeout(self, xpath):
        """Ожидаем элемент на отображение с ошибкой по таймауту."""
        try:
            WebDriverWait(self.browser, self.time_wait).until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
        except TimeoutException:
            raise TimeoutException
        except Exception as e:
            log_any_error(f"[ERR] Возникла ошибка elem_vis_with_timeout\n{e}")
            time.sleep(2)

    def elem_invis(self, xpath):
        """Ожидаем элемент на исчезновение."""
        try:
            WebDriverWait(self.browser, self.time_wait).until(
                EC.invisibility_of_element_located((By.XPATH, xpath))
            )
        except Exception as e:
            log_any_error(f"[ERR] Возникла ошибка elem_invis\n{e}")
            time.sleep(2)

    def elem_clickable(self, xpath):
        """Ожидаем элемент на клик."""
        try:
            WebDriverWait(self.browser, self.time_wait).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
        except Exception as e:
            log_any_error(f"[ERR] Возникла ошибка elem_clickable\n{e}")
            time.sleep(2)

    def quit(self):
        """Закрывает браузер."""
        self.browser.quit()
