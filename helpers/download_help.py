#!/usr/bin/python3

from time import sleep
from io import BytesIO
from pyrogram import Client
from telegram import ChatAction
from sqlite3 import IntegrityError
from telegram.error import BadRequest
from deezloader.models.track import Track
from deezloader.models.album import Album
from deezloader.__utils__ import what_kind
from deezloader.exceptions import TrackNotFound
from deezloader.__dee_api__ import API as deezer_API
from configs.set_configs import deez_api, tg_bot_api
from inlines.inline_keyboards import create_keyboard_artist

from .db_help import (
	write_dwsongs, select_dwsongs, delete_dwsongs
)

from deezloader.exceptions import (
	NoDataApi, InvalidLink, AlbumNotFound
)

from utils.utils import (
	get_quality, get_url_path,
	set_path, get_size, logging_bot
)

from configs.customs import (
	send_image_track_query, send_image_artist_query,
	send_image_playlist_query, send_image_album_query,
	album_too_long, track_too_long, empty_image_url
)

from utils.utils_data import (
	track_spo_data, track_dee_data,
	artist_dee_data, playlist_dee_data,
	playlist_spo_data, album_dee_data,
	album_spo_data, convert_spoty_to_dee_link_track
)

from configs.bot_settings import (
	bunker_channel, seconds_limits_album,
	seconds_limits_track, max_song_per_playlist,
	method_save, output_songs,
	recursive_quality, recursive_download,
	make_zip, upload_max_size_user,
	user_errors, progress_status_rate
)

deezer_api = deezer_API()
tg_bot = tg_bot_api.bot
l_telegram, l_uploads, l_downloads, l_links = logging_bot()

def log_error(log, exc_info = False):
	l_downloads.error(log, exc_info = exc_info)

def write_db(track_md5, file_id, n_quality, chat_id):
	try:
		write_dwsongs(track_md5, file_id, n_quality, chat_id)
	except IntegrityError:
		pass

class DOWNLOAD_HELP:
	def __init__(
		self,
		queues_started: list,
		queues_finished: list,
		tg_user_api: Client,
		create_zips: bool,
	) -> None:

		global make_zip

		self.tg_user_api = tg_user_api
		self.queues_started = queues_started
		self.queues_finished = queues_finished

		if not create_zips:
			make_zip = False

