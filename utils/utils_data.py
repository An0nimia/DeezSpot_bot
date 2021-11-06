#!/usr/bin/python3

from deezloader.easy_spoty import Spo
from configs.set_configs import SetConfigs
from deezloader.exceptions import NoDataApi
from deezloader.libutils.utils import get_ids
from utils.utils import get_quality_dee_s_quality
from deezloader.deezloader.dee_api import API as deezer_api

from inlines.inline_query_results import (
	create_result_article_artist, create_result_article_track,
	create_result_article_album, create_result_article_playlist,
	create_result_article_artist_album, create_result_article_artist_radio,
	create_result_article_artist_playlist, create_result_article_chart_album,
	create_result_article_chart_artist, create_result_article_chart_track,
	create_result_article_track_audio, create_result_not_found,
	create_result_article_track_and_audio
)

def shazam_song(song):
	data = SetConfigs.acrcloud_api.recognize_audio(song)
	status = data['status']

	if status['msg'] != "Success":
		return

	song_tags = data['metadata']['music'][0]

	artists = [
		artist['name']
		for artist in song_tags['artists']
	]

	artist = " & ".join(artists)

	if "genres" in song_tags:
		genres = [
			genre['name']
			for genre in song_tags['genres']
		]

		genre = " & ".join(genres)
	else:
		genre = "Unknown"

	album = song_tags['album']['name']
	label = song_tags['label']
	external_ids = song_tags['external_ids']

	if "upc" in external_ids:
		upc = f"upc:{external_ids['upc']}"

	if "isrc" in external_ids:
		isrc = f"isrc:{external_ids['isrc']}"
		data_track = deezer_api.get_track(isrc)
		track_link = data_track['link']
		album_link = data_track['album']['link']
		artist_link = data_track['artist']['link']
		image_url = data_track['album']['cover_xl']
	else:
		track_link = None
		album_link = None
		image_url = None

	release_date = song_tags['release_date']
	title = song_tags['title']

	return (
		artist, genre,
		album, label,
		track_link, album_link,
		artist_link, image_url,
		release_date, title
	)

#OLD SPOTIFY DOWNLOAD
def track_spo_to_dee_data(link):
	link_dee = SetConfigs.deez_api.convert_spoty_to_dee_link_track(link)
	dee_data = track_dee_data(link_dee)

	return dee_data

def track_spo_data(link):
	ids = get_ids(link)
	data = Spo.get_track(ids)
	image_url = data['album']['images'][0]['url']
	name = data['name']
	artist = data['artists'][0]['name']
	album = data['album']['name']
	date = data['album']['release_date']
	duration = data['duration_ms'] // 1000

	return (
		image_url, name,
		artist, album,
		date, link, duration
	)

def track_dee_data(link):
	ids = get_ids(link)
	data = deezer_api.get_track(ids)
	md5_image = data['md5_image']
	image_url = deezer_api.get_img_url(md5_image, size = "1000x1000")
	name = data['title']
	artist = data['artist']['name']
	album = data['album']['title']
	date = data['album']['release_date']
	link_dee = data['link']
	duration = data['duration']

	return (
		image_url, name,
		artist, album,
		date, link_dee, duration
	)

def artist_dee_data(link):
	ids = get_ids(link)
	data = deezer_api.get_artist(ids)
	name = data['name']
	image_url = data['picture_xl']
	nb_album = data['nb_album']
	nb_fan = data['nb_fan']

	return (
		name, image_url,
		nb_album, nb_fan
	)

def playlist_dee_data(link):
	ids = get_ids(link)
	data = deezer_api.get_playlist(ids)
	nb_tracks = data['nb_tracks']
	n_fans = data['fans']
	image_url = data['picture_xl']
	creation_date = data['creation_date']
	creator = data['creator']['name']
	tracks = data['tracks']['data']

	return (
		nb_tracks, n_fans,
		image_url, creation_date,
		creator, tracks
	)

def playlist_spo_data(link):
	ids = get_ids(link)
	data = Spo.get_playlist(ids)
	n_fans = data['followers']['total']
	image_url = data['images'][0]['url']
	creation_date = data['tracks']['items'][0]['added_at']
	creator = data['owner']['display_name']
	tracks = data['tracks']['items']
	nb_tracks = len(tracks)

	return (
		nb_tracks, n_fans,
		image_url, creation_date,
		creator, tracks
	)

