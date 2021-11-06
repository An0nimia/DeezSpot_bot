#!/usr/bin/python3

from datetime import datetime

from configs.bot_settings import root_ids, warning_for_banning

from configs.customs import (
	bot_settings_config, banning_msg1, banning_msg2,
	version, bot_name, creator,
	forum, active_since,
	last_reset, date_start
)

from helpers.db_help import (
	select_users_settings, write_users_settings,
	update_users_settings, write_banned,
	select_banned, select_all_banned,
	select_all_downloads, select_all_users
)

def users_set_cache(chat_id, users_data):
	user_exist = True

	if not chat_id in users_data:
		match = select_users_settings(chat_id)

		if not match:
			user_exist = False
			quality = bot_settings_config[0][2]
			zips = bot_settings_config[1][2]
			tracks = bot_settings_config[2][2]
			lang = bot_settings_config[3][2]
			search_method = bot_settings_config[4][2]

			write_users_settings(
				chat_id, quality,
				zips, tracks,
				lang, search_method
			)
		else:
			quality = match[0]
			zips = bool(match[1])
			tracks = bool(match[2])
			lang = match[3]
			search_method = match[4]

		users_data[chat_id] = {
			"quality": quality,
			"zips": zips,
			"tracks": tracks,
			"lang": lang,
			"search_method": search_method,
			"last_message": None,
			"messages_sent": 0,
			"times": 0,
			"c_downloads": {}
		}

	return user_exist

def user_setting_save_db(chat_id, user_data):
	quality = user_data['quality']
	zips = user_data['zips']
	tracks = user_data['tracks']
	lang = user_data['lang']
	search_method = user_data['search_method']

	update_users_settings(
		chat_id, quality,
		zips, tracks,
		lang, search_method
	)

def check_flood(date, user_data, chat_id):
	if chat_id in root_ids:
		return

	last_message = user_data['last_message']

	if not last_message:
		user_data['last_message'] = date
		return

	user_data['last_message'] = date
	time_passed = (date - last_message).seconds

	if time_passed < 4:
		user_data['messages_sent'] += 1
	else:
		user_data['messages_sent'] = 0

	messages_sent = user_data['messages_sent']

	if messages_sent == 3:
		user_data['messages_sent'] = 0
		user_data['times'] += 1
		return banning_msg1, 0

	times = user_data['times']

	if times == warning_for_banning:
		write_banned(chat_id)
		return banning_msg2, 1

def kill_threads(users_data):
	for c_user_data in users_data.values():
		for c_thread in c_user_data['c_downloads'].values():
			c_thread['thread'].kill()

		c_user_data['c_downloads'].clear()

def is_banned(chat_id):
	match = select_banned(chat_id)

	if match:
		return True

	return False

def get_banned_ids():
	match = select_all_banned()

	chat_ids = [
		chat_id[0]
		for chat_id in match
	]

	chat_ids = set(chat_ids)
	return chat_ids

def get_tot_downloads():
	match = select_all_downloads()
	tot = len(match)
	return tot

def get_tot_users():
	match = select_all_users()
	tot = len(match)
	return tot

def get_info():
	tot_users = get_tot_users()
	tot_downloads = get_tot_downloads()
	time_now = datetime.now()
	days_no_accidents = (time_now - date_start).days

	info_msg = (
		f"🔺 Version: {version}\
		\n📅 Active since: {active_since}\
		\n🔻 Name: {bot_name}\
		\n✒️ Creator: {creator}\
		\n📅 Last reset: {last_reset}\
		\n📣 Forum: {forum}\
		\n👥 Users: {tot_users}\
		\n⬇️ Total downloads: {tot_downloads}\
		\n📅 DAYS WITHOUT ACCIDENTS⚠️: {days_no_accidents}"
	)

	return info_msg