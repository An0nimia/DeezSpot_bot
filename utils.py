#!/usr/bin/python3

from time import sleep
from requests import get
from os import path, makedirs
from bs4 import BeautifulSoup
import spotipy.oauth2 as oauth2
from configparser import ConfigParser

from sqlite3 import (
	connect, OperationalError, IntegrityError
)

from settings import (
	db_file, loc_dir,
	ini_file, song_default_image
)

config = ConfigParser()
config.read(ini_file)

try:
	ya_key = config['yandex']['key']
except KeyError:
	print("Something went wrong with configuration file")
	exit()

def request(url):
	try:
		thing = get(url)
	except:
		thing = get(url)

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

		except IntegrityError:
			break

def view_db(execution):
	conn = connect(db_file)
	c = conn.cursor()
	match = c.execute(execution).fetchone()
	conn.close()
	return match

def check_image(image1, ids, kind):
	if kind == "track":
		if not image1:
			URL = "https://www.deezer.com/track/%s" % ids
			body = get(URL).text

			image1 = (
				BeautifulSoup(body, "html.parser")
				.find("meta", property = "og:image")
				.get("content")
				.replace("500x500", "1000x1000")
			)
	
	elif kind == "album":
		if not image1:
			URL = "https://www.deezer.com/album/%s" % ids
			body = request(URL).text

			image1 = (
				BeautifulSoup(body, "html.parser")
				.find("img", class_ = "img_main")
				.get("src")
				.replace("200x200", "1000x1000")
			)

	ima = request(image1).content

	if len(ima) == 13:
		image1 = song_default_image

	return image1

def get_image(image):
	imag = image.split("/")

	if imag[-2] == "image" or imag[-2] == "":
		imag = loc_dir + imag[-1]
	else:
		imag = loc_dir + imag[-2]

	image = request(image)
	img = open(imag, "wb")
	img.write(image.content)
	img.close()
	image.url = imag
	return image

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

def initialize():
	if not path.isdir(loc_dir):
		makedirs(loc_dir)

	conn = connect(db_file)
	c = conn.cursor()
	c.execute("CREATE TABLE IF NOT EXISTS DWSONGS (id text, query text, quality text, PRIMARY KEY (id, quality))")
	c.execute("CREATE TABLE IF NOT EXISTS BANNED (banned int, PRIMARY KEY (banned))")
	c.execute("CREATE TABLE IF NOT EXISTS CHAT_ID (chat_id int, PRIMARY KEY (chat_id))")
	conn.commit()
	conn.close()

def generate_token():
	return oauth2.SpotifyClientCredentials(
		client_id = "c6b23f1e91f84b6a9361de16aba0ae17",
		client_secret = "237e355acaa24636abc79f1a089e6204"
	).get_access_token()

def fast_split(thing):
	return (
		thing
		.split("(")[-1]
		.split(")")[0]
	)

def image_resize(image, size):
	size = "{}x{}".format(size, size)
	return image.replace("1000x1000", size)