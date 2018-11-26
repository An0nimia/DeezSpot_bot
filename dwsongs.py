#!/usr/bin/python3
import os
import json
import shutil
import sqlite3
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
users = {}
artist = {}
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
conn = sqlite3.connect(local + "/dwsongs.db")
c = conn.cursor()
try:
   c.execute("CREATE TABLE DWSONGS (id text, query text, quality text)")
   conn.commit()
except sqlite3.OperationalError:
   None
conn.close()
def generate_token():
    token = oauth2.SpotifyClientCredentials(client_id="4fe3fecfe5334023a1472516cc99d805", client_secret="0f02b7c483c04257984695007a4a8d5c").get_access_token()
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
def sendAudio(chat_id, audio, lang, music, image=None):
    bot.sendChatAction(chat_id, "upload_audio")
    conn = sqlite3.connect(local + "/dwsongs.db")
    c = conn.cursor()
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
        request = requests.post(url, params=data, files=file)
        audio = json.loads(request.text)['result']['audio']['file_id']
        if request.status_code == 413:
         bot.sendMessage(chat_id, translate(lang, "The song is too big to be sent"))
        else:
            c.execute("INSERT INTO DWSONGS(id, query, quality) values('%s', '%s', '%s')" % (music, audio, qualit[chat_id]))
            conn.commit()
       else:
           bot.sendAudio(chat_id, audio)
    except:
       bot.sendMessage(chat_id, translate(lang, "An error has occured during sending song, please contact @An0nimia for explain the issue, thanks :)"))
    conn.close()
def track(music, chat_id, lang, quality):
    global spo
    conn = sqlite3.connect(local + "/dwsongs.db")
    c = conn.cursor()
    c.execute("SELECT query FROM DWSONGS WHERE id = '%s' and quality = '%s'" % (music, quality))
    z = c.fetchone()
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
            url = json.loads(requests.get("http://api.deezer.com/track/" + music.split("/")[-1]).text)
            try:
               image = url['album']['cover_xl'].replace("1000", "90")
            except:
               URL = "http://www.deezer.com/track/" + music.split("/")[-1]
               try:
                  images = requests.get(URL).text
               except:
                  images = requests.get(URL).text
               image = BeautifulSoup(images, "html.parser").find("img", class_="img_main").get("src").replace("120", "90")
            z = downloa.download_trackdee(music, check=False, quality=quality, recursive=False)
        except deezloader.TrackNotFound:
           try:
              if "spotify" in music:
               z = dwytsongs.download_trackspo(music, check=False)
              elif "deezer" in music:
               z = dwytsongs.download_trackdee(music, check=False)
           except dwytsongs.TrackNotFound as error:
              bot.sendMessage(chat_id, translate(lang, str(error) + " :("))
        except:
           bot.sendMessage(chat_id, translate(lang, "An error has occured during downloading song, please contact @An0nimia for explain the issue, thanks :)"))
           conn.close()
           return
        conn.close()
        sendAudio(chat_id, z, lang, music, image)
