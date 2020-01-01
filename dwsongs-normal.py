#!/usr/bin/python3

import os
import telepot
import logging
import dwytsongs
from time import sleep
from shutil import rmtree
from pprint import pprint
from spotipy import Spotify
from mutagen.mp3 import MP3
from threading import Thread
from mutagen.flac import FLAC
from bs4 import BeautifulSoup
from acrcloud import ACRcloud
from requests import post, get
import spotipy.oauth2 as oauth2
from mutagen.easyid3 import EasyID3
from configparser import ConfigParser
from deezloader import Login, exceptions
from sqlite3 import connect, OperationalError
from mutagen.id3._util import ID3NoHeaderError

from telepot.namedtuple import (
	ReplyKeyboardMarkup, KeyboardButton,
	ReplyKeyboardRemove, InlineKeyboardMarkup,
	InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent
)

path = os.getcwd()
setting = path + "/DeezloaderAn0n_bot/setting.ini"
config = ConfigParser()
config.read(setting)

#Path to Download the Songs
local = "/media/pimedia/Deezloader/"

try:
	deezer_token = config['login']['token']
	bot_token = config['bot']['token']
	acrcloud_key = config['acrcloud']['key']
	acrcloud_hash = config['acrcloud']['secret']
	acrcloud_host = config['acrcloud']['host']
	ya_key = config['yandex']['key']
	version = config['bot_info']['version']
	creator = config['bot_info']['creator']
	donation_link = config['bot_info']['donation']
	group_link = config['bot_info']['group']
except KeyError:
	print("Something went wrong with configuration file")
	exit()

downloa = Login(deezer_token)
bot = telepot.Bot(bot_token)
bot_name = bot.getMe()['username']
users = {}
date = {}
del1 = 0
del2 = 0
free = 1
default_time = 0
is_audio = 0
root = 560950095
telegram_audio_api_limit = 50000000
send_image_track_query = "?? Track: %s \n?? Artist: %s \n?? Album: %s \n?? Date: %s"
send_image_album_query = "?? Album: %s \n?? Artist: %s \n?? Date: %s \n?? Tracks amount: %d"
send_image_playlist_query = "?? Creation: %s \n?? User: %s \n?? Tracks amount: %d"
insert_query = "INSERT INTO DWSONGS (id, query, quality) values ('%s', '%s', '%s')"
where_query = "SELECT query FROM DWSONGS WHERE id = '{}' and quality = '{}'"
db_file = local + "dwsongs.db"
loc_dir = local + "Songs/"

config = {
	"key": acrcloud_key,
	"secret": acrcloud_hash,
	"host": acrcloud_host
}

acrcloud = ACRcloud(config)

logging.basicConfig(
	filename = "dwsongs.log",
	level = logging.WARNING,
	format = "%(asctime)s %(levelname)s %(name)s %(message)s"
)

if not os.path.isdir(loc_dir):
	os.makedirs(loc_dir)

conn = connect(db_file)
c = conn.cursor()

try:
	c.execute("CREATE TABLE DWSONGS (id text, query text, quality text)")
	c.execute("CREATE TABLE BANNED (banned int)")
	c.execute("CREATE TABLE CHAT_ID (chat_id int)")
	conn.commit()
except OperationalError:
	pass

def generate_token():
	return oauth2.SpotifyClientCredentials(
		client_id = "c6b23f1e91f84b6a9361de16aba0ae17",
		client_secret = "237e355acaa24636abc79f1a089e6204"
	).get_access_token()

spo = Spotify(
	generate_token()
)

def request(url, chat_id = None, control = False):
	try:
		thing = get(url)
	except:
		thing = get(url)

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

def init_user(chat_id, msg):
	try:
		users[chat_id]
	except KeyError:
		try:
			langua = msg['from']['language_code']
		except KeyError:
			langua = "en"

		users[chat_id] = {
			"quality": "MP3_320",
			"tongue": langua,
			"c_downloads": 0,

		}

def translate(language, sms):
	try:
		language = language.split("-")[0]

		if not "en" in language:
			api = (
				"https://translate.yandex.net/api/v1.5/tr.json/translate?key=%s&text=%s&lang=en-%s"
				% (
					ya_key,
					sms,
					language
				)
			)

			sms = request(api).json()['text'][0]
	except:
		pass

	return sms

def delete(chat_id):
	global del2

	del2 += 1

	if ans == "2":
		users[chat_id]['c_downloads'] -= 1

def write_db(execution):
	conn = connect(db_file)
	c = conn.cursor()

	while True:
		sleep(1)

		try:
			c.execute(execution)
			conn.commit()
			conn.close()
			break
		except OperationalError:
			pass

