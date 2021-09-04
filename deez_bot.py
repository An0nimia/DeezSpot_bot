#!/usr/bin/python3

from time import sleep
from telegram import ParseMode
from logging import basicConfig, WARN
from pyrogram import idle as tg_user_start
from telegram import MessageEntity, Update
from utils.special_thread import magicThread
from utils.converter_bytes import convert_bytes_to
from helpers.download_help import DOWNLOAD_HELP, DW
from telegram.error import BadRequest, Unauthorized
from configs.set_configs import tg_bot_api, tg_user_api
from utils.utils_data import create_response_article, shazam_song

from helpers.db_help import (
	delete_banned, select_all_users, write_banned
)

from configs.customs import (
	not_found_query_gif, shazam_audio_query,
	shazam_function_msg, max_download_user_msg,
	help_msg, help_photo, feedback_text, what_can_I_do,
	donate_text, reasons_text
)

from configs.bot_settings import (
	download_dir_max_size, time_sleep,
	output_shazam, recorded_file_max_size,
	root_ids, bunker_channel,
	owl_channel, max_download_user, log_errors
)

from utils.utils_users_bot import (
	user_setting_save_db, users_set_cache,
	check_flood, get_banned_ids,
	get_info, kill_threads
)

from utils.utils import (
	is_supported_link, get_download_dir_size,
	check_config_bot, clear_download_dir,
	clear_recorded_dir, show_menu, create_tmux
)

from telegram.ext import (
	CommandHandler, MessageHandler, Filters,
	InlineQueryHandler, CallbackQueryHandler
)

from inlines.inline_keyboards import (
	create_keyboad_search, create_keyboard_settings,
	create_keyboard_qualities, create_shazamed_keyboard,
	create_keyboard_search_method, create_banned_keyboard,
	create_c_dws_user_keyboard, create_donation_keyboard
)

check_config_bot()

mode_bot = show_menu()
bot_chat_id = tg_bot_api.bot.id
bot = tg_bot_api.bot
banned_ids = get_banned_ids()
queues_started = [0]
queues_finished = [0]
tg_user_api.start()
users_data = {}
roots_data = {}

dw_helper = DOWNLOAD_HELP(
	queues_started, queues_finished, tg_user_api
)

basicConfig(
	format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
	level = WARN,
	filename = log_errors
)

to_ban = Filters.user(banned_ids)

def ban_chat_id(chat_id):
	write_banned(chat_id)
	to_ban.add_chat_ids(chat_id)

def help_check_user(chat_id, date = None):
	if (mode_bot == 1) and (not chat_id in root_ids):
		bot.send_message(
			chat_id = chat_id,
			text = "BOT IS UNDER MAINTENANCE"
		)

		to_ban.add_chat_ids(chat_id)

		return

	users_set_cache(chat_id, users_data)

	if date:
		user_data = users_data[chat_id]
		result = check_flood(date, user_data, chat_id)

		if result:
			msg, mode = result

			bot.send_message(
				chat_id = chat_id,
				text = msg
			)

			if mode == 1:
				to_ban.add_chat_ids(chat_id)
				del users_data[chat_id]

def help_download(link, chat_id):
	if chat_id in to_ban.user_ids:
		return

	if not is_supported_link(link):
		text = "THIS LINK IS NOT SUPPORTED :("

		bot.send_message(
			chat_id = chat_id,
			text = text
		)

		return

	c_user_data = users_data[chat_id]
	c_downloads = c_user_data['c_downloads']

	if len(c_downloads) == max_download_user:
		bot.send_message(
			chat_id = chat_id,
			text = max_download_user_msg
		)

		return

	to_hash = f"{link}{c_user_data['quality']}"
	hash_link = hash(to_hash)
	new_ins = DW(dw_helper, chat_id, c_user_data, hash_link)

	t = magicThread(
		target = new_ins.download,
		args = (link, )
	)

	c_downloads[hash_link] = {
		"link": link,
		"thread": t,
		"dw": new_ins
	}

	t.start()

