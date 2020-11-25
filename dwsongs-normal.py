#!/usr/bin/python3

import os
import logging
import dwytsongs
from utils import *
from settings import *
from time import sleep
from shutil import rmtree
from spotipy import Spotify
from mutagen.mp3 import MP3
from threading import Thread
from mutagen.flac import FLAC
from acrcloud import ACRcloud
from mutagen.easyid3 import EasyID3
from configparser import ConfigParser
from deezloader.utils import what_kind
from deezloader import Login, exceptions
from mutagen.id3._util import ID3NoHeaderError

from deezloader.deezer_settings import (
	api_track, api_album,
	api_playlist, api_search_trk
)

from telegram.ext import (
	CommandHandler, Updater, Filters,
	CallbackQueryHandler, InlineQueryHandler, MessageHandler
)

from telegram import (
	Bot, ReplyKeyboardMarkup, error, ReplyKeyboardRemove,
	InlineKeyboardMarkup, TelegramError, InputMediaPhoto,
	InlineQueryResultArticle, InputTextMessageContent
)

config = ConfigParser()
config.read(ini_file)

try:
	deezer_token = config['login']['token']
	bot_token = config['bot']['token']
	acrcloud_key = config['acrcloud']['key']
	acrcloud_hash = config['acrcloud']['secret']
	acrcloud_host = config['acrcloud']['host']
	version = config['bot_info']['version']
	creator = config['bot_info']['creator']
	donation_link = config['bot_info']['donation']
	group_link = config['bot_info']['group']
except KeyError:
	print("Something went wrong with configuration file")
	exit()

downloa = Login(deezer_token)
sets = Updater(bot_token, use_context = True)
bot = Bot(bot_token)
users = {}
date = {}
del1 = 0
del2 = 0
free = 1
is_audio = 0
initialize()

config = {
	"key": acrcloud_key,
	"secret": acrcloud_hash,
	"host": acrcloud_host
}

acrcloud = ACRcloud(config)

