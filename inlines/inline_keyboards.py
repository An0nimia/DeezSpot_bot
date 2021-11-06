#!/usr/bin/python3

from deezloader.libutils.utils import get_ids
from helpers.db_help import select_all_banned
from deezloader.deezloader.deezer_settings import qualities as dee_qualities
from deezloader.spotloader.spotify_settings import qualities as spo_qualities

from telegram import (
	InlineKeyboardMarkup, InlineKeyboardButton
)

from configs.customs import (
	commands_queries, artist_commands_queries,
	bot_settings_config, inline_textes, search_methods,
	donation, source_code_bot, source_code_lib
)

__back_keyboard = [
	[
		InlineKeyboardButton(
			inline_textes['back']['text'],
			callback_data = "/back_home"
		)
	]
]

__commands_queries = list(
	commands_queries.values()
)

__l_commands_queries = len(__commands_queries)

def create_keyboad_search(to_search):
	keyboad_search = [
		[
			InlineKeyboardButton(
				command['text'],
				switch_inline_query_current_chat = command['query'] % to_search
			)
			for command in __commands_queries[
				line:line + 2
			]
		]
		for line in range(0, __l_commands_queries, 2)
	]

	search_keyboard = InlineKeyboardMarkup(keyboad_search)
	return search_keyboard

__artist_commands_queries = list(
	artist_commands_queries.values()
)

__l_artist_commands_queries = len(__artist_commands_queries)

def create_keyboard_artist(link):
	ids = get_ids(link)
	query = f"artist:{ids}"

	keyboad_artist = [
		[
			InlineKeyboardButton(
				command['text'],
				switch_inline_query_current_chat = command['query'] % query
			)
			for command in __artist_commands_queries[
				line:line + 2
			]
		]
		for line in range(0, __l_artist_commands_queries, 2)
	]

	artist_keyboard = InlineKeyboardMarkup(keyboad_artist)
	return artist_keyboard

__l_bot_settings = len(bot_settings_config)
__dict_seach_methods = dict(search_methods)

def create_keyboard_settings(datas):
	datas = list(
		datas.values()
	)

	keyboard_settings = []

	for line in range(0, __l_bot_settings, 2):
		c_array = []

		for line2 in range(line, line + 2):
			if line2 >= __l_bot_settings:
				continue

			c_data = bot_settings_config[line2]
			msg = c_data[0]
			cmd = c_data[1]
			data = datas[line2]

			if type(data) is bool:
				if data:
					msg += ": ✅"
				else:
					msg += ": 🚫"
			else:
				if cmd == "search_method":
					data = __dict_seach_methods[data]

				msg += f": {data}"

			c_keyboard = InlineKeyboardButton(
				msg,
				callback_data = f"/edit_setting_{cmd}"
			)

			c_array.append(c_keyboard)

		keyboard_settings.append(c_array)

	settings_keyboard = InlineKeyboardMarkup(keyboard_settings)
	return settings_keyboard

__qualities_dee = list(
	dee_qualities.keys()
)

__qualities_spo = list(
	spo_qualities.keys()
)

__l_qualities = len(__qualities_dee)

def create_keyboard_qualities():
	keyboad_qualities = [
		[
			InlineKeyboardButton(
				f"{quality_dee}/{quality_spo}",
				callback_data = f"/edit_setting_quality_{quality_dee}"
			)
			for quality_dee, quality_spo in zip(
				__qualities_dee[
					line:line + 2
				],
				__qualities_spo[
					line:line + 2
				]
			)
		]
		for line in range(0, __l_qualities, 2)
	]

	keyboad_qualities += __back_keyboard
	qualities_keyboard = InlineKeyboardMarkup(keyboad_qualities)

	return qualities_keyboard

__l_search_methods = len(search_methods)

def create_keyboard_search_method():
	keyboad_search_methods = [
		[
			InlineKeyboardButton(
				search_method[1],
				callback_data = f"/edit_setting_search_method_{search_method[0]}"
			)
			for search_method in search_methods[
				line:line + 2
			]
		]
		for line in range(0, __l_search_methods, 2)
	]

	keyboad_search_methods += __back_keyboard
	qualities_keyboard = InlineKeyboardMarkup(keyboad_search_methods)
	return qualities_keyboard

def create_shazamed_keyboard(track_link, album_link, artist_link):
	keyboard_shazamed = [
		[
			InlineKeyboardButton(
				inline_textes['download_track']['text'],
				callback_data = f"/down:{track_link}"
			)
		],
		[
			InlineKeyboardButton(
				inline_textes['download_album']['text'],
				callback_data = f"/down:{album_link}"
			)
		],
		[
			InlineKeyboardButton(
				inline_textes['download_artist']['text'],
				callback_data = f"/down:{artist_link}"
			)
		]
	]

	shazamed_keyboard = InlineKeyboardMarkup(keyboard_shazamed)
	return shazamed_keyboard

def create_banned_keyboard():
	users_ids = select_all_banned()
	l_users_ids = len(users_ids)

	keyboard_banned = [
		[
			InlineKeyboardButton(
				user_id[0],
				callback_data = f"/unban_{user_id[0]}"
			)
			for user_id in users_ids[
				line:line + 2
			]
		]
		for line in range(0, l_users_ids, 2)
	]

	banned_keyboard = InlineKeyboardMarkup(keyboard_banned)
	return banned_keyboard

def create_c_dws_user_keyboard(dws: dict):
	keyboad_dws = [
		InlineKeyboardMarkup(
			[
				[
					InlineKeyboardButton(
						"Press here to delete this download 🚫",
						callback_data = f"/kill_dw_{key}"
					)
				]
			]
		) for key in dws.keys()
	]

	return keyboad_dws

def create_info_keyboard():
	keyboard_info = [
		[
			InlineKeyboardButton(
				"💸 PAYPAL DONATION HERE 🥺",
				url = donation
			)
		],
		[
			InlineKeyboardButton(
				"👨‍💻 BOT Source code HERE",
				url = source_code_bot

			)
		],
		[
			InlineKeyboardButton(
				"👨‍💻 LIB Source code HERE",
				url = source_code_lib

			)
		]
	]

	info_keyboard = InlineKeyboardMarkup(keyboard_info)

	return info_keyboard