def handle_inline_queries(update: Update, context):
	inline_query = update.inline_query
	chat_id = inline_query.from_user.id

	if chat_id in to_ban.user_ids:
		return

	help_check_user(chat_id)
	query_id = inline_query.id
	query = inline_query.query
	c_user_data = users_data[chat_id]
	results = create_response_article(query, c_user_data)

	try:
		bot.answer_inline_query(
			inline_query_id = query_id,
			results = results
		)
	except BadRequest:
		pass

def handle_callback_queries(update: Update, context):
	callback_query = update.callback_query
	chat_id = callback_query.from_user.id

	if chat_id in to_ban.user_ids:
		return

	msg = callback_query.message
	date = msg.date
	help_check_user(chat_id, date)
	msg_id = msg.message_id
	query_id = callback_query.id
	data = callback_query.data
	c_user_data = users_data[chat_id]
	text = "Your settings"
	answer = "DONE"
	mode = 0

	if data == "/edit_setting_quality":
		text = "Qualities"
		c_keyboard = create_keyboard_qualities()

	elif data == "/edit_setting_search_method":
		text = "Search methods"
		c_keyboard = create_keyboard_search_method()

	elif data == "/edit_setting_zips":
		zips = c_user_data['zips']

		if zips:
			c_user_data['zips'] = False
		else:
			c_user_data['zips'] = True

		c_keyboard = create_keyboard_settings(c_user_data)
		user_setting_save_db(chat_id, c_user_data)

	elif data == "/edit_setting_tracks":
		tracks = c_user_data['tracks']

		if tracks:
			c_user_data['tracks'] = False
		else:
			c_user_data['tracks'] = True

		c_keyboard = create_keyboard_settings(c_user_data)
		user_setting_save_db(chat_id, c_user_data)

	elif data.startswith("/unban_"):
		c_data = data.replace("/unban_", "")
		c_chat_id = int(c_data)
		text = "BANNED USERS"
		delete_banned(c_chat_id)
		to_ban.remove_chat_ids(c_chat_id)
		c_keyboard = create_banned_keyboard()
		answer = f"UNBANNED {c_chat_id}"

	elif data.startswith("/edit_setting_quality_"):
		c_data = data.replace("/edit_setting_quality_", "")
		c_user_data['quality'] = c_data
		c_keyboard = create_keyboard_settings(c_user_data)
		user_setting_save_db(chat_id, c_user_data)

	elif data.startswith("/edit_setting_search_method_"):
		c_data = data.replace("/edit_setting_search_method_", "")
		c_user_data['search_method'] = c_data
		c_keyboard = create_keyboard_settings(c_user_data)
		user_setting_save_db(chat_id, c_user_data)

	elif data.startswith("/down:"):
		mode = "down:"
		answer = "GOOD CHOICE :)"
		c_data = data.replace("/down:", "")

	elif data == "/back_home":
		c_keyboard = create_keyboard_settings(c_user_data)

	elif data.startswith("/kill_dw_"):
		mode = "kill"
		answer = "DOWNLOAD DELETED :)"
		c_hash = data.replace("/kill_dw_", "")
		i_c_hash = int(c_hash)
		c_dws = c_user_data['c_downloads']

		if not i_c_hash in c_dws:
			answer = "THIS IS AN OLD DOWNLOAD :)"
		else:
			t = c_dws[i_c_hash]['thread']
			t.kill()
			del c_dws[i_c_hash]

	else:
		mode = 1
		answer = "Sorry isn't avalaible :("

	if mode == 0:
		bot.edit_message_text(
			chat_id = chat_id,
			message_id = msg_id,
			text = text,
			reply_markup = c_keyboard
		)

	bot.answer_callback_query(
		callback_query_id = query_id,
		text = answer
	)

	if mode == "kill":
		bot.delete_message(
			chat_id = chat_id,
			message_id = msg_id
		)

	elif mode == "down:":
		help_download(c_data, chat_id)

