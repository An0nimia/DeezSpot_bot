#!/usr/bin/python3

from pyrogram import Client
from acrcloud import ACRcloud
from telegram.ext import Updater
from configparser import ConfigParser
from utils.utils import check_config_file
from deezloader.deezloader import DeeLogin
from deezloader.spotloader import SpoLogin
from .bot_settings import settings_file, user_session

config = ConfigParser()
config.read(settings_file)
check_config_file(config)

class SetConfigs:
	queues_started, queues_finished = 0, 0

	__arl_token = config['deez_login']['arl']
	__email_dee = config['deez_login']['mail']
	__pwd_dee = config['deez_login']['pwd']

	__email_spo = config['spot_login']['mail']
	__pwd_spo = config['spot_login']['pwd']

	__bot_token = config['telegram']['bot_token']

	__acrcloud_key = config['acrcloud']['key']
	__acrcloud_secret = config['acrcloud']['secret']
	__acrcloud_host = config['acrcloud']['host']

	__api_id = config['pyrogram']['api_id']
	__api_hash = config['pyrogram']['api_hash']

	__acrcloud_config = {
		"key": __acrcloud_key,
		"secret": __acrcloud_secret,
		"host": __acrcloud_host
	}

	@classmethod
	def __init__(cls, mode_bot):
		if mode_bot in [3, 4]:
			cls.create_zips = False
		else:
			cls.create_zips = True

		cls.tg_bot_api = Updater(token = cls.__bot_token)
		cls.tg_bot_id = cls.tg_bot_api.bot.name

		cls.deez_api = DeeLogin(
			arl = cls.__arl_token,
			email = cls.__email_dee,
			password = cls.__pwd_dee
		)

		cls.spot_api = SpoLogin(cls.__email_spo, cls.__pwd_spo)

		cls.acrcloud_api = ACRcloud(cls.__acrcloud_config)
		cls.tg_user_api = Client(user_session, config_file = settings_file)
		cls.tg_user_api.start()