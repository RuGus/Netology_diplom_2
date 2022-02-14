import configparser

from vk_api.bot_longpoll import VkBotEventType

from selection.selection import Selection
from vk.vk_tools import create_group_session

config = configparser.ConfigParser()
config.read("config.ini")

db_name = config["VK"]["db_name"]
fields = config["VK"]["fields"]

# Перед запуском заполни config.ini
token = config["VK"]["token"]
group_id = int(config["VK"]["group_id"])

#
if __name__ == '__main__':
    #
    vk, longpoll = create_group_session(group_id, token)
    print("---Bot started!---")
    while True:
        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                message = event.obj["message"]
                message_text = message["text"]
                user_id = message["from_id"]
                user_selection = Selection(db_name, vk, user_id, fields)
                user_selection.processing_selection(message_text)
                del(user_selection)
