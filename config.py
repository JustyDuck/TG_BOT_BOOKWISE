from aiogram import Dispatcher, F
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from User import comand


class Settings(BaseSettings):
    bot_token: SecretStr
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


config = Settings()


def register_routers(dp: Dispatcher):
    comand.router.message.filter(F.chat.type == "private")
    dp.include_router(comand.router)
