#!/usr/bin/python3

from pyrogram import Client
from deezloader import Login
from acrcloud import ACRcloud
from telegram.ext import Updater
from configparser import ConfigParser
from utils.utils import check_config_file
from .bot_settings import settings_file, user_session

config = ConfigParser()
config.read(settings_file)
check_config_file(config)

__arl_token = config['deez_login']['token']
__email = config['deez_login']['mail']
__password = config['deez_login']['password']
__bot_token = config['telegram']['bot_token']
__acrcloud_key = config['acrcloud']['key']
__acrcloud_secret = config['acrcloud']['secret']
__acrcloud_host = config['acrcloud']['host']
api_id = config['pyrogram']['api_id']
api_hash = config['pyrogram']['api_hash']

__acrcloud_config = {
	"key": __acrcloud_key,
	"secret": __acrcloud_secret,
	"host": __acrcloud_host
}

tg_bot_api = Updater(token = __bot_token)
tg_bot_id = tg_bot_api.bot.name

deez_api = Login(
	arl = __arl_token,
	email = __email,
	password = __password
)

acrcloud_api = ACRcloud(__acrcloud_config)
tg_user_api = Client(user_session, config_file = settings_file)