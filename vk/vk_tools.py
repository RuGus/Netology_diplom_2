"""Инструменты для работы с VK."""

from ast import While
from random import randrange
from time import sleep
from sqlalchemy import true

from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll


def create_group_session(group_id, token, api_version="5.131"):
    """Создание сессии ВК сообщества.

    Args:
        group_id (int): ИД сообщества.
        token (str): Токен сообщества.
        api_version (str, optional): Версия АПИ. По умолчанию "5.131".

    Returns:
        vk_session, longpoll: Сессии сообщества
    """
    vk_session = VkApi(token=token, api_version=api_version)
    vk_session._auth_token()
    longpoll = VkBotLongPoll(vk_session, group_id)
    return vk_session, longpoll


def create_user_session(user_token, api_version="5.131"):
    """Создание сессии пользователя ВК.

    Args:
        user_token (str): Токен пользователя.
        api_version (str, optional): Версия АПИ. По умолчанию "5.131".

    Returns:
        vk_user_session: Сессия пользователя.
    """
    vk_user_session = VkApi(token=user_token, api_version=api_version)
    return vk_user_session


def write_message_to_vk_user(vk_session, user_id, message, attachment=""):
    """Отправка сообщения пользователю от сообщества.

    Args:
        vk_session (object): Сессия пользователя ВК.
        user_id (int): ИД пользователя.
        message (str): Сообщение пользователю.
        attachment (str): Перечень вложений через ",".
    """
    vk_session.method('messages.send', {
        'user_id': user_id,
        'message': message,
        'random_id': randrange(10 ** 7),
        'attachment': attachment, })


def get_vk_user_info(vk_session, user_id, fields=None):
    """Получение информации по пользователю.

    Args:
        vk_session (object): Сессия пользователя ВК.
        user_id (int): ИД пользователя.
        fields (list, optional): Список доп. полей.

    Returns:
        dict: Информация о пользователе из ВК.
    """
    user_info = vk_session.method(
        'users.get', {'user_ids': user_id, 'fields': fields, })[0]
    return user_info


def get_vk_user_profile_photos(vk_session, user_id):
    """Получение фотографий из профиля пользователя.

    Args:
        vk_session (object): Сессия пользователя ВК.
        user_id (int): ИД пользователя.

    Returns:
        dict: Словарь с фотографиями.
    """
    user_profile_photos = vk_session.method('photos.get', {
        'owner_id': user_id,
        'album_id': "profile",
        "extended": 1,
        "rev": 1,
    })
    return user_profile_photos


def search_vk_user(vk_session, target):
    """Поиск пользователя.

    Args:
        vk_session (object): Сессия пользователя ВК.
        target (str): Цель поиска.

    Returns:
        int: Идентификатор пользователя.
    """
    target_user_id = None
    try:
        user_info = get_vk_user_info(vk_session, target)
        target_user_id = user_info["id"]
    except:
        request_dict = {'q': target, "count": 1}
        search_result = vk_session.method('users.search', request_dict)
        if not search_result.get("count"):
            target_user_id = search_result["items"][0]["id"]
    return target_user_id


def select_pair(vk_session, add_fields, shown_user_ids_list):
    """Подбор пары.

    Args:
        vk_session (object): Сессия пользователя ВК.
        add_fields (dict): Поля поиска.
        shown_user_ids_list (list): Список ИД ранее показанных пользователей.

    Returns:
        int: Идентификатор подобранного пользователя.
    """
    offset = 0
    pair_user_id = -1
    request_dict = {"q": ""}
    request_dict.update(add_fields)
    search_result = vk_session.method('users.search', request_dict)
    if search_result.get("count"):
        search_result_items = search_result["items"]
        for item in search_result_items:
            if item["id"] not in shown_user_ids_list:
                pair_user_id = item["id"]
                break
    return pair_user_id


def get_best_size_url(sizes):
    """Получение фотографии с лучшим размером.

    Args:
        sizes (dict): Словарь с размерами фото из ВК.

    Returns:
        str: Ссылка на фото.
    """
    best_size_photo_url = None
    sizes_dict = {}
    for size in sizes:
        sizes_dict[size["type"]] = size["url"]
    if sizes_dict:
        best_size_photo_url = sizes_dict[max(sizes_dict.keys())]
    return best_size_photo_url