def Link(music, chat_id, lang, quality, msg):
    global spo
    links1 = []
    links2 = []
    image = []
    array3.append(chat_id)
    try:
       conn = sqlite3.connect(local + "/dwsongs.db")
       c = conn.cursor()
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
         for a in tracks['tracks']['items']:
             c.execute("SELECT query FROM DWSONGS WHERE id = '%s' and quality = '%s'" % (a['external_urls']['spotify'], quality))
             links2.append(a['external_urls']['spotify'])
             if c.fetchone() != None:
              links1.append(a['external_urls']['spotify'])
         if tracks['total_tracks'] != 50:
            for a in range(tracks['total_tracks'] // 50):
                try:
                   tracks2 = spo.next(tracks['tracks'])
                except:
                   token = generate_token()
                   spo = spotipy.Spotify(auth=token)
                   tracks2 = spo.next(tracks['tracks'])
                for a in tracks2['items']:
                    c.execute("SELECT query FROM DWSONGS WHERE id = '%s' and quality = '%s'" % (a['external_urls']['spotify'], quality))
                    links2.append(a['external_urls']['spotify'])
                    if c.fetchone() != None:
                     links1.append(a['external_urls']['spotify'])
         bot.sendPhoto(chat_id, tracks['images'][0]['url'], caption="Album:" + tracks['name'] + "\nArtist:" + tracks['artists'][0]['name'] + "\nDate:" + tracks['release_date'])
         if len(links1) <= (tracks['total_tracks'] // 2):
          z = downloa.download_albumspo(music, check=False, quality=quality, recursive=False)
         else:
             for a in links2:
                 track(a, chat_id, lang, quality)
        elif "playlist/" in music:
         if "?" in music:
          music,a = music.split("?")
         musi = music.split("/")
         try:
            tracks = spo.user_playlist_tracks(musi[-3], playlist_id=musi[-1])
         except Exception as a:
            if not "The access token expired" in str(a):
             bot.sendMessage(chat_id, translate(lang, "Invalid link ;"), reply_to_message_id=msg)
             delete(chat_id)
             return
            token = generate_token()
            spo = spotipy.Spotify(auth=token)
            tracks = spo.user_playlist_tracks(musi[-3], playlist_id=musi[-1])
         for a in tracks['items']:
             track(a['track']['external_urls']['spotify'], chat_id, lang, quality)
         if tracks['total'] != 100:
            for a in range(tracks['total'] // 100):
                try:
                   tracks = spo.next(tracks)
                except:
                   token = generate_token()
                   spo = spotipy.Spotify(auth=token)
                   tracks = spo.next(tracks)
                for a in tracks['items']:
                    track(a['track']['external_urls']['spotify'], chat_id, lang, quality)
       elif "deezer" in music:
        if "track/" in music:
         if "?" in music:
          music,a = music.split("?")
         url = json.loads(requests.get("http://api.deezer.com/track/" + music.split("/")[-1]).text)
         try:
            if "error" in str(url):
             bot.sendMessage(chat_id, translate(lang, "Invalid link ;"), reply_to_message_id=msg)
             return
         except KeyError:
            None
         try:
            imag = url['album']['cover_xl']
         except:
            URL = "http://www.deezer.com/track/" + music.split("/")[-1]
            try:
               imag = requests.get(URL).text
            except:
               imag = requests.get(URL).text
            imag = BeautifulSoup(imag, "html.parser").find("img", class_="img_main").get("src").replace("120", "1000")
         for a in url['contributors']:
             if a['role'] == "Main":
              artist = a['name']
              break
         bot.sendPhoto(chat_id, imag, caption="Track:" + url['title'] + "\nArtist:" + artist + "\nAlbum:" + url['album']['title'] + "\nDate:" + url['album']['release_date'])
         track(music, chat_id, lang, quality)
        elif "album/" in music:
         if "?" in music:
          music,a = music.split("?")
         url = json.loads(requests.get("http://api.deezer.com/album/" + music.split("/")[-1]).text)
         try:
            if "error" in str(url):
             bot.sendMessage(chat_id, translate(lang, "Invalid link ;"), reply_to_message_id=msg)
             delete(chat_id)
             return
         except KeyError:
            None
         try:
            imag = url['cover_xl']
         except:
            try:
               imag = requests.get(URL).text
            except:
               imag = requests.get(URL).text
            imag = BeautifulSoup(imag, "html.parser").find("img", class_="img_main").get("src").replace("120", "1000")
         for a in url['tracks']['data']:
             image.append(imag.replace("1000", "90"))
             c.execute("SELECT query FROM DWSONGS WHERE id = '%s' and quality = '%s'" % (a['link'], quality))
             links2.append(a['link'])
             if c.fetchone() != None:
              links1.append(a['link'])
         for a in url['contributors']:
             if a['role'] == "Main":
              artist = a['name']
              break
         bot.sendPhoto(chat_id, imag, caption="Album:" + url['title'] + "\nArtist:" + artist + "\nDate:" + url['release_date'])
         if len(links1) <= (url['nb_tracks'] // 2):
          z = downloa.download_albumdee(music, check=False, quality=quality, recursive=False)
         else:
             for a in links2:
                 track(a, chat_id, lang, quality)
        elif "playlist/" in music:
         if "?" in music:
          music,a = music.split("?")
         url = json.loads(requests.get("https://api.deezer.com/playlist/" + music.split("/")[-1]).text)
         try:
            if "error" in str(url):
             bot.sendMessage(chat_id, translate(lang, "Invalid link ;"), reply_to_message_id=msg)
             delete(chat_id)
             return
         except KeyError:
            None
         bot.sendPhoto(chat_id, url['picture_xl'], caption="Creation:" + url['creation_date'] + "\nUser:" + url['creator']['name'])
         for a in url['tracks']['data']:
             track(a['link'], chat_id, lang, quality)
       else:
           delete(chat_id)
           return
       try:
          for a in range(len(z)):
              sendAudio(chat_id, z[a], lang, links2[a], image[a])
       except NameError:
          None
    except deezloader.AlbumNotFound:
       bot.sendMessage(chat_id, translate(lang, "Album not found :("))
    except:
       bot.sendMessage(chat_id, translate(lang, "An error has occurred while sending the song. For more information, please contact @An0nimia Thanks :)"))
    bot.sendMessage(chat_id, translate(lang, "FINISHED"), reply_to_message_id=msg)
    delete(chat_id)
def Audio(audio, chat_id, lang):
    global spo
    global goes
    bot.sendChatAction(chat_id, "upload_photo")
    goes = 1
    file = local + "/Songs/" + audio + ".ogg"
    bot.download_file(audio, file)
    audio = acrcloud.recognizer(config, file)
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
    try:
       msg['from']['language_code'] 
    except KeyError:
       msg['from'] = {"language_code": "en"}
    tags = query_data.split(">")
    if query_data == "Infos with too many bytes" or query_data == "No informations":
     bot.answerCallbackQuery(query_id, translate(msg['from']['language_code'], query_data))
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
             bot.answerCallbackQuery(query_id, translate(msg['from']['language_code'], "Wait to finish and press download again, did you thought that you could download how much songs did you want? :)"), show_alert=True)
             return
            else:
                users[from_id] += 1
         except KeyError:
            users[from_id] = 1
        bot.answerCallbackQuery(query_id, translate(msg['from']['language_code'], "Song is downloading"))
        try:
           qualit[from_id]
        except KeyError:
           qualit[from_id] = "MP3_320"
        Thread(target=Link, args=(query_data, from_id, msg['from']['language_code'], qualit[from_id], msg['message']['message_id'])).start()
def search(msg):
    global spo
    query_id, from_id, query_string = telepot.glance(msg, flavor='inline_query')
    if query_string == "":
     return
    try:
       search1 = spo.search(q=query_string, limit=20)['tracks']['items']
    except:
       token = generate_token()
       spo = spotipy.Spotify(auth=token)
       search1 = spo.search(q=query_string, limit=20)['tracks']['items']
    try:
       search2 = spo.search(q="album:" + query_string, limit=20)['tracks']['items']
    except:
       token = generate_token()
       spo = spotipy.Spotify(auth=token)
       search2 = spo.search(q="album:" + query_data, limit=20)['tracks']['items']
    for a in search2:
        search1.append({"external_urls": {"spotify": a['album']['external_urls']['spotify']}})
        search1[len(search1) - 1]['name'] = a['album']['name'] + " (Album)"
        search1[len(search1) - 1]['artists'] = a['artists']
        search1[len(search1) - 1]['album'] = {"images": [a['album']['images'][0]]}
    result = []
    for a in search1[::-1]:
        if not a['external_urls']['spotify'] in str(result):
         result.append(InlineQueryResultArticle(id=a['external_urls']['spotify'], title=a['name'] + "\n" + a['artists'][0]['name'], thumb_url=a['album']['images'][0]['url'], input_message_content=InputTextMessageContent(message_text=a['external_urls']['spotify'])))
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
    if content_type == "text" and msg['text'] == "/start":
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Welcome to @DeezloaderRMX_bot"))
     bot.sendPhoto(chat_id, open("example.jpg", "rb"), caption="The bot commands can find here")
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Please select between"))
     try:
        qualit[chat_id]
     except KeyError:
        qualit[chat_id] = "MP3_320"
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Press for search songs or album\nP.S. Remember you can do this digiting @ in your keyboard and select DeezloaderRMX_bot"),
                    reply_markup=InlineKeyboardMarkup(
                                     inline_keyboard=[
                                                [InlineKeyboardButton(text="Search", switch_inline_query_current_chat="")]
                                     ]
                         ))
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Send a Deezer or Spotify link to download"))
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Send a song o vocal message to recognize the track"))
    elif content_type == "text" and msg['text'] == "/quality":
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Choose the quality that you want to download the song"),
                     reply_markup=ReplyKeyboardMarkup(
                                 keyboard=[
                                     [KeyboardButton(text="FLAC"), KeyboardButton(text="MP3_320")],
                                     [KeyboardButton(text="MP3_256"), KeyboardButton(text="MP3_128")]
                                 ]
                     ))
    elif content_type == "text" and (msg['text'] == "FLAC" or msg['text'] == "MP3_320" or msg['text'] == "MP3_256" or msg['text'] == "MP3_128"):
     qualit[chat_id] = msg['text']
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "The songs will be downloaded with " + msg['text'] + " quality"), reply_markup=ReplyKeyboardRemove())
     if msg['text'] != "MP3_128":
      bot.sendMessage(chat_id, translate(msg['from']['language_code'], "The songs that cannot be downloaded with the quality that you choose will be downloaded in quality MP3_128"))
    elif content_type == "voice" or content_type == "audio":
     try:
        qualit[chat_id]
     except KeyError:
        qualit[chat_id] = "MP3_320"
     Thread(target=Audio, args=(msg[content_type]['file_id'], chat_id, msg['from']['language_code'])).start()
    elif content_type == "text":
     try:
        qualit[chat_id]
     except KeyError:
        qualit[chat_id] = "MP3_320"
     Thread(target=Link, args=(msg['text'], chat_id, msg['from']['language_code'], qualit[chat_id], msg['message_id'])).start()