def audio_handler(update: Update, context):
	msg = update.message
	chat_id = msg.from_user.id
	msg_id = msg.message_id
	date = msg.date
	help_check_user(chat_id, date)
	audio = msg.audio

	if not audio:
		audio = msg.voice

	audio_size = convert_bytes_to(audio.file_size, "mb")

	if audio_size > recorded_file_max_size:
		bot.send_message(
			chat_id = chat_id,
			text = f"PLEASE SEND A FILE AUDIO/RECORD LOWER THAN {recorded_file_max_size} MB =)"
		)

		return

	file_id = audio.file_id
	c_file = bot.get_file(file_id)

	try:
		queues_started[0] += 1

		out = c_file.download(
			custom_path = f"{output_shazam}{file_id}"
		)

		resp = shazam_song(out)
	finally:
		queues_finished[0] += 1

	if not resp:
		bot.send_message(
			chat_id = chat_id,
			text = "I CANNOT SHAZAM THE SONG RETRY :("
		)

		return

	artist, genre,\
		album, label,\
			track_link, album_link,\
				artist_link, image_url,\
					release_date, title = resp

	if track_link:
		reply_markup = create_shazamed_keyboard(track_link, album_link, artist_link)
	else:
		reply_markup = None
		image_url = not_found_query_gif

	bot.send_photo(
		chat_id = chat_id,
		photo = image_url,
		reply_to_message_id = msg_id,
		reply_markup = reply_markup,
		caption = (
			shazam_audio_query
			% (
				artist,
				genre,
				album,
				label,
				release_date,
				title
			)
		)
	)

def start_command(update: Update, context):
	msg = update.message
	chat_id = msg.from_user.id
	date = msg.date
	help_check_user(chat_id, date)

	bot.send_message(
		chat_id = chat_id,
		text = "YOU JUST PRESSED START YOU WON A NICE DAY :)))",
		reply_markup = create_keyboad_search("")
	)

def settings_command(update: Update, context):
	msg = update.message
	chat_id = msg.from_user.id
	date = msg.date
	help_check_user(chat_id, date)
	c_user_data = users_data[chat_id]

	bot.send_message(
		chat_id = chat_id,
		text = "Your settings",
		reply_markup = create_keyboard_settings(c_user_data)
	)

def quality_command(update: Update, context):
	msg = update.message
	chat_id = msg.from_user.id
	date = msg.date
	help_check_user(chat_id, date)
	c_user_data = users_data[chat_id]

	bot.send_message(
		chat_id = chat_id,
		text = f"Current quality {c_user_data['quality']}",
		reply_markup = create_keyboard_qualities()
	)

def managing_banned_command(update: Update, context):
	msg = update.message
	chat_id = msg.from_user.id

	bot.send_message(
		chat_id = chat_id,
		text = "Banned users",
		reply_markup = create_banned_keyboard()
	)

def add_banned_command(update: Update, context):
	msg = update.message
	chat_id = msg.from_user.id

	if not chat_id in roots_data:
		roots_data[chat_id] = {
			"stage": None
		}

	bot.send_message(
		chat_id = chat_id,
		text = "Send me the user to ban"
	)

	roots_data[chat_id]['stage'] = "add_banned"

def send_global_msg_command(update: Update, context):
	msg = update.channel_post
	text = msg.text
	audio = msg.audio
	document = msg.document
	animation = msg.animation
	sticker = msg.sticker
	video = msg.video
	photo = msg.photo
	to_send = None
	method = None

	if text:
		to_send = text
		method = bot.send_message
	elif audio:
		to_send = audio.file_id
		method = bot.send_audio
	elif document:
		to_send = document.file_id
		method = bot.send_document
	elif animation:
		to_send = animation.file_id
		method = bot.send_animation
	elif sticker:
		to_send = sticker.file_id
		method = bot.send_sticker
	elif video:
		to_send = video.file_id
		method = bot.send_video
	elif photo:
		to_send = photo[0].file_id
		method = bot.send_photo

	all_user = select_all_users()
	
	for user_id in all_user:
		c_user_id = user_id[0]

		try:
			method(c_user_id, to_send)
		except (BadRequest, Unauthorized):
			pass

