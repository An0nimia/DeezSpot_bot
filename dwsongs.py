#!/usr/bin/python3
import os
import json
import shutil
import spotipy
import telepot
import mutagen
import setting
import acrcloud
import requests
import dwytsongs
import deezloader
from time import sleep
from mutagen.mp3 import MP3
from threading import Thread
from mutagen.flac import FLAC
from bs4 import BeautifulSoup
import spotipy.oauth2 as oauth2
from mutagen.easyid3 import EasyID3
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent
downloa = deezloader.Login(setting.username, setting.password)
token = setting.token
bot = telepot.Bot(token)
stage = {}
users = {}
artist = {}
langua = {}
qualit = {}
array2 = []
array3 = []
local = os.getcwd()
temp = 0
goes = 0
config = {
          "key": "d8d8e2b3e982d8413bd8f3f7f3b5b51a",
          "secret": "Xy0DL8AGiG4KBInav12P2TYMKSFRQYyclZyw3cu5",
          "host": "http://identify-eu-west-1.acrcloud.com"
}
if not os.path.isdir(local + "/Songs"):
 os.makedirs(local + "/Songs")
def generate_token():
    credentials = oauth2.SpotifyClientCredentials(client_id="4fe3fecfe5334023a1472516cc99d805", client_secret="0f02b7c483c04257984695007a4a8d5c")
    token = credentials.get_access_token()
    return token
spotoken = generate_token()
spo = spotipy.Spotify(auth=spotoken)
def translate(language, sms):
    try:
       language = language.split("-")[0]
       api = "https://translate.yandex.net/api/v1.5/tr.json/translate?key=trnsl.1.1.20181114T193428Z.ec0fb3fb93e116c0.24b2ccfe2d150324e23a5571760e9a827d953003&text=%s&lang=en-%s" % (sms, language)
       sms = json.loads(requests.get(api).text)['text'][0]
    except:
       None
    return sms
def delete(chat_id):
    global temp
    try:
       users[chat_id] -= 1
    except KeyError:
       None
    array2.append(chat_id)
    temp = 1
def sendAudio(chat_id, audio, image, lang):
    url = "https://api.telegram.org/bot" + token + "/sendAudio"
    try:
       tag = EasyID3(audio.name)
       duration = MP3(audio.name).info.length
    except mutagen.id3._util.ID3NoHeaderError:
       tag = FLAC(audio.name)
       duration = tag.info.length
    data = {
            "chat_id": chat_id,
            "duration": duration,
            "performer": tag['artist'],
            "title": tag['title']
    }
    file = {
            "audio": audio,
            "thumb": requests.get(image).content
    }
    if requests.post(url, params=data, files=file).status_code == 413:
     bot.sendMessage(chat_id, translate(lang, "The song is too big to be sended"))