def start2(msg):
    print(msg)
    content_type, chat_type, chat_id = telepot.glance(msg)
    try:
       msg['from']['language_code']
    except KeyError:
       msg['from'] = {"language_code": "en"}
    if content_type == "text" and msg['text'] == "/start":
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Welcome to @DeezloaderRMX_bot"))
     bot.sendPhoto(chat_id, open("example.jpg", "rb"), caption=translate(msg['from']['language_code'], "The bot commands can find here"))
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Please select between"))
     try:
        qualit[chat_id]
     except KeyError:
        qualit[chat_id] = "MP3_320"
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Press for search songs \nP.S. Remember you can do this digiting @ in your keyboard and select DeezloaderRMX_bot"),
                    reply_markup=InlineKeyboardMarkup(
                                     inline_keyboard=[
                                                [InlineKeyboardButton(text="Search", switch_inline_query_current_chat="")]
                                     ]
                         ))
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Send a Deezer or Spotify link to download"))
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Send a song o vocal message to recognize the track"))
    elif content_type == "text" and msg['text'] == "/quality":
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Choose the quality that you want to download the song"),
                     reply_markup=ReplyKeyboardMarkup(
                                 keyboard=[
                                     [KeyboardButton(text="FLAC"), KeyboardButton(text="MP3_320")],
                                     [KeyboardButton(text="MP3_256"), KeyboardButton(text="MP3_128")]
                                 ]
                     )) 
    elif content_type == "text" and (msg['text'] == "FLAC" or msg['text'] == "MP3_320" or msg['text'] == "MP3_256" or msg['text'] == "MP3_128"):
     qualit[chat_id] = msg['text']
     bot.sendMessage(chat_id, translate(msg['from']['language_code'], "The songs will be downloaded with " + msg['text'] + " quality"), reply_markup=ReplyKeyboardRemove())
     if msg['text'] != "MP3_128":
      bot.sendMessage(chat_id, translate(msg['from']['language_code'], "The songs that cannot be downloaded with the quality that you choose will be downloaded in quality MP3_128"))
    elif content_type == "voice" or content_type == "audio":
     try:
        qualit[chat_id]
     except KeyError:
        qualit[chat_id] = "MP3_320"
     Thread(target=Audio, args=(msg[content_type]['file_id'], chat_id, msg['from']['language_code'])).start()
    elif content_type == "text":
     music = msg['text']
     try:
        qualit[chat_id]
     except KeyError:
        qualit[chat_id] = "MP3_320"
     try:
        if users[chat_id] == 2:
         bot.sendMessage(chat_id, translate(msg['from']['language_code'], "Wait to finish and resend the link, did you thought that you could download how much songs did you want? :)"))
        else:
            users[chat_id] += 1
            Thread(target=Link, args=(music, chat_id, msg['from']['language_code'], qualit[chat_id], msg['message_id'])).start()
     except KeyError:
        users[chat_id] = 1
        Thread(target=Link, args=(music, chat_id, msg['from']['language_code'], qualit[chat_id], msg['message_id'])).start()
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
           sleep(8)
           if temp == 1 and (goes == 0 or goes == 2):
            if len(array2) == len(array3):
             for a in os.listdir(local + "/Songs"):
                 shutil.rmtree(local + "/Songs/" + a)
             del array2[:]
             del array3[:]
except KeyboardInterrupt:
   os.rmdir(local + "/Songs")
   print("\nSTOPPED")
