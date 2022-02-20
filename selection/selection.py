"""Алгоритм подбора."""
import json
from datetime import date, datetime

from db.db_tools import SelectionDB
from vk.vk_tools import (create_user_session, get_vk_user_3_foto_attachment_value, get_vk_user_3_foto_url,
                         get_vk_user_info, get_vk_user_link, search_vk_user,
                         select_pair, write_message_to_vk_user)


def calculate_years(start_dt, end_dt):
    """Количество лет между дата/время.

    Args:
        start_dt (datetime): Дата/время начала отрезка.
        end_dt (datetime): Дата/время конца отрезка.

    Returns:
        int: Количество лет
    """
    delta = (end_dt.month, end_dt.day) < (start_dt.month, start_dt.day)
    return end_dt.year - start_dt.year - delta


class Selection:
    """Класс подбора пары в ВК.

    Args:
        db_name (str): Путь до БД.
        group_vk_session (object): Сессия сообщества ВК.
        user_id (int): ИД пользователя ВК, выполняющего поиск.
        fields (list): Список полей подбора.
    """

    def __init__(self, db_name, group_vk_session, user_id, fields) -> None:
        self.db = SelectionDB(db_name)
        self.group_vk_session = group_vk_session

        self.user_id = user_id
        self.user_token = None
        self.user_vk_session = None

        self.selection_id = None
        self.stage_id = None
        self.fields = fields

        self.target_user_id = None
        self.target_user_info = {}

        self.pair_user_info = {}
        self.pair_user_id = None

    def stage_0_write_hello_message(self, next_stage=True):
        """Шаг 0. Вывод приветствия.

        Args:
            next_stage (bool, optional): Флаг необходимости перехода к следующему шагу.
        """
        answer = "Я бот подбора партнера. Приступим к подбору?(да/нет)"
        write_message_to_vk_user(self.group_vk_session, self.user_id, answer)
        if next_stage:
            self.next_stage()

    def stage_1_get_user_token(self, next_stage=True):
        """Шаг 1. Запрос токена пользователя.

        Args:
            next_stage (bool, optional): Флаг необходимости перехода к следующему шагу.
        """
        answer = "Введите токен пользователя VK от имени которого будет производиться подбор."
        write_message_to_vk_user(self.group_vk_session, self.user_id, answer)
        if next_stage:
            self.next_stage()

    def stage_2_get_target_user_id(self, next_stage=True):
        """Шаг 2. Запрос целевого пользователя для подбора.

        Args:
            next_stage (bool, optional): Флаг необходимости перехода к следующему шагу.
        """
        answer = "Введите имя пользователя или его id в ВК, для которого мы ищем пару."
        write_message_to_vk_user(self.group_vk_session, self.user_id, answer)
        if next_stage:
            self.next_stage()

    def stage_3_get_target_user_info(self, next_stage=True):
        """Шаг 3. Пользователь найден.

        Args:
            next_stage (bool, optional): Флаг необходимости перехода к следующему шагу.
        """

        answer = f"""Целевой пользователь найден!
        {get_vk_user_link(self.target_user_id)}"""
        write_message_to_vk_user(self.group_vk_session, self.user_id, answer)
        if next_stage:
            self.next_stage()

    def stage_4_get_pair(self, next_stage=True):
        """Шаг 4. Поиск пары.

        Args:
            next_stage (bool, optional): Флаг необходимости перехода к следующему шагу.
        """
        answer = "Поиск пары"
        write_message_to_vk_user(self.group_vk_session, self.user_id, answer)
        if next_stage:
            self.next_stage()

    def get_data_from_user(self, data):
        """Вывод сообщения с запросом недостающих данных.

        Args:
            data (str): Наименование поля с данными.
        """
        answer = f"Для подбора не хватает данных. Введите {data}"
        write_message_to_vk_user(self.group_vk_session, self.user_id, answer)

    def create_new_selection(self):
        """Создание новой записи о подборе в БД.
        """
        self.db.create_selection(self.user_id)
        self.selection_id = self.db.get_active_selection_id(self.user_id)
        self.stage_id = self.db.get_stage_id(self.selection_id)

    def get_exist_selection(self):
        """Восстановление существующего подбора из БД.
        """
        self.selection_id = self.db.get_active_selection_id(self.user_id)
        selection_info = self.db.get_selection(self.selection_id)
        self.user_id = selection_info[0]
        self.stage_id = selection_info[5]
        self.target_user_id = selection_info[2]
        if selection_info[3]:
            target_user_info = selection_info[3]
            target_user_info = target_user_info.replace("'", '"')
            target_user_info = target_user_info.replace("True", "true")
            target_user_info = target_user_info.replace("False", "false")
            target_user_info = json.loads(target_user_info)
            self.target_user_info = target_user_info
        elif self.target_user_id:
            self.target_user_info = get_vk_user_info(
                self.user_vk_session, self.target_user_id, self.fields)
        self.user_token = selection_info[1]
        self.pair_user_id = selection_info[-1]
        if self.user_token:
            self.user_vk_session = create_user_session(self.user_token)

    def get_selection(self):
        """Получение подбора.
        """
        is_new_selection = not self.db.active_selection_exists(self.user_id)
        if is_new_selection:
            self.create_new_selection()
        else:
            self.get_exist_selection()

    def next_stage(self):
        """Переход к следующему шагу подбора.
        """
        self.db.next_stage(self.selection_id)

    def close_selection(self):
        """Завершение подбора без результата.
        """
        answer = "Подбор завершен. Спасибо."
        write_message_to_vk_user(self.group_vk_session, self.user_id, answer)
        self.db.close_seletion(self.selection_id)

    def complete_selection(self):
        """Завершение подбора с выводом результата.
        """
        answer = ""
        attachment = ""
        if self.pair_user_id and self.pair_user_id != -1:
            self.db.set_result_vk_user_id(self.selection_id, self.pair_user_id)
            pair_user_url = get_vk_user_link(self.pair_user_id)
            attachment = get_vk_user_3_foto_attachment_value(
                self.user_vk_session, self.pair_user_id)
            answer = f"""Подобрана пара:
            {pair_user_url}"""
            write_message_to_vk_user(
            self.group_vk_session, self.user_id, answer, attachment)
            self.db.add_user_id_to_shown(self.selection_id, self.pair_user_id)
            answer = "Искать дальше?(да/нет)"
            write_message_to_vk_user(
                self.group_vk_session, self.user_id, answer)
        else:
            answer = "К сожалению, не удалось подобрать пару."
            write_message_to_vk_user(
                self.group_vk_session, self.user_id, answer)
            self.close_selection()

    def required_data_out(self):
        """Получение списка отсутствующих полей.

        Returns:
            list: Список полей без данных.
        """
        required_data_list = self.fields.split(",")
        out_data_list = []
        for item in required_data_list:
            if not self.target_user_info.get(item):
                out_data_list.append(item)
            elif item == "bdate":
                try:
                    datetime.strptime(self.target_user_info.get(
                        item), "%d.%m.%Y").date()
                except:
                    out_data_list.append(item)
        return out_data_list

    def processing_selection(self, message_text=None):
        """Выполнение подбора.

        Args:
            message_text (str, optional): Сообщение от пользоваателя.
        """

        self.get_selection()

        # Обработка необходимого шага подбора
        # Приветствие и запрос начала работы
        if self.stage_id == 0:
            self.stage_0_write_hello_message()
        # Запрос токена
        if self.stage_id == 1:
            message_text.lower()
            if message_text == "да":
                self.stage_1_get_user_token()
            elif message_text == "нет":
                self.close_selection()
            else:
                self.stage_0_write_hello_message(next_stage=False)
        # Запрос пользователя
        elif self.stage_id == 2:
            user_token = message_text
            try:
                user_vk_session = create_user_session(user_token)
                get_vk_user_info(user_vk_session, self.user_id)
                self.db.set_vk_user_token(self.selection_id, user_token)
                self.stage_2_get_target_user_id()
            except Exception as e:
                print(e)
                self.stage_1_get_user_token(next_stage=False)
        # Поиск целевого пользователя
        elif self.stage_id == 3:
            target_user = message_text
            if target_user:
                target_user_id = search_vk_user(
                    self.user_vk_session, target_user)
                if target_user_id:
                    self.target_user_id = target_user_id
                    self.target_user_info = get_vk_user_info(
                        self.user_vk_session, self.target_user_id, self.fields)
                    self.db.set_target_user_id(
                        self.selection_id, self.target_user_id)
                    self.db.set_target_user_info(
                        self.selection_id, self.target_user_info)
                    self.stage_3_get_target_user_info()
                    self.processing_selection()
                else:
                    self.stage_2_get_target_user_id(next_stage=False)
            else:
                self.stage_2_get_target_user_id(next_stage=False)
        # Проверяем полноту данных
        elif self.stage_id == 4:
            if not self.required_data_out():
                self.stage_4_get_pair()
                self.processing_selection()
            elif not message_text:
                data = self.required_data_out()[0]
                self.get_data_from_user(data)
            elif message_text:
                data = self.required_data_out()[0]
                self.target_user_info[data] = message_text
                self.db.set_target_user_info(
                    self.selection_id, self.target_user_info)
                self.processing_selection()
        # Ищем пару
        elif self.stage_id == 5:
            shown_user_ids_list = self.db.get_shown_user_ids(
                self.user_id, self.target_user_id)
            if message_text == "нет":
                self.close_selection()
            else:    
                if not self.pair_user_id or self.pair_user_id in shown_user_ids_list:
                    # Расчет доп параметров
                    # Название города пары
                    if isinstance(self.target_user_info["city"], dict):
                        self.pair_user_info["hometown"] = self.target_user_info["city"]["title"]
                    else:
                        self.pair_user_info["hometown"] = self.target_user_info["city"]
                    # Возраст пары
                    a_date = datetime.strptime(
                        self.target_user_info["bdate"], "%d.%m.%Y").date()
                    b_date = date.today()
                    age = calculate_years(a_date, b_date)
                    self.pair_user_info["age"] = age
                    # Пол пары
                    self.pair_user_info["sex"] = 0
                    if self.target_user_info["sex"] == 1:
                        self.pair_user_info["sex"] = 2
                    elif self.target_user_info["sex"] == 2:
                        self.pair_user_info["sex"] = 1

                    add_fields = {
                        "hometown": self.pair_user_info["hometown"],
                        "age_from": self.pair_user_info["age"],
                        "age_to": self.pair_user_info["age"],
                        "sex": self.pair_user_info["sex"],
                        "status": 6,
                    }
                    self.pair_user_id = select_pair(
                        self.user_vk_session, add_fields, shown_user_ids_list)
                    self.db.set_result_vk_user_id(
                        self.selection_id, self.pair_user_id)
                    self.processing_selection()
                else:
                    self.complete_selection()