def shazam_command(update: Update, context):
	msg = update.message
	chat_id = msg.from_user.id
	date = msg.date
	help_check_user(chat_id, date)

	bot.send_message(
		chat_id = chat_id,
		text = shazam_function_msg
	)

def kill_dw_command(update: Update, context):
	msg = update.message
	chat_id = msg.from_user.id
	date = msg.date
	help_check_user(chat_id, date)
	c_user_data = users_data[chat_id]
	c_downloads = c_user_data['c_downloads']

	if not c_downloads:
		bot.send_message(
			chat_id = chat_id,
			text = "There aren't any download in progress"
		)

		return

	keybords_dws = create_c_dws_user_keyboard(c_downloads)

	for c_download, keyboard in zip(
		c_downloads.values(), keybords_dws
	):
		c_text = f"{c_download['link']} in {c_user_data['quality']}"

		bot.send_message(
			chat_id = chat_id,
			text = c_text,
			reply_markup = keyboard
		)

def info_command(update: Update, context):
	msg = update.message
	chat_id = msg.from_user.id
	date = msg.date
	help_check_user(chat_id, date)

	bot.send_message(
		chat_id = chat_id,
		text = get_info(),
		parse_mode = ParseMode.HTML,
		reply_markup = create_donation_keyboard()
	)

def reasons_command(update: Update, context):
	msg = update.message
	chat_id = msg.from_user.id
	date = msg.date
	help_check_user(chat_id, date)

	bot.send_message(
		chat_id = chat_id,
		text = reasons_text
	)

def help_command(update: Update, context):
	msg = update.message
	chat_id = msg.from_user.id
	date = msg.date
	help_check_user(chat_id, date)

	bot.send_photo(
		chat_id = chat_id,
		photo = help_photo,
		caption = help_msg
	)

	bot.send_message(
		chat_id = chat_id,
		text = what_can_I_do
	)

def feedback_command(update: Update, context):
	msg = update.message
	chat_id = msg.from_user.id
	date = msg.date
	help_check_user(chat_id, date)

	bot.send_message(
		chat_id = chat_id,
		text = feedback_text
	)

def donate_command(update: Update, context):
	msg = update.message
	chat_id = msg.from_user.id
	date = msg.date
	help_check_user(chat_id, date)

	bot.send_message(
		chat_id = chat_id,
		text = donate_text,
		reply_markup = create_donation_keyboard()
	)

def msgs_handler(update: Update, context):
	msg = update.message
	chat_id = msg.from_user.id
	text = msg.text

	if chat_id in roots_data:
		if roots_data[chat_id]['stage'] == "add_banned":
			ban_chat_id(text)
			roots_data[chat_id]['stage'] = None

			bot.send_message(
				chat_id = chat_id,
				text = f"User {text} has been blocked"
			)

			return

	date = msg.date
	help_check_user(chat_id, date)

	bot.send_message(
		chat_id = chat_id,
		text = text,
		reply_markup = create_keyboad_search(text)
	)

def controls_links(update: Update, context):
	msg = update.message
	chat_id = msg.from_user.id
	date = msg.date
	help_check_user(chat_id, date)
	entity_link = msg.entities[0]
	link = msg.parse_entity(entity_link)
	help_download(link, chat_id)

dispatcher = tg_bot_api.dispatcher

start_handler = CommandHandler(
	"start",
	start_command,
	filters = ~ to_ban, run_async = True
)

dispatcher.add_handler(start_handler)

settings_handler = CommandHandler(
	"settings",
	settings_command,
	filters = ~ to_ban, run_async = True
)

dispatcher.add_handler(settings_handler)

quality_handler = CommandHandler(
	"quality",
	quality_command,
	filters = ~ to_ban, run_async = True
)

dispatcher.add_handler(quality_handler)