def check_image(image1, ids):
	if not image1:
		URL = "https://www.deezer.com/track/%s" % ids
		body = request(URL).text

		image1 = (
			BeautifulSoup(body, "html.parser")
			.find("meta", property = "og:image")
			.get("content")
			.replace("500x500", "1000x1000")
		)

	ima = request(image1).content

	if len(ima) == 13:
		image1 = "https://e-cdns-images.dzcdn.net/images/cover/1000x1000-000000-80-0-0.jpg"
	
	return image1

def sendall(msg):
	conn = connect(db_file)
	c = conn.cursor()
	alls = c.execute("SELECT chat_id FROM CHAT_ID").fetchall()
	conn.close()

	for a in alls:
		sendMessage(a[0], msg)

def statisc(chat_id, do):
	conn = connect(db_file)
	c = conn.cursor()

	if do == "USERS":
		c.execute("SELECT chat_id FROM CHAT_ID where chat_id = '%d'" % chat_id)

		if not c.fetchone():
			write_db("INSERT INTO CHAT_ID (chat_id) values ('%d')" % chat_id)

		c.execute("SELECT chat_id FROM CHAT_ID")

	elif do == "TRACKS":
		c.execute("SELECT id FROM DWSONGS")

	infos = len(
		c.fetchall()
	)

	conn.close()
	return infos

def check_flood(chat_id, time_now = 0):
	conn = connect(db_file)
	c = conn.cursor()
	exist = c.execute("SELECT banned FROM BANNED where banned = '%d'" % chat_id).fetchone()
	conn.close()

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
					write_db("INSERT INTO BANNED (banned) values ('%d')" % chat_id)
					del date[chat_id]
					sendMessage(chat_id, "You are banned :)")
	except KeyError:
		date[chat_id] = {
			"time": time_now,
			"tries": 3,
			"msg": 0
		}

def sendMessage(chat_id, text, reply_markup = None, reply_to_message_id = None):
	sleep(default_time)

	try:
		bot.sendMessage(
			chat_id,
			translate(
				users[chat_id]['tongue'], text
			),
			reply_markup = reply_markup,
			reply_to_message_id = reply_to_message_id
		)
	except:
		pass

def sendPhoto(chat_id, photo, caption = None, reply_markup = None):
	sleep(default_time)

	try:
		bot.sendChatAction(chat_id, "upload_photo")

		bot.sendPhoto(
			chat_id,
			photo,
			caption = caption,
			reply_markup = reply_markup
		)
	except:
		pass

def sendAudio(chat_id, audio, link = None, image = None, youtube = False):
	sleep(default_time)

    try:
		bot.sendChatAction(chat_id, "upload_audio")

		if os.path.isfile(audio):
			try:
				tag = EasyID3(audio)
				duration = MP3(audio).info.length
			except ID3NoHeaderError:
				tag = FLAC(audio)
				duration = tag.info.length

			if os.path.getsize(audio) < telegram_audio_api_limit:
				data = {
					"chat_id": chat_id,
					"duration": int(duration),
					"performer": tag['artist'][0],
					"title": tag['title'][0]
				}

				file_param = {
					"audio": open(audio, "rb"),
					"thumb": image

				}

				url = "https://api.telegram.org/bot%s/sendAudio" % bot_token

				try:
					request = post(
						url,
						params = data,
						files = file_param,
						timeout = 40
					)
				except:
					request = post(
						url,
						params = data,
						files = file_param,
						timeout = 40
					)

				file_id = request.json()['result']['audio']['file_id']
			
				if not youtube:
					quality = (
						audio
						.split("(")[-1]
						.split(")")[0]
					)

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
				sendMessage(chat_id, "Song too be to be sent :(")
		else:
			bot.sendAudio(chat_id, audio)

	except telepot.exception.TelegramError:
		sendMessage(chat_id, "Sorry the track %s doesn't seem readable on Deezer :(" % link)

