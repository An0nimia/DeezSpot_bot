#!/usr/bin/python3
import os
import sys
import json
import shutil
import sqlite3
import spotipy
import telepot
import mutagen
import setting
import logging
import acrcloud
import requests
import dwytsongs
import deezloader
from time import sleep
from pprint import pprint
from mutagen.mp3 import MP3
from threading import Thread
from datetime import datetime
from mutagen.flac import FLAC
from bs4 import BeautifulSoup
import spotipy.oauth2 as oauth2
from mutagen.easyid3 import EasyID3
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent
downloa = deezloader.Login(setting.username, setting.password)
token = setting.token
bot = telepot.Bot(token)
users = {}
qualit = {}
date = {}
array2 = []
array3 = []
local = os.getcwd()
temp = 0
goes = 0
FMT = "%H:%M:%S"
logging.basicConfig(filename="dwsongs.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
config = {
          "key": "d8d8e2b3e982d8413bd8f3f7f3b5b51a",
          "secret": "Xy0DL8AGiG4KBInav12P2TYMKSFRQYyclZyw3cu5",
          "host": "https://identify-eu-west-1.acrcloud.com"
}
if not os.path.isdir("Songs"):
 os.makedirs("Songs")
db_file = local + "/dwsongs.db"
loc_dir = local + "/Songs/"
conn = sqlite3.connect(db_file)
c = conn.cursor()
try:
   c.execute("CREATE TABLE DWSONGS (id text, query text, quality text)")
   c.execute("CREATE TABLE BANNED (banned int)")
   c.execute("CREATE TABLE CHAT_ID (chat_id int)")
   conn.commit()
except sqlite3.OperationalError:
   None
def generate_token():
    token = oauth2.SpotifyClientCredentials(client_id="4fe3fecfe5334023a1472516cc99d805", client_secret="0f02b7c483c04257984695007a4a8d5c").get_access_token()
    return token
spo = spotipy.Spotify(auth=generate_token())
def statisc(chat_id, do):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    if do == "USERS":
     c.execute("SELECT chat_id FROM CHAT_ID where chat_id = '%d'" % chat_id)
     if c.fetchone() == None:
      while True:
          sleep(1)
          try:
             c.execute("INSERT INTO CHAT_ID(chat_id) values('%d')" % chat_id)
             conn.commit()
             break
          except sqlite3.OperationalError:
             None
     c.execute("SELECT chat_id FROM CHAT_ID")
     infos = len(c.fetchall())
    elif do == "TRACKS":
     c.execute("SELECT id FROM DWSONGS")
     infos = len(c.fetchall())
    conn.close()
    return str(infos)
def check_flood(chat_id, lang, msg):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT banned FROM BANNED where banned = '%d'" % chat_id)
    if c.fetchone() != None:
     conn.close()
     return "BANNED"
    try:
       time = msg['date'] - date[chat_id]['time']
       date[chat_id]['time'] = msg['date']
       if time <= 4:
        date[chat_id]['msg'] += 1
        if time <= 4 and date[chat_id]['msg'] > 4:
         date[chat_id]['msg'] = 0
         date[chat_id]['tries'] -= 1
         bot.sendMessage(chat_id, translate(lang, "It is appearing that you are trying to flood, you have to wait more that four second to send another message.\n" + str(date[chat_id]['tries']) + " possibilites :)"))
         if date[chat_id]['tries'] == 0:
          while True:
              sleep(1)
              try:
                 c.execute("INSERT INTO BANNED(banned) values('%d')" % chat_id)
                 conn.commit()
                 conn.close()
                 break
              except sqlite3.OperationalError:
                 None
          del date[chat_id]
          bot.sendMessage(chat_id, translate(lang, "You are banned :)"))
          return
    except KeyError:
       try: 
          date[chat_id] = {"time": msg['date'], "tries": 3, "msg": 0}
       except KeyError:
          None
def translate(language, sms):
    try:
       language = language.split("-")[0]
       api = "https://translate.yandex.net/api/v1.5/tr.json/translate?key=trnsl.1.1.20181114T193428Z.ec0fb3fb93e116c0.24b2ccfe2d150324e23a5571760e9a827d953003&text=%s&lang=en-%s" % (sms, language)
       try:
          sms = json.loads(requests.get(api).text)['text'][0]
       except:
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
def sendAudio(chat_id, audio, lang, music, image=None):
    bot.sendChatAction(chat_id, "upload_audio")
    try:
       url = "https://api.telegram.org/bot" + token + "/sendAudio"
       if os.path.isfile(audio):
        audio = open(audio, "rb")
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
        try:
           request = requests.post(url, params=data, files=file)
        except:
           request = requests.post(url, params=data, files=file)
        if request.status_code == 413:
         bot.sendMessage(chat_id, translate(lang, "The song is too big to be sent"))
        else:
            audio = json.loads(request.text)['result']['audio']['file_id']
            conn = sqlite3.connect(db_file)
            c = conn.cursor()
            while True:
                sleep(1)
                try:
                   c.execute("INSERT INTO DWSONGS(id, query, quality) values('%s', '%s', '%s')" % (music, audio, qualit[chat_id]))
                   conn.commit()
                   conn.close()
                   break
                except sqlite3.OperationalError:
                   None
       else:
           bot.sendAudio(chat_id, audio)
    except Exception as a:
       logging.info(chat_id)
       logging.warning(a)
       bot.sendMessage(chat_id, translate(lang, "An error has occured during sending song, please contact @An0nimia for explain the issue, thanks :)"))
def track(music, chat_id, lang, quality):
    global spo
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT query FROM DWSONGS WHERE id = '%s' and quality = '%s'" % (music, quality))
    z = c.fetchone()
    conn.close()
    if z != None:
     sendAudio(chat_id, z[0], lang, music)
    else: 
        try:
           if "spotify" in music:
            try:
               url = spo.track(music)
            except:
               token = generate_token()
               spo = spotipy.Spotify(auth=token)
               url = spo.track(music)
            image = url['album']['images'][2]['url']
            z = downloa.download_trackspo(music, check=False, quality=quality, recursive=False)
           elif "deezer" in music:
            try:
               url = json.loads(requests.get("https://api.deezer.com/track/" + music.split("/")[-1]).text)
            except:
               url = json.loads(requests.get("https://api.deezer.com/track/" + music.split("/")[-1]).text)
            try:
               if url['error']:
                bot.sendMessage(chat_id, translate(lang, "Track not found :(\nhttps://www.deezer.com/track/" + music.split("/")[-1]))
                return
            except KeyError:
               None
            try:
               image = url['album']['cover_xl'].replace("1000", "90")
            except AttributeError:
               URL = "https://www.deezer.com/track/" + music.split("/")[-1]
               try:
                  imag = requests.get(URL).text
               except:
                  imag = requests.get(URL).text
               image = BeautifulSoup(imag, "html.parser").find("img", class_="img_main").get("src").replace("120", "90")
            z = downloa.download_trackdee(music, check=False, quality=quality, recursive=False)
        except deezloader.TrackNotFound:
           try:
              if "spotify" in music:
               z = dwytsongs.download_trackspo(music, check=False)
              elif "deezer" in music:
               z = dwytsongs.download_trackdee(music, check=False)
           except dwytsongs.TrackNotFound as error:
              bot.sendMessage(chat_id, translate(lang, str(error) + " :("))
              return
        except Exception as a:
           logging.info(chat_id)
           logging.warning(a)
           logging.warning(music)
           bot.sendMessage(chat_id, translate(lang, "An error has occured during downloading song, please contact @An0nimia for explain the issue, thanks :)"))
           return
        sendAudio(chat_id, z, lang, music, image)
def Link(music, chat_id, lang, quality, msg):
    global spo
    done = 0
    links1 = []
    links2 = []
    image = []
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
             bot.sendMessage(chat_id, translate(lang, "Invalid link ;"), reply_to_message_id=msg)
             delete(chat_id)
             return
            token = generate_token()
            spo = spotipy.Spotify(auth=token)
            url = spo.track(music)
         bot.sendPhoto(chat_id, url['album']['images'][0]['url'], caption="Track:" + url['name'] + "\nArtist:" + url['album']['artists'][0]['name'] + "\nAlbum:" + url['album']['name'] + "\nDate:" + url['album']['release_date'])
         track(music, chat_id, lang, quality)
         done = 1
        elif "album/" in music:
         if "?" in music:
          music,a = music.split("?")
         try:
            tracks = spo.album(music)
         except Exception as a:
            if not "The access token expired" in str(a):
             bot.sendMessage(chat_id, translate(lang, "Invalid link ;"), reply_to_message_id=msg)
             delete(chat_id)
             return
            token = generate_token()
            spo = spotipy.Spotify(auth=token)
            tracks = spo.album(music)
         for a in range(tracks['total_tracks']):
             image.append(tracks['images'][2]['url'])
         conn = sqlite3.connect(db_file)
         c = conn.cursor()
         for a in tracks['tracks']['items']:
             c.execute("SELECT query FROM DWSONGS WHERE id = '%s' and quality = '%s'" % (a['external_urls']['spotify'], quality))
             links2.append(a['external_urls']['spotify'])
             if c.fetchone() != None:
              links1.append(a['external_urls']['spotify'])
         bot.sendPhoto(chat_id, tracks['images'][0]['url'], caption="Album:" + tracks['name'] + "\nArtist:" + tracks['artists'][0]['name'] + "\nDate:" + tracks['release_date'] + "\nTracks number:" + str(tracks['total_tracks']))
         tot = tracks['total_tracks']
         tracks = tracks['tracks']
         if tot != 50:
            for a in range(tot // 50):
                try:
                   tracks2 = spo.next(tracks)
                except:
                   token = generate_token()
                   spo = spotipy.Spotify(auth=token)
                   tracks2 = spo.next(tracks)
                for a in tracks2['items']:
                    c.execute("SELECT query FROM DWSONGS WHERE id = '%s' and quality = '%s'" % (a['external_urls']['spotify'], quality))
                    links2.append(a['external_urls']['spotify'])
                    if c.fetchone() != None:
                     links1.append(a['external_urls']['spotify'])
         conn.close()
         if len(links1) <= (tot // 2):
          z = downloa.download_albumspo(music, check=False, quality=quality, recursive=False)
         else:
             for a in links2:
                 track(a, chat_id, lang, quality)
         done = 1
        elif "playlist/" in music:
         if "?" in music:
          music,a = music.split("?")
         musi = music.split("/")
         try:
            tracks = spo.user_playlist(musi[-3], playlist_id=musi[-1])
         except Exception as a:
            if not "The access token expired" in str(a):
             bot.sendMessage(chat_id, translate(lang, "Invalid link ;"), reply_to_message_id=msg)
             delete(chat_id)
             return
            token = generate_token()
            spo = spotipy.Spotify(auth=token)
            tracks = spo.user_playlist(musi[-3], playlist_id=musi[-1])
         try:
            bot.sendPhoto(chat_id, tracks['images'][0]['url'], caption="Creation:" + tracks['tracks']['items'][0]['added_at'] + "\nUser:" + tracks['owner']['display_name'] + "\nTracks number:" + str(tracks['tracks']['total']))
         except TypeError:
            bot.sendPhoto(chat_id, tracks['images'][0]['url'], caption="Creation:" + tracks['tracks']['items'][0]['added_at'] + "\nTracks number:" + str(tracks['tracks']['total']))
         for a in tracks['tracks']['items']:
             track(a['track']['external_urls']['spotify'], chat_id, lang, quality)
         tot = tracks['tracks']['total']
         tracks = tracks['tracks']
         if tot != 100:
            for a in range(tot // 100):
                try:
                   tracks = spo.next(tracks)
                except:
                   token = generate_token()
                   spo = spotipy.Spotify(auth=token)
                   tracks = spo.next(tracks)
                for a in tracks['items']:
                    track(a['track']['external_urls']['spotify'], chat_id, lang, quality)
         done = 1
        else:
            bot.sendMessage(chat_id, translate(lang, "Sorry :( The bot doesn't support this link"))
       elif "deezer" in music:
        if "track/" in music:
         if "?" in music:
          music,a = music.split("?")
         try:
            url = json.loads(requests.get("https://api.deezer.com/track/" + music.split("/")[-1]).text)
         except:
            url = json.loads(requests.get("https://api.deezer.com/track/" + music.split("/")[-1]).text)
         try:
            if url['error']:
             bot.sendMessage(chat_id, translate(lang, "Invalid link ;)"), reply_to_message_id=msg)
             delete(chat_id)
             return
         except KeyError:
            None
         imag = url['album']['cover_xl']
         if imag == None:
          URL = "https://www.deezer.com/track/" + music.split("/")[-1]
          try:
             imag = requests.get(URL).text
          except:
             imag = requests.get(URL).text
          imag = BeautifulSoup(imag, "html.parser").find("img", class_="img_main").get("src").replace("120", "1000")
         artist = url['artist']['name']
         bot.sendPhoto(chat_id, imag, caption="Track:" + url['title'] + "\nArtist:" + artist + "\nAlbum:" + url['album']['title'] + "\nDate:" + url['album']['release_date'])
         track(music, chat_id, lang, quality)
         done = 1
        elif "album/" in music:
         if "?" in music:
          music,a = music.split("?")
         try:
            url = json.loads(requests.get("https://api.deezer.com/album/" + music.split("/")[-1]).text)
         except:
            url = json.loads(requests.get("https://api.deezer.com/album/" + music.split("/")[-1]).text)
         try:
            if url['error']:
             bot.sendMessage(chat_id, translate(lang, "Invalid link ;"), reply_to_message_id=msg)
             delete(chat_id)
             return
         except KeyError:
            None
         imag = url['cover_xl']
         if imag == None:
          URL = "https://www.deezer.com/album/" + music.split("/")[-1]
          try:
             imag = requests.get(URL).text
          except:
             imag = requests.get(URL).text
          imag = BeautifulSoup(imag, "html.parser").find("img", class_="img_main").get("src").replace("200", "1000")
         conn = sqlite3.connect(db_file)
         c = conn.cursor()
         for a in url['tracks']['data']:
             image.append(imag.replace("1000", "90"))
             c.execute("SELECT query FROM DWSONGS WHERE id = '%s' and quality = '%s'" % (a['link'], quality))
             links2.append(a['link'])
             if c.fetchone() != None:
              links1.append(a['link'])
         conn.close()
         artist = url['artist']['name']
         bot.sendPhoto(chat_id, imag, caption="Album:" + url['title'] + "\nArtist:" + artist + "\nDate:" + url['release_date'] + "\nTracks number:" + str(url['nb_tracks']))
         if len(links1) <= (url['nb_tracks'] // 2):
          z = downloa.download_albumdee(music, check=False, quality=quality, recursive=False)
         else:
             for a in links2:
                 track(a, chat_id, lang, quality)
         done = 1
        elif "playlist/" in music:
         if "?" in music:
          music,a = music.split("?")
         try:
            url = json.loads(requests.get("https://api.deezer.com/playlist/" + music.split("/")[-1]).text)
         except:
            url = json.loads(requests.get("https://api.deezer.com/playlist/" + music.split("/")[-1]).text)
         try:
            if url['error']:
             bot.sendMessage(chat_id, translate(lang, "Invalid link ;"), reply_to_message_id=msg)
             delete(chat_id)
             return
         except KeyError:
            None
         if url['duration'] == 0:
          bot.sendMessage(chat_id, translate(lang, "Invalid link ;"), reply_to_message_id=msg)
          delete(chat_id)
          return
         bot.sendPhoto(chat_id, url['picture_xl'], caption="Creation:" + url['creation_date'] + "\nUser:" + url['creator']['name'] + "\nTracks number:" + str(url['nb_tracks']))
         for a in url['tracks']['data']:
             track(a['link'], chat_id, lang, quality)
         done = 1
        else:
            bot.sendMessage(chat_id, translate(lang, "Sorry :( The bot doesn't support this link"))
       try:
          for a in range(len(z)):
              sendAudio(chat_id, z[a], lang, links2[a], image[a])
       except NameError:
          None
    except deezloader.AlbumNotFound:
       bot.sendMessage(chat_id, translate(lang, "Album not found :("))
       bot.sendMessage(chat_id, translate(lang, "Try to search it throught inline mode or search the link on Deezer"))
    except Exception as a:
       logging.info(chat_id)
       logging.warning(a)
       logging.warning(music)
       bot.sendMessage(chat_id, translate(lang, "An error has occured during downloading song, please contact @An0nimia for explain the issue, thanks :)"))
    if done == 1:
     bot.sendMessage(chat_id, translate(lang, "FINISHED :)"), reply_to_message_id=msg)
    delete(chat_id)
def Audio(audio, chat_id, lang):
    global spo
    global goes
    goes = 1
    file = loc_dir + audio + ".ogg"
    try:
       bot.download_file(audio, file)
    except telepot.exception.TelegramError:
       bot.sendMessage(chat_id, translate(lang, "File sent too big, please send a file max 20 MB size"))
       return
    audio = acrcloud.recognizer(config, file)
    try:
       os.remove(file)
    except FileNotFoundError:
       None
    if audio['status']['msg'] != "Success":
     bot.sendMessage(chat_id, translate(lang, "Sorry cannot detect the song from audio :(, retry..."))
    else:
        bot.sendChatAction(chat_id, "upload_photo")
        artist = audio['metadata']['music'][0]['artists'][0]['name']
        track = audio['metadata']['music'][0]['title']
        album = audio['metadata']['music'][0]['album']['name']
        try:
           date = audio['metadata']['music'][0]['release_date']
           album += "_" + date
        except KeyError:
           None 
        try:
           label = audio['metadata']['music'][0]['label']
           album += "_" + label
        except KeyError:
           None
        try:
           genre = audio['metadata']['music'][0]['genres'][0]['name']
           album += "_" + genre
        except KeyError:
           None
        if len(album) > 64:
         album = "Infos with too many bytes"
        elif len(album.split("_")) == 1:
         album = "No informations"
        try: 
           url = json.loads(requests.get("https://api.deezer.com/search/track/?q=" + track.replace("#", "") + " + " + artist.replace("#", "")).text)
        except:
           url = json.loads(requests.get("https://api.deezer.com/search/track/?q=" + track.replace("#", "") + " + " + artist.replace("#", "")).text) 
        try:
           for a in range(url['total'] + 1):
               if url['data'][a]['title'] == track:
                id = url['data'][a]['link']
                image = url['data'][a]['album']['cover_xl']
                break
        except IndexError:
           try:
              try:
                 id = "https://open.spotify.com/track/" + audio['metadata']['music'][0]['external_metadata']['spotify']['track']['id']
              except:
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
              try:
                 url = json.loads(requests.get("https://api.deezer.com/track/" + id.split("/")[-1]).text)
              except:
                 url = json.loads(requests.get("https://api.deezer.com/track/" + id.split("/")[-1]).text)
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
    try:
       msg['from']['language_code']
    except KeyError:
       msg['from'] = {"language_code": "en"}
    lang = msg['from']['language_code']
    tags = query_data.split("_")
    if query_data == "Infos with too many bytes" or query_data == "No informations":
     bot.answerCallbackQuery(query_id, translate(lang, query_data))
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
             bot.answerCallbackQuery(query_id, translate(lang, "Wait to finish and press download again, did you thought that you could download how much songs did you want? :)"), show_alert=True)
             return
            else:
                users[from_id] += 1
         except KeyError:
            users[from_id] = 1
        bot.answerCallbackQuery(query_id, translate(lang, "Song is downloading"))
        try:
           qualit[from_id]
        except KeyError:
           qualit[from_id] = "MP3_320"
        Thread(target=Link, args=(query_data, from_id, lang, qualit[from_id], msg['message']['message_id'])).start()
def search(msg):
    query_id, from_id, query_string = telepot.glance(msg, flavor='inline_query')
    if query_string == "":
     return
    try:
       msg['from']['language_code']
    except KeyError:
       msg['from'] = {"language_code": "en"}
    if check_flood(from_id, msg['from']['language_code'], msg) == "BANNED":
     return
    try:
       search1 = json.loads(requests.get("https://api.deezer.com/search?q=" + query_string.replace("#", "")).text)
    except:
       search1 = json.loads(requests.get("https://api.deezer.com/search?q=" + query_string.replace("#", "")).text)
    try:
       if search1['error']:
        return
    except KeyError:
       None
    search1 = search1['data']
    for a in search1:
        try:
           if "https://www.deezer.com/album/" + str(a['album']['id']) in str(search1):
            continue
        except KeyError:
           continue    
        search1.append({"link": "https://www.deezer.com/album/" + str(a['album']['id'])})
        search1[len(search1) - 1]['title'] = a['album']['title'] + " (Album)"
        search1[len(search1) - 1]['artist'] = {"name": a['artist']['name']}
        if a['album']['cover_xl'] != None:
         search1[len(search1) - 1]['album'] = {"cover_xl": a['album']['cover_xl']}
        else:
            try:
               url = requests.get("https://www.deezer.com/album/" + str(a['album']['id'])).text
            except:
               url = requests.get("https://www.deezer.com/album/" + str(a['album']['id'])).text
            search1[len(search1) - 1]['album'] = {"cover_xl": BeautifulSoup(url, "html.parser").find("img", class_="img_main").get("src").replace("200", "1000")}
    result = [InlineQueryResultArticle(id=a['link'], title=a['title'] + "\n" + a['artist']['name'], thumb_url=a['album']['cover_xl'], input_message_content=InputTextMessageContent(message_text=a['link'])) for a in search1]
    try:
       bot.answerInlineQuery(query_id, result)
    except telepot.exception.TelegramError:
       None
def up(msg):
    pass
def start1(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    try:
       msg['from']['language_code']
    except KeyError:
       msg['from'] = {"language_code": "en"}
    lang = msg['from']['language_code']
    if check_flood(chat_id, lang, msg) == "BANNED":
     return
    statisc(chat_id, "USERS")
    if content_type == "text" and msg['text'] == "/start":
     bot.sendPhoto(chat_id, open("example.jpg", "rb"), caption=translate(lang, "The bot commands can find here"))
     try:
        qualit[chat_id]
     except KeyError:
        qualit[chat_id] = "MP3_320"
     bot.sendMessage(chat_id, translate(lang, "Press for search songs or album\nP.S. Remember you can do this digiting @ in your keyboard and select DeezloaderRMX_bot"),
                    reply_markup=InlineKeyboardMarkup(
                                     inline_keyboard=[
                                                [InlineKeyboardButton(text="Search", switch_inline_query_current_chat="")]
                                     ]
                         ))
     bot.sendMessage(chat_id, translate(lang, "Send a Deezer or Spotify link to download\nSend a song o vocal message to recognize the track"))
    elif content_type == "text" and msg['text'] == "/quality":
     bot.sendMessage(chat_id, translate(lang, "Choose the quality that you want to download the song"),
                     reply_markup=ReplyKeyboardMarkup(
                                 keyboard=[
                                     [KeyboardButton(text="FLAC"), KeyboardButton(text="MP3_320Kbps")],
                                     [KeyboardButton(text="MP3_256Kbps"), KeyboardButton(text="MP3_128Kbps")]
                                 ]
                     ))
    elif content_type == "text" and (msg['text'] == "FLAC" or msg['text'] == "MP3_320Kbps" or msg['text'] == "MP3_256Kbps" or msg['text'] == "MP3_128Kbps"):
     qualit[chat_id] = msg['text'].replace("Kbps", "")
     bot.sendMessage(chat_id, translate(lang, "The songs will be downloaded with " + msg['text'] + " quality"), reply_markup=ReplyKeyboardRemove())
     if msg['text'] != "MP3_128Kbps":
      bot.sendMessage(chat_id, translate(lang, "The songs that cannot be downloaded with the quality that you choose will be downloaded in quality 128Kbps"))
    elif content_type == "voice" or content_type == "audio":
     try:
        qualit[chat_id]
     except KeyError:
        qualit[chat_id] = "MP3_320"
     Thread(target=Audio, args=(msg[content_type]['file_id'], chat_id, lang)).start()
    elif content_type == "text" and msg['text'] == "/info":
     bot.sendMessage(chat_id, "Version: 1.7\nName:@DeezloaderRMX_bot\nCreator:@An0nimia\nDonation:https://www.paypal.me/An0nimia\nForum:https://t.me/DeezloaderRMXbot\nUsers:" + statisc(chat_id, "USERS") + "\nTracks downloaded:" + statisc(chat_id, "TRACKS"))
    elif content_type == "text":
     try:
        qualit[chat_id]
     except KeyError:
        qualit[chat_id] = "MP3_320"
     try:
        msg['entities']
        Thread(target=Link, args=(msg['text'], chat_id, lang, qualit[chat_id], msg['message_id'])).start()
     except KeyError:
        bot.sendMessage(chat_id, translate(lang, "Press"),reply_markup=InlineKeyboardMarkup(
                                     inline_keyboard=[
                                                [InlineKeyboardButton(text="Search", switch_inline_query_current_chat=msg['text'])]
                                     ]
                        ))
def start2(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    try:
       msg['from']['language_code']
    except KeyError:
       msg['from'] = {"language_code": "en"}
    lang = msg['from']['language_code']
    if check_flood(chat_id, lang, msg) == "BANNED":
     return
    statisc(chat_id, "USERS")
    pprint(msg)
    if content_type == "text" and msg['text'] == "/start":
     bot.sendPhoto(chat_id, open("example.jpg", "rb"), caption=translate(lang, "The bot commands can find here"))
     try:
        qualit[chat_id]
     except KeyError:
        qualit[chat_id] = "MP3_320"
     bot.sendMessage(chat_id, translate(lang, "Press for search songs \nP.S. Remember you can do this digiting @ in your keyboard and select DeezloaderRMX_bot"),
                    reply_markup=InlineKeyboardMarkup(
                                     inline_keyboard=[
                                                [InlineKeyboardButton(text="Search", switch_inline_query_current_chat="")]
                                     ]
                         ))
     bot.sendMessage(chat_id, translate(lang, "Send a Deezer or Spotify link to download\nSend a song o vocal message to recognize the track"))
    elif content_type == "text" and msg['text'] == "/quality":
     bot.sendMessage(chat_id, translate(lang, "Choose the quality that you want to download the song"),
                     reply_markup=ReplyKeyboardMarkup(
                                 keyboard=[
                                     [KeyboardButton(text="FLAC"), KeyboardButton(text="MP3_320Kbps")],
                                     [KeyboardButton(text="MP3_256Kbps"), KeyboardButton(text="MP3_128Kbps")]
                                 ]
                     )) 
    elif content_type == "text" and (msg['text'] == "FLAC" or msg['text'] == "MP3_320Kbps" or msg['text'] == "MP3_256Kbps" or msg['text'] == "MP3_128Kbps"):
     qualit[chat_id] = msg['text'].replace("Kbps", "")
     bot.sendMessage(chat_id, translate(lang, "The songs will be downloaded with " + msg['text'] + " quality"), reply_markup=ReplyKeyboardRemove())
     if msg['text'] != "MP3_128Kbps":
      bot.sendMessage(chat_id, translate(lang, "The songs that cannot be downloaded with the quality that you choose will be downloaded in quality 128Kbps"))
    elif content_type == "voice" or content_type == "audio":
     try:
        qualit[chat_id]
     except KeyError:
        qualit[chat_id] = "MP3_320"
     Thread(target=Audio, args=(msg[content_type]['file_id'], chat_id, lang)).start()
    elif content_type == "text" and msg['text'] == "/info":
     bot.sendMessage(chat_id, "Version: 1.7\nName:@DeezloaderRMX_bot\nCreator:@An0nimia\nDonation:https://www.paypal.me/An0nimia\nForum:https://t.me/DeezloaderRMXbot\nUsers:" + statisc(chat_id, "USERS") + "\nTracks downloaded:" + statisc(chat_id, "TRACKS"))
    elif content_type == "text":
     music = msg['text']
     try:
        qualit[chat_id]
     except KeyError:
        qualit[chat_id] = "MP3_320"
     try:
        if users[chat_id] == 3:
         bot.sendMessage(chat_id, translate(lang, "Wait to finish and resend the link, did you thought that you could download how much songs did you want? :)"))
        else:
            try:
               msg['entities']
               users[chat_id] += 1
               Thread(target=Link, args=(music, chat_id, lang, qualit[chat_id], msg['message_id'])).start()
            except KeyError:
               bot.sendMessage(chat_id, translate(lang, "Press"),reply_markup=InlineKeyboardMarkup(
                                     inline_keyboard=[
                                                [InlineKeyboardButton(text="Search", switch_inline_query_current_chat=msg['text'])]
                                     ]
                               ))   
     except KeyError:
        try:
           msg['entities']
           users[chat_id] = 1
           Thread(target=Link, args=(music, chat_id, lang, qualit[chat_id], msg['message_id'])).start()
        except KeyError:
           bot.sendMessage(chat_id, translate(lang, "Press"),reply_markup=InlineKeyboardMarkup(
                                     inline_keyboard=[
                                                [InlineKeyboardButton(text="Search", switch_inline_query_current_chat=msg['text'])]
                                     ]
                           ))
try:
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
       sys.exit(0)
   print("Bot started")
   while True:
       sleep(1)
       if temp == 1 and (goes == 0 or goes == 2):
        if len(array2) == len(array3):
         for a in os.listdir(loc_dir):
             shutil.rmtree(loc_dir + a)
         del array2[:]
         del array3[:]
       now = datetime.now()
       if datetime.strptime(str(now.hour) + ":" + str(now.minute) + ":" + str(now.second), FMT) == datetime.strptime("00:00:00", FMT) or datetime.strptime(str(now.hour) + ":" + str(now.minute) + ":" + str(now.second), FMT) == datetime.strptime("12:00:00", FMT):
        downloa = deezloader.Login(setting.username, setting.password)
except KeyboardInterrupt:
   os.rmdir(loc_dir)
   print("\nSTOPPED")