logging.basicConfig(
	filename = "dwsongs.log",
	level = logging.ERROR,
	format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

spo = Spotify(
	generate_token()
)

def reque(url, chat_id = None, control = False):
	thing = request(url)

	if control:
		try:
			if thing.json()['error']['message'] == "Quota limit exceeded":
				sendMessage(chat_id, "Please send the link again :(")
				return
		except KeyError:
			pass

		try:
			if thing.json()['error']:
				sendMessage(chat_id, "No result has been found :(")
				return
		except KeyError:
			pass

	return thing

def init_user(chat_id, tongue):
	try:
		users[chat_id]
	except KeyError:
		users[chat_id] = {
			"quality": "MP3_320",
			"tongue": tongue,
			"c_downloads": 0
		}

def authorized(chat_id, date = 0):
	global free

	ok = True

	if (
		(
			(
				check_flood(chat_id, date) == "BANNED"
			) or free == 0
		) and not chat_id in roots
	):
		ok = False

	return ok

def delete(chat_id):
	global del2

	del2 += 1

	if ans == "2":
		users[chat_id]['c_downloads'] -= 1

def check_flood(chat_id, time_now = 0):
	query = "SELECT banned FROM BANNED where banned = '%d'" % chat_id
	exist = view_db(query)

	if exist:
		return "BANNED"

	if time_now == 0:
		return

	try:
		time = time_now - date[chat_id]['time']

		if time > 30:
			date[chat_id]['msg'] = 0

		date[chat_id]['time'] = time_now

		if time <= 4:
			date[chat_id]['msg'] += 1

			if time <= 4 and date[chat_id]['msg'] > 4:
				date[chat_id]['msg'] = 0
				date[chat_id]['tries'] -= 1

				sendMessage(
					chat_id,
					"It is appearing you are trying to flood, you have to wait more than four second to send another message.\n%d possibilites :)" % date[chat_id]['tries']
				)

				if date[chat_id]['tries'] == 0:
					query = "INSERT INTO BANNED (banned) values ('%d')" % chat_id
					write_db(query)
					del date[chat_id]
					sendMessage(chat_id, "You are banned :)")
	except KeyError:
		date[chat_id] = {
			"time": time_now,
			"tries": 3,
			"msg": 0
		}

def create_keyboard(array, chat_id):
	keyboard = [
		[]
	]

	for a in array:
		keyboard[0] += [
			InlineKeyboardButton(
				"{}: {}".format(
					a.capitalize(), users[chat_id][a]
				),
				callback_data = "%s" % a
			)
		]

	return keyboard

def sendMessage(chat_id, text, reply_markup = None, reply_to_message_id = None):
	sleep(default_time)

	try:
		users[chat_id]['tongue']
	except KeyError:
		users[chat_id]['tongue'] = "en"

	try:
		bot.sendChatAction(chat_id, "typing")

		return bot.sendMessage(
			chat_id,
			translate(
				users[chat_id]['tongue'], text
			),
			reply_markup = reply_markup,
			reply_to_message_id = reply_to_message_id
		)
	except (error.Unauthorized, error.TimedOut, error.BadRequest):
		pass

def sendPhoto(chat_id, photo, caption = None, reply_markup = None):
	sleep(default_time)

	try:
		bot.sendChatAction(chat_id, "upload_photo")

		return bot.sendPhoto(
			chat_id, photo,
			caption = caption,
			reply_markup = reply_markup
		)
	except (error.Unauthorized, error.TimedOut):
		pass

def sendAudio(
	chat_id, audio,
	link = None,
	image = None,
	youtube = False
):
	sleep(default_time)

	try:
		if os.path.isfile(audio):
			bot.sendChatAction(chat_id, "upload_audio")

			try:
				tag = EasyID3(audio)
				duration = int(MP3(audio).info.length)
			except ID3NoHeaderError:
				tag = FLAC(audio)
				duration = int(tag.info.length)

			if os.path.getsize(audio) < telegram_audio_api_limit:
				file_id = bot.sendAudio(
					chat_id, open(audio, "rb"),
					thumb = open(image.url, "rb"),
					duration = duration,
					performer = tag['artist'][0],
					title = tag['title'][0]
				)['audio']['file_id']

				if not youtube:
					quality = fast_split(audio)
					link = "track/%s" % link.split("/")[-1]

					write_db(
						insert_query
						% (
							link,
							file_id,
							quality
						)
					)
			else:
				sendMessage(chat_id, "Song too big :(")
		else:
			bot.sendAudio(chat_id, audio)
	except error.BadRequest:
		sendMessage(chat_id, "Sorry the track %s doesn't seem readable on Deezer :(" % link)

def track(link, chat_id, quality):
	global spo

	lin = "track/%s" % link.split("/")[-1]
	qua = quality.split("MP3_")[-1]
	query = where_query.format(lin, qua)
	match = view_db(query)

	if match:
		sendAudio(chat_id, match[0])
	else:
		try:
			youtube = False

			if "spotify" in link:
				try:
					url = spo.track(link)
				except:
					spo = Spotify(
						generate_token()
					)

					url = spo.track(link)

				try:
					image = url['album']['images'][2]['url']
				except IndexError:
					image = image_resize(song_default_image, 90)

				mode = downloa.download_trackspo

			elif "deezer" in link:
				ids = link.split("/")[-1]
				api_link = api_track % ids
				kind = "track"

				try:
					url = reque(api_link, chat_id, True).json()['album']['cover_xl']
				except AttributeError:
					return

				image = image_resize(
					check_image(url, ids, kind), 90
				)

				mode = downloa.download_trackdee

			z = mode(
				link,
				quality = quality,
				recursive_quality = True,
				recursive_download = True,
				not_interface = not_interface
			)
		except (exceptions.TrackNotFound, exceptions.NoDataApi):
			sendMessage(chat_id, "Track doesn't %s exist on Deezer or maybe it isn't readable, it'll be downloaded from YouTube..." % link)

			try:
				if "spotify" in link:
					mode = dwytsongs.download_trackspo

				elif "deezer" in link:
					mode = dwytsongs.download_trackdee

				z = mode(
					link,
					recursive_download = True,
					not_interface = not_interface
				)

				youtube = True
			except:
				sendMessage(chat_id, "Sorry I cannot download this song %s :(" % link)
				return

		image = get_image(image)
		sendAudio(chat_id, z, link, image, youtube)

def Link(link, chat_id, quality, message_id):
	global spo
	global del1

	del1 += 1
	done = 0
	quali = quality.split("MP3_")[-1]
	link = what_kind(link)
	link = link.split("?")[0]
	ids = link.split("/")[-1]

	try:
		if "track/" in link:
			if "spotify" in link:
				try:
					url = spo.track(link)
				except Exception as a:
					if not "The access token expired" in str(a):
						sendMessage(
							chat_id, "Invalid link %s ;)" % link,
							reply_to_message_id = message_id
						)

						delete(chat_id)
						return

					spo = Spotify(
						generate_token()
					)

					url = spo.track(link)

				try:
					image1 = url['album']['images'][0]['url']
				except IndexError:
					image1 = song_default_image
				
				name = url['name']
				artist = url['album']['artists'][0]['name']
				album = url['album']['name']
				date = url['album']['release_date']

			elif "deezer" in link:
				kind = "track"
				api_link = api_track % ids

				try:
					url = reque(api_link, chat_id, True).json()
				except AttributeError:
					delete(chat_id)
					return

				image1 = check_image(
					url['album']['cover_xl'], ids, kind
				)

				name = url['title']
				artist = url['artist']['name']
				album = url['album']['title']
				date = url['album']['release_date']

			if any(
				a in link
				for a in services_supported
			):
				sendPhoto(
					chat_id, image1,
					caption = (
						send_image_track_query
						% (
							name,
							artist,
							album,
							date
						)
					)
				)

				track(link, chat_id, quality)
			else:
				sendMessage(chat_id, not_supported_links % link)

		elif "album/" in link:
			links = []
			count = [0]

			if "spotify" in link:
				try:
					tracks = spo.album(link)
				except Exception as a:
					if not "The access token expired" in str(a):
						sendMessage(
							chat_id, "Invalid link %s ;)" % link,
							reply_to_message_id = message_id
						)

						delete(chat_id)
						return

					spo = Spotify(
						generate_token()
					)

					tracks = spo.album(link)

				try:
					image3 = tracks['images'][2]['url']
					image1 = tracks['images'][0]['url']
				except IndexError:
					image3 = image_resize(song_default_image, 90)
					image1 = song_default_image

				name = tracks['name']
				artist = tracks['artists'][0]['name']
				date = tracks['release_date']
				tot = tracks['total_tracks']

				def lazy(a):
					count[0] += a['duration_ms']

					links.append(
						a['external_urls']['spotify']
					)

				for a in tracks['tracks']['items']:
					lazy(a)

				tracks = tracks['tracks']

				for a in range(tot // 50 - 1):
					try:
						tracks = spo.next(tracks)
					except:
						spo = Spotify(
							generate_token()
						)

						tracks = spo.next(tracks)

					for a in tracks['items']:
						lazy(a)

				count[0] //= 1000
				mode = downloa.download_albumspo

			elif "deezer" in link:
				api_link = api_album % ids
				kind = "album"

				try:
					url = reque(api_link, chat_id, True).json()
				except AttributeError:
					delete(chat_id)
					return

				count[0] = url['duration']
				image1 = check_image(url['cover_xl'], ids, kind)
				image3 = image_resize(image1, 90)
				tot = url['nb_tracks']

				links = [
					a['link'] for a in url['tracks']['data']
				]

				name = url['title']
				artist = url['artist']['name']
				date = url['release_date']
				mode = downloa.download_albumdee

			if any(
				a in link
				for a in services_supported
			):
				if count[0] > seconds_limits_album:
					sendMessage(chat_id, "If you do this again I will come to your home and I will ddos your ass :)")
					delete(chat_id)
					return

				message_id = sendPhoto(
					chat_id, image1,
					caption = (
						send_image_album_query
						% (
							name,
							artist,
							date,
							tot
						)
					)
				)['message_id']

				conn = connect(db_file)
				c = conn.cursor()
				exists = []

				for a in links:
					ids = a.split("/")[-1]
					lins = "track/%s" % ids

					exist = c.execute(
						where_query.format(lins, quali)
					).fetchone()

					if exist:
						exists.append(exist)

				if len(exists) < len(links) // 3:
					z = mode(
						link,
						quality = quality,
						recursive_quality = True,
						recursive_download = True,
						not_interface = not_interface
					)

					image3 = get_image(image3)

					for a in range(
						len(z)
					):
						sendAudio(chat_id, z[a], links[a], image3)
				else:
					for a in links:
						track(a, chat_id, quality)

				done = 1
			else:
				sendMessage(chat_id, not_supported_links % link)

		elif "playlist/" in link:
			links = []

			if "spotify" in link:
				musi = link.split("/")

				try:
					tracks = spo.user_playlist(musi[-3], musi[-1])
				except Exception as a:
					if not "The access token expired" in str(a):
						sendMessage(
							chat_id, "Invalid link ;)",
							reply_to_message_id = message_id
						)

						delete(chat_id)
						return

					spo = Spotify(
						generate_token()
					)

					tracks = spo.user_playlist(musi[-3], musi[-1])

				try:
					image1 = tracks['images'][0]['url']
				except IndexError:
					image1 = song_default_image

				def lazy(a):
					try:
						links.append(
							a['track']['external_urls']['spotify']
						)
					except (KeyError, TypeError):
						links.append("Error :(")

				for a in tracks['tracks']['items']:
					lazy(a)

				added = tracks['tracks']['items'][0]['added_at']
				owner = tracks['owner']['display_name']
				tot = tracks['tracks']['total']
				tracks = tracks['tracks']

				for a in range(tot // 100 - 1):
					try:
						tracks = spo.next(tracks)
					except:
						spo = Spotify(
							generate_token()
						)

						tracks = spo.next(tracks)

					for a in tracks['items']:
						lazy(a)

			elif "deezer" in link:
				api_link = api_playlist % ids

				try:
					url = reque(api_link, chat_id, True).json()
				except AttributeError:
					delete(chat_id)
					return

				links = [
					a['link']
					for a in url['tracks']['data']
				]

				image1 = url['picture_xl']
				tot = url['nb_tracks']
				added = url['creation_date']
				owner = url['creator']['name']

			if any(
				a in link
				for a in services_supported
			):

				if tot > max_songs:
					sendMessage(chat_id, "Fuck you")
					delete(chat_id)
					return

				sendPhoto(
					chat_id, image1,
					caption = (
						send_image_playlist_query
						% (
							added,
							owner,
							tot
						)
					)
				)

				for a in links:
					if a.startswith("http"):
						try:
							track(a, chat_id, quality)
						except:
							sendMessage(chat_id, "Cannot download %s:(" % a)
					else:
						sendMessage(chat_id, a)

				done = 1
			else:
				sendMessage(chat_id, not_supported_links % link)
		
		elif "artist/" in link:
			if "deezer" in link:
				api_link = api_artist % ids

				try:
					url = reque(api_link, chat_id, True).json()
				except AttributeError:
					delete(chat_id)
					return

				keyboard = [
					[
						InlineKeyboardButton(
							queries['top']['text'],
							callback_data = queries['top']['query'] % api_link
						),
						InlineKeyboardButton(
							queries['albums']['text'],
							callback_data = queries['albums']['query'] % api_link
						)
					],
					[
						InlineKeyboardButton(
							queries['radio']['text'],
							callback_data = queries['radio']['query'] % api_link
						),
						InlineKeyboardButton(
							queries['related']['text'],
							callback_data = queries['related']['query'] % api_link
						)
					]
				]

				image1 = url['picture_xl']
				artist = url['name']
				albums = url['nb_album']
				fans = url['nb_fan']

			if any(
				a in link
				for a in services_supported[1:]
			):
				sendPhoto(
					chat_id, image1,
					caption = (
						send_image_artist_query
						% (
							artist,
							albums,
							fans
						)
					),
					reply_markup = InlineKeyboardMarkup(keyboard)
				)
			else:
				sendMessage(chat_id, not_supported_links % link)

		else:
			sendMessage(chat_id, not_supported_links % link)

	except FileNotFoundError:
		sendMessage(
			chat_id, "Resend link please...",
			reply_to_message_id = message_id
		)

	except error.TimedOut:
		sendMessage(chat_id, "Retry after a few minutes")

	except exceptions.QuotaExceeded:
		sendMessage(chat_id, "Please send the link %s again :(" % link)

	except exceptions.AlbumNotFound:
		sendMessage(chat_id, "Album %s didn't find on Deezer :(" % link)
		sendMessage(chat_id, "Try to search it throught inline mode or search the link on Deezer")

	except Exception as a:
		logging.error(a)
		logging.error(quality)
		logging.error(link)

		sendMessage(
			chat_id, "OPS :( Something went wrong please send to @An0nimia this link: {} {}, if this happens again".format(link, quality)
		)

	if done == 1:
		sendMessage(
			chat_id, end_message,
			reply_to_message_id = message_id,
			reply_markup = InlineKeyboardMarkup(end_keyboard)
		)

	delete(chat_id)

def Audio(audio, chat_id):
	global spo
	global is_audio

	is_audio = 1
	audi = "{}{}.ogg".format(loc_dir, audio)

	try:
		bot.getFile(audio).download(audi)
	except TelegramError:
		sendMessage(chat_id, "File sent is too big, please send a file lower than 20 MB")
		is_audio = 0
		return

	audio = acrcloud.recognizer(audi)
	is_audio = 0	

	try:
		os.remove(audi)
	except FileNotFoundError:
		pass

	if audio['status']['msg'] != "Success":
		sendMessage(chat_id, "Sorry cannot detect the song from audio :(, retry...")
		return

	infos = audio['metadata']['music'][0]
	artist = infos['artists'][0]['name']
	track = infos['title']
	album = infos['album']['name']

	try:
		date = infos['release_date']
		album += "_%s" % date
	except KeyError:
		album += "_"

	try:
		label = infos['label']
		album += "_%s" % label
	except KeyError:
		album += "_"

	try:
		genre = infos['genres'][0]['name']
		album += "_%s" % genre
	except KeyError:
		album += "_"

	if len(album) > 64:
		album = "Infos with too many bytes"

	try:
		song = "{} - {}".format(track, artist)
		
		url = reque(
			api_search_trk % song.replace("#", ""), chat_id, True
		).json()
	except AttributeError:
		return

	try:
		for a in range(url['total'] + 1):
			if url['data'][a]['title'] == track:
				ids = url['data'][a]['link']
				image = url['data'][a]['album']['cover_xl']
				break
	except IndexError:
		try:
			ids = "https://open.spotify.com/track/%s" % infos['external_metadata']['spotify']['track']['id']

			try:
				url = spo.track(ids)
			except:
				spo = Spotify(
					generate_token()
				)

				url = spo.track(ids)

			image = url['album']['images'][0]['url']
		except KeyError:
			try:
				ids = api_track % infos['external_metadata']['deezer']['track']['id']

				try:
					url = reque(ids, chat_id, True).json()
				except AttributeError:
					return

				image = url['album']['cover_xl']
			except KeyError:
				sendMessage(chat_id, "Sorry I can't Shazam the track :(")
				return

	keyboard = [
		[
			InlineKeyboardButton(
				queries['download']['text'],
				callback_data = ids
			),
			InlineKeyboardButton(
				queries['info']['text'],
				callback_data = album
			)
		]
	]

	sendPhoto(
		chat_id, image,
		caption = "{} - {}".format(track, artist),
		reply_markup = InlineKeyboardMarkup(keyboard)
	)

def inline(message_id, chat_id, query_data, query_id, tongue):
	try:
		if query_data in settingss or query_data in qualities:
			if query_data == "quality":
				keyboard = qualities_keyboard

			elif query_data == "tongue":
				if users[chat_id]['tongue'] != "en":
					users[chat_id]['tongue'] = "en"
				else:
					users[chat_id]['tongue'] = tongue

				keyboard = create_keyboard(settingss, chat_id)

			elif query_data in qualities:
				users[chat_id]['quality'] = query_data
				keyboard = create_keyboard(settingss, chat_id)

			try:
				bot.editMessageReplyMarkup(
					chat_id, message_id,
					reply_markup = InlineKeyboardMarkup(keyboard)
				)
			except error.BadRequest:
				pass

			bot.answerCallbackQuery(
				query_id,
				translate(
					users[chat_id]['tongue'], "DONE ✅"
				)
			)

		elif "artist" in query_data:
			keyboard = []
			link = api_artist % query_data.split("/")[4]

			try:
				url = reque(
					query_data.replace("down", ""),
					chat_id, True
				).json()
			except AttributeError:
				return

			if "album" in query_data:
				keyboard += [
					[
						InlineKeyboardButton(
							"{} - {}".format(a['title'], a['release_date']),
							callback_data = a['link']
						)
					] for a in url['data']
				]

				keyboard.append(
					[
						InlineKeyboardButton(
							queries['back']['text'],
							callback_data = link
						)
					]
				)

			elif "down" in query_data:
				if ans == "2":
					if users[chat_id]['c_downloads'] == 3:
						bot.answerCallbackQuery(
							query_id,
							translate(
								users[chat_id]['tongue'],
								"Wait the end and repeat the step, did you think you could download how much songs you wanted? ;)"
							),
							show_alert = True
						)

						return
					else:
						users[chat_id]['c_downloads'] += 1

				bot.answerCallbackQuery(
					query_id,
					translate(
						users[chat_id]['tongue'], "Songs are downloading ⬇️"
					)
				)

				for a in url['data']:
					Link(
						"https://www.deezer.com/track/%d" % a['id'],
						chat_id,
						users[chat_id]['quality'],
						message_id
					)

					if ans == "2":
						users[chat_id]['c_downloads'] += 1

				if ans == "2":
					users[chat_id]['c_downloads'] -= 1

			elif "radio" in query_data or "top" in query_data:
				if "radio" in query_data:
					method = "radio"
				else:
					method = "top?limit=30"

				keyboard += [
					[
						InlineKeyboardButton(
							"{} - {}".format(a['artist']['name'], a['title']),
							callback_data = "https://www.deezer.com/track/%d" % a['id']
						)
					] for a in url['data']
				]

				keyboard.append(
					[
						InlineKeyboardButton(
							"GET ALL ⬇️",
							callback_data = "{}/{}/down".format(link, method)
						)
					]
				)

				keyboard.append(
					[
						InlineKeyboardButton(
							queries['back']['text'],
							callback_data = link
						)
					]
				)

			elif "related" in query_data:
				keyboard = [
					[
						InlineKeyboardButton(
							"{} - {}".format(a['name'], a['nb_fan']),
							callback_data = api_artist % str(a['id'])
						)
					] for a in url['data']
				]

				keyboard.append(
					[
						InlineKeyboardButton(
							queries['back']['text'],
							callback_data = link
						)
					]
				)

			else:
				keyboard = [
					[
						InlineKeyboardButton(
							queries['top']['text'],
							callback_data = queries['top']['query'] % link
						),
						InlineKeyboardButton(
							queries['albums']['text'],
							callback_data = queries['albums']['query'] % link
						)
					],
					[
						InlineKeyboardButton(
							queries['radio']['text'],
							callback_data = queries['radio']['query'] % link
						),
						InlineKeyboardButton(
							queries['related']['text'],
							callback_data = queries['related']['query'] % link
						)
					]
				]

				bot.editMessageMedia(
					chat_id, message_id,
					media = InputMediaPhoto(
						url['picture_xl'],
						caption = (
							send_image_artist_query
							% (
								url['name'],
								url['nb_album'],
								url['nb_fan']
							)
						)
					)
				)

			try:
				bot.editMessageReplyMarkup(
					chat_id, message_id,
					reply_markup = InlineKeyboardMarkup(keyboard)
				)
			except error.BadRequest:
				pass

		else:
			tags = query_data.split("_")

			if tags[0] == "Infos with too many bytes":
				bot.answerCallbackQuery(
					query_id,
					translate(
						users[chat_id]['tongue'], query_data
					)
				)

			elif len(tags) == 4:
				bot.answerCallbackQuery(
					query_id,
					(
						tags_query
						% (
							tags[0],
							tags[1],
							tags[2],
							tags[3]
						)
					),
					show_alert = True
				)

			else:
				if ans == "2":
					if users[chat_id]['c_downloads'] == 3:
						bot.answerCallbackQuery(
							query_id,
							translate(
								users[chat_id]['tongue'], "Wait the end and repeat the step, did you think you could download how much songs you wanted? ;)"
							),
							show_alert = True
						)

						return
					else:
						users[chat_id]['c_downloads'] += 1

				bot.answerCallbackQuery(
					query_id,
					translate(
						users[chat_id]['tongue'], "Song is downloading"
					)
				)

				Link(
					query_data, chat_id,
					users[chat_id]['quality'], message_id
				)
	except TelegramError:
		pass

def download(update, context):
	infos_user = update.effective_user
	chat_id = infos_user.id
	infos_query = update.callback_query
	message_id = infos_query.message.message_id
	query_data = infos_query.data
	query_id = infos_query.id

	if not authorized(chat_id):
		return

	try:
		tongue = infos_user.language_code
	except AttributeError:
		tongue = "en"

	init_user(chat_id, tongue)

	Thread(
		target = inline,
		args = (
			message_id, chat_id,
			query_data, query_id, tongue
		)
	).start()

def search(update, context):
	infos_user = update.effective_user
	chat_id = infos_user.id
	infos_query = update.inline_query
	query_string = infos_query.query
	query_id = infos_query.id

	if not authorized(chat_id):
		return

	try:
		tongue = infos_user.language_code
	except AttributeError:
		tongue = "en"

	init_user(chat_id, tongue)

	if ".chart." == query_string:
		search1 = request(api_chart).json()

		result = [
			InlineQueryResultArticle(
				id = a['link'],
				title = a['title'],
				description = (
					"Artist: {}\nAlbum: {}".format(
						a['artist']['name'],
						a['album']['title']
					)
				),
				thumb_url = a['album']['cover_big'],
				input_message_content = InputTextMessageContent(a['link'])
			) for a in search1['tracks']['data']
		]

		result += [
			InlineQueryResultArticle(
				id = "https://www.deezer.com/album/%d" % a['id'],
				title = "%s (Album)" %  a['title'],
				description = (
					"Artist: {}\nPosition: {}".format(
						a['artist']['name'],
						a['position']
					)
				),
				thumb_url = a['cover_big'],
				input_message_content = InputTextMessageContent(
					"https://www.deezer.com/album/%d" % a['id']
				)
			) for a in search1['albums']['data']
		]

		result += [
			InlineQueryResultArticle(
				id = a['link'],
				title = a['name'],
				description = "Position: %d" % a['position'],
				thumb_url = a['picture_big'],
				input_message_content = InputTextMessageContent(a['link'])
			) for a in search1['artists']['data']
		]

		result += [
			InlineQueryResultArticle(
				id = a['link'],
				title = a['title'],
				description = (
					"N° tracks: {}\nUser: {}".format(
						a['nb_tracks'],
						a['user']['name']
					)
				),
				thumb_url = a['picture_big'],
				input_message_content = InputTextMessageContent(a['link'])
			) for a in search1['playlists']['data']
		]
	else:
		query_string = query_string.replace("#", "")
		search = query_string
		method = ""

		if "alb:" in query_string or "art:" in query_string or "pla:" in query_string:
			search = query_string.split(query_string[:4])[-1]
	
			if "alb:" in query_string:
				method = "album"
			elif "art:" in query_string:
				method = "artist"
			elif "pla:" in query_string:
				method = "playlist"

			search1 = request(
				api_type1.format(method, search)
			).json()

			try:
				if search1['error']:
					return
			except KeyError:
				pass

			if "alb:" in query_string:
				result = [
					InlineQueryResultArticle(
						id = a['link'],
						title = a['title'],
						description = (
							"Artist: {}\nTracks: {}".format(
								a['artist']['name'],
								a['nb_tracks']
							)
						),
						thumb_url = a['cover_big'],
						input_message_content = InputTextMessageContent(a['link'])
					) for a in search1['data']
				]

			elif "art:" in query_string:
				result = [
					InlineQueryResultArticle(
						id = a['link'],
						title = a['name'],
						description = (
							"Albums: {}\nFollowers: {}".format(
								a['nb_album'],
								a['nb_fan']
							)
						),
						thumb_url = a['picture_big'],
						input_message_content = InputTextMessageContent(a['link'])
					) for a in search1['data']
				]

			elif "pla:" in query_string:
				result = [
					InlineQueryResultArticle(
						id = a['link'],
						title = a['title'],
						description = (
							"N° tracks: {}\nUser: {}".format(
								a['nb_tracks'],
								a['user']['name']
							)
						),
						thumb_url = a['picture_big'],
						input_message_content = InputTextMessageContent(a['link'])
					) for a in search1['data']
				]
		else:
			if "lbl:" in query_string or "trk:" in query_string:
				search = query_string.split(query_string[:4])[-1]

				if "lbl:" in query_string:
					method = "label"

				elif "trk:" in query_string:
					method = "track"

			search1 = request(
				api_type2.format(method, search)
			).json()

			try:
				if search1['error']:
					return
			except KeyError:
				pass

			result = [
				InlineQueryResultArticle(
					id = a['link'],
					title = a['title'],
					description = (
						"Artist: {}\nAlbum: {}".format(
							a['artist']['name'],
							a['album']['title']
						)
					),
					thumb_url = a['album']['cover_big'],
					input_message_content = InputTextMessageContent(a['link'])
				) for a in search1['data']
			]

			already = []

			for a in search1['data']:
				ids = a['album']['id']

				if not ids in already:
					result += [
						InlineQueryResultArticle(
							id = ids,
							title = "%s (Album)" % a['album']['title'],
							description = a['artist']['name'],
							thumb_url = a['album']['cover_big'],
							input_message_content = InputTextMessageContent(
								"https://www.deezer.com/album/%d" % a['album']['id']
							)
						)
					]

					already.append(ids)

	try:
		bot.answerInlineQuery(query_id, result)
	except (error.BadRequest, error.TimedOut):
		pass

def menu(update, context):
	global free

	infos_chat = update.effective_chat
	chat_id = infos_chat.id
	infos_message = update.effective_message
	date = infos_message.date.timestamp()
	text = infos_message.text
	caption = infos_message.caption
	message_id = infos_message.message_id
	is_audio = infos_message.audio
	is_voice = infos_message.voice
	things = infos_message.entities
	infos_user = update.effective_user

	if not authorized(chat_id, date):
		return

	if not text:
		text = caption

	if not view_db(user_exist % chat_id):
		statisc(chat_id, "USERS")

		bot.sendMessage(
			chat_id, help_message,
			reply_markup = InlineKeyboardMarkup(first_time_keyboard)
		)

		return

	try:
		tongue = infos_user.language_code
	except AttributeError:
		tongue = "en"

	init_user(chat_id, tongue)

	if text == "/start":
		sendPhoto(
			chat_id, open(photo, "rb"),
			start_message
		)

		keyboard = [
			[
				InlineKeyboardButton(
					queries['s_art']['text'],
					switch_inline_query_current_chat = queries['s_art']['query'] % ""
				),
				InlineKeyboardButton(
					queries['s_alb']['text'],
					switch_inline_query_current_chat = queries['s_alb']['query'] % ""
				)
			],
			[
				InlineKeyboardButton(
					queries['s_pla']['text'],
					switch_inline_query_current_chat = queries['s_pla']['query'] % ""
				),
				InlineKeyboardButton(
						queries['s_lbl']['text'],
						switch_inline_query_current_chat = queries['s_lbl']['query'] % ""
					)
			],
			[
				InlineKeyboardButton(
					queries['s_trk']['text'],
					switch_inline_query_current_chat = queries['s_trk']['query'] % ""
				),
				InlineKeyboardButton(
					queries['s_']['text'],
					switch_inline_query_current_chat = queries['s_']['query'] % ".chart."
				)
			],
		]

		sendMessage(
			chat_id, "Choose what you prefer",
			reply_markup = InlineKeyboardMarkup(keyboard)
		)

	elif text == "/info":
		sendMessage(
			chat_id,
			info_msg
			% (
				version,
				bot_name,
				creator,
				donation_link,
				group_link,
				statisc(chat_id, "USERS"),
				statisc(chat_id, "TRACKS")
			)
		)

	elif text == "/settings":
		sendMessage(
			chat_id, "Settings",
			reply_markup = InlineKeyboardMarkup(
				create_keyboard(settingss, chat_id)
			)
		)

	elif text == "/shazam":
		sendMessage(chat_id, "Send the audio or voice message to identify the song")

	elif text == "/help":
		bot.sendMessage(chat_id, help_message)

	elif is_audio or is_voice:
		if is_audio:
			file_id = is_audio['file_id']
		else:
			file_id = is_voice['file_id']

		Thread(
			target = Audio,
			args = (file_id, chat_id)
		).start()

	elif text:
		if chat_id in roots and "the cat is on the table" in text:
			what = text.split("the cat is on the table ")[-1]

			if what == "1":
				free = 1

			elif what == "0":
				free = 0

		elif len(things) == 0:
			keyboard = [
				[
					InlineKeyboardButton(
						queries['s_art']['text'],
						switch_inline_query_current_chat = queries['s_art']['query'] % text
					),
					InlineKeyboardButton(
						queries['s_alb']['text'],
						switch_inline_query_current_chat = queries['s_alb']['query'] % text
					)
				],
				[
					InlineKeyboardButton(
						queries['s_pla']['text'],
						switch_inline_query_current_chat = queries['s_pla']['query'] % text
					),
					InlineKeyboardButton(
							queries['s_lbl']['text'],
							switch_inline_query_current_chat = queries['s_lbl']['query'] % text
						)
				],
				[
					InlineKeyboardButton(
						queries['s_trk']['text'],
						switch_inline_query_current_chat = queries['s_trk']['query'] % text
					),
					InlineKeyboardButton(
						queries['s_']['text'],
						switch_inline_query_current_chat = queries['s_']['query'] % text
					)
				],
			]

			sendMessage(chat_id, "Press",
				reply_markup = InlineKeyboardMarkup(keyboard)
			)

		else:
			if ans == "2" and users[chat_id]['c_downloads'] == 3:
				sendMessage(chat_id, "Wait the end and repeat the step, did you think you could download how much songs you wanted? ;)")
			else:
				if ans == "2":
					users[chat_id]['c_downloads'] += 1
				
				linked = infos_message.parse_entity(things[0])
				
				Thread(
					target = Link,
					args = (
						linked, chat_id,
						users[chat_id]['quality'], message_id
					)
				).start()

try:
	print("1): Free")
	print("2): Strict")
	ans = input("Choose: ")

	if ans == "1" or ans == "2":
		for a in comandss:
			sets.dispatcher.add_handler(
				CommandHandler(a, menu)
			)

		sets.dispatcher.add_handler(
			MessageHandler(
				Filters.audio |
				Filters.text |
				Filters.voice |
				Filters.photo,
				menu
			)
		)

		sets.dispatcher.add_handler(
			InlineQueryHandler(search)
		)

		sets.dispatcher.add_handler(
			CallbackQueryHandler(download)
		)

		sets.start_polling()
	else:
		raise KeyboardInterrupt

	print("Bot started")

	while True:
		sleep(1)
		path = os.statvfs("/")
		free_space = path.f_bavail * path.f_frsize

		if (del1 <= del2 and is_audio == 0) or free_space <= limit:
			del1 = 0
			del2 = 0

			for a in os.listdir(loc_dir):
				try:
					rmtree(loc_dir + a)
				except NotADirectoryError:
					os.remove(loc_dir + a)
				except OSError:
					pass
except KeyboardInterrupt:
	print("\nSTOPPING...")
	sets.stop()
	os.rmdir(loc_dir)
	exit()
