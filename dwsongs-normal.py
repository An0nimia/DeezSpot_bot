#!/usr/bin/python3

import os
import sys
import shutil
import sqlite3
import spotipy
import telepot
import mutagen
import logging
import acrcloud
import requests
import dwytsongs
import deezloader
import configparser
from time import sleep
from pprint import pprint
from mutagen.mp3 import MP3
from threading import Thread
from mutagen.flac import FLAC
from bs4 import BeautifulSoup
import spotipy.oauth2 as oauth2
from mutagen.easyid3 import EasyID3
from telepot.namedtuple import (
	ReplyKeyboardMarkup, KeyboardButton,
	ReplyKeyboardRemove, InlineKeyboardMarkup,
	InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent
)

config = configparser.ConfigParser()
config.read("setting.ini")

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
	sys.exit(0)

downloa = deezloader.Login(deezer_token)

bot = telepot.Bot(bot_token)
bot_name = bot.getMe()['username']

users = {}
qualit = {}
date = {}
languag = {}

del1 = 0
del2 = 0
free = 1
default_time = 0.8
is_audio = 0

send_image_track_query = "Track: %s\nArtist: %s\nAlbum: %s\nDate: %s"
send_image_album_query = "Album: %s\nArtist: %s\nDate: %s\nTracks amount: %d"
send_image_playlist_query = "Creation: %s\nUser: %s\nTracks amount: %d"
insert_query = "INSERT INTO DWSONGS(id, query, quality) values('%s', '%s', '%s')"
where_query = "SELECT query FROM DWSONGS WHERE id = '%s' and quality = '%s'"

local = os.getcwd()
db_file = local + "/dwsongs.db"
loc_dir = local + "/Songs/"

config = {
	"key": acrcloud_key,
	"secret": acrcloud_hash,
	"host": acrcloud_host
}

acrcloud = acrcloud.ACRcloud(config)

logging.basicConfig(
	filename = "dwsongs.log",
	level = logging.WARNING,
	format = "%(asctime)s %(levelname)s %(name)s %(message)s"
)

if not os.path.isdir(loc_dir):
	os.makedirs(loc_dir)

conn = sqlite3.connect(db_file)
c = conn.cursor()

try:
	c.execute("CREATE TABLE DWSONGS (id text, query text, quality text)")
	c.execute("CREATE TABLE BANNED (banned int)")
	c.execute("CREATE TABLE CHAT_ID (chat_id int)")
	conn.commit()
except sqlite3.OperationalError:
	pass

def generate_token():
	return oauth2.SpotifyClientCredentials(
		client_id = "c6b23f1e91f84b6a9361de16aba0ae17",
		client_secret = "237e355acaa24636abc79f1a089e6204"
	).get_access_token()

spo = spotipy.Spotify(
	auth = generate_token()
)

def request(url, chat_id=None, control=False):
	try:
		thing = requests.get(url)
	except:
		thing = requests.get(url)

	if control == True:
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

	try:
		users[chat_id] -= 1
	except KeyError:
		pass

def write_db(execution):
	conn = sqlite3.connect(db_file)
	c = conn.cursor()

	while True:
		sleep(1)

		try:
			c.execute(execution)
			conn.commit()
			conn.close()
			break
		except sqlite3.OperationalError:
			pass

def sendall(msg):
	conn = sqlite3.connect(db_file)
	c = conn.cursor()
	alls = c.execute("SELECT chat_id FROM CHAT_ID").fetchall()

	for a in alls:
		sendMessage(a[0], msg)

def statisc(chat_id, do):
	conn = sqlite3.connect(db_file)
	c = conn.cursor()

	if do == "USERS":
		c.execute("SELECT chat_id FROM CHAT_ID where chat_id = '%d'" % chat_id)

		if c.fetchone() == None:
			write_db("INSERT INTO CHAT_ID(chat_id) values('%d')" % chat_id)

		c.execute("SELECT chat_id FROM CHAT_ID")

	elif do == "TRACKS":
		c.execute("SELECT id FROM DWSONGS")

	infos = len(
		c.fetchall()
	)

	conn.close()
	return str(infos)