def track(link, chat_id, quality):
	global spo

	conn = connect(db_file)
	c = conn.cursor()
	lin = "track/%s" % link.split("/")[-1]
	qua = quality.split("MP3_")[-1]

	match = c.execute(
		where_query.format(lin, qua)
	).fetchone()

	conn.close()

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
					image = "https://e-cdns-images.dzcdn.net/images/cover/90x90-000000-80-0-0.jpg"

				z = downloa.download_trackspo(
					link,
					quality = quality,
					recursive_quality = True,
					recursive_download = True,
					not_interface = True
				)

			elif "deezer" in link:
				ids = link.split("/")[-1]

				try:
					url = request(
						"https://api.deezer.com/track/%s" % ids, chat_id, True
					).json()['album']['cover_xl']
				except AttributeError:
					return

				image = check_image(url, ids).replace("1000x1000", "90x90")

				z = downloa.download_trackdee(
					link,
					quality = quality,
					recursive_quality = True,
					recursive_download = True,
					not_interface = True
				)
		except (exceptions.TrackNotFound, exceptions.NoDataApi):
			sendMessage(chat_id, "Track doesn't %s exist on Deezer or maybe it isn't readable, it'll be downloaded from YouTube..." % link)

			try:
				if "spotify" in link:
					z = dwytsongs.download_trackspo(
						link,
						recursive_download = True,
						not_interface = True
					)

				elif "deezer" in link:
					z = dwytsongs.download_trackdee(
						link,
						recursive_download = True,
						not_interface = True
					)

				youtube = True
			except:
				sendMessage(chat_id, "Sorry I cannot download this song %s :(" % link)
				return

		image = request(image).content
		sendAudio(chat_id, z, link, image, youtube)