def get_min_pop_photo_id(best_photo_dict):
    """Получение наименее популярной фотографии.

    Args:
        best_photo_dict (dict): Словарь с фотографиями.

    Returns:
        int: Идентификатор фото.
    """
    min_pop_photo_id = None
    for photo_id, photo_params in best_photo_dict.items():
        if not min_pop_photo_id:
            min_pop_photo_id = photo_id
        else:
            min_photo = best_photo_dict[min_pop_photo_id]
            min_likes_count = min_photo["likes_count"]
            min_comments_count = min_photo["comments_count"]
            current_photo = photo_params
            current_likes_count = current_photo["likes_count"]
            current_comments_count = current_photo["comments_count"]
            if current_likes_count < min_likes_count:
                min_pop_photo_id = photo_id
            elif current_likes_count == min_likes_count:
                if current_comments_count < min_comments_count:
                    min_pop_photo_id = photo_id
    return min_pop_photo_id


def get_3_pop_photo(user_photo_items):
    """Получение 3 самых популярных фотографий.

    Args:
        user_photo_items (dict): Словарь с фотографиями из ВК.

    Returns:
        dict: Словарь фото.
    """
    pop_photo_url_list = []
    best_photo_dict = {}
    for item in user_photo_items:
        likes_count = item["likes"]["count"]
        comments_count = item["comments"]["count"]
        current_photo_id = item["id"]
        if len(best_photo_dict) < 3:
            best_photo_dict[current_photo_id] = {
                "likes_count": likes_count,
                "comments_count": comments_count,
                "url": get_best_size_url(item["sizes"]),
            }
        else:
            min_pop_photo_id = get_min_pop_photo_id(best_photo_dict)
            min_photo = best_photo_dict[min_pop_photo_id]
            min_likes_count = min_photo["likes_count"]
            min_comments_count = min_photo["comments_count"]
            current_photo_id = item["id"]
            current_likes_count = item["likes"]["count"]
            current_comments_count = item["comments"]["count"]
            if current_likes_count < min_likes_count:
                best_photo_dict.pop(min_pop_photo_id)
                best_photo_dict[current_photo_id] = {
                    "likes_count": likes_count,
                    "comments_count": comments_count,
                    "url": get_best_size_url(item["sizes"]),
                }
            elif current_likes_count == min_likes_count:
                if current_comments_count < min_comments_count:
                    best_photo_dict.pop(min_pop_photo_id)
                    best_photo_dict[current_photo_id] = {
                        "likes_count": likes_count,
                        "comments_count": comments_count,
                        "url": get_best_size_url(item["sizes"]),
                    }
    return best_photo_dict


def get_vk_user_3_foto_url(vk_session, user_id):
    """Получение url 3 самых популярных фотографий из профиля пользователя.

    Args:
        vk_session (object): Сессия пользователя в ВК.
        user_id (int): ИД пользователя.

    Returns:
        list: Список ссылок на фото.
    """
    user_photo = get_vk_user_profile_photos(vk_session, user_id)
    photo_links = []
    if 0 < user_photo["count"] <= 3:
        for item in user_photo["items"]:
            photo_links.append(get_best_size_url(item["sizes"]))
    elif user_photo["count"] > 3:
        photo_links = get_3_pop_photo(user_photo["items"])
    return photo_links


def get_vk_user_3_foto_attachment_value(vk_session, user_id):
    """Получение значения attachment с 3 самыми популярными фотографиями
    из профиля пользователя.

    Args:
        vk_session (object): Сессия пользователя в ВК.
        user_id (int): ИД пользователя.

    Returns:
        str: Значение attachment.
    """
    user_photo = get_vk_user_profile_photos(vk_session, user_id)
    attachment = ""
    if 0 < user_photo["count"] <= 3:
        for item in user_photo["items"]:
            attachment += f'photo{user_id}_{item["id"]},'
    elif user_photo["count"] > 3:
        best_photo_dict = get_3_pop_photo(user_photo["items"])
        for key in best_photo_dict:
            attachment += f'photo{user_id}_{key},'
    print(attachment)
    return attachment


def get_vk_user_link(user_id):
    """Получение ссылки на пользователя ВК.

    Args:
        user_id (int): Идентификатор пользователя ВК.

    Returns:
        str: Ссылка на пользователя.
    """
    link = "https://vk.com/"
    if user_id:
        link += f"id{user_id}"
    return link