def check_flood(chat_id, msg):
	conn = sqlite3.connect(db_file)
	c = conn.cursor()
	c.execute("SELECT banned FROM BANNED where banned = '%d'" % chat_id)

	if c.fetchone() != None:
		conn.close()
		return "BANNED"

	try:
		time = msg['date'] - date[chat_id]['time']

		if time > 30:
			date[chat_id]['msg'] = 0

		date[chat_id]['time'] = msg['date']

		if time <= 4:
			date[chat_id]['msg'] += 1

			if time <= 4 and date[chat_id]['msg'] > 4:
				date[chat_id]['msg'] = 0
				date[chat_id]['tries'] -= 1

				sendMessage(
					chat_id,
					"It is appearing you are trying to flood, you have to wait more that four second to send another message.\n%d possibilites :)"
					% (
						date[chat_id]['tries']
					)
				)

				if date[chat_id]['tries'] == 0:
					write_db("INSERT INTO BANNED(banned) values('%d')" % chat_id)
					del date[chat_id]
					sendMessage(chat_id, "You are banned :)")
	except KeyError:
		try:
			date[chat_id] = {
				"time": msg['date'],
				"tries": 3,
				"msg": 0
			}
		except KeyError:
			pass

def sendMessage(chat_id, text, reply_markup=None, reply_to_message_id=None):
	sleep(default_time)

	try:
		bot.sendMessage(
			chat_id,
			translate(
				languag[chat_id], text
			),
			reply_markup = reply_markup,
			reply_to_message_id = reply_to_message_id
		)
	except Exception as a:
		logging.warning("While sending message error 275")
		logging.warning(a)

def sendPhoto(chat_id, photo, caption=None, reply_markup=None):
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

def sendAudio(chat_id, audio, link=None, image=None, youtube=False):
	sleep(default_time)

	try:
		bot.sendChatAction(chat_id, "upload_audio")

		if os.path.isfile(audio):
			try:
				tag = EasyID3(audio)
				
				duration = int(
					MP3(
						audio
					).info.length
				)
			except mutagen.id3._util.ID3NoHeaderError:
				tag = FLAC(audio)
				
				duration = int(
					tag.info.length
				)

			if os.path.getsize(audio) < 50000000:
				data = {
						"chat_id": chat_id,
						"duration": duration,
						"performer": tag['artist'][0],
						"title": tag['title'][0]
				}

				file_param = {
						"audio": open(audio, "rb"),
						"thumb": image

				}

				url = "https://api.telegram.org/bot" + bot_token + "/sendAudio"
				
				try:
					request = requests.post(
						url,
						params = data,
						files = file_param,
						timeout = 8
					)
				except:
					request = requests.post(
						url,
						params = data,
						files = file_param,
						timeout = 8
					)

				pprint(
					request.json()
				)

				file_id = request.json()['result']['audio']['file_id']

				if youtube == False:
					quality = (
						audio
						.split("(")[-1]
						.split(")")[0]
					)

					write_db(
						insert_query
						% (
							link,
							file_id,
							quality
						)
					)
			else:
				sendMessage(chat_id, "The song is bigger than 50 MB, more than the api support")
		else:
			bot.sendAudio(chat_id, audio)

	except telepot.exception.TelegramError:
		sendMessage(chat_id, "Sorry the track doesn't seem readable on Deezer :(")

	except Exception as a:
		logging.warning("While sending audio 457")
		logging.warning(a)
		sendMessage(chat_id, "Sorry for some reason I can't send the track :(")