class DW:
	def __init__(
		self,
		helper: DOWNLOAD_HELP,
		chat_id: int,
		user_data: dict,
		hash_link: int
	) -> None:

		self.__tg_user_api = helper.tg_user_api
		self.__queues_started = helper.queues_started
		self.__queues_finished = helper.queues_finished
		self.__chat_id = chat_id
		self.__quality = user_data['quality']
		self.__n_quality = get_quality(self.__quality)
		self.__send_to_user_tracks = user_data['tracks']
		self.__send_to_user_zips = user_data['zips']
		self.__hash_link = hash_link
		self.__c_download = user_data['c_downloads']

	def __before_dw(self):
		self.__queues_started[0] += 1

	def __after_dw(self):
		self.__queues_finished[0] += 1

	def __finished(self):
		try:
			del self.__c_download[self.__hash_link]
		except KeyError:
			pass

	def __upload_audio(self, file_id):
		if self.__send_to_user_tracks:
			tg_bot.send_chat_action(
				chat_id = self.__chat_id,
				action = ChatAction.UPLOAD_AUDIO
			)

			sleep(0.1)
			l_uploads.info(f"UPLOADING: {file_id}")

			tg_bot.send_audio(
				chat_id = self.__chat_id,
				audio = file_id
			)

	def __upload_zip(self, file_id):
		if self.__send_to_user_zips:
			tg_bot.send_chat_action(
				chat_id = self.__chat_id,
				action = ChatAction.UPLOAD_DOCUMENT
			)

			sleep(0.1)
			l_uploads.info(f"UPLOADING: {file_id}")

			tg_bot.send_document(
				chat_id = self.__chat_id,
				document = file_id
			)

	def __upload_audio_track(self, track: Track):
		c_path = track.song_path
		track_md5 = track.track_md5
		md5_image = track.md5_image
		image_bytes1 = deezer_api.choose_img(md5_image, "90x90")
		io_image = BytesIO(image_bytes1)
		io_image.name = md5_image
		duration = track.duration
		performer = track.artist
		title = track.music
		f_format = track.file_format
		tag = track.tags
		track_quality = track.quality

		file_name = set_path(tag, self.__n_quality, f_format, 1)
		track_size = get_size(c_path, "gb")

		if track_size > upload_max_size_user:
			tg_bot.send_message(
				chat_id = self.__chat_id,
				text = f"THE SONG {track.song_name} IS TOO BIG TO BE UPLOADED\
					, MAX {upload_max_size_user} GB\
					, CURRENT {track_size} GB :("
			)

			return

		if track_quality != self.__n_quality:
			tg_bot.send_message(
				chat_id = self.__chat_id,
				text = (
					f"⚠ The {title} - {performer} can't be downloaded in {self.__quality} quality :( ⚠\
					\nIT HAS BEEN DOWNLOADED IN {track_quality}"
				)
			)

		file_id = self.__tg_user_api.send_audio(
			chat_id = bunker_channel,
			audio = c_path,
			thumb = io_image,
			duration = duration,
			performer = performer,
			title = title,
			file_name = file_name
		).audio.file_id

		write_db(
			track_md5, file_id,
			track_quality, self.__chat_id
		)

		self.__upload_audio(file_id)

	def __download_track(self, url):
		try:
			track = deez_api.download_trackdee(
				url,
				output_dir = output_songs,
				quality_download = self.__quality,
				recursive_quality = recursive_quality,
				recursive_download = recursive_download,
				method_save = method_save
			)
		except TrackNotFound as error:
			log_error(error, exc_info = True)

			tg_bot.send_message(
				chat_id = self.__chat_id,
				text = f"Cannot download {url} :("
			)

			return

		progress_message_id = tg_bot.send_message(
			chat_id = self.__chat_id,
			text = f"Starting uploading {track.song_name} ..."
		).message_id

		self.__upload_audio_track(track)

		tg_bot.delete_message(
			chat_id = self.__chat_id,
			message_id = progress_message_id
		)

	def __progress_status(self, current, total, times, album_name):
		c_time = times[0]

		if current == total:
			msg_id = times[1]

			tg_bot.delete_message(
				chat_id = self.__chat_id,
				message_id = msg_id
			)

		if (c_time % progress_status_rate == 0):
			c_progress = f"{current * 100 / total:.1f}%"
			c_text = f"Uploading {album_name}: {c_progress}"
			l_uploads.info(c_text)

			if c_time == 0:
				msg_id = tg_bot.send_message(
					chat_id = self.__chat_id,
					text = c_text
				).message_id

				times.append(msg_id)
			else:
				msg_id = times[1]

				try:
					tg_bot.edit_message_text(
						chat_id = self.__chat_id,
						message_id = msg_id,
						text = c_text
					)
				except BadRequest:
					pass

		times[0] += 1

	def __upload_zip_album(self, album: Album):
		times = [0]
		album_name = album.album_name
		md5_image = album.md5_image
		image_bytes2 = deezer_api.choose_img(md5_image, "320x320")
		image_io2 = BytesIO(image_bytes2)
		image_io2.name = md5_image
		progress_args = (times, album_name)
		path_zip = album.zip_path
		album_md5 = album.album_md5
		zip_size = get_size(path_zip, "gb")
		album_quality = album.tracks[0].quality

		if zip_size > upload_max_size_user:
			tg_bot.send_message(
				chat_id = self.__chat_id,
				text = f"THE ZIP IS TOO BIG TO BE UPLOADED\
					, MAX {upload_max_size_user} GB\
					, CURRENT {zip_size} GB :("
			)

			write_db(
				album_md5, "TOO BIG",
				album_quality, self.__chat_id
			)

			return

		file_id = self.__tg_user_api.send_document(
			chat_id = bunker_channel,
			document = path_zip,
			thumb = image_io2,
			progress = self.__progress_status,
			progress_args = progress_args
		).document.file_id

		write_db(
			album_md5, file_id,
			album_quality, self.__chat_id
		)

		self.__upload_zip(file_id)

	def __upload_audio_album(
		self,
		track: Track,
		image_bytes1,
		num_track, nb_tracks,
		progress_message_id
	):
		c_path = track.song_path
		track_md5 = track.track_md5
		image_io1 = BytesIO(image_bytes1)
		image_io1.name = track_md5
		duration = track.duration
		performer = track.artist
		title = track.music
		f_format = track.file_format
		tag = track.tags
		file_name = set_path(tag, self.__n_quality, f_format, 1)
		c_progress = f"Uploading ({num_track}/{nb_tracks}): {title}"
		c_progress += f" {num_track * 100 / nb_tracks:.1f}%"
		l_uploads.info(c_progress)

		tg_bot.edit_message_text(
			chat_id = self.__chat_id,
			message_id = progress_message_id,
			text = c_progress
		)

		if track.success:
			track_size = get_size(c_path, "gb")

			if track_size > upload_max_size_user:
				tg_bot.send_message(
					chat_id = self.__chat_id,
					text = f"THE SONG {track.song_name} IS TOO BIG TO BE UPLOADED\
						, MAX {upload_max_size_user} GB\
						, CURRENT {track_size} GB :("
				)

				return

			track_quality = track.quality

			if track_quality != self.__n_quality:
				tg_bot.send_message(
					chat_id = self.__chat_id,
					text = (
						f"⚠ The {title} - {performer} can't be downloaded in {self.__quality} quality :( ⚠\
						\nIT HAS BEEN DOWNLOADED IN {track_quality}"
					)
				)

			file_id = self.__tg_user_api.send_audio(
				chat_id = bunker_channel,
				audio = c_path,
				thumb = image_io1,
				duration = duration,
				performer = performer,
				title = title,
				file_name = file_name
			).audio.file_id

			write_db(
				track_md5, file_id,
				track_quality, self.__chat_id
			)

			self.__upload_audio(file_id)
		else:
			tg_bot.send_message(
				chat_id = self.__chat_id,
				text = f"Cannot download {track.song_name} :("
			)

	def __download_album(self, url):
		album = deez_api.download_albumdee(
			url,
			output_dir = output_songs,
			quality_download = self.__quality,
			recursive_quality = recursive_quality,
			recursive_download = recursive_download,
			make_zip = make_zip,
			method_save = method_save
		)

		md5_image = album.md5_image
		nb_tracks = album.nb_tracks
		image_bytes1 = deezer_api.choose_img(md5_image, "90x90")
		num_track = 1

		progress_message_id = tg_bot.send_message(
			chat_id = self.__chat_id,
			text = "Starting uploading..."
		).message_id

		for track in album.tracks:
			self.__upload_audio_album(
				track, image_bytes1, num_track,
				nb_tracks, progress_message_id
			)

			num_track += 1

		tg_bot.delete_message(
			chat_id = self.__chat_id,
			message_id = progress_message_id
		)

		if make_zip:
			self.__upload_zip_album(album)
		else:
			write_db(
				album.album_md5, "TOO BIG",
				self.__quality, self.__chat_id
			)

	def __send_for_debug(self, link, error):
		err_str = f"ERROR WITH THIS LINK {link} {self.__quality}"

		tg_bot.send_message(
			chat_id = self.__chat_id,
			text = err_str
		)

		sleep(0.1)

		tg_bot.send_message(
			chat_id = user_errors,
			text = err_str
		)

		log_error(error, exc_info = True)
		log_error(err_str)

	def __check_track(self, link):
		link_path = get_url_path(link)
		match = select_dwsongs(link_path, self.__n_quality)

		if match:
			file_id = match[0]

			try:
				self.__upload_audio(file_id)
			except BadRequest:
				delete_dwsongs(file_id)
				self.__check_track(link)
		else:
			try:
				self.__download_track(link)
			except Exception as error:
				self.__send_for_debug(link, error)

	def __check_album(self, link, tracks):
		link_path = get_url_path(link)
		match = select_dwsongs(link_path, self.__n_quality)

		if match:
			file_id = match[0]

			if file_id != "TOO BIG":
				try:
					self.__upload_zip(file_id)
				except BadRequest:
					delete_dwsongs(file_id)
					self.__check_album(link, tracks)

			if self.__send_to_user_tracks:
				for track in tracks:
					c_link = track['link']
					c_link_path = get_url_path(c_link)
					c_match = select_dwsongs(c_link_path, self.__n_quality)

					if not c_match:
						tg_bot.send_message(
							chat_id = self.__chat_id,
							text = f"The song {c_link} isn't avalaible :("
						)

						continue

					c_file_id = c_match[0]

					try:
						self.__upload_audio(c_file_id)
					except BadRequest:
						delete_dwsongs(c_file_id)
						self.__check_track(c_link)
		else:
			try:
				self.__download_album(link)
			except Exception as error:
				self.__send_for_debug(link, error)

	def __send_photo(
		self, chat_id,
		image_url, caption,
		reply_markup = None
	):
		try:
			data = tg_bot.send_photo(
				chat_id = chat_id,
				photo = image_url,
				caption = caption,
				reply_markup = reply_markup
			)
		except BadRequest:
			data = tg_bot.send_photo(
				chat_id = chat_id,
				photo = empty_image_url,
				caption = caption,
				reply_markup = reply_markup
			)

		return data

	def download(self, link):
		try:
			l_links.info(link)
			stat = 1
			self.__before_dw()
			link = what_kind(link)

			if "track/" in link:
				if "spotify.com" in link:
					try:
						image_url, name,\
							artist, album,\
								date, link_dee, duration = track_spo_data(link)
					except TrackNotFound:
						tg_bot.send_message(
							chat_id = self.__chat_id,
							text = f"Cannot download {link} :("
						)

						return

				elif "deezer.com" in link:
					image_url, name,\
						artist, album,\
							date, link_dee, duration = track_dee_data(link)

				if duration > seconds_limits_track:
					tg_bot.send_message(
						chat_id = self.__chat_id,
						text = track_too_long
					)

					return

				caption = (
					send_image_track_query
					% (
						name,
						artist,
						album,
						date
					)
				)

				msg_id = self.__send_photo(
					self.__chat_id, image_url, caption
				).message_id

				self.__check_track(link_dee)

			elif "artist/" in link:
				stat = 0

				if "deezer.com" in link:
					name, image_url,\
						nb_album, nb_fan = artist_dee_data(link)
				else:
					return

				caption = (
					send_image_artist_query
					% (
						name,
						nb_album,
						nb_fan
					)
				)

				reply_markup = create_keyboard_artist(link)

				msg_id = self.__send_photo(
					self.__chat_id, image_url, caption,
					reply_markup = reply_markup
				).message_id

			elif "album/" in link:
				if "spotify.com" in link:
					image_url, album,\
						artist, date,\
						nb_tracks, tracks,\
						duration, link_dee = album_spo_data(link)

				elif "deezer.com" in link:
					image_url, album,\
						artist, date,\
						nb_tracks, tracks,\
						duration, link_dee = album_dee_data(link)

				if duration > seconds_limits_album:
					tg_bot.send_message(
						chat_id = self.__chat_id,
						text = album_too_long
					)

					return

				caption = (
					send_image_album_query
					% (
						album,
						artist,
						date,
						nb_tracks
					)
				)

				msg_id = self.__send_photo(
					self.__chat_id, image_url, caption
				).message_id

				self.__check_album(link_dee, tracks)

			elif "playlist/" in link:
				if "spotify.com" in link:
					mode = "spotify"

					try:
						nb_tracks, n_fans,\
							image_url, creation_data,\
								creator, tracks = playlist_spo_data(link)
					except IndexError:
						tg_bot.send_message(
							chat_id = self.__chat_id,
							text = f"This playlist is unreadable :("
						)

						return

				elif "deezer.com" in link:
					mode = "deezer"

					nb_tracks, n_fans,\
						image_url, creation_data,\
							creator, tracks = playlist_dee_data(link)

				caption = (
					send_image_playlist_query
					% (
						creation_data,
						creator,
						nb_tracks,
						n_fans
					)
				)

				msg_id = self.__send_photo(
					self.__chat_id, image_url, caption
				).message_id

				if nb_tracks > max_song_per_playlist:
					tg_bot.send_message(
						chat_id = self.__chat_id,
						text = f"This playlist contains {nb_tracks} tracks only the first {max_song_per_playlist} will be downloaded"
					)

				for track, index in zip(
					tracks, range(max_song_per_playlist)
				):
					if mode == "deezer":
						c_link = track['link']

					elif mode == "spotify":
						c_track = track['track']

						if not c_track:
							continue

						external_urls = c_track['external_urls']

						if not external_urls:
							tg_bot.send_message(
								chat_id = self.__chat_id,
								text = f"The track \"{c_track['name']}\" is not avalaible on Spotify :("
							)

							continue

						spoty_url = external_urls['spotify']

						try:
							c_link = convert_spoty_to_dee_link_track(spoty_url)
						except (NoDataApi, TrackNotFound):
							tg_bot.send_message(
								chat_id = self.__chat_id,
								text = f"Cannot download {spoty_url} :("
							)

							continue

					self.__check_track(c_link)

			else:
				tg_bot.send_message(
					chat_id = self.__chat_id,
					text = "Can you just send normal links?, THANKS :)"
				)

				return

			if stat == 1:
				tg_bot.send_message(
					chat_id = self.__chat_id,
					text = "FINISHED =)",
					reply_to_message_id = msg_id
				)
		except AlbumNotFound as error:
			tg_bot.send_message(
				chat_id = self.__chat_id,
				text = error.msg
			)
		except (NoDataApi, InvalidLink) as error:
			if type(error) is NoDataApi:
				text = f"This {link} doesn't exist :("

			elif type(error) is InvalidLink:
				text = f"INVALID LINK {link} :("

			tg_bot.send_message(
				chat_id = self.__chat_id,
				text = text
			)
		except Exception as error:
			try:
				self.__send_for_debug(link, error)
			except Exception as error:
				log_error(f"{link} {self.__quality} {self.__chat_id}")
				log_error(error, exc_info = True)
		finally:
			self.__after_dw()
			self.__finished()