to_root = Filters.user(root_ids)

managing_banned_handler = CommandHandler(
	"managing_banned",
	managing_banned_command,
	filters = to_root, run_async = True
)

dispatcher.add_handler(managing_banned_handler)

add_banned_handler = CommandHandler(
	"add_banned",
	add_banned_command,
	filters = to_root, run_async = True
)

dispatcher.add_handler(add_banned_handler)

shazam_handler = CommandHandler(
	"shazam",
	shazam_command,
	filters = ~ to_ban, run_async = True
)

dispatcher.add_handler(shazam_handler)

kill_dw_handler = CommandHandler(
	"kill_dw",
	kill_dw_command,
	filters = ~ to_ban, run_async = True
)

dispatcher.add_handler(kill_dw_handler)

info_handler = CommandHandler(
	"info",
	info_command,
	filters = ~ to_ban, run_async = True
)

dispatcher.add_handler(info_handler)

reasons_handler = CommandHandler(
	"reasons",
	reasons_command,
	filters = ~ to_ban, run_async = True
)

dispatcher.add_handler(reasons_handler)

help_handler = CommandHandler(
	"help",
	help_command,
	filters = ~ to_ban, run_async = True
)

dispatcher.add_handler(help_handler)

feedback_handler = CommandHandler(
	"feedback",
	feedback_command,
	filters = ~ to_ban, run_async = True
)

dispatcher.add_handler(feedback_handler)

donate_handler = CommandHandler(
	"donate",
	donate_command,
	filters = ~ to_ban, run_async = True
)

dispatcher.add_handler(donate_handler)

filter_owl_channel = Filters.chat(owl_channel)

send_global_msg_handler = MessageHandler(
	filter_owl_channel,
	send_global_msg_command,
	run_async = True
)

dispatcher.add_handler(send_global_msg_handler)

filter_url = Filters.entity(
	MessageEntity.URL
)

control_links = MessageHandler(
	(
		filter_url &
		~ to_ban
	), controls_links, run_async = True
)

dispatcher.add_handler(control_links)

filter_text = Filters.text

msgs = MessageHandler(
	(
		filter_text &
		~ to_ban
	), msgs_handler, run_async = True
)

dispatcher.add_handler(msgs)

filter_shazam = (Filters.voice | Filters.audio)
filter_bunker_channel = Filters.chat(bunker_channel)
filter_no_bot = Filters.via_bot(bot_chat_id)

audio_msgs = MessageHandler(
	(
		filter_shazam &
		~ filter_no_bot &
		~ to_ban &
		~ filter_bunker_channel
	), audio_handler, run_async = True
)

dispatcher.add_handler(audio_msgs)

inline_queries = InlineQueryHandler(
	handle_inline_queries, run_async = True
)

dispatcher.add_handler(inline_queries)

callback_queries = CallbackQueryHandler(
	handle_callback_queries, run_async = True
)

dispatcher.add_handler(callback_queries)

tg_bot_api.start_polling()

def checking():
	while True:
		sleep(time_sleep)
		dir_size = get_download_dir_size()
		print(f"STATUS DOWNLOADS {queues_started[0]}/{queues_finished[0]} {dir_size}/{download_dir_max_size}")

		if (
			dir_size >= download_dir_max_size
		) or (
			queues_started[0] == queues_finished[0]
		):
			tg_bot_api.stop()
			kill_threads(users_data)
			sleep(3)
			queues_started[0] = 0
			queues_finished[0] = 0
			clear_download_dir()
			clear_recorded_dir()
			tg_bot_api.start_polling()

tmux_session = None
tmux_session = create_tmux()

check_thread = magicThread(target = checking)
check_thread.start()

tg_user_start()

print("\nEXITTING WAIT A FEW SECONDS :)")
tg_bot_api.stop()
tg_user_api.stop()
check_thread.kill()
kill_threads(users_data)
clear_download_dir()
clear_recorded_dir()

if tmux_session:
	tmux_session.kill_session()