def Link(link, chat_id, quality, msg):
	global spo
	global del1

	del1 += 1
	done = 0
	links1 = []
	links2 = []
	quali = quality.split("MP3_")[-1]
	link = link.split("?")[0]

	try:
		if "spotify" in link:
			if "track/" in link:
				try:
					url = spo.track(link)
				except Exception as a:
					if not "The access token expired" in str(a):
						sendMessage(
							chat_id, "Invalid link %s ;)" % link,
							reply_to_message_id = msg['message_id']
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
					image1 = "https://e-cdns-images.dzcdn.net/images/cover/1000x1000-000000-80-0-0.jpg"

				sendPhoto(
					chat_id, image1,
					caption = (
						send_image_track_query
						% (
							url['name'],
							url['album']['artists'][0]['name'],
							url['album']['name'],
							url['album']['release_date']
						)
					)
				)

				track(link, chat_id, quality)

			elif "album/" in link:
				try:
					tracks = spo.album(link)
				except Exception as a:
					if not "The access token expired" in str(a):
						sendMessage(
							chat_id, "Invalid link %s ;)" % link,
							reply_to_message_id = msg['message_id']
						)

					delete(chat_id)
					return

					spo = Spotify(
						generate_token()
					)

					tracks = spo.album(link)

				try:
					image3 = tracks['images'][2]['url']
					image2 = tracks['images'][1]['url']
					image1 = tracks['images'][0]['url']
				except IndexError:
					image3 = "https://e-cdns-images.dzcdn.net/images/cover/90x90-000000-80-0-0.jpg"
					image2 = "https://e-cdns-images.dzcdn.net/images/cover/320x320-000000-80-0-0.jpg"
					image1 = "https://e-cdns-images.dzcdn.net/images/cover/1000x1000-000000-80-0-0.jpg"

				tot = tracks['total_tracks']
				conn = connect(db_file)
				c = conn.cursor()
				lin = "album/%s" % link.split("/")[-1]
				count = [0]

				sendPhoto(
					chat_id, image1,
					caption = (
						send_image_album_query
						% (
							tracks['name'],
							tracks['artists'][0]['name'],
							tracks['release_date'],
							tot
						)
					)
				)

				def lazy(a):
					count[0] += a['duration_ms']
					lin = "track/%s" % a['external_urls']['spotify'].split("/")[-1]

					c.execute(
						where_query.format(lin, quali)
					)

					links2.append(lin)

					if c.fetchone():
						links1.append(lin)

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

				conn.close()

				if (count[0] / 1000) > 40000:
					sendMessage(chat_id, "If you do this again I will come to your home and I will ddos your ass :)")
					delete(chat_id)
					return

				if len(links1) != tot:
					z = downloa.download_albumspo(
						link,
						quality = quality,
						recursive_quality = True,
						recursive_download = True,
						not_interface = True
					)
				else:
					for a in links2:
						track(a, chat_id, quality)

				done = 1

			elif "playlist/" in link:
				musi = link.split("/")

				try:
					tracks = spo.user_playlist(musi[-3], musi[-1])
				except Exception as a:
					if not "The access token expired" in str(a):
						sendMessage(
							chat_id, "Invalid link ;)",
							reply_to_message_id = msg['message_id']
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
					image1 = "https://e-cdns-images.dzcdn.net/images/cover/1000x1000-000000-80-0-0.jpg"

				tot = tracks['tracks']['total']

				if tot > 400:
					sendMessage(chat_id, "Fuck you")
					delete(chat_id)
					return

				sendPhoto(
					chat_id, image1,
					caption = (
						send_image_playlist_query
						% (
							tracks['tracks']['items'][0]['added_at'],
							tracks['owner']['display_name'],
							tot
						)
					)
				)

				def lazy(a):
					try:
						track(
							a['track']['external_urls']['spotify'],
							chat_id,
							quality
						)
					except:
						try:
							sendMessage(chat_id, "%s Not found :(" % a['track']['name'])
						except:
							sendMessage(chat_id, "Error :(")

				for a in tracks['tracks']['items']:
					lazy(a)

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

				done = 1

			else:
				sendMessage(chat_id, "Sorry :( The bot doesn't support this link")

		elif "deezer" in link:
			ids = link.split("/")[-1]

			if "track/" in link:
				try:
					url = request(
						"https://api.deezer.com/track/%s" % ids, chat_id, True
					).json()
				except AttributeError:
					delete(chat_id)
					return

				image1 = check_image(
					url['album']['cover_xl'], ids
				)

				sendPhoto(
					chat_id, image1,
					caption = (
						send_image_track_query
						% (
							url['title'],
							url['artist']['name'],
							url['album']['title'],
							url['album']['release_date']
						)
					)
				)

				track(link, chat_id, quality)

			elif "album/" in link:
				try:
					url = request(
						"https://api.deezer.com/album/%s" % ids, chat_id, True
					).json()
				except AttributeError:
					delete(chat_id)
					return

				if url['duration'] > 40000:
					sendMessage(chat_id, "If you do this again I will come to your home and I will ddos your ass :)")
					delete(chat_id)
					return

				image1 = url['cover_xl']

				if not image1:
					URL = "https://www.deezer.com/album/%s" % ids
					image1 = request(URL).text

					image1 = (
						BeautifulSoup(image1, "html.parser")
						.find("img", class_ = "img_main")
						.get("src")
						.replace("200x200", "1000x1000")
					)

				ima = request(image1).content

				if len(ima) == 13:
					image1 = "https://e-cdns-images.dzcdn.net/images/cover/1000x1000-000000-80-0-0.jpg"

				image2 = image1.replace("1000x1000", "320x320")
				image3 = image1.replace("1000x1000", "90x90")
				conn = connect(db_file)
				c = conn.cursor()
				lin = "album/%s" % ids

				for a in url['tracks']['data']:
					lin = "track/%s" % a['link'].split("/")[-1]

					c.execute(
						where_query.format(lin, quali)
					)

					links2.append(lin)

					if c.fetchone():
						links1.append(lin)

				conn.close()
				tot = url['nb_tracks']

				sendPhoto(
					chat_id, image1,
					caption = (
						send_image_album_query
						% (
							url['title'],
							url['artist']['name'],
							url['release_date'],
							tot
						)
					)
				)

				if len(links1) != tot:
					z = downloa.download_albumdee(
						link,
						quality = quality,
						recursive_quality = True,
						recursive_download = True,
						not_interface = True
					)
				else:
					for a in links2:
						track(a, chat_id, quality)

				done = 1

			elif "playlist/" in link:
				try:
					url = request(
						"https://api.deezer.com/playlist/%s" % ids, chat_id, True
					).json()
				except AttributeError:
					delete(chat_id)
					return

				tot = url['nb_tracks']

				if tot > 400:
					sendMessage(chat_id, "Fuck you")
					delete(chat_id)
					return

				sendPhoto(
					chat_id, url['picture_xl'],
					caption = (
						send_image_playlist_query
						% (
							url['creation_date'],
							url['creator']['name'],
							tot
						)
					)
				)

				for a in url['tracks']['data']:
					try:
						track(a['link'], chat_id, quality)
					except:
						song = "{} - {}".format(a['title'], a['artist']['name'])
						sendMessage(chat_id, "Cannot download %s :(" % song)

				done = 1

			elif "artist/" in link:
				link = "https://api.deezer.com/artist/%s" % ids

				try:
					url = request(link, chat_id, True).json()
				except AttributeError:
					delete(chat_id)
					return

				sendPhoto(
					chat_id, url['picture_xl'],
					caption = (
						"?? Artist: %s \n?? Album numbers: %d \n?? Fans on Deezer: %d"
						% (
							url['name'],
							url['nb_album'],
							url['nb_fan']
						)
					),
					reply_markup = InlineKeyboardMarkup(
						inline_keyboard = [
							[
								InlineKeyboardButton(
									text = "TOP 30 ??",
									callback_data = "%s/top?limit=30" % link
								),
								InlineKeyboardButton(
									text = "ALBUMS ??",
									callback_data = "%s/albums" % link
								)
							],
							[
								InlineKeyboardButton(
									text = "RADIO ??",
									callback_data = "%s/radio" % link
								),
								InlineKeyboardButton(
									text = "RELATED ??",
									callback_data = "%s/related" % link
								)
							]
						]
					)
				)

			else:
				sendMessage(chat_id, "Sorry :( The bot doesn't support this link %s :(" % link)

		else:
			sendMessage(chat_id, "Sorry :( The bot doesn't support this link %s :(" % link)

		try:
			image3 = request(image3).content

			for a in range(
				len(z)
			):
				sendAudio(chat_id, z[a], links2[a], image3)
		except NameError:
			pass

	except exceptions.QuotaExceeded:
		sendMessage(chat_id, "Please send the link %s again :(" % link)

	except exceptions.AlbumNotFound:
		sendMessage(chat_id, "Album %s didn't find on Deezer :(" % link)
		sendMessage(chat_id, "Try to search it throught inline mode or search the link on Deezer")

	except Exception as a:
		logging.warning(a)
		logging.warning(quality)
		logging.warning(link)

		sendMessage(
			chat_id, "OPS :( Something went wrong please send to @An0nimia this link: {} {}, if this happens again".format(link, quality)
		)

	if done == 1:
		sendMessage(
			chat_id, "FINISHED :) Rate me here https://t.me/BotsArchive/298",
			reply_to_message_id = msg['message_id'],
			reply_markup = InlineKeyboardMarkup(
				inline_keyboard = [
					[
						InlineKeyboardButton(
							text = "SHARE",
							url = "tg://msg?text=Start @%s for download all the songs which you want ;)" % bot_name
						)
					]
				]
			)
		)

	delete(chat_id)

def Audio(audio, chat_id):
	global spo
	global is_audio

	is_audio = 1
	audi = "{}{}.ogg".format(loc_dir, audio)

	try:
		bot.download_file(audio, audi)
	except telepot.exception.TelegramError:
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

	artist = audio['metadata']['music'][0]['artists'][0]['name']
	track = audio['metadata']['music'][0]['title']
	album = audio['metadata']['music'][0]['album']['name']

	try:
		date = audio['metadata']['music'][0]['release_date']
		album += "_%s" % date
	except KeyError:
		album += "_"

	try:
		label = audio['metadata']['music'][0]['label']
		album += "_%s" % label
	except KeyError:
		album += "_"

	try:
		genre = audio['metadata']['music'][0]['genres'][0]['name']
		album += "_%s" % genre
	except KeyError:
		album += "_"

	if len(album) > 64:
		album = "Infos with too many bytes"

	try:
		song = "{} - {}".format(track, artist)
		
		url = request(
			"https://api.deezer.com/search/track/?q=%s" % song.replace("#", ""), chat_id, True
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
			ids = "https://open.spotify.com/track/%s" % audio['metadata']['music'][0]['external_metadata']['spotify']['track']['id']

			try:
				url = spo.track(ids)
			except:
				spo = Spotify(
					generate_token()
				)

				url = spo.track(ids)

			image = url['album']['images'][0]['url']
		except KeyError:
			pass

		try:
			ids = "https://api.deezer.com/track/%s" % audio['metadata']['music'][0]['external_metadata']['deezer']['track']['id']

			try:
				url = request(ids, chat_id, True).json()
			except AttributeError:
				return

			image = url['album']['cover_xl']
		except KeyError:
			pass

	try:
		sendPhoto(
			chat_id, image,
			caption = "{} - {}".format(track, artist),
			reply_markup = InlineKeyboardMarkup(
				inline_keyboard = [
					[
						InlineKeyboardButton(
							text = "Download ??",
							callback_data = ids
						),
						InlineKeyboardButton(
							text = "Info ?",
							callback_data = album
						)
					]
				]
			)
		)
	except:
		sendMessage(chat_id, "Error :(")

def inline(msg, from_id, query_data, query_id):
	if "artist" in query_data:
		message_id = msg['message']['message_id']
		keyboard = []
		link = "https://api.deezer.com/artist/%s" % query_data.split("/")[4]

		try:
			url = request(
				query_data.replace("down", ""),
				from_id, True
			).json()
		except AttributeError:
			return

		if "album" in query_data:
			keyboard += [
				[
					InlineKeyboardButton(
						text = "{} - {}".format(a['title'], a['release_date']),
						callback_data = a['link']
					)
				] for a in url['data']
			]

			keyboard.append(
				[
					InlineKeyboardButton(
						text = "BACK ??",
						callback_data = link
					)
				]
			)

		elif "down" in query_data:
			if ans == "2":
				if users[from_id]['c_downloads'] == 3:
					bot.answerCallbackQuery(
						query_id,
						translate(
							users[from_id]['tongue'],
							"Wait the end and repeat the step, did you think you could download how much songs you wanted? ;)"
						),
						show_alert = True
					)

					return
				else:
					users[from_id]['c_downloads'] += 1

			bot.answerCallbackQuery(
				query_id,
				translate(
					users[from_id]['tongue'], "Songs are downloading ??"
				)
			)

			for a in url['data']:
				Link(
					"https://www.deezer.com/track/%d" % a['id'],
					from_id,
					users[from_id]['quality'],
					msg['message']
				)

				if ans == "2":
					users[from_id]['c_downloads'] += 1

			if ans == "2":
				users[from_id]['c_downloads'] -= 1

		elif "radio" in query_data or "top" in query_data:
			if "radio" in query_data:
				method = "radio"
			else:
				method = "top?limit=30"

			keyboard += [
				[
					InlineKeyboardButton(
						text = "{} - {}".format(a['artist']['name'], a['title']),
						callback_data = "https://www.deezer.com/track/%d" % a['id']
					)
				] for a in url['data']
			]

			keyboard.append(
				[
					InlineKeyboardButton(
						text = "GET ALL ??",
						callback_data = "{}/{}/down".format(link, method)
					)
				]
			)

			keyboard.append(
				[
					InlineKeyboardButton(
						text = "BACK ??",
						callback_data = link
					)
				]
			)

		elif "related" in query_data:
			keyboard = [
				[
					InlineKeyboardButton(
						text = "{}- {}".format(a['name'], a['nb_fan']),
						callback_data = "https://api.deezer.com/artist/%d" % a['id']
					)
				] for a in url['data']
			]

			keyboard.append(
				[
					InlineKeyboardButton(
						text = "BACK ??",
						callback_data = link
					)
				]
			)

		else:
			bot.deleteMessage(
				(
					from_id, message_id

				)
			)

			keyboard = [
				[
					InlineKeyboardButton(
						text = "TOP 30 ??",
						callback_data = "%s/top?limit=30" % link
					),
					InlineKeyboardButton(
						text = "ALBUMS ??",
						callback_data = "%s/albums" % link
					)
				],
				[
					InlineKeyboardButton(
						text = "RADIO ??",
						callback_data = "%s/radio" % link
					),
					InlineKeyboardButton(
						text = "RELATED ??",
						callback_data = "%s/related" % link
					)
				]
			]

			sendPhoto(
				from_id, url['picture_xl'],
				caption = (
					"?? Artist: %s \n?? Album numbers: %d \n?? Fans on Deezer: %d"
					% (
						url['name'],
						url['nb_album'],
						url['nb_fan']
					)
				),
				reply_markup = InlineKeyboardMarkup(
					inline_keyboard = keyboard
				)
			)

		try:
			bot.editMessageReplyMarkup(
				(
					(
						from_id, message_id
					)
				),
				reply_markup = InlineKeyboardMarkup(
					inline_keyboard = keyboard
				)
			)
		except telepot.exception.TelegramError:
			pass
	else:
		tags = query_data.split("_")

		if tags[0] == "Infos with too many bytes":
			bot.answerCallbackQuery(
				query_id,
				translate(
					users[from_id]['tongue'], query_data
				)
			)

		elif len(tags) == 4:
			bot.answerCallbackQuery(
				query_id,
				text = (
					"?? Album: %s\n?? Date: %s\n?? Label: %s\n?? Genre: %s"
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
				if users[from_id]['c_downloads'] == 3:
					bot.answerCallbackQuery(
						query_id,
						translate(
							users[from_id]['tongue'], "Wait the end and repeat the step, did you think you could download how much songs you wanted? ;)"
						),
						show_alert = True
					)

					return
				else:
					users[from_id]['c_downloads'] += 1

			bot.answerCallbackQuery(
				query_id,
				translate(
					users[from_id]['tongue'], "Song is downloading"
				)
			)

			Link(
				query_data, from_id,
				users[from_id]['quality'], msg['message']
			)

def download(msg):
	query_id, from_id, query_data = telepot.glance(msg, flavor = "callback_query")
	init_user(from_id, msg)

	Thread(
		target = inline,
		args = (
			msg, from_id,
			query_data, query_id
		)
	).start()

def search(msg):
	query_id, from_id, query_string = telepot.glance(msg, flavor = "inline_query")

	if check_flood(from_id) == "BANNED":
		return

	init_user(from_id, msg)

	if "" == query_string:
		search1 = request("https://api.deezer.com/chart").json()

		result = [
			InlineQueryResultArticle(
				id = a['link'],
				title = a['title'],
				description = a['artist']['name'],
				thumb_url = a['album']['cover_big'],
				input_message_content = InputTextMessageContent(
					message_text = a['link']
				)
			) for a in search1['tracks']['data']
		]

		result += [
			InlineQueryResultArticle(
				id = "https://www.deezer.com/album/%d" % a['id'],
				title = "%s (Album)" %  a['title'],
				description = a['artist']['name'],
				thumb_url = a['cover_big'],
				input_message_content = InputTextMessageContent(
					message_text = "https://www.deezer.com/album/%d" % a['id']
				)
			) for a in search1['albums']['data']
		]

		result += [
			InlineQueryResultArticle(
				id = a['link'],
				title = "%d" % a['position'],
				description = a['name'],
				thumb_url = a['picture_big'],
				input_message_content = InputTextMessageContent(
					message_text = a['link']
				)
			) for a in search1['artists']['data']
		]

		result += [
			InlineQueryResultArticle(
				id = a['link'],
				title = a['title'],
				description = "N° tracks: %d" % a['nb_tracks'],
				thumb_url = a['picture_big'],
				input_message_content = InputTextMessageContent(
					message_text = a['link']
				)
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
					"https://api.deezer.com/search/{}/?q={}".format(method, search)
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
						description = a['artist']['name'],
						thumb_url = a['cover_big'],
						input_message_content = InputTextMessageContent(
							message_text = a['link']
						)
					) for a in search1['data']
				]

			elif "art:" in query_string:
				result = [
					InlineQueryResultArticle(
						id = a['link'],
						title = a['name'],
						thumb_url = a['picture_big'],
						input_message_content = InputTextMessageContent(
							message_text = a['link']
						)
					) for a in search1['data']
				]

			elif "pla:" in query_string:
				result = [
					InlineQueryResultArticle(
						id = a['link'],
						title = a['title'],
						description = "N° tracks: %d" % a['nb_tracks'],
						thumb_url = a['picture_big'],
						input_message_content = InputTextMessageContent(
							message_text = a['link']
						)
					) for a in search1['data']
				]
		else:
			if "lbl:" in query_string or "trk:" in query_string:
				search = query_string.split(query_string[:4])[-1]

				if "lbl:" in query_string:
					method = "label"
				else:
					method = "track"

			search1 = request(
				"https://api.deezer.com/search/?q={}:'{}'".format(method, search)
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
					description = a['artist']['name'],
					thumb_url = a['album']['cover_big'],
					input_message_content = InputTextMessageContent(
						message_text = a['link']
					)
				) for a in search1['data']
			]

			for a in search1['data']:
				try:
					if "https://www.deezer.com/album/%d" % a['album']['id'] in str(result):
						continue
				except KeyError:
					continue

				result += [
					InlineQueryResultArticle(
						id = "https://www.deezer.com/album/%d" % a['album']['id'],
						title = "%s (Album)" % a['album']['title'],
						description = a['artist']['name'],
						thumb_url = a['album']['cover_big'],
						input_message_content = InputTextMessageContent(
							message_text = "https://www.deezer.com/album/%d" % a['album']['id']
						)
					)
				]

	try:
		bot.answerInlineQuery(query_id, result)
	except telepot.exception.TelegramError:
		pass

def nada(msg):
	pass

def start(msg):
	global free

	content_type, chat_type, chat_id = telepot.glance(msg)

	if free == 0 and chat_id != root:
		return

	if check_flood(chat_id, msg['date']) == "BANNED" and chat_id != root:
		return

	pprint(msg)
	statisc(chat_id, "USERS")
	init_user(chat_id, msg)

	if content_type == "text" and msg['text'] == "/start":
		try:
			sendPhoto(
				chat_id, open("example.jpg", "rb"),
				caption = "Welcome to @%s \nPress '/' to get commands list" % bot_name
			)
		except FileNotFoundError:
			pass

		sendMessage(
			chat_id,
			"Press for search what you prefer" +
			"\nP.S. Remember you can do this digiting @ in your keyboard and select %s" % bot_name +
			"\nSend a Deezer or Spotify link to download \nSend a song o vocal message to recognize the track",
			reply_markup = InlineKeyboardMarkup(
				inline_keyboard = [
					[
						InlineKeyboardButton(
							text = "Search by artist ??",
							switch_inline_query_current_chat = "art: "
						),
						InlineKeyboardButton(
							text = "Search by album ??",
							switch_inline_query_current_chat = "alb: "
						)
					],
					[
						InlineKeyboardButton(
							text = "Search playlist ??",
							switch_inline_query_current_chat = "pla: "
						),
						InlineKeyboardButton(
								text = "Search label ??",
								switch_inline_query_current_chat = "lbl: "
							)
					],
					[
						InlineKeyboardButton(
							text = "Search track ??",
							switch_inline_query_current_chat = "trk: "
						),
						InlineKeyboardButton(
							text = "Global search ??",
							switch_inline_query_current_chat = ""
						)
					]
				]
			)
		)

	elif content_type == "text" and msg['text'] == "/translator":
		if users[chat_id]['tongue'] != "en":
			users[chat_id]['tongue'] = "en"
			sendMessage(chat_id, "Now the language is english")
		else:
			users[chat_id]['tongue'] = msg['from']['language_code']
			sendMessage(chat_id, "Now the bot will use the Telegram app language")

	elif content_type == "text" and msg['text'] == "/quality":
		sendMessage(
			chat_id, "Select default download quality\nCURRENTLY: %s ??" % users[chat_id]['quality'],
			reply_markup = ReplyKeyboardMarkup(
				keyboard = [
					[
						KeyboardButton(
							text = "FLAC"
						),
						KeyboardButton(
							text = "MP3_320Kbps"
						)
					],
					[
						KeyboardButton(
							text = "MP3_256Kbps"
						),
						KeyboardButton(
							text = "MP3_128Kbps"
						)
					]
				]
			)
		)

	elif content_type == "text" and (
		msg['text'] == "FLAC" or 
		msg['text'] == "MP3_320Kbps" or 
		msg['text'] == "MP3_256Kbps" or 
		msg['text'] == "MP3_128Kbps"
	):
		users[chat_id]['quality'] = msg['text'].replace("Kbps", "")

		sendMessage(
			chat_id, "Songs will be downloaded in %s quality ??" % msg['text'],
			reply_markup = ReplyKeyboardRemove()
		)

		sendMessage(chat_id, "Songs which cannot be downloaded in quality you have chosen will be downloaded in the best quality possible")

	elif content_type == "voice" or content_type == "audio":
		Thread(
			target = Audio,
			args = (msg[content_type]['file_id'], chat_id)
		).start()

	elif content_type == "text" and msg['text'] == "/info":
		sendMessage(
			chat_id,
			"?? Version: %s \n?? Name: @%s \n?? Creator: @%s \n?? Donation: %s \n?? Forum: %s \n?? Users: %d \n?? Total downloads: %d"
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

	elif content_type == "text" and chat_id == root and "the cat is on the table" in msg['text']:
		what = msg['text'].split("the cat is on the table ")[-1]

		if what == "1":
			free = 1

		elif what == "0":
			free = 0

		else:
			Thread(
				target = sendall,
				args = (what,)
			).start()

	elif content_type == "text":
		text = msg['text'].replace("'", "")

		try:
			msg['entities']

			if ans == "2" and users[chat_id]['c_downloads'] == 3:
				sendMessage(chat_id, "Wait the end and repeat the step, did you think you could download how much songs you wanted? ;)")
			else:
				if ans == "2":
					users[chat_id]['c_downloads'] += 1

				Thread(
					target = Link,
					args = (
						text, chat_id,
						users[chat_id]['quality'], msg
					)
				).start()
		except KeyError:
			sendMessage(chat_id, "Press",
				reply_markup = InlineKeyboardMarkup(
					inline_keyboard = [
						[
							InlineKeyboardButton(
								text = "Search artist ??",
								switch_inline_query_current_chat = "art: %s" % text
							),
							InlineKeyboardButton(
								text = "Search album ??",
								switch_inline_query_current_chat = "alb: %s" % text
							)
						],
						[
							InlineKeyboardButton(
								text = "Search playlist ??",
								switch_inline_query_current_chat = "pla: %s" % text
							),
							InlineKeyboardButton(
								text = "Search label ??",
								switch_inline_query_current_chat = "lbl: %s" % text
							)
						],
						[
							InlineKeyboardButton(
								text = "Search track ??",
								switch_inline_query_current_chat = "trk: %s" % text
							),
							InlineKeyboardButton(
								text = "Search global ??",
								switch_inline_query_current_chat = text
							)
						]
					]
				)
			)

try:
	ans = "1"
	bot.message_loop(
		{
			"chat": start,
			"callback_query": download,
			"inline_query": search,
			"chosen_inline_result": nada
		}
	)

                        

                             
                   
    
                  
                               
                           
                                
    
   
      
        

	print("Bot started")

	while True:
		sleep(1)
		path = os.statvfs("/")
		free_space = path.f_bavail * path.f_frsize

		if (del1 == del2 and is_audio == 0) or free_space <= 4000000000 or del2 > del1:
			del1 = 0
			del2 = 0

                                
        
                        
                              
                           
                   
         
except KeyboardInterrupt:
                  
	print("\nSTOPPED")
