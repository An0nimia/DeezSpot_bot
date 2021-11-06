#!/usr/bin/python3

from helpers.db_help import select_dwsongs
from utils.utils import my_round, get_url_path
from configs.customs import not_found_query_gif

from telegram import (
	InlineQueryResultArticle, InputTextMessageContent,
	InlineQueryResultAudio, InlineQueryResultCachedAudio,
	InlineQueryResultGif
)

def create_result_article_artist(datas):
	results = [
		InlineQueryResultArticle(
			id = data['id'],
			title = data['name'],
			input_message_content = InputTextMessageContent(
				data['link']
			),
			description = (
				f"Album number: {data['nb_album']}" +
				f"\nFan number: {data['nb_fan']}"
			),
			thumb_url = data['picture_big']
		)
		for data in datas
	]

	return results

def create_result_article_track(datas):
	results = [
		InlineQueryResultArticle(
			id = data['id'],
			title = data['title'],
			input_message_content = InputTextMessageContent(
				data['link']
			),
			description = (
				f"Artist: {data['artist']['name']}" +
				f"\nAlbum: {data['album']['title']}" +
				f"\nDuration: {my_round(data['duration'] / 60)}" +
				f"\nRank: {data['rank']}"
			),
			thumb_url = data['album']['cover_big']
		)
		for data in datas
	]

	return results

def create_result_article_track_audio(datas, quality):
	results = []

	for data in datas:
		ids = data['id']
		link = get_url_path(data['link'])
		match = select_dwsongs(link, quality)

		if match:
			audio_file_id = match[0]

			article = InlineQueryResultCachedAudio(
				id = ids,
				audio_file_id = audio_file_id,
			)
		else:
			article = InlineQueryResultAudio(
				id = ids,
				audio_url = data['preview'],
				title = data['title'],
				performer = data['artist']['name'],
				audio_duration = data['duration'],
				input_message_content = InputTextMessageContent(
					data['link']
				)
			)

		results.append(article)

	return results

def create_result_article_track_and_audio(datas, quality):
	results = []

	for data in datas:
		ids = data['id']
		link = get_url_path(data['link'])
		match = select_dwsongs(link, quality)

		if match:
			audio_file_id = match[0]

			article = InlineQueryResultCachedAudio(
				id = ids,
				audio_file_id = audio_file_id,
			)
		else:
			article = InlineQueryResultArticle(
				id = data['id'],
				title = data['title'],
				input_message_content = InputTextMessageContent(
					data['link']
				),
				description = (
					f"Artist: {data['artist']['name']}" +
					f"\nAlbum: {data['album']['title']}" +
					f"\nDuration: {my_round(data['duration'] / 60)}" +
					f"\nRank: {data['rank']}"
				),
				thumb_url = data['album']['cover_big']
			)

		results.append(article)

	return results

def create_result_article_album(datas):
	results = [
		InlineQueryResultArticle(
			id = data['id'],
			title = data['title'],
			input_message_content = InputTextMessageContent(
				data['link']
			),
			description = (
				f"Tracks number: {data['nb_tracks']}" +
				f"\nArtist: {data['artist']['name']}"
			),
			thumb_url = data['cover_big']
		)
		for data in datas
	]

	return results

def create_result_article_artist_album(datas):
	results = [
		InlineQueryResultArticle(
			id = data['id'],
			title = data['title'],
			input_message_content = InputTextMessageContent(
				data['link']
			),
			description = (
				f"Release date: {data['release_date']}" +
				f"\nFans: {data['fans']}"
			),
			thumb_url = data['cover_big']
		)
		for data in datas
	]

	return results

def create_result_article_playlist(datas):
	results = [
		InlineQueryResultArticle(
			id = data['id'],
			title = data['title'],
			input_message_content = InputTextMessageContent(
				data['link']
			),
			description = (
				f"Tracks number: {data['nb_tracks']}" +
				f"\nUser: {data['user']['name']}" +
				f"\nCreation: {data['creation_date']}"
			),
			thumb_url = data['picture_big']
		)
		for data in datas
	]

	return results

def create_result_article_artist_playlist(datas):
	results = [
		InlineQueryResultArticle(
			id = data['id'],
			title = data['title'],
			input_message_content = InputTextMessageContent(
				data['link']
			),
			description = (
				f"User: {data['user']['name']}" +
				f"\nCreation: {data['creation_date']}"
			),
			thumb_url = data['picture_big']
		)
		for data in datas
	]

	return results

def create_result_article_artist_radio(datas):
	results = [
		InlineQueryResultArticle(
			id = data['id'],
			title = data['title'],
			input_message_content = InputTextMessageContent(
				f"https://deezer.com/track/{data['id']}"
			),
			description = (
				f"Artist: {data['artist']['name']}" +
				f"\nAlbum: {data['album']['title']}" +
				f"\nDuration: {my_round(data['duration'] / 60)}" +
				f"\nRank: {data['rank']}"
			),
			thumb_url = data['album']['cover_big']
		)
		for data in datas
	]

	return results

def create_result_article_chart_album(datas):
	results = [
		InlineQueryResultArticle(
			id = data['id'],
			title = data['title'],
			input_message_content = InputTextMessageContent(
				data['link']
			),
			description = (
				f"Position: {data['position']}" +
				f"\nArtist: {data['artist']['name']}"
			),
			thumb_url = data['cover_big']
		)
		for data in datas
	]

	return results

def create_result_article_chart_artist(datas):
	results = [
		InlineQueryResultArticle(
			id = data['id'],
			title = data['name'],
			input_message_content = InputTextMessageContent(
				data['link']
			),
			description = f"Position: {data['position']}",
			thumb_url = data['picture_big']
		)
		for data in datas
	]

	return results

def create_result_article_chart_track(datas):
	results = [
		InlineQueryResultArticle(
			id = data['id'],
			title = data['title'],
			input_message_content = InputTextMessageContent(
				data['link']
			),
			description = (
				f"Artist: {data['artist']['name']}" +
				f"\nAlbum: {data['album']['title']}" +
				f"\nDuration: {my_round(data['duration'] / 60)}" +
				f"\nRank: {data['rank']}" +
				f"\nPosition: {data['position']}"
			),
			thumb_url = data['album']['cover_big']
		)
		for data in datas
	]

	return results

def create_result_not_found():
	results = [
		InlineQueryResultGif(
			id = "not_found",
			gif_url = not_found_query_gif,
			thumb_url = not_found_query_gif,
			title = "ERROR 404 :)",
			input_message_content = InputTextMessageContent(
				"YOU ARE WONDERFUL =)"
			),
		)
	]

	return results