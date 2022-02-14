"""Инструменты для работы с базой данных."""

import sqlite3 as sql
import uuid
from datetime import datetime


class SelectionDB:
    """Класс для работы с БД подбора.
    
    Args:
        db_filename (str): Путь до БД.
    """

    def __init__(self, db_filename):
        self.connection = sql.connect(db_filename)
        # Создаем структуру таблицы для хранения информации о подборах
        with self.connection:
            cursor = self.connection.cursor()
            sql_query = """CREATE TABLE IF NOT EXISTS selections(
                    vk_user_id INT,
                    vk_user_token TEXT,
                    vk_target_id INT,
                    vk_target_info TEXT,
                    selection_id TEXT,
                    stage_id INT,                   
                    start_date TEXT,
                    upadte_date TEXT,
                    end_date TEXT,
                    is_closed INT,
                    result_vk_user_id INT);
            """
            cursor.execute(sql_query)
            self.connection.commit()

    def create_selection(self, user_id):
        """Создание нового подбора"""
        with self.connection:
            cursor = self.connection.cursor()
            selection_id = uuid.uuid4()
            start_date = datetime.now()
            upadte_date = start_date
            stage_id = 1
            sql_query = f"""INSERT INTO selections(vk_user_id, selection_id, stage_id, start_date, upadte_date, is_closed) 
                    VALUES('{user_id}', '{selection_id}', '{stage_id}', '{start_date}', '{upadte_date}', 0);
            """
            cursor.execute(sql_query)
            self.connection.commit()

        return selection_id

    def get_selection(self, selection_id):
        """Получение существующего подбора."""
        with self.connection:
            cursor = self.connection.cursor()
            sql_query = f"""
            SELECT * FROM selections WHERE selection_id = '{selection_id}';
            """
            cursor.execute(sql_query)
            selection_info = cursor.fetchone()
        return selection_info

    def get_stage_id(self, selection_id):
        """Получение шага подбора."""
        with self.connection:
            cursor = self.connection.cursor()
            sql_query = f"""
            SELECT stage_id FROM selections WHERE selection_id = '{selection_id}';
            """
            cursor.execute(sql_query)
            stage_id = cursor.fetchone()[0]
        return stage_id

    def get_vk_target_info(self, selection_id):
        """Получение информации о целевом пользователе."""
        with self.connection:
            cursor = self.connection.cursor()
            sql_query = f"""
            SELECT vk_target_info FROM selections WHERE selection_id = '{selection_id}';
            """
            cursor.execute(sql_query)
            stage_id = cursor.fetchone()[0]
        return stage_id

    def get_active_selection_id(self, user_id):
        """Получение активного подбора."""
        with self.connection:
            cursor = self.connection.cursor()
            sql_query = f"""SELECT selection_id FROM selections WHERE vk_user_id = '{user_id}' and is_closed != 1;
            """
            cursor.execute(sql_query)
            selection_id = cursor.fetchone()[0]
        return selection_id

    def set_result_vk_user_id(self, selection_id, result_vk_user_id):
        """Запись подобранной пары."""
        upadte_date = datetime.now()
        with self.connection:
            cursor = self.connection.cursor()
            sql_query = f"""
            UPDATE selections SET result_vk_user_id = {result_vk_user_id}, upadte_date = '{upadte_date}' WHERE selection_id = '{selection_id}';
            """
            cursor.execute(sql_query)
            self.connection.commit()

    def set_vk_user_token(self, selection_id, vk_user_token):
        """Запись токена пользователя."""
        upadte_date = datetime.now()
        with self.connection:
            cursor = self.connection.cursor()
            sql_query = f"""
            UPDATE selections SET vk_user_token = '{vk_user_token}', upadte_date = '{upadte_date}' WHERE selection_id = '{selection_id}';
            """
            cursor.execute(sql_query)
            self.connection.commit()

    def set_target_user_id(self, selection_id, vk_target_id):
        """Запись ИД целевого пользователя."""
        upadte_date = datetime.now()
        with self.connection:
            cursor = self.connection.cursor()
            sql_query = f"""
            UPDATE selections SET vk_target_id = {vk_target_id}, upadte_date = '{upadte_date}' WHERE selection_id = '{selection_id}';
            """
            cursor.execute(sql_query)
            self.connection.commit()

    def set_target_user_info(self, selection_id, vk_target_info):
        """Запись ИД целевого пользователя."""
        upadte_date = datetime.now()
        with self.connection:
            cursor = self.connection.cursor()
            sql_query = f"""
            UPDATE selections SET vk_target_info = "{vk_target_info}", upadte_date = '{upadte_date}' WHERE selection_id = '{selection_id}';
            """
            cursor.execute(sql_query)
            self.connection.commit()

    def close_seletion(self, selection_id):
        """Закрытие подбора"""
        end_date = datetime.now()
        upadte_date = end_date
        with self.connection:
            cursor = self.connection.cursor()
            sql_query = f"""
            UPDATE selections SET is_closed = True, end_date = '{end_date}', upadte_date = '{upadte_date}' WHERE selection_id = '{selection_id}';
            """
            cursor.execute(sql_query)
            self.connection.commit()

    def next_stage(self, selection_id):
        """Переход к следующему шагу подбора."""
        stage_id = self.get_stage_id(selection_id)
        stage_id += 1
        upadte_date = datetime.now()
        with self.connection:
            cursor = self.connection.cursor()
            sql_query = f"""
            UPDATE selections SET stage_id = {stage_id}, upadte_date = '{upadte_date}' WHERE selection_id = '{selection_id}';
            """
            cursor.execute(sql_query)
            self.connection.commit()

    def active_selection_exists(self, user_id):
        """Проверка существования активного подбора."""
        result = False
        with self.connection:
            cursor = self.connection.cursor()
            sql_query = f"""SELECT * FROM selections WHERE vk_user_id = '{user_id}' and is_closed != 1;
            """
            cursor.execute(sql_query)
            active_selections = cursor.fetchall()
        if active_selections:
            result = True
        return result

    def get_shown_user_ids(self, user_id, vk_target_id):
        """Получение списка показанных ранее результатов подбора."""
        with self.connection:
            cursor = self.connection.cursor()
            sql_query = f"""SELECT result_vk_user_id FROM selections WHERE vk_user_id = '{user_id}' and vk_target_id = '{vk_target_id}' and is_closed = 1;
            """
            cursor.execute(sql_query)
            ids_list = []
            for item in cursor.fetchall():
                ids_list.append(item[0])
        return ids_list