def track(link, chat_id, quality):
	global spo

	conn = sqlite3.connect(db_file)
	c = conn.cursor()

	c.execute(
		where_query
		% (
			link,
			quality.split("MP3_")[-1]
		)
	)

	match = c.fetchone()
	conn.close()

	if match != None:
		sendAudio(chat_id, match[0])
	else:
		try:
			youtube = False

			if "spotify" in link:
				try:
					url = spo.track(link)
				except:
					spo = spotipy.Spotify(
						auth = generate_token()
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
					recursive_download=True,
				)

			elif "deezer" in link:
				ids = link.split("/")[-1]

				try:
					url = request(
						"https://api.deezer.com/track/" + ids, chat_id, True
					).json()
				except AttributeError:
					return

				try:
					image = url['album']['cover_xl'].replace("1000x1000", "90x90")
				except AttributeError:
					URL = "https://www.deezer.com/track/" + ids
					image = request(URL).text

					image = (
						BeautifulSoup(image, "html.parser")
						.find("meta", property="og:image")
						.get("content")
						.replace("500x500", "90x90")
					)

				ima = request(image).content

				if len(ima) == 13:
					image = "https://e-cdns-images.dzcdn.net/images/cover/90x90-000000-80-0-0.jpg"

				z = downloa.download_trackdee(
					link,
					quality = quality,
					recursive_quality = True,
					recursive_download = True,
				)
		except (deezloader.exceptions.TrackNotFound, deezloader.exceptions.NoDataApi):
			sendMessage(chat_id, "Track doesn't exist on Deezer or maybe it isn't readable, it'll be downloaded from YouTube...")

			try:
				if "spotify" in link:
					z = dwytsongs.download_trackspo(
						link, check = False
					)

				elif "deezer" in link:
					z = dwytsongs.download_trackdee(
						link, check = False
					)

				youtube = True
			except dwytsongs.TrackNotFound:
				sendMessage(chat_id, "Sorry I cannot download this song :(")
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
	
	if "?" in link:
		link = link.split("?")[0]

	try:
		if "spotify" in link:
			if "track/" in link:
				try:
					url = spo.track(link)
				except Exception as a:
					if not "The access token expired" in str(a):
						sendMessage(
							chat_id, "Invalid link ;)",
							reply_to_message_id = msg['message_id']
						)

						delete(chat_id)
						return

					spo = spotipy.Spotify(
						auth = generate_token()
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
							chat_id, "Invalid link ;)",
							reply_to_message_id = msg['message_id']
						)

					delete(chat_id)
					return

					spo = spotipy.Spotify(
						auth = generate_token()
					)

					tracks = spo.album(link)

				try:
					image3 = tracks['images'][2]['url']
					image1 = tracks['images'][0]['url']
				except IndexError:
					image3 = "https://e-cdns-images.dzcdn.net/images/cover/90x90-000000-80-0-0.jpg"
					image1 = "https://e-cdns-images.dzcdn.net/images/cover/1000x1000-000000-80-0-0.jpg"

				tot = tracks['total_tracks']
				conn = sqlite3.connect(db_file)
				c = conn.cursor()
				count = 0

				for a in tracks['tracks']['items']:
					count += a['duration_ms']

					c.execute(
						where_query
						% (
							a['external_urls']['spotify'],
							quali
						)
					)

					links2.append(
						a['external_urls']['spotify']
					)

					if c.fetchone() != None:
						links1.append(
							a['external_urls']['spotify']
						)

				if (count / 1000) > 40000:
					sendMessage(chat_id, "If you do this again I will come to your home and I will ddos your ass :)")
					delete(chat_id)
					return

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

				tracks = tracks['tracks']

				if tot != 50:
					for a in range(tot // 50):
						try:
							tracks2 = spo.next(tracks)
						except:
							spo = spotipy.Spotify(
								auth = generate_token()
							)

							tracks2 = spo.next(tracks)

						for a in tracks2['items']:
							c.execute(
								where_query
								% (
									a['external_urls']['spotify'], qualit
								)
							)

							links2.append(
								a['external_urls']['spotify']
							)

							if c.fetchone() != None:
								links1.append(
									a['external_urls']['spotify']
								)

				conn.close()

				if len(links1) != tot:
					z = downloa.download_albumspo(
						link,
						quality = quality,
						recursive_quality = True,
						recursive_download = True
					)
				else:
					for a in links2:
						track(a, chat_id, quality)

				done = 1

			elif "playlist/" in link:
				musi = link.split("/")

				try:
					tracks = spo.user_playlist(
						musi[-3],
						playlist_id = musi[-1]
					)
				except Exception as a:
					if not "The access token expired" in str(a):
						sendMessage(
							chat_id, "Invalid link ;)",
							reply_to_message_id = msg['message_id']
						)

						delete(chat_id)
						return

					spo = spotipy.Spotify(
						auth = generate_token()
					)

					tracks = spo.user_playlist(
						musi[-3],
						playlist_id = musi[-1]
					)

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

				for a in tracks['tracks']['items']:
					try:
						track(
							a['track']['external_urls']['spotify'],
							chat_id,
							quality
						)
					except KeyError:
						try:
							sendMessage(chat_id, a['track']['name'] + " Not found :(")
						except KeyError:
							sendMessage(chat_id, "Error :(")

				tot = tracks['tracks']['total']
				tracks = tracks['tracks']

				if tot != 100:
					for a in range(tot // 100):
						try:
							tracks = spo.next(tracks)
						except:
							spo = spotipy.Spotify(
								auth = generate_token()
							)

							tracks = spo.next(tracks)
						for a in tracks['items']:
							try:
								track(
									a['track']['external_urls']['spotify'],
									chat_id,
									quality
								)
							except KeyError:
								try:
									sendMessage(chat_id, a['track']['name'] + " Not found :(")
								except KeyError:
									sendMessage(chat_id, "Error :(")

				done = 1

			else:
				sendMessage(chat_id, "Sorry :( The bot doesn't support this link")

		elif "deezer" in link:
			if "track/" in link:
				try:
					url = request(
						"https://api.deezer.com/track/" + link
						.split("/")[-1],
						chat_id,
						True
					).json()
				except AttributeError:
					delete(chat_id)
					return

				image1 = url['album']['cover_xl']

				if image1 == None:
					URL = "https://www.deezer.com/track/" + link.split("/")[-1]
					image1 = request(URL).text

					image1 = (
						BeautifulSoup(image1, "html.parser")
						.find("meta", property="og:image")
						.get("content")
						.replace("500x500", "90x90")
					)

				ima = request(image1).content

				if len(ima) == 13:
					image1 = "https://e-cdns-images.dzcdn.net/images/cover/1000x1000-000000-80-0-0.jpg"

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
						"https://api.deezer.com/album/" + link
						.split("/")[-1],
						chat_id,
						True
					).json()
				except AttributeError:
					delete(chat_id)
					return

				if url['duration'] > 40000:
					sendMessage(chat_id, "If you do this again I will come to your home and I will ddos your ass :)")
					delete(chat_id)
					return

				image1 = url['cover_xl']

				if image1 == None:
					URL = "https://www.deezer.com/album/" + link.split("/")[-1]
					image1 = request(URL).text

					image1 = (
						BeautifulSoup(image1, "html.parser")
						.find("img", class_="img_main")
						.get("src")
						.replace("200x200", "1000x1000")
					)

				ima = request(image1).content

				if len(ima) == 13:
					image1 = "https://e-cdns-images.dzcdn.net/images/cover/1000x1000-000000-80-0-0.jpg"

				image3 = image1.replace("1000x1000", "90x90")

				conn = sqlite3.connect(db_file)
				c = conn.cursor()

				for a in url['tracks']['data']:
					c.execute(
						where_query
						% (
							a['link'],
							quali
						)
					)

					links2.append(a['link'])

					if c.fetchone() != None:
						links1.append(a['link'])

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
						recursive_download = True
					)
				else:
					for a in links2:
						track(a, chat_id, quality)
				
				done = 1

			elif "playlist/" in link:
				try:
					url = request(
						"https://api.deezer.com/playlist/" + link
						.split("/")[-1],
						chat_id,
						True
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
					track(
						a['link'],
						chat_id,
						quality
					)

				done = 1

			elif "artist/" in link:
				link = "https://api.deezer.com/artist/" + link.split("/")[-1]

				try:
					url = request(link, chat_id, True).json()
				except AttributeError:
					delete(chat_id)
					return

				sendPhoto(
					chat_id, url['picture_xl'],
					caption = (
						"Artist:" + url['name'] + 
						"\nAlbum numbers:" + str(url['nb_album']) +
						"\nFans on Deezer:" + str(url['nb_fan'])
					),
					reply_markup = InlineKeyboardMarkup(
						inline_keyboard = [
							[
								InlineKeyboardButton(
									text = "TOP 30",
									callback_data = link + "/top?limit=30"
								),
								InlineKeyboardButton(
									text = "ALBUMS",
									callback_data = link + "/albums"
								)
							],
							[
								InlineKeyboardButton(
									text = "RADIO",
									callback_data = link + "/radio"
								)
							]
						]
					)
				)

			else:
				sendMessage(chat_id, "Sorry :( The bot doesn't support this link")

		else:
			sendMessage(chat_id, "Sorry :( The bot doesn't support this link")

		try:
			image3 = request(image3).content

			for a in range(len(z)):
				sendAudio(chat_id, z[a], links2[a], image3)
		except NameError:
			pass

	except deezloader.exceptions.QuotaExceeded:
		sendMessage(chat_id, "Please send the link again :(")

	except deezloader.exceptions.AlbumNotFound:
		sendMessage(chat_id, "Album didn't find on Deezer :(")
		sendMessage(chat_id, "Try to search it throught inline mode or search the link on Deezer")

	except Exception as a:
		logging.warning(a)
		logging.warning(link)
		sendMessage(chat_id, "OPS :( Something went wrong please contact @An0nimia to explain the issue, if this happens again")

	if done == 1:
		sendMessage(
			chat_id, "FINISHED :) Rate me here https://t.me/BotsArchive/298",
			reply_to_message_id = msg['message_id'],
			reply_markup = InlineKeyboardMarkup(
				inline_keyboard = [
					[
						InlineKeyboardButton(
							text = "SHARE",
							url = "tg://msg?text=Start @" + bot_name + " for download all the songs which you want ;)"
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
	audi = loc_dir + audio + ".ogg"

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
		album += "_" + date
	except KeyError:
		album += "_"

	try:
		label = audio['metadata']['music'][0]['label']
		album += "_" + label
	except KeyError:
		album += "_"

	try:
		genre = audio['metadata']['music'][0]['genres'][0]['name']
		album += "_" + genre
	except KeyError:
		album += "_"

	if len(album) > 64:
		album = "Infos with too many bytes"

	try:
		url = request(
			"https://api.deezer.com/search/track/?q=" + track
			.replace("#", "") + " + " + artist
			.replace("#", ""),
			chat_id,
			True
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
			ids = "https://open.spotify.com/track/" + audio['metadata']['music'][0]['external_metadata']['spotify']['track']['id']

			try:
				url = spo.track(ids)
			except:
				spo = spotipy.Spotify(
					auth = generate_token()
				)

				url = spo.track(ids)

			image = url['album']['images'][0]['url']
		except KeyError:
			pass

		try:
			ids = "https://api.deezer.com/track/" + str(audio['metadata']['music'][0]['external_metadata']['deezer']['track']['id'])

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
			caption = track + " - " + artist,
			reply_markup = InlineKeyboardMarkup(
				inline_keyboard = [
					[
						InlineKeyboardButton(
							text = "Download",
							callback_data = ids
						),
						InlineKeyboardButton(
							text = "Info",
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

		array = []

		if "album" in query_data:
			try:
				url = request(query_data, from_id, True).json()
			except AttributeError:
				return

			array += [
				[
					InlineKeyboardButton(
						text = a['title'] + " - " + a['release_date'].replace("-", "/"),
						callback_data = a['link']
					)
				] for a in url['data']
			]

			array.append(
				[
					InlineKeyboardButton(
						text = "BACK 🔙",
						callback_data = query_data.split("/")[-2] + "/" + "artist"
					)
				]
			)

			bot.editMessageReplyMarkup(
				(
					(
						from_id, message_id
					)
				),
				reply_markup = InlineKeyboardMarkup(
					inline_keyboard = array
				)
			)

		elif "down" in query_data:
			if ans == "2":
				if users[from_id] == 3:
					bot.answerCallbackQuery(
						query_id,
						translate(
							languag[from_id],
							"Wait the end and repeat the step, did you think you could download how much songs you wanted? ;)"
						),
						show_alert = True
					)

					return
				else:
					users[from_id] += 1

			bot.answerCallbackQuery(
				query_id,
				translate(
					languag[from_id], "Songs are downloading"
				)
			)

			try:
				url = request(
					"https://api.deezer.com/artist/" + query_data
					.split("/")[-4] + "/" + query_data
					.split("/")[-1],
					from_id,
					True
				).json()
			except AttributeError:
				return

			for a in url['data']:
				Link(
					"https://www.deezer.com/track/" + str(a['id']),
					from_id,
					qualit[from_id],
					msg['message']
				)

				if ans == "2":
					users[from_id] += 1

			if ans == "2":
				users[from_id] -= 1

		elif "radio" in query_data or "top" in query_data:
			try:
				url = request(query_data, from_id, True).json()
			except AttributeError:
				return

			array += [
				[
					InlineKeyboardButton(
						text = a['artist']['name'] + " - " + a['title'],
						callback_data = "https://www.deezer.com/track/" + str(a['id'])
					)
				] for a in url['data']
			]

			array.append(
				[
					InlineKeyboardButton(
						text = "GET ALL ⬇️",
						callback_data = query_data.split("/")[-2] + "/artist/down/" + query_data.split("/")[-1]
					)
				]
			)

			array.append(
				[
					InlineKeyboardButton(
						text = "BACK 🔙",
						callback_data = query_data.split("/")[-2] + "/" + "artist"
					)
				]
			)

			bot.editMessageReplyMarkup(
				(
					(
						from_id, message_id
					)
				),
				reply_markup = InlineKeyboardMarkup(
					inline_keyboard = array
				)
			)

		else:
			link = "https://api.deezer.com/artist/" + query_data.split("/")[-2]

			try:
				url = request("https://api.deezer.com/artist/" + query_data.split("/")[-2], from_id, True).json()
			except AttributeError:
				return

			bot.editMessageReplyMarkup(
				(
					(
						from_id, message_id
					)
				),
				reply_markup = InlineKeyboardMarkup(
					inline_keyboard = [
						[
							InlineKeyboardButton(
								text = "TOP 30",
								callback_data = link + "/top?limit=30"
							),
							InlineKeyboardButton(
								text = "ALBUMS",
								callback_data = link + "/albums"
							)
						],
						[
							InlineKeyboardButton(
								text = "RADIO",
								callback_data = link + "/radio"
							)
						]
					]
				)
			)
	else:
		tags = query_data.split("_")

		if tags[0] == "Infos with too many bytes":
			bot.answerCallbackQuery(
				query_id,
				translate(
					languag[from_id], query_data
				)
			)

		elif len(tags) == 4:
			bot.answerCallbackQuery(
				query_id,
				text = (
					"Album: %s\nDate: %s\nLabel: %s\nGenre: %s"
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
				if users[from_id] == 3:
					bot.answerCallbackQuery(
						query_id,
						translate(
							languag[from_id], "Wait the end and repeat the step, did you think you could download how much songs you wanted? ;)"
						),
						show_alert = True
					)

					return
				else:
					users[from_id] += 1

			bot.answerCallbackQuery(
				query_id,
				translate(
					languag[from_id], "Song is downloading"
				)
			)

			Link(
				query_data, from_id,
				qualit[from_id],
				msg['message']
			)

def download(msg):
	query_id, from_id, query_data = telepot.glance(
		msg, flavor = "callback_query"
	)

	try:
		languag[from_id]
	except KeyError:
		try:
			languag[from_id] = msg['from']['language_code']
		except KeyError:
			languag[from_id] = "en"

	try:
		qualit[from_id]
	except KeyError:
		qualit[from_id] = "MP3_320"

	try:
		users[from_id]
	except KeyError:
		users[from_id] = 0

	Thread(
		target = inline,
		args = (
			msg, from_id,
			query_data, query_id
		)
	).start()

def search(msg):
	query_id, from_id, query_string = telepot.glance(
		msg, flavor = "inline_query"
	)

	try:
		languag[from_id] = msg['from']['language_code']
	except KeyError:
		languag[from_id] = "en"

	if check_flood(from_id, msg) == "BANNED":
		return

	query_string = query_string.replace("#", "")

	if "" == query_string:
		search1 = request("http://api.deezer.com/chart/").json()

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
				id = "https://www.deezer.com/album/" + str(a['id']),
				title = a['title'] + " (Album)",
				description = a['artist']['name'],
				thumb_url = a['cover_big'],
				input_message_content = InputTextMessageContent(
					message_text = "https://www.deezer.com/album/" + str(a['id'])
				)
			) for a in search1['albums']['data']
		]

		result += [
			InlineQueryResultArticle(
				id = a['link'],
				title = str(a['position']),
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
				description = "N° tracks:" + str(a['nb_tracks']),
				thumb_url = a['picture_big'],
				input_message_content = InputTextMessageContent(
					message_text = a['link']
				)
			) for a in search1['playlists']['data']
		]

	elif "album:" in query_string:
		search1 = request(
			"https://api.deezer.com/search/album/?q=" + query_string
			.split("album:")[1]
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
				thumb_url = a['cover_big'],
				input_message_content = InputTextMessageContent(
					message_text = a['link']
				)
			) for a in search1['data']
		]

	elif "artist:" in query_string:
		search1 = request(
			"https://api.deezer.com/search/artist/?q=" + query_string
			.split("artist:")[1]
		).json()

		try:
			if search1['error']:
				return
		except KeyError:
			pass

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

	else:
		search1 = request("https://api.deezer.com/search?q=" + query_string).json()

		try:
			if search1['error']:
				return
		except KeyError:
			pass

		search1 = search1['data']
		result = [
			InlineQueryResultArticle(
				id = a['link'],
				title = a['title'],
				description = a['artist']['name'],
				thumb_url = a['album']['cover_big'],
				input_message_content = InputTextMessageContent(
					message_text = a['link']
				)
			) for a in search1
		]

		for a in search1:
			try:
				if "https://www.deezer.com/album/" + str(a['album']['id']) in str(result):
					continue
			except KeyError:
				continue

			result += [
				InlineQueryResultArticle(
					id = "https://www.deezer.com/album/" + str(a['album']['id']),
					title = a['album']['title'] + " (Album)",
					description = a['artist']['name'],
					thumb_url = a['album']['cover_big'],
					input_message_content = InputTextMessageContent(
						message_text = "https://www.deezer.com/album/" + str(a['album']['id'])
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

	if free == 0 and chat_id != 560950095:
		return

	pprint(msg)

	try:
		languag[chat_id]
	except KeyError:
		try:
			languag[chat_id] = msg['from']['language_code']
		except KeyError:
			languag[chat_id] = "en"

	if check_flood(chat_id, msg) == "BANNED":
		return

	statisc(chat_id, "USERS")

	try:
		qualit[chat_id]
	except KeyError:
		qualit[chat_id] = "MP3_320"

	try:
		users[chat_id]
	except KeyError:
		users[chat_id] = 0

	if content_type == "text" and msg['text'] == "/start":
		try:
			sendPhoto(
					chat_id, open("example.jpg", "rb"),
					caption = "Welcome to @" + bot_name + "\nPress '/' to get commands list"
			)
		except FileNotFoundError:
			pass

		sendMessage(
			chat_id,
			"Press for search songs or albums or artists\nP.S. Remember you can do this digiting @ in your keyboard and select " +
			bot_name +
			"\nSend a Deezer or Spotify link to download\nSend a song o vocal message to recognize the track",
			reply_markup = InlineKeyboardMarkup(
				inline_keyboard = [
					[
						InlineKeyboardButton(
							text = "Search by artist",
							switch_inline_query_current_chat = "artist:"
						),
						InlineKeyboardButton(
							text = "Search by album",
							switch_inline_query_current_chat = "album:"
						)
					],
					[
						InlineKeyboardButton(
							text = "Global search",
							switch_inline_query_current_chat = ""
						)
					]
				]
			)
		)

	elif content_type == "text" and msg['text'] == "/translator":
		if languag[chat_id] != "en":
			languag[chat_id] = "en"
			sendMessage(chat_id, "Now the language is english")
		else:
			languag[chat_id] = msg['from']['language_code']
			sendMessage(chat_id, "Now the bot will use the Telegram app language")

	elif content_type == "text" and msg['text'] == "/quality":
		sendMessage(
			chat_id, "Select default download quality\nCURRENTLY: " + qualit[chat_id],
			reply_markup = ReplyKeyboardMarkup(
				keyboard=[
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
		qualit[chat_id] = msg['text'].replace("Kbps", "")

		sendMessage(
			chat_id, "Songs will be downloaded in " + msg['text'] + " quality",
			reply_markup = ReplyKeyboardRemove()
		)

		sendMessage(chat_id, "Songs which cannot be downloaded in quality you have chosen will be downloaded in the best quality possible")

	elif content_type == "voice" or content_type == "audio":
		Thread(
			target = Audio,
			args = (
				msg[content_type]['file_id'],
				chat_id
			)
		).start()

	elif content_type == "text" and msg['text'] == "/info":
		sendMessage(
			chat_id,
			"Version: %s\nName: @%s\nCreator: @%s\nDonation: %s\nForum: %s\nUsers: %s\nTotal downloads: %s"
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

	elif content_type == "text" and chat_id == 560950095 and "the cat is on the table" in msg['text']:
		what = msg['text'].split("the cat is on the table ")[1]

		if what == "1":
			free = 1

		elif what == "0":
			free = 0

		else:
			Thread(
				target = sendall,
				args = (
					what,
				)
			).start()

	elif content_type == "text":
		try:
			msg['entities']

			if ans == "2" and users[chat_id] == 3:
				sendMessage(chat_id, "Wait the end and repeat the step, did you think you could download how much songs you wanted? ;)")
			else:
				if ans == "2":
					users[chat_id] += 1

				Thread(
					target = Link,
					args = (
						msg['text'].replace("'", ""),
						chat_id, qualit[chat_id], msg
					)
				).start()
		except KeyError:
			sendMessage(chat_id, "Press",
				reply_markup = InlineKeyboardMarkup(
					inline_keyboard = [
						[
							InlineKeyboardButton(
								text = "Search artist",
								switch_inline_query_current_chat = "artist:" + msg['text']
							),
							InlineKeyboardButton(
								text = "Search album",
								switch_inline_query_current_chat = "album:" + msg['text']
							)
						],
						[
							InlineKeyboardButton(
								text = "Search global",
								switch_inline_query_current_chat = msg['text']
							)
						]
					]
				)
			)
try:
	print("""
	1): Free
	2): Strict
	""")
	ans = input("Choose: ")

	if ans == "1" or ans == "2":
		bot.message_loop(
			{
				"chat": start,
				"callback_query": download,
				"inline_query": search,
				"chosen_inline_result": nada
			}
		)
	else:
		sys.exit(0)

	print("Bot started")

	while True:
		sleep(1)
		path = os.statvfs("/")
		free_space = path.f_bavail * path.f_frsize

		if (del1 == del2 and is_audio == 0) or free_space <= 2000000000:
			del1, del2 = 0, 0

			for a in os.listdir(loc_dir):
				try:
					shutil.rmtree(loc_dir + a)
				except NotADirectoryError:
					os.remove(loc_dir + a)
except KeyboardInterrupt:
	os.rmdir(loc_dir)
	print("\nSTOPPED")
