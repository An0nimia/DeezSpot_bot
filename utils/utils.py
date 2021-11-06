#!/usr/bin/python3

from urllib.parse import urlparse
from requests import get as req_get
from shutil import disk_usage, rmtree
from helpers.db_help import initialize_db
from libtmux import Server as tmux_server
from .converter_bytes import convert_bytes_to
from deezloader.libutils.utils import var_excape
from deezloader.deezloader.deezer_settings import qualities as dee_qualities
from deezloader.spotloader.spotify_settings import qualities as spo_qualities

from logging import (
	getLogger, FileHandler,
	Formatter, Logger
)

from configs.bot_settings import (
	output_songs, supported_link, output_shazam,
	logs_path, logger_names,
	log_uploads, log_downloads
)

from os import (
	walk, listdir, mkdir,
	remove, system,
	name as os_name
)

from os.path import (
	getsize, join,
	islink, isdir
)

__qualities_dee = list(
	dee_qualities.keys()
)

__qualities_spo = list(
	spo_qualities.keys()
)

def check_config_file(config):
	if not "arl" in config['deez_login']:
		print("Something went wrong with the login token in the configuration file")
		exit()

	if (
		not "api_id" in config['pyrogram']
	) or (
		not "api_hash" in config['pyrogram']
	):
		print("Something went wrong with pyrogram in the configuration file")
		exit()

	if not "bot_token" in config['telegram']:
		print("Something went wrong with the telegram token in the configuration file")
		exit()

	if (
		not "key" in config['acrcloud']
	) or (
		not "secret" in config['acrcloud']
	) or (
		not "host" in config['acrcloud']
	):
		print("Something went wrong with acrcloud in the configuration file")
		exit()

def get_netloc(link):
	netloc = urlparse(link).netloc

	return netloc

def is_supported_link(link):
	is_supported = True
	netloc = urlparse(link).netloc

	if not any(
		c_link == netloc
		for c_link in supported_link
	):
		return False

	return is_supported

def __get_tronc(string):
	l_encoded = len(
		string.encode()
	)

	if l_encoded > 242:
		n_tronc = len(string) - l_encoded - 242
	else:
		n_tronc = 242

	return n_tronc

def set_path(song_metadata, song_quality, file_format, method_save):
	album = var_excape(song_metadata['album'])
	artist = var_excape(song_metadata['artist'])
	music = var_excape(song_metadata['music'])

	if method_save == 0:
		discnum = song_metadata['discnum']
		tracknum = song_metadata['tracknum']
		song_name = f"{album} CD {discnum} TRACK {tracknum}"

	elif method_save == 1:
		song_name = f"{music} - {artist}"

	elif method_save == 2:
		isrc = song_metadata['isrc']
		song_name = f"{music} - {artist} [{isrc}]"

	elif method_save == 3:
		discnum = song_metadata['discnum']
		tracknum = song_metadata['tracknum']
		song_name = f"{discnum}:{tracknum} - {music} - {artist}"

	n_tronc = __get_tronc(song_name)
	song_path = f"{song_name[:n_tronc]} ({song_quality}){file_format}"

	return song_path

def get_quality_dee_s_quality(dee_quality):
	chosen = dee_qualities[dee_quality]
	s_quality = chosen['s_quality']

	return s_quality

def get_quality_spo(dee_quality):
	index = __qualities_dee.index(dee_quality)
	chosen = __qualities_spo[index]

	return chosen

def get_quality_spo_s_quality(spo_quality):
	chosen = spo_qualities[spo_quality]
	s_quality = chosen['s_quality']

	return s_quality

def get_url_path(link):
	parsed = urlparse(link)
	path = parsed.path
	s_path = path.split("/")
	path = f"{s_path[-2]}/{s_path[-1]}"

	return path

def my_round(num):
	rounded = round(num, 2)

	return rounded

def get_image_bytes(image_url):
	content = req_get(image_url).content

	return content

def get_avalaible_disk_space():
	total, used, free = disk_usage("/")
	total = convert_bytes_to(total, "gb")
	used = convert_bytes_to(used, "gb")
	free = convert_bytes_to(free, "gb")

	return free

def get_download_dir_size():
	total_size = 0

	for dirpath, dirnames, filenames in walk(output_songs):
		for f in filenames:
			fp = join(dirpath, f)

			if not islink(fp):
				total_size += getsize(fp)

	total_size = convert_bytes_to(total_size, "gb")

	return total_size

def clear_download_dir():
	dirs = listdir(output_songs)

	for c_dir in dirs:
		cc_dir = join(output_songs, c_dir)

		if isdir(cc_dir):
			rmtree(cc_dir)

def clear_recorded_dir():
	files = listdir(output_shazam)

	for c_file in files:
		cc_file = join(output_shazam, c_file)
		remove(cc_file)

def create_recorded_dir():
	if not isdir(output_shazam):
		mkdir(output_shazam)

def create_download_dir():
	if not isdir(output_songs):
		mkdir(output_songs)

def create_log_dir():
	if not isdir(logs_path):
		mkdir(logs_path)

def logging_bot() -> list[Logger]:
	formatter = Formatter(
		"%(asctime)s - %(name)s - %(levelname)s - %(message)s"
	)

	loggers = []

	for logger, level, log_path in logger_names:
		fu = FileHandler(log_path)
		fu.setFormatter(formatter)
		c_logger = getLogger(logger)
		c_logger.setLevel(level)
		c_logger.addHandler(fu)
		loggers.append(c_logger)

	return loggers

def check_config_bot():
	initialize_db()
	create_recorded_dir()
	create_download_dir()
	create_log_dir()

def get_size(f, size) -> float:
	b_size = getsize(f)
	mb_size = convert_bytes_to(b_size, size)

	return mb_size

def show_menu():
	print("1): TEST MODE")
	print("2): COOL MODE")
	print("3): TEST MODE (NO ZIP)")
	print("4): COOL MODE (NO ZIP)")

	ans = input("How to use it?: ")

	if ans == "1":
		choice = 1
	elif ans == "2":
		choice = 2
	elif ans == "3":
		choice = 3
	elif ans == "4":
		choice = 4
	else:
		exit()

	return choice

def clear():
	cmd = None

	if os_name == "nt":
		cmd = "cls"
	else:
		cmd = "clear"

	return cmd

def create_tmux():
	cclear = clear()
	system(cclear)
	server = tmux_server()

	info = {
		"session_name": "deez_bot"
	}

	session = server.find_where(info)

	try:
		window = session.attached_window
	except AttributeError:
		print("Must be executed after typed tmux new -s deez_bot :)")
		raise KeyboardInterrupt

	pan_top_right = window.split_window(vertical = False)
	pan_top_right.send_keys(cclear)
	pan_top_right.send_keys(f"tail -f {log_downloads}")
	pan_bot_left = pan_top_right.split_window(vertical = True)
	pan_bot_left.send_keys(cclear)
	pan_bot_left.send_keys(f"tail -n2 -f {log_uploads}")
	#pan_bot_right = pan_bot_left.split_window(vertical = False)
	#pan_bot_right.send_keys(cclear)
	#pan_bot_right.send_keys(f"tail -n2 -f {log_downloads}")
	return session