def album_dee_data(link):
	ids = get_ids(link)
	data = deezer_api.get_album(ids)
	md5_image = data['md5_image']
	image_url = deezer_api.get_img_url(md5_image, size = "1000x1000")
	album = data['title']
	artist = data['artist']['name']
	date = data['release_date']
	nb_tracks = data['nb_tracks']
	tracks = data['tracks']['data']
	duration = data['duration']
	link_dee = data['link']

	return (
		image_url, album,
		artist, date,
		nb_tracks, tracks,
		duration, link_dee
	)

def convert_spoty_to_dee_link_track(link):
	link_dee = SetConfigs.deez_api.convert_spoty_to_dee_link_track(link)

	return link_dee

def album_spo_data_to_dee(link):
	link_dee = SetConfigs.deez_api.convert_spoty_to_dee_link_album(link)
	dee_data = album_dee_data(link_dee)

	return dee_data

def album_spo_data(link):
	ids = get_ids(link)
	data = Spo.get_album(ids)
	image_url = data['images'][0]['url']
	album = data['name']
	artist = data['artists'][0]['name']
	date = data['release_date']
	nb_tracks = data['total_tracks']
	tracks = data['tracks']['items']
	duration = 0

	for track in tracks:
		duration += track['duration_ms']

	duration //= 1000

	return (
		image_url, album,
		artist, date,
		nb_tracks, tracks,
		duration, link
	)

def __lazy_create(search_method):
	if search_method == "results_audio":
		c_create_article = create_result_article_track_audio
		mode = "results_audio"

	elif search_method == "results_article":
		c_create_article = create_result_article_track
		mode = 0

	elif search_method == "results_audio_article":
		c_create_article = create_result_article_track_and_audio
		mode = "results_audio"

	return c_create_article, mode

def create_response_article(query: str, user_data):
	s_art = "art: "
	s_alb = "alb: "
	s_pla = "pla: "
	s_trk = "trk: "
	s_art_id = "artist:"
	mode = 0
	search_method = user_data['search_method']

	if search_method.startswith("results_audio"):
		user_quality = user_data['quality']
		quality = get_quality_dee_s_quality(user_quality)

	if query.startswith(s_art):
		c_query = query.replace(s_art, "")
		c_api = deezer_api.search_artist
		c_create_article = create_result_article_artist

	elif query.startswith(s_alb):
		c_query = query.replace(s_alb, "")
		c_api = deezer_api.search_album
		c_create_article = create_result_article_album

	elif query.startswith(s_pla):
		c_query = query.replace(s_pla, "")
		c_api = deezer_api.search_playlist
		c_create_article = create_result_article_playlist

	elif query.startswith(s_trk):
		c_query = query.replace(s_trk, "")
		c_api = deezer_api.search_track
		c_create_article, mode = __lazy_create(search_method)

	elif query.startswith(s_art_id):
		c_query = query.replace(s_art_id, "")
		s_c_query = c_query.split(":")
		c_query = s_c_query[0]
		path = s_c_query[1]

		if path == "top":
			c_api = deezer_api.get_artist_top_tracks
			c_create_article, mode = __lazy_create(search_method)

		elif path == "albums":
			c_api = deezer_api.get_artist_top_albums
			c_create_article = create_result_article_artist_album

		elif path == "related":
			c_api = deezer_api.get_artist_related
			c_create_article = create_result_article_artist

		elif path == "radio":
			c_api = deezer_api.get_artist_radio
			c_create_article = create_result_article_artist_radio

		elif path == "playlists":
			c_api = deezer_api.get_artist_top_playlists
			c_create_article = create_result_article_artist_playlist

		else:
			return

	else:
		c_query = query

		if c_query == "":
			mode = 1
			c_api = deezer_api.get_chart
		else:
			c_api = deezer_api.search
			c_create_article, mode = __lazy_create(search_method)

	try:
		data = c_api(c_query)
	except NoDataApi:
		return create_result_not_found()

	if mode == 0:
		data = data['data']
		results = c_create_article(data)

	elif mode == 1:
		tracks = data['tracks']['data']
		albums = data['albums']['data']
		artists = data['artists']['data']
		playlists = data['playlists']['data']

		if search_method == "results_audio":
			results = create_result_article_track_audio(tracks, quality)
		elif search_method == "results_article":
			results = create_result_article_chart_track(tracks)
		elif search_method == "results_audio_article":
			results = create_result_article_track_and_audio(tracks, quality)

		results += create_result_article_chart_album(albums)
		results += create_result_article_chart_artist(artists)
		results += create_result_article_playlist(playlists)

	elif mode == "results_audio":
		data = data['data']
		results = c_create_article(data, quality)

	return results