def Link1(music, chat_id, lang, quality):
    global spo
    image = []
    links = []
    array3.append(chat_id)
    try:
       if "spotify" in music:
        if "track/" in music:
         if "?" in music:
           music,a = music.split("?")
         try:
            url = spo.track(music)
         except Exception as a:
            if not "The access token expired" in str(a):
             delete(chat_id)
             return
            token = generate_token()
            spo = spotipy.Spotify(auth=token)
            url = spo.track(music)
         image.append(url['album']['images'][2]['url'])
         links.append(music)
         z = downloa.download_trackspo(music, check=False, quality=quality, recursive=False)
        elif "album/" in music:
         if "?" in music:
          music,a = music.split("?")
         try:
            tracks = spo.album(music)
         except Exception as a:
            if not "The access token expired" in str(a):
             bot.sendMessage(chat_id, translate(lang, "Invalid link ;)"))
             delete(chat_id)
             return
            token = generate_token()
            spo = spotipy.Spotify(auth=token)
            tracks = spo.album(music)
         b = tracks['total_tracks']   
         for a in range(b):
             image.append(tracks['images'][2]['url'])
         for a in tracks['tracks']['items']:
             links.append(a['external_urls']['spotify'])
         if b != 50:
          for a in range(b // 50):
              try:
                 tracks = spo.next(tracks['tracks'])
              except:
                 token = generate_token()
                 spo = spotipy.Spotify(auth=token)
                 tracks = spo.next(tracks['tracks'])
              for a in tracks['items']:
                  links.append(a['external_urls']['spotify'])
         msg = telepot.message_identifier(bot.sendMessage(chat_id, translate(lang, ("About " + str((b * 13) // 60)) + " minutes")))
         z = downloa.download_albumspo(music, check=False, quality=quality, recursive=False)
        elif "playlist/" in music:
         if "?" in music:
          music,a = music.split("?")
         musi = music.split("/")
         try:
            tracks = spo.user_playlist_tracks(musi[-3], playlist_id=musi[-1])
         except Exception as a:
            if not "The access token expired" in str(a):
             bot.sendMessage(chat_id, translate(lang, "Invalid link ;)"))
             delete(chat_id)
             return
            token = generate_token()
            spo = spotipy.Spotify(auth=token)
            tracks = spo.user_playlist_tracks(musi[-3], playlist_id=musi[-1])
         for a in tracks['items']:
             image.append(a['track']['album']['images'][2]['url'])
             links.append(a['track']['external_urls']['spotify'])
         if tracks['total'] != 100:
          for a in range(tracks['total'] // 100):
              try:
                 tracks = spo.next(tracks)
              except:
                 token = generate_token()
                 spo = spotipy.Spotify(auth=token)
                 tracks = spo.next(tracks)
              for a in tracks['items']:
                  image.append(a['track']['album']['images'][2]['url'])
                  links.append(a['track']['external_urls']['spotify'])
         bot.sendMessage(chat_id, translate(lang, ("About " + str((tracks['total'] * 13) // 60)) + " minutes"))
         z = downloa.download_playlistspo(music, check=False, quality=quality, recursive=False)
       elif "deezer" in music:
        if "track/" in music:
         if "?" in music:
          music,a = music.split("?")
         url = json.loads(requests.get("http://api.deezer.com/track/" + music.split("/")[-1]).text)
         try:
            if "error" in str(url):
             bot.sendMessage(chat_id, translate(lang, "Invalid link ;)"))
             delete(chat_id)
             return
         except KeyError:
            None
         try:
            image.append(url['album']['cover_xl'].replace("1000", "90"))
         except:
            URL = "http://www.deezer.com/track/" + music.split("/")[-1]
            try:
               images = requests.get(URL).text
            except:
               images = requests.get(URL).text
            image.append(BeautifulSoup(images, "html.parser").find("img", class_="img_main").get("src").replace("200", "1200"))
         z = downloa.download_trackdee(music, check=False, quality=quality, recursive=False)
        elif "album/" in music:
         if "?" in music:
          music,a = music.split("?")
         url = json.loads(requests.get("http://api.deezer.com/album/" + music.split("/")[-1]).text)
         try:
            if "error" in str(url):
             bot.sendMessage(chat_id, translate(lang, "Invalid link ;)"))
             delete(chat_id)
             return
         except KeyError:
            None
         for a in range(url['nb_tracks']):
             try:
                image.append(url['cover_xl'].replace("1000", "90"))
             except:
                URL = "http://www.deezer.com/album/" + music.split("/")[-1]
                try:
                   images = requests.get(URL).text
                except:
                   images = requests.get(URL).text
                image.append(BeautifulSoup(images, "html.parser").find("img", class_="img_main").get("src").replace("200", "1200"))
         b = url['nb_tracks']
         msg = telepot.message_identifier(bot.sendMessage(chat_id,  translate(lang, ("About " + str((b * 13) // 60)) + " minutes")))
         z = downloa.download_albumdee(music, check=False, quality=quality, recursive=False)
        elif "playlist/" in music:
         if "?" in music:
          music,a = music.split("?")
         url = json.loads(requests.get("https://api.deezer.com/playlist/" + music.split("/")[-1]).text)
         try:
            if "error" in str(url):
             bot.sendMessage(chat_id, translate(lang, "Invalid link ;)"))
             delete(chat_id)
             return
         except KeyError:
            None
         times = 0
         for a in url['tracks']['data']:
             image.append(json.loads(requests.get("http://api.deezer.com/track/" + str(a['id'])).text)['album']['cover_xl'].replace("1000", "90"))
             links.append(a['link'])
             times += 1
         bot.sendMessage(chat_id, translate(lang, ("About " + str((times * 13) // 60)) + " minutes"))
         z = downloa.download_playlistdee(music, check=False, quality=quality, recursive=False)  
       if type(z) is str:
        z = [z] 
       for b in range(len(z)):
           try:
              sendAudio(chat_id, open(z[b], "rb"), image[b], lang)
           except FileNotFoundError:
              Link2(chat_id, links[b], image, lang)
    except deezloader.TrackNotFound:
       Link2(chat_id, music, image, lang)
    except deezloader.AlbumNotFound:
       bot.deleteMessage(msg)
       bot.sendMessage(chat_id, translate(lang, ("About " + str((b * 40) // 60)) + " minutes"))
       Link2(chat_id, music, image, lang)
    except deezloader.InvalidLink as error:
       bot.sendMessage(chat_id, translate(lang, str(error)))
    except dwytsongs.TrackNotFound as error:
       bot.sendMessage(chat_id, translate(lang, str(error) + " :("))
    except UnboundLocalError:
       bot.sendMessage(chat_id, translate(lang, "Invalid link ;)")) 
    delete(chat_id)
def Link2(chat_id, music, image, lang):
    if "spotify" in music:
     if "track" in music:
      z = dwytsongs.download_trackspo(music, check=False)
     elif "album" in music:
      z = dwytsongs.download_albumspo(music, check=False)
    elif "deezer" in music:
     if "track" in music:
      z = dwytsongs.download_trackdee(music, check=False)
     elif "album" in music:
      z = dwytsongs.download_albumdee(music, check=False)
    if type(z) is str:
     z = [z]
    for a in range(len(z)):
        try:
           sendAudio(chat_id, open(z[a], "rb"), image[a], lang)
        except FileNotFoundError:
           bot.sendMessage(chat_id, translate(lang, "Error downloading " + z[a].split(".")[-1] + " :("))
def Audio(audio, chat_id, lang):
    global spo
    global goes
    langua[chat_id] = lang
    goes = 1
    file = local + "/Songs/" + audio + ".ogg"
    bot.download_file(audio, file)
    audio = acrcloud.recognizer(config, file)
    print(audio)
    try:
       os.remove(file)
    except FileNotFoundError:
       None
    if audio['status']['msg'] != "Success":
     bot.sendMessage(chat_id, translate(lang, "Sorry cannot detect the song from audio :(, retry..."))
    else:
        artist = audio['metadata']['music'][0]['artists'][0]['name']
        track = audio['metadata']['music'][0]['title']
        album = audio['metadata']['music'][0]['album']['name']
        try:
           date = audio['metadata']['music'][0]['release_date']
           album += ">" + date
        except KeyError:
           None 
        try:
           label = audio['metadata']['music'][0]['label']
           album += ">" + label
        except KeyError:
           None
        try:
           genre = audio['metadata']['music'][0]['genres'][0]['name']
           album += ">" + genre
        except KeyError:
           None
        if len(album) > 64:
         album = "Infos with too many bytes"
        elif len(album.split(">")) == 1:
         album = "No informations"
        url = json.loads(requests.get("https://api.deezer.com/search/track/?q=" + track.replace("#", "") + " + " + artist.replace("#", "")).text)
        try:
           for a in range(url['total'] + 1):
               if url['data'][a]['title'] == track:
                id = url['data'][a]['link']
                image = url['data'][a]['album']['cover_xl']
                break
        except IndexError:
           try:
              id = "https://open.spotify.com/track/" + audio['metadata']['music'][0]['external_metadata']['spotify']['track']['id']
              try:
                 url = spo.track(id)
              except:
                 token = generate_token()
                 spo = spotipy.Spotify(auth=token)
                 url = spo.track(id)
              image = url['album']['images'][0]['url']
           except KeyError:
              None
           try:
              id = "https://www.deezer.com/track/" + str(audio['metadata']['music'][0]['external_metadata']['deezer']['track']['id'])
              url = json.loads(requests.get("http://api.deezer.com/track/" + id.split("/")[-1]).text)
              image = url['album']['cover_xl']
           except KeyError:
              None
        try:
           bot.sendPhoto(chat_id, image, caption=track + " - " + artist,
                         reply_markup=InlineKeyboardMarkup(
                                     inline_keyboard=[
                                                [InlineKeyboardButton(text="Download", callback_data=id), InlineKeyboardButton(text="Info", callback_data=album)]
                                     ]
                         ))
        except:
           bot.sendMessage(chat_id, translate(lang, "Error :("))
    goes = 2
def download(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor="callback_query")
    tags = query_data.split(">")
    if query_data == "Infos with too many bytes" or query_data == "No informations":
     bot.answerCallbackQuery(query_id, translate(langua[from_id], query_data))
    elif len(tags) == 2:
     bot.answerCallbackQuery(query_id, text="Album: " + tags[0] + "\nDate: " + tags[1], show_alert=True)
    elif len(tags) == 3:
     bot.answerCallbackQuery(query_id, text="Album: " + tags[0] + "\nDate: " + tags[1] + "\nLabel: " + tags[2], show_alert=True)
    elif len(tags) == 4:
     bot.answerCallbackQuery(query_id, text="Album: " + tags[0] + "\nDate: " + tags[1] + "\nLabel: " + tags[2] + "\nGenre: " + tags[3], show_alert=True)
    else:
        if ans != "1":
         try:
            if users[from_id] == 2:
             bot.answerCallbackQuery(query_id, translate(langua[from_id], "Wait to finish and repress download, did you thought that you could download how much songs did you want? :)"), show_alert=True)
             return
            else:
                users[from_id] += 1
         except KeyError:
            users[from_id] = 1
        bot.answerCallbackQuery(query_id, translate(langua[from_id], "Song is downloading"))
        try:
           name = qualit[from_id]
        except KeyError:
           qualit[from_id] = "MP3_320"
        Thread(target=Link1, args=(query_data, from_id, langua[from_id], qualit[from_id])).start()
def search(msg):
    global spo
    query_id, from_id, query_string = telepot.glance(msg, flavor='inline_query')
    query_string = query_string.split(",")
    try:
       if len(query_string) == 2:
        search = spo.search(q="track:" + query_string[0] + " artist:" + query_string[1], limit=30)
       else:
           search = spo.search(q="track:" + query_string[0], limit=30)
    except:
       token = generate_token()
       spo = spotipy.Spotify(auth=token)
       if len(query_string) == 2:
        search = spo.search(q="track:" + query_string[0] + " artist:" + query_string[1], limit=30)
       else:
           search = spo.search(q="track:" + query_string[0], limit=30)
    try:       
       result = ([InlineQueryResultArticle(id=a['external_urls']['spotify'], title=a['name'] + "\n" + a['artists'][0]['name'], thumb_url=a['album']['images'][0]['url'], input_message_content=
                                              InputTextMessageContent(message_text=a['external_urls']['spotify'])
                                             ) for a in search['tracks']['items']
                ])
    except IndexError:
       return
    try:
       bot.answerInlineQuery(query_id, result)
    except telepot.exception.TelegramError:
       None
def up(msg):
    result_id, from_id, query_string = telepot.glance(msg, flavor='chosen_inline_result')
    if ans != "1":
     try:
        if users[from_id] == 2:
         bot.sendMessage(from_id, translate(msg['from']['language_code'], "You are downloading to much songs :)"))
         return
        else:
            users[from_id] += 1
     except KeyError:
        users[from_id] = 1
    try:
       name = qualit[from_id]
    except KeyError:
       qualit[from_id] = "MP3_320"
    Thread(target=Link1, args=(result_id, from_id, msg['from']['language_code'] ,qualit[from_id])).start()
def start1(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    try:
        stage[chat_id]
    except KeyError:
        stage[chat_id] = 0
    if content_type == "text" and msg['text'] == "/start":
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Welcome to @DeezloaderRMX_bot"))
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "This bot has been created for download songs by a Spotify or Deezer link, by an artist and song name or by an audio or voice message"))
     bot.sendPhoto(chat_id, open("example.jpg", "rb"), caption="The bot commands can find here")
    elif content_type == "text" and msg['text'] == "/link":
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Insert a Deezer or Spotify link to download"))
     stage[chat_id] = 1
    elif content_type == "text" and msg['text'] != "/link" and msg['text'] != "/name" and msg['text'] != "/quality" and stage[chat_id] == 1:
     music = msg['text']
     try:
        name = qualit[chat_id]
     except KeyError:
        qualit[chat_id] = "MP3_320"
     Thread(target=Link1, args=(music, chat_id, msg['from']['language_code'], qualit[chat_id])).start()
    elif content_type == "text" and msg['text'] == "/name":
     try:
        name = qualit[chat_id]
     except KeyError:
        qualit[chat_id] = "MP3_320"
     langua[chat_id] = msg['from']['language_code']
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Press for search songs \n P.S. Insert like this: 'song name, artist's name'"),
                    reply_markup=InlineKeyboardMarkup(
                                     inline_keyboard=[
                                                [InlineKeyboardButton(text="Search", switch_inline_query_current_chat="")]
                                     ]
                         ))
     stage[chat_id] = 2 
    elif content_type == "text" and msg['text'] == "/quality":
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Choose the quality that you want to download the song"),
                     reply_markup=ReplyKeyboardMarkup(
                                 keyboard=[
                                     [KeyboardButton(text="FLAC"), KeyboardButton(text="MP3_320")],
                                     [KeyboardButton(text="MP3_256"), KeyboardButton(text="MP3_128")]
                                 ]
                     ))
     stage[chat_id] = 3
    elif content_type == "text" and (msg['text'] == "FLAC" or msg['text'] == "MP3_320" or msg['text'] == "MP3_256" or msg['text'] == "MP3_128") and stage[chat_id] == 3:
     qualit[chat_id] = msg['text']
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "The songs will be downloaded with " + msg['text'] + " quality"), reply_markup=ReplyKeyboardRemove())
     if msg['text'] != "MP3_128":
      bot.sendMessage(chat_id, translate(msg['from']['language_code'], "The songs that cannot be downloaded with the quality that you choose will be downloaded in quality MP3_128"))
     stage[chat_id] = 4
    elif content_type == "voice" or content_type == "audio":
     audio = msg[content_type]['file_id']
     try:
        name = qualit[chat_id]
     except KeyError:
        qualit[chat_id] = "MP3_320"
     Thread(target=Audio, args=(audio, chat_id, msg['from']['language_code'])).start()
def start2(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    try:
        stage[chat_id]
    except KeyError:
        stage[chat_id] = 0
    if content_type == "text" and msg['text'] == "/start":
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Welcome to @DeezloaderRMX_bot"))
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "This bot has been created for download songs by a Spotify or Deezer link, by an artist and song name or by an audio or voice message"))
     bot.sendPhoto(chat_id, open("example.jpg", "rb"), caption=translate(msg['from']['language_code'], "The bot commands can find here"))
    elif content_type == "text" and msg['text'] == "/link":
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Insert a Deezer or Spotify link to download"))
     stage[chat_id] = 1
    elif content_type == "text" and msg['text'] != "/link" and msg['text'] != "/name" and msg['text'] != "/quality" and stage[chat_id] == 1:
     music = msg['text']
     try:
        name = qualit[chat_id]
     except KeyError:
        qualit[chat_id] = "MP3_320"
     print(msg)
     try:
        if users[chat_id] == 2:
         bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Wait to finish and resend the " + content_type + ", did you thought that you could download how much songs did you want? :)"))
        else:
            users[chat_id] += 1
            Thread(target=Link1, args=(music, chat_id, msg['from']['language_code'], qualit[chat_id])).start()
     except KeyError:
        users[chat_id] = 1
        Thread(target=Link1, args=(music, chat_id, msg['from']['language_code'], qualit[chat_id])).start()
    elif content_type == "text" and msg['text'] == "/name":
     try:
        name = qualit[chat_id]
     except KeyError:
        qualit[chat_id] = "MP3_320"
     langua[chat_id] = msg['from']['language_code']
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Press for search songs \n P.S. Insert like this: 'song name, artist's name'"),
                    reply_markup=InlineKeyboardMarkup(
                                     inline_keyboard=[
                                                [InlineKeyboardButton(text="Search", switch_inline_query_current_chat="")]
                                     ]
                         ))
     stage[chat_id] = 2
    elif content_type == "text" and msg['text'] == "/quality":
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Choose the quality that you want to download the song"),
                     reply_markup=ReplyKeyboardMarkup(
                                 keyboard=[
                                     [KeyboardButton(text="FLAC"), KeyboardButton(text="MP3_320")],
                                     [KeyboardButton(text="MP3_256"), KeyboardButton(text="MP3_128")]
                                 ]
                     ))
     stage[chat_id] = 3
    elif content_type == "text" and (msg['text'] == "FLAC" or msg['text'] == "MP3_320" or msg['text'] == "MP3_256" or msg['text'] == "MP3_128") and stage[chat_id] == 3:
     qualit[chat_id] = msg['text']
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "The songs will be downloaded with " + msg['text'] + " quality"), reply_markup=ReplyKeyboardRemove())
     if msg['text'] != "MP3_128":
      bot.sendMessage(chat_id, translate(msg['from']['language_code'], "The songs that cannot be downloaded with the quality that you choose will be downloaded in quality MP3_128"))
     stage[chat_id] = 4
    elif content_type == "voice" or content_type == "audio":
     audio = msg[content_type]['file_id']
     try:
        name = qualit[chat_id]
     except KeyError:
        qualit[chat_id] = "MP3_320"
     Thread(target=Audio, args=(audio, chat_id, msg['from']['language_code'])).start()
try:
   while True:
       print("1):Free")
       print("2):Strict")
       print("3):Exit")
       ans = input("Choose:")
       if ans == "1":
        bot.message_loop({
                          "chat": start1,
                          "callback_query": download,
                          "inline_query": search,
                          "chosen_inline_result": up
                         })
       elif ans == "2":
        bot.message_loop({
                          "chat": start2,
                          "callback_query": download,
                          "inline_query": search,
                          "chosen_inline_result": up
                         })
       else:
           break
       print("Bot started")
       while True:
           sleep(1)
           if temp == 1 and (goes == 0 or goes == 2):
            if len(array2) == len(array3):
             for a in os.listdir(local + "/Songs"):
                 shutil.rmtree(local + "/Songs/" + a)
                 del array2[:]
                 del array3[:]
except KeyboardInterrupt:
   os.rmdir(local + "/Songs")
   print("\nSTOPPED")
