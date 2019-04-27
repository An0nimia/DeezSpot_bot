#!/usr/bin/python3
import os
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
from pyrogram import Client
from threading import Thread
from datetime import datetime
from mutagen.flac import FLAC
from bs4 import BeautifulSoup
import spotipy.oauth2 as oauth2
from mutagen.easyid3 import EasyID3
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent
downloa = deezloader.Login(setting.username, setting.password, setting.deezer_token)
token = setting.token
bot = telepot.Bot(token)
bot_name = input("Insert bot name:")
app = Client("my_account", "887439", "5e347289fb55cc88406b1180326b145d")
app.start()
users = {}
qualit = {}
date = {}
languag = {}
del1 = 0
del2 = 0
local = os.getcwd()
db_file = local + "/dwsongs.db"
loc_dir = local + "/Songs/"
config = {
          "key": "de46e5c7420b418d73717c6b9ab0ba79",
          "secret": "IQzjk1uwooSt7ilW7wt872QlcFMuO51zaZ0gw4xQ",
          "host": "https://identify-eu-west-1.acrcloud.com"
}
logging.basicConfig(filename="dwsongs.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
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
    return oauth2.SpotifyClientCredentials(client_id="c6b23f1e91f84b6a9361de16aba0ae17", client_secret="237e355acaa24636abc79f1a089e6204").get_access_token()
spo = spotipy.Spotify(auth=generate_token())
def request(url, chat_id=0, control=False):
    try:
       thing = requests.get(url)
    except:
       thing = requests.get(url)
    if control == True:
     try:
        if thing.json()['error']['message'] == "Quota limit exceeded":
         sendMessage(chat_id, translate(languag[chat_id], "Please send the link again :("))
         return
     except KeyError:
        pass
     try:
        if thing.json()['error']:
         sendMessage(chat_id, translate(languag[chat_id], "No result has been found :("))
         return
     except KeyError:
        pass
    return thing
def translate(language, sms):
    try:
       language = language.split("-")[0]
       api = "https://translate.yandex.net/api/v1.5/tr.json/translate?key=trnsl.1.1.20181114T193428Z.ec0fb3fb93e116c0.24b2ccfe2d150324e23a5571760e9a827d953003&text=%s&lang=en-%s" % (sms, language)
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
def statisc(chat_id, do):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    if do == "USERS":
     c.execute("SELECT chat_id FROM CHAT_ID where chat_id = '%d'" % chat_id)
     if c.fetchone() == None:
      write_db("INSERT INTO CHAT_ID(chat_id) values('%d')" % chat_id)
     c.execute("SELECT chat_id FROM CHAT_ID")
     infos = len(c.fetchall())
    elif do == "TRACKS":
     c.execute("SELECT id FROM DWSONGS")
     infos = len(c.fetchall())
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
         sendMessage(chat_id, translate(languag[chat_id], "It is appearing you are trying to flood, you have to wait more that four second to send another message.\n" + str(date[chat_id]['tries']) + " possibilites :)"))
         if date[chat_id]['tries'] == 0:
          write_db("INSERT INTO BANNED(banned) values('%d')" % chat_id)
          del date[chat_id]
          sendMessage(chat_id, translate(languag[chat_id], "You are banned :)"))
    except KeyError:
       try: 
          date[chat_id] = {"time": msg['date'], "tries": 3, "msg": 0}
       except KeyError:
          pass
def sendZip(chat_id, link, zip_name="", quality="", image=""):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT query FROM DWSONGS WHERE id = '%s' and quality = '%s'" % (link, quality.split("MP3_")[-1]))
    z = c.fetchone()
    if z != None:
     file_id = z[0] 
    else:
        quality = zip_name.split("(")[-1].split(")")[0]
        imag = image.url.split("/")
        if imag[-2] == "image":
         imag = loc_dir + imag[-1]
        else:
            imag = loc_dir + imag[-2]
        try:
           open(imag, "wb").write(image.content)
           file_id = app.send_document(bot_name, zip_name, thumb=imag)['document']['file_id']
           write_db("INSERT INTO DWSONGS(id, query, quality) values('%s', '%s', '%s')" % (link, file_id, quality.split("MP3_")[-1]))
        except:
           sendMessage(chat_id, translate(languag[chat_id], "Nothing to send :("))
    try:
       bot.sendDocument(chat_id, file_id)
    except:
       sendMessage(chat_id, translate(languag[chat_id], "Sorry I can do nothing"))   
def sendMessage(chat_id, text, reply_markup="", reply_to_message_id=""):
    sleep(0.8)
    try:
       bot.sendMessage(chat_id, text, reply_markup=reply_markup, reply_to_message_id=reply_to_message_id)
    except:
       pass
def sendPhoto(chat_id, photo, caption="", reply_markup=""):
    sleep(0.8)
    try:
       bot.sendChatAction(chat_id, "upload_photo")
       bot.sendPhoto(chat_id, photo, caption=caption, reply_markup=reply_markup)
    except telepot.exception.TelegramError:
       pass
def sendAudio(chat_id, audio, link="", image=None, youtube=False):
    sleep(0.8)
    try:
       bot.sendChatAction(chat_id, "upload_audio") 
       if os.path.isfile(audio):
        audio = open(audio, "rb")
        try:
           tag = EasyID3(audio.name)
           duration = int(MP3(audio.name).info.length)
        except mutagen.id3._util.ID3NoHeaderError:
           tag = FLAC(audio.name)
           duration = int(tag.info.length)
        data = {
                "chat_id": chat_id,
                "duration": duration,
                "performer": tag['artist'][0],
                "title": tag['title'][0]
        }
        file = {
                "audio": audio,
                "thumb": image.content
        }
        url = "https://api.telegram.org/bot" + token + "/sendAudio"
        try:
           request = requests.post(url, params=data, files=file, timeout=20)
        except:
           request = requests.post(url, params=data, files=file, timeout=20)
        if request.status_code != 200:
         sendMessage(chat_id, translate(languag[chat_id], "The song " + tag['artist'][0] + " - " + tag['title'][0] + " is too big to be sent :(, wait..."))
         imag = image.url.split("/")
         if imag[-2] == "image":
          imag = loc_dir + imag[-1]
         else:
             imag = loc_dir + imag[-2]
         open(imag, "wb").write(image.content)
         file_id = app.send_audio(bot_name, audio.name, thumb=imag, duration=duration, performer=tag['artist'][0], title=tag['title'][0])['audio']['file_id']
         bot.sendAudio(chat_id, file_id)
        else:
            file_id = request.json()['result']['audio']['file_id']
        if youtube == False:
         write_db("INSERT INTO DWSONGS(id, query, quality) values('%s', '%s', '%s')" % (link, file_id, audio.name.split("(")[-1].split(")")[0]))
       else:
           bot.sendAudio(chat_id, audio)
    except telepot.exception.TelegramError:
       sendMessage(chat_id, translate(languag[chat_id], "Sorry the track doesn't seem readable on Deezer :("))
    except:
       sendMessage(chat_id, translate(languag[chat_id], "Sorry for some reason I can't send the track :("))
def track(link, chat_id, quality):
    global spo
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT query FROM DWSONGS WHERE id = '%s' and quality = '%s'" % (link, quality.split("MP3_")[-1]))
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
               spo = spotipy.Spotify(auth=generate_token())
               url = spo.track(link)
            try:
               image = url['album']['images'][2]['url']
            except IndexError:
               image = "https://e-cdns-images.dzcdn.net/images/cover/90x90-000000-80-0-0.jpg"
            z = downloa.download_trackspo(link, quality=quality, recursive_quality=False, recursive_download=False)
           elif "deezer" in link:
            try:
               url = request("https://api.deezer.com/track/" + link.split("/")[-1], chat_id, True).json()
            except AttributeError:
               return
            try:
               image = url['album']['cover_xl'].replace("1000x1000", "90x90")
            except AttributeError:
               URL = "https://www.deezer.com/track/" + link.split("/")[-1]
               image = request(URL).text
               image = BeautifulSoup(image, "html.parser").find("img", class_="img_main").get("src").replace("120x120", "90x90")
            ima = request(image).content
            if len(ima) == 13:
             image = "https://e-cdns-images.dzcdn.net/images/cover/90x90-000000-80-0-0.jpg"
            z = downloa.download_trackdee(link, quality=quality, recursive_quality=False, recursive_download=False)
        except deezloader.TrackNotFound:
           sendMessage(chat_id, translate(languag[chat_id], "Track doesn't exist on Deezer or maybe it isn't readable, it'll be downloaded from YouTube..."))
           try:
              if "spotify" in link:
               z = dwytsongs.download_trackspo(link, check=False)
              elif "deezer" in link:
               z = dwytsongs.download_trackdee(link, check=False)
              youtube = True
           except dwytsongs.TrackNotFound:
              sendMessage(chat_id, translate(languag[chat_id], "Sorry I cannot download this song :("))
              return
        image = request(image)
        sendAudio(chat_id, z, link, image, youtube)
def Link(link, chat_id, quality, msg):
    global spo
    global del1
    del1 += 1
    done = 0
    links1 = []
    links2 = []
    try:
       if "spotify" in link:
        if "track/" in link:
         if "?" in link:
          link,a = link.split("?")
         try:
            url = spo.track(link)
         except Exception as a:
            if not "The access token expired" in str(a):
             sendMessage(chat_id, translate(languag[chat_id], "Invalid link ;)"), reply_to_message_id=msg['message_id'])
             delete(chat_id)
             return
            spo = spotipy.Spotify(auth=generate_token())
            url = spo.track(link)
         try:
            image1 = url['album']['images'][0]['url']
         except IndexError:
            image1 = "https://e-cdns-images.dzcdn.net/images/cover/1000x1000-000000-80-0-0.jpg"
         sendPhoto(chat_id, image1, caption="Track:" + url['name'] + "\nArtist:" + url['album']['artists'][0]['name'] + "\nAlbum:" + url['album']['name'] + "\nDate:" + url['album']['release_date'])
         track(link, chat_id, quality)
        elif "album/" in link:
         if "?" in link:
          link,a = link.split("?")
         try:
            tracks = spo.album(link)
         except Exception as a:
            if not "The access token expired" in str(a):
             sendMessage(chat_id, translate(languag[chat_id], "Invalid link ;)"), reply_to_message_id=msg['message_id'])
             delete(chat_id)
             return
            spo = spotipy.Spotify(auth=generate_token())
            tracks = spo.album(link)
         try:
            image2 = tracks['images'][2]['url']
            image1 = tracks['images'][0]['url']
         except IndexError:
            image2 = "https://e-cdns-images.dzcdn.net/images/cover/90x90-000000-80-0-0.jpg"
            image1 = "https://e-cdns-images.dzcdn.net/images/cover/1000x1000-000000-80-0-0.jpg"
         tot = tracks['total_tracks']
         conn = sqlite3.connect(db_file)
         c = conn.cursor()
         exist = c.execute("SELECT query FROM DWSONGS WHERE id = '%s' and quality = '%s'" % (link, quality.split("MP3_")[-1])).fetchone()
         count = 0
         for a in tracks['tracks']['items']:
             count += a['duration_ms']
             c.execute("SELECT query FROM DWSONGS WHERE id = '%s' and quality = '%s'" % (a['external_urls']['spotify'], quality.split("MP3_")[-1]))
             links2.append(a['external_urls']['spotify'])
             if c.fetchone() != None and exist != None:
              links1.append(a['external_urls']['spotify'])
         if (count / 1000) > 40000:
          sendMessage(chat_id, translate(languag[chat_id], "If you do this again I will come to your home and I will ddos your ass :)"))
          delete(chat_id)
          return
         sendPhoto(chat_id, image1, caption="Album:" + tracks['name'] + "\nArtist:" + tracks['artists'][0]['name'] + "\nDate:" + tracks['release_date'] + "\nTracks amount:" + str(tot))
         tracks = tracks['tracks']
         if tot != 50:
            for a in range(tot // 50):
                try:
                   tracks2 = spo.next(tracks)
                except:
                   spo = spotipy.Spotify(auth=generate_token())
                   tracks2 = spo.next(tracks)
                for a in tracks2['items']:
                    c.execute("SELECT query FROM DWSONGS WHERE id = '%s' and quality = '%s'" % (a['external_urls']['spotify'], quality.split("MP3_")[-1]))
                    links2.append(a['external_urls']['spotify'])
                    if c.fetchone() != None and exist != None:
                     links1.append(a['external_urls']['spotify'])
         conn.close()
         if len(links1) != tot:
          z,zip_name = downloa.download_albumspo(link, quality=quality, recursive_quality=False, recursive_download=False, create_zip=True)
         else:
             sendZip(chat_id, link, quality=quality)
             for a in links2:
                 track(a, chat_id, quality)
         done = 1
        elif "playlist/" in link:
         if "?" in link:
          link,a = link.split("?")
         musi = link.split("/")
         try:
            tracks = spo.user_playlist(musi[-3], playlist_id=musi[-1])
         except Exception as a:
            if not "The access token expired" in str(a):
             sendMessage(chat_id, translate(languag[chat_id], "Invalid link ;)"), reply_to_message_id=msg['message_id'])
             delete(chat_id)
             return
            spo = spotipy.Spotify(auth=generate_token())
            tracks = spo.user_playlist(musi[-3], playlist_id=musi[-1])
         try:
            image1 = tracks['images'][0]['url']
         except IndexError:
            image1 = "https://e-cdns-images.dzcdn.net/images/cover/1000x1000-000000-80-0-0.jpg"
         tot = tracks['tracks']['total']
         if tot > 400:
          sendMessage(chat_id, translate(languag[chat_id], "Fuck you"))
          delete(chat_id)
          return
         sendPhoto(chat_id, image1, caption="Creation:" + tracks['tracks']['items'][0]['added_at'] + "\nUser:" + str(tracks['owner']['display_name']) + "\nTracks amount:" + str(tot))
         for a in tracks['tracks']['items']:
             try:
                track(a['track']['external_urls']['spotify'], chat_id, quality)
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
                   spo = spotipy.Spotify(auth=generate_token())
                   tracks = spo.next(tracks)
                for a in tracks['items']:
                    try:
                       track(a['track']['external_urls']['spotify'], chat_id, quality)
                    except KeyError:
                       try:
                          sendMessage(chat_id, a['track']['name'] + " Not found :(")
                       except KeyError:
                          sendMessage(chat_id, "Error :(")
         done = 1
        else:
            sendMessage(chat_id, translate(languag[chat_id], "Sorry :( The bot doesn't support this link"))
       elif "deezer" in link:
        if "track/" in link:
         if "?" in link:
          link,a = link.split("?")
         try: 
            url = request("https://api.deezer.com/track/" + link.split("/")[-1], chat_id, True).json()
         except AttributeError:
            delete(chat_id)
            return
         image1 = url['album']['cover_xl']
         if image1 == None:
          URL = "https://www.deezer.com/track/" + link.split("/")[-1]
          image1 = request(URL).text
          image1 = BeautifulSoup(image1, "html.parser").find("img", class_="img_main").get("src").replace("120x120", "1000x1000")
         ima = request(image1).content
         if len(ima) == 13:
          image1 = "https://e-cdns-images.dzcdn.net/images/cover/1000x1000-000000-80-0-0.jpg"
         sendPhoto(chat_id, image1, caption="Track:" + url['title'] + "\nArtist:" + url['artist']['name'] + "\nAlbum:" + url['album']['title'] + "\nDate:" + url['album']['release_date'])
         track(link, chat_id, quality)
        elif "album/" in link:
         if "?" in link:
          link,a = link.split("?")
         try: 
            url = request("https://api.deezer.com/album/" + link.split("/")[-1], chat_id, True).json()
         except AttributeError:
            delete(chat_id)
            return
         if url['duration'] > 40000:
          sendMessage(chat_id, translate(languag[chat_id], "If you do this again I will come to your home and I will ddos your ass :)"))
          delete(chat_id)
          return
         image1 = url['cover_xl']
         if image1 == None:
          URL = "https://www.deezer.com/album/" + link.split("/")[-1]
          image1 = request(URL).text
          image1 = BeautifulSoup(image1, "html.parser").find("img", class_="img_main").get("src").replace("200x200", "1000x1000")
         ima = request(image1).content
         if len(ima) == 13:
          image1 = "https://e-cdns-images.dzcdn.net/images/cover/1000x1000-000000-80-0-0.jpg"
         image2 = image1.replace("1000x1000", "90x90")
         conn = sqlite3.connect(db_file)
         c = conn.cursor()
         exist = c.execute("SELECT query FROM DWSONGS WHERE id = '%s' and quality = '%s'" % (link, quality.split("MP3_")[-1])).fetchone()
         for a in url['tracks']['data']:
             c.execute("SELECT query FROM DWSONGS WHERE id = '%s' and quality = '%s'" % (a['link'], quality.split("MP3_")[-1]))
             links2.append(a['link'])
             if c.fetchone() != None and exist != None:
              links1.append(a['link'])
         conn.close()
         tot = url['nb_tracks']
         sendPhoto(chat_id, image1, caption="Album:" + url['title'] + "\nArtist:" + url['artist']['name'] + "\nDate:" + url['release_date'] + "\nTracks amount:" + str(tot))
         if len(links1) != tot:
          z,zip_name = downloa.download_albumdee(link, quality=quality, recursive_quality=False, recursive_download=False, create_zip=True)
         else:
             sendZip(chat_id, link, quality=quality)
             for a in links2:
                 track(a, chat_id, quality)
         done = 1
        elif "playlist/" in link:
         if "?" in link:
          link,a = link.split("?")
         try:
            url = request("https://api.deezer.com/playlist/" + link.split("/")[-1], chat_id, True).json()
         except AttributeError:
            delete(chat_id)
            return
         tot = url['nb_tracks']
         if tot > 400:
          sendMessage(chat_id, translate(languag[chat_id], "Fuck you"))
          delete(chat_id)
          return
         sendPhoto(chat_id, url['picture_xl'], caption="Creation:" + url['creation_date'] + "\nUser:" + url['creator']['name'] + "\nTracks amount:" + str(tot))
         for a in url['tracks']['data']:
             track(a['link'], chat_id, quality)
         done = 1
        elif "artist/" in link:
         if "?" in link:
          link,a = link.split("?")
         link = "https://api.deezer.com/artist/" + link.split("/")[-1]
         try:
            url = request(link, chat_id, True).json()
         except AttributeError:
            delete(chat_id)
            return
         sendPhoto(chat_id, url['picture_xl'], caption="Artist:" + url['name'] + "\nAlbum numbers:" + str(url['nb_album']) + "\nFans on Deezer:" + str(url['nb_fan']),
                   reply_markup=InlineKeyboardMarkup(
                               inline_keyboard=[
                                                [InlineKeyboardButton(text="TOP 30", callback_data=link + "/top?limit=30"), InlineKeyboardButton(text="ALBUMS", callback_data=link + "/albums")],
                                                [InlineKeyboardButton(text="RADIO", callback_data=link + "/radio")]
                               ]
                  ))
        else:
            sendMessage(chat_id, translate(languag[chat_id], "Sorry :( The bot doesn't support this link"))
       else:
           sendMessage(chat_id, translate(languag[chat_id], "Sorry :( The bot doesn't support this link"))
       try:
          image2 = request(image2)
          for a in range(len(z)):
              sendAudio(chat_id, z[a], links2[a], image2)
          sendZip(chat_id, link, zip_name, quality, image2)
       except NameError:
          pass
    except deezloader.QuotaExceeded:
       sendMessage(chat_id, translate(languag[chat_id], "Please send the link again :("))
    except deezloader.AlbumNotFound:
       sendMessage(chat_id, translate(languag[chat_id], "Album didn't find on Deezer :("))
       sendMessage(chat_id, translate(langug[chat_id], "Try to search it throught inline mode or search the link on Deezer"))
    except Exception as a:
       logging.warning(a)
       logging.info(link)
       sendMessage(chat_id, translate(languag[chat_id], "OPS :( Something went wrong please contact @An0nimia to explain the issue, if this happens again, and be sure to using @DeezloaderRMX_bot"))
    try:
       if done == 1:
        sendMessage(chat_id, translate(languag[chat_id], "FINISHED :)"), reply_to_message_id=msg['message_id'])
    except:
       pass
    delete(chat_id)
def Audio(audio, chat_id):
    global spo
    file = loc_dir + audio + ".ogg"
    try:
       bot.download_file(audio, file)
    except telepot.exception.TelegramError:
       sendMessage(chat_id, translate(languag[chat_id], "File sent is too big, please send a file lower than 20 MB"))
       return
    audio = acrcloud.recognizer(config, file)
    try:
       os.remove(file)
    except FileNotFoundError:
       pass
    if audio['status']['msg'] != "Success":
     sendMessage(chat_id, translate(languag[chat_id], "Sorry cannot detect the song from audio :(, retry..."))
    else:
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
           url = request("https://api.deezer.com/search/track/?q=" + track.replace("#", "") + " + " + artist.replace("#", ""), chat_id, True).json()
        except AttributeError:
           return 
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
                 spo = spotipy.Spotify(auth=generate_token())
                 url = spo.track(id)
              image = url['album']['images'][0]['url']
           except KeyError:
              pass
           try:
              id = "https://api.deezer.com/track/" + str(audio['metadata']['music'][0]['external_metadata']['deezer']['track']['id'])
              try:
                 url = request(id, chat_id, True).json()
              except AttributeError:
                 return
              image = url['album']['cover_xl']
           except KeyError:
              pass
        try:
           sendPhoto(chat_id, image, caption=track + " - " + artist,
                     reply_markup=InlineKeyboardMarkup(
                                 inline_keyboard=[
                                                [InlineKeyboardButton(text="Download", callback_data=id), InlineKeyboardButton(text="Info", callback_data=album)]
                                 ]
                     ))
        except:
           sendMessage(chat_id, translate(languag[chat_id], "Error :("))
def inline(msg, from_id, query_data, query_id):
    if "artist" in query_data:
     message_id = msg['message']['message_id']
     array = []
     if "album" in query_data:
      try:
         url = request(query_data, from_id, True).json()
      except AttributeError:
         return
      for a in url['data']:
          array.append([InlineKeyboardButton(text=a['title'] + " - " + a['release_date'].replace("-", "/"), callback_data=a['link'])])
      array.append([InlineKeyboardButton(text="BACK 🔙", callback_data=query_data.split("/")[-2] + "/" + "artist")])
      bot.editMessageReplyMarkup(((from_id, message_id)),
                                 reply_markup=InlineKeyboardMarkup(
                                             inline_keyboard=array
                                 ))
     elif "down" in query_data:
      if ans == "2":
       if users[from_id] == 3:
        bot.answerCallbackQuery(query_id, translate(languag[from_id], "Wait the end and repeat the step, did you think you could download how much songs you wanted? ;)"), show_alert=True)
        return
       else:
           users[from_id] += 1
      bot.answerCallbackQuery(query_id, translate(languag[from_id], "Songs are downloading"))
      try:
         url = request("https://api.deezer.com/artist/" + query_data.split("/")[-4] + "/" + query_data.split("/")[-1], from_id, True).json()
      except AttributeError:
         return
      for a in url['data']:
          Link("https://www.deezer.com/track/" + str(a['id']), from_id, qualit[from_id], msg['message'])
          if ans == "2":
           users[from_id] += 1
      if ans == "2":
       users[from_id] -= 1
     elif "radio" in query_data or "top" in query_data:
      try:
         url = request(query_data, from_id, True).json()
      except AttributeError:
         return
      for a in url['data']:
          array.append([InlineKeyboardButton(text=a['artist']['name'] + " - " + a['title'], callback_data="https://www.deezer.com/track/" + str(a['id']))])
      array.append([InlineKeyboardButton(text="GET ALL ⬇️", callback_data=query_data.split("/")[-2] + "/" + "artist/down/" + query_data.split("/")[-1])])
      array.append([InlineKeyboardButton(text="BACK 🔙", callback_data=query_data.split("/")[-2] + "/" + "artist")])
      bot.editMessageReplyMarkup(((from_id, message_id)),
                                 reply_markup=InlineKeyboardMarkup(
                                             inline_keyboard=array
                                 ))
     else:
         link = "https://api.deezer.com/artist/" + query_data.split("/")[-2]
         try:
            url = request("https://api.deezer.com/artist/" + query_data.split("/")[-2], from_id, True).json()
         except AttributeError:
            return
         bot.editMessageReplyMarkup(((from_id, message_id)),
                                 reply_markup=InlineKeyboardMarkup(
                                             inline_keyboard=[
                                                        [InlineKeyboardButton(text="TOP 30", callback_data=link + "/top?limit=30"), InlineKeyboardButton(text="ALBUMS", callback_data=link + "/albums")],
                                                        [InlineKeyboardButton(text="RADIO", callback_data=link + "/radio")]
                                             ]
                                 ))
    else:
        tags = query_data.split("_")
        if tags[0] == "Infos with too many bytes":
         bot.answerCallbackQuery(query_id, translate(languag[from_id], query_data))
        elif len(tags) == 4:
         bot.answerCallbackQuery(query_id, text="Album: " + tags[0] + "\nDate: " + tags[1] + "\nLabel: " + tags[2] + "\nGenre: " + tags[3], show_alert=True)
        else:
            if ans == "2":
             if users[from_id] == 3:
              bot.answerCallbackQuery(query_id, translate(languag[from_id], "Wait the end and repeat the step, did you think you could download how much songs you wanted? ;)"), show_alert=True)
              return
             else:
                 users[from_id] += 1
            bot.answerCallbackQuery(query_id, translate(languag[from_id], "Song is downloading"))
            Link(query_data, from_id, qualit[from_id], msg['message'])
def download(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor="callback_query")
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
    Thread(target=inline, args=(msg, from_id, query_data, query_id)).start()
def search(msg):
    query_id, from_id, query_string = telepot.glance(msg, flavor="inline_query")
    try:
       languag[from_id] = msg['from']['language_code']
    except KeyError:
       languag[from_id] = "en"
    if check_flood(from_id, msg) == "BANNED":
     return
    if "" == query_string:
     search1 = request("http://api.deezer.com/chart/").json()
     result = [InlineQueryResultArticle(id=a['link'], title=a['title'], description=a['artist']['name'], thumb_url=a['album']['cover_big'], input_message_content=InputTextMessageContent(message_text=a['link'])) for a in search1['tracks']['data']]
     result += [InlineQueryResultArticle(id="https://www.deezer.com/album/" + str(a['id']), title=a['title'] + " (Album)", description=a['artist']['name'], thumb_url=a['cover_big'], input_message_content=InputTextMessageContent(message_text="https://www.deezer.com/album/" + str(a['id']))) for a in search1['albums']['data']]
     result += [InlineQueryResultArticle(id=a['link'], title=str(a['position']), description=a['name'], thumb_url=a['picture_big'], input_message_content=InputTextMessageContent(message_text=a['link'])) for a in search1['artists']['data']]
     result += [InlineQueryResultArticle(id=a['link'], title=a['title'], description="N° tracks:" + str(a['nb_tracks']), thumb_url=a['picture_big'], input_message_content=InputTextMessageContent(message_text=a['link'])) for a in search1['playlists']['data']]
    elif "album:" in query_string:
     search1 = request("https://api.deezer.com/search/album/?q=" + query_string.split("album:")[1].replace("#", "")).json()
     try:
        if search1['error']:
         return
     except KeyError:
        pass
     result = [InlineQueryResultArticle(id=a['link'], title=a['title'], description=a['artist']['name'], thumb_url=a['cover_big'], input_message_content=InputTextMessageContent(message_text=a['link'])) for a in search1['data']]
    elif "artist:" in query_string:
     search1 = request("https://api.deezer.com/search/artist/?q=" + query_string.split("artist:")[1].replace("#", "")).json()
     try:
        if search1['error']:
         return
     except KeyError:
        pass
     result = [InlineQueryResultArticle(id=a['link'], title=a['name'], thumb_url=a['picture_big'], input_message_content=InputTextMessageContent(message_text=a['link'])) for a in search1['data']]
    else:
        search1 = request("https://api.deezer.com/search?q=" + query_string.replace("#", "")).json()
        try:
           if search1['error']:
            return
        except KeyError:
           pass
        search1 = search1['data']
        result = [InlineQueryResultArticle(id=a['link'], title=a['title'], description=a['artist']['name'], thumb_url=a['album']['cover_big'], input_message_content=InputTextMessageContent(message_text=a['link'])) for a in search1]
        for a in search1:
            try:
               if "https://www.deezer.com/album/" + str(a['album']['id']) in str(result):
                continue
            except KeyError:
               continue
            result += [InlineQueryResultArticle(id="https://www.deezer.com/album/" + str(a['album']['id']), title=a['album']['title'] + " (Album)", description=a['artist']['name'], thumb_url=a['album']['cover_big'], input_message_content=InputTextMessageContent(message_text="https://www.deezer.com/album/" + str(a['album']['id'])))]
    try:
       bot.answerInlineQuery(query_id, result)
    except telepot.exception.TelegramError:
       pass
def up(msg):
    pass
def start(msg):
    pprint(msg)
    content_type, chat_type, chat_id = telepot.glance(msg)
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
        sendPhoto(chat_id, open("example.png", "rb"), caption=translate(languag[chat_id], "Welcome to @DeezloaderRMX_bot\nPress '/' to get commands list"))
     except FileNotFoundError:
        pass
     sendMessage(chat_id, translate(languag[chat_id], "Press for search songs or albums or artists\nP.S. Remember you can do this digiting @ in your keyboard and select DeezloaderRMX_bot\nSend a Deezer or Spotify link to download\nSend a song o vocal message to recognize the track"),
                 reply_markup=InlineKeyboardMarkup(
                             inline_keyboard=[
                                            [InlineKeyboardButton(text="Search by artist", switch_inline_query_current_chat="artist:"), InlineKeyboardButton(text="Search by album", switch_inline_query_current_chat="album:")],
                                            [InlineKeyboardButton(text="Global search", switch_inline_query_current_chat="")]
                             ]
                ))
    elif content_type == "text" and msg['text'] == "/translator":
     if languag[chat_id] != "en":
      languag[chat_id] = "en"
      sendMessage(chat_id, translate(languag[chat_id], "Now the language is english"))
     else:
         languag[chat_id] = msg['from']['language_code']
         sendMessage(chat_id, translate(languag[chat_id], "Now the bot will use the Telegram app language"))
    elif content_type == "text" and msg['text'] == "/quality":
     sendMessage(chat_id, translate(languag[chat_id], "Select default download quality"),
                 reply_markup=ReplyKeyboardMarkup(
                             keyboard=[
                                     [KeyboardButton(text="FLAC"), KeyboardButton(text="MP3_320Kbps")],
                                     [KeyboardButton(text="MP3_256Kbps"), KeyboardButton(text="MP3_128Kbps")]
                             ]
                ))
    elif content_type == "text" and (msg['text'] == "FLAC" or msg['text'] == "MP3_320Kbps" or msg['text'] == "MP3_256Kbps" or msg['text'] == "MP3_128Kbps"):
     qualit[chat_id] = msg['text'].replace("Kbps", "")
     sendMessage(chat_id, translate(languag[chat_id], "Songs will be downloaded in " + msg['text'] + " quality"), reply_markup=ReplyKeyboardRemove())
     sendMessage(chat_id, translate(languag[chat_id], "Songs which cannot be downloaded in quality you have chosen will be downloaded in the best quality possible"))
    elif content_type == "voice" or content_type == "audio":
     Thread(target=Audio, args=(msg[content_type]['file_id'], chat_id)).start()
    elif content_type == "text" and msg['text'] == "/info":
     sendMessage(chat_id, "Version: 1.2 RMX\nName:@DeezloaderRMX_bot\nCreator:@An0nimia\nDonation:https://www.paypal.me/An0nimia\nForum:https://t.me/DeezloaderRMX_group\nUsers:" + statisc(chat_id, "USERS") + "\nTotal downloads:" + statisc(chat_id, "TRACKS"))
    elif content_type == "text":
     try:
        msg['entities']
        if ans == "2" and users[chat_id] == 3:
         sendMessage(chat_id, translate(languag[chat_id], "Wait the end and repeat the step, did you think you could download how much songs you wanted? ;)"))
        else:
            if ans == "2":
             users[chat_id] += 1
            Thread(target=Link, args=(msg['text'].replace("'", ""), chat_id, qualit[chat_id], msg)).start()
     except KeyError:
        sendMessage(chat_id, translate(languag[chat_id], "Press"),
                    reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[
                                               [InlineKeyboardButton(text="Search artist", switch_inline_query_current_chat="artist:" + msg['text']), InlineKeyboardButton(text="Search album", switch_inline_query_current_chat="album:" + msg['text'])],
                                               [InlineKeyboardButton(text="Search global", switch_inline_query_current_chat=msg['text'])]
                                ]
                   ))
try:
   print("1):Free")
   print("2):Strict")
   ans = input("Choose:")
   if ans == "1" or ans == "2":
    bot.message_loop({
                      "chat": start,
                      "callback_query": download,
                      "inline_query": search,
                      "chosen_inline_result": up
                     })
    print("Bot started")
    while True:
        sleep(1)
        if del1 == del2:
         del1,del2 = 0,0
         for a in os.listdir(loc_dir):
             try:
                shutil.rmtree(loc_dir + a)
             except NotADirectoryError:
                os.remove(loc_dir + a)
        now = datetime.now()
        if now.hour % 1 == 0 and now.minute == 0 and now.second == 0:
         downloa = deezloader.Login(setting.username, setting.password, setting.deezer_token)
except KeyboardInterrupt:
   os.rmdir(loc_dir)
   print("\nSTOPPED")
