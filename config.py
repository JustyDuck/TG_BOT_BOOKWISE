from aiogram import Dispatcher, F
import configparser
from typing import List
from User import command


class Settings:
    def __init__(self, config_file: str):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    @property
    def bot_token(self) -> str:
        return self.config['bot']['bot_token']

    @property
    def admin_user_ids(self) -> str:
        return self.config['bot']['admin_user_ids']

    def get_admin_user_ids(self) -> List[int]:
        return [int(admin_id.strip()) for admin_id in

                self.admin_user_ids.split(',') if admin_id.strip()]


config = Settings('config.ini')


def register_routers(dp: Dispatcher):
    command.router.message.filter(F.chat.type == "private")
    dp.include_router(command.router)