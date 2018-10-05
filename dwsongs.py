#!/usr/bin/python3
import os
import json
import shutil
import setting
import spotipy
import telepot
import acrcloud
import requests
import threading
import dwytsongs
import deezloader
from time import sleep
from bs4 import BeautifulSoup
import spotipy.oauth2 as oauth2
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
downloa = deezloader.Login(setting.username, setting.password)
token = setting.token
bot = telepot.Bot(token)
stage = {}
users = {}
artist = {}
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
def delete(chat_id):
    global temp
    try:
       users[chat_id] -= 1
    except KeyError:
       None
    array2.append(chat_id)
    temp = 1
def sendAudio(chat_id, audio, image):
    url = "https://api.telegram.org/bot" + token + "/sendAudio"
    data = {
            "chat_id": chat_id
    }
    file = {
            "audio": audio,
            "thumb": requests.get(image).content
    }
    requests.post(url, params=data, files=file)
def Link1(music, chat_id):
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
         z = downloa.download_trackspo(music, check=False)
        elif "album/" in music:
         if "?" in music:
          music,a = music.split("?")
         try:
            tracks = spo.album(music)
         except Exception as a:
            if not "The access token expired" in str(a):
             bot.sendMessage(chat_id, "Invalid link ;)")
             delete(chat_id)
             return
            token = generate_token()
            spo = spotipy.Spotify(auth=token)
            tracks = spo.album(music)
         for a in range(tracks['total_tracks']):
             image.append(tracks['images'][2]['url'])
         for a in tracks['tracks']['items']:
             links.append(a['external_urls']['spotify'])
         b = tracks['total_tracks']
         for a in range(b // 50):
             try:
                tracks = spo.next(tracks['tracks'])
             except:
                token = generate_token()
                spo = spotipy.Spotify(auth=token)
                tracks = spo.next(tracks['tracks'])
             for a in tracks['items']:
                 links.append(a['external_urls']['spotify'])
         msg = telepot.message_identifier(bot.sendMessage(chat_id, ("About " + str((b * 13) // 60)) + " minutes"))
         z = downloa.download_albumspo(music, check=False)
        elif "playlist/" in music:
         if "?" in music:
          music,a = music.split("?")
         musi = music.split("/")
         try:
            tracks = spo.user_playlist_tracks(musi[-3], playlist_id=musi[-1])
         except Exception as a:
            if not "The access token expired" in str(a):
             bot.sendMessage(chat_id, "Invalid link ;)")
             delete(chat_id)
             return
            token = generate_token()
            spo = spotipy.Spotify(auth=token)
            tracks = spo.user_playlist_tracks(musi[-3], playlist_id=musi[-1])
         for a in tracks['items']:
             image.append(a['track']['album']['images'][2]['url'])
             links.append(a['track']['external_urls']['spotify'])
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
         bot.sendMessage(chat_id, ("About " + str((tracks['total'] * 13) // 60)) + " minutes")
         z = downloa.download_playlistspo(music, check=False)
       elif "deezer" in music:
        if "track/" in music:
         if "?" in music:
          music,a = music.split("?")
         url = json.loads(requests.get("http://api.deezer.com/track/" + music.split("/")[-1]).text)
         try:
            if "error" in str(url):
             bot.sendMessage(chat_id, "Invalid link ;)")
             delete(chat_id)
             return
         except KeyError:
            None
         try:
            image.append(url['album']['cover_xl'].replace("1000", "90"))
         except:
            URL = "http://www.deezer.com/track/" + music.split("/")[-1]
            try:
               image = requests.get(URL).text
            except:
               image = requests.get(URL).text
            image = BeautifulSoup(image, "html.parser").find("img", class_="img_main").get("src").replace("200", "1200")
         z = downloa.download_trackdee(music, check=False)
        elif "album/" in music:
         if "?" in music:
          music,a = music.split("?")
         url = json.loads(requests.get("http://api.deezer.com/album/" + music.split("/")[-1]).text)
         try:
            if "error" in str(url):
             bot.sendMessage(chat_id, "Invalid link ;)")
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
                   image = requests.get(URL).text
                except:
                   image = requests.get(URL).text
                image = BeautifulSoup(image, "html.parser").find("img", class_="img_main").get("src").replace("200", "1200")
         b = url['nb_tracks']
         msg = telepot.message_identifier(bot.sendMessage(chat_id,  ("About " + str((b * 13) // 60)) + " minutes"))
         z = downloa.download_albumdee(music, check=False)
        elif "playlist/" in music:
         if "?" in music:
          music,a = music.split("?")
         url = json.loads(requests.get("https://api.deezer.com/playlist/" + music.split("/")[-1] + "/tracks").text)
         try:
            if "error" in str(url):
             bot.sendMessage(chat_id, "Invalid link ;)")
             delete(chat_id)
             return
         except KeyError:
            None
         times = 0
         for a in url['data']:
             image.append(json.loads(requests.get("http://api.deezer.com/track/" + str(a['id'])).text)['album']['cover_xl'].replace("1000", "90"))
             times += 1
         bot.sendMessage(chat_id, ("About " + str((times * 13) // 60)) + " minutes")
         z = downloa.download_playlistdee(music, check=False)  
       if type(z) is str:
        z = [z]
       for b in range(len(z)):
           try:
              sendAudio(chat_id, open(z[b], "rb"), image[b])
           except FileNotFoundError:
              Link2(chat_id, links[b], image[b])
    except deezloader.TrackNotFound as error:
       Link2(chat_id, music, image[0])
    except deezloader.AlbumNotFound as error: 
       bot.editMessageText(msg, ("About " + str((b * 22) // 60)) + " minutes")
       Link2(chat_id, music, image)
    except deezloader.InvalidLink as error:
       bot.sendMessage(chat_id, str(error))
    except dwytsongs.TrackNotFound as error:
       bot.sendMessage(chat_id, str(error) + " :(")
    except UnboundLocalError:
       bot.sendMessage(chat_id, "Invalid link ;)")
    delete(chat_id)
def Name1(artist, song, chat_id):
    global spo
    array3.append(chat_id)
    try:
       try:
          search = spo.search(q="track:" + song + " artist:" + artist)
       except:
          token = generate_token()
          spo = spotipy.Spotify(auth=token)
          search = spo.search(q="track:" + song + " artist:" + artist)
       try:
          image = search['tracks']['items'][0]['album']['images'][2]['url']
       except IndexError:
          bot.sendMessage(chat_id, "Song not found :(")
          delete(chat_id)
          return
       a = downloa.download_name(artist, song, check=False)
       sendAudio(chat_id, open(a, "rb"), image)
    except deezloader.TrackNotFound:
       Name2(artist, song, chat_id, image)
    except dwytsongs.TrackNotFound as error:
       bot.sendMessage(chat_id, str(error) + " :(")
    delete(chat_id)
def Link2(chat_id, music, image):
    try:
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
        image = [image]
       for a in range(len(z)): 
           try:
              sendAudio(chat_id, open(z[a], "rb"), image[a])
           except FileNotFoundError:
              bot.sendMessage(chat_id, "Error downloading " + z.split("/")[-1] + " :(")
    except UnboundLocalError:
       bot.sendMessage(chat_id, "Invalid link ;)")
def Name2(artist, song, chat_id, image):
    a = dwytsongs.download_name(artist, song, check=False)
    sendAudio(chat_id, open(a, "rb"), image)
def Audio(audio, chat_id):
    global spo
    global goes
    goes = 1
    file = local + "/Songs/" + audio + ".ogg"
    bot.download_file(audio, file)
    audio = acrcloud.recognizer(config, file)
    try:
       os.remove(file)
    except FileNotFoundError:
       None
    if audio['status']['msg'] != "Success":
     bot.sendMessage(chat_id, "Sorry cannot detect the song from audio :(, retry...")
    else:
        artist = audio['metadata']['music'][0]['artists'][0]['name']
        track = audio['metadata']['music'][0]['title']
        album = audio['metadata']['music'][0]['album']['name']
        try:
           date = audio['metadata']['music'][0]['release_date']
        except KeyError:
           None 
        try:
           label = audio['metadata']['music'][0]['label']
        except KeyError:
           None
        try:
           genre = audio['metadata']['music'][0]['genres'][0]['name']
        except KeyError:
           None
        try:
           album += ">" + date
        except NameError:
           None 
        try:
           album += ">" + label
        except NameError:
           None
        try:
           album += ">" + genre
        except NameError:
           None
        if len(album) > 64:
         album = "Infos with too many bytes"
        if len(album.split(">")) == 1:
         album = "No informations"
        url = json.loads(requests.get("https://api.deezer.com/search/track/?q=" + track.replace("#", "") + " + " + artist.replace("#", "")).text)
        try:
           for a in range(url['total'] + 1):
               if url['data'][a]['title'] == track or url['data'][a]['title_short'] in track:
                id = url['data'][a]['link']
                image = url['data'][a]['album']['cover_xl']
                break
        except IndexError:
           try:
              url = json.loads(requests.get("https://api.deezer.com/search/track/?q=" + track.replace("#", "").split(" ")[0] + " + " + artist.replace("#", "")).text)
              for a in range(url['total'] + 1):
                  if track.split(" ")[0] in url['data'][a]['title']:
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
           bot.sendMessage(chat_id, "Error :(")
    goes = 2
def download(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor="callback_query")
    tags = query_data.split(">")
    if query_data == "Infos with too many bytes" or query_data == "No informations":
     bot.answerCallbackQuery(query_id, query_data)
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
             bot.answerCallbackQuery(query_id, "Wait to finish and repress download, did you thought that you could download how much songs did you want? :)", show_alert=True)
             return
            else:
                users[from_id] += 1
                bot.answerCallbackQuery(query_id, "Song is downloading")
         except KeyError:
            users[from_id] = 1
        bot.answerCallbackQuery(query_id, "Song is downloading")
        threading.Thread(target=Link1, args=(query_data, from_id)).start()
def start1(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    try:
        stage[chat_id]
    except KeyError:
        stage[chat_id] = 0
    if content_type == "text" and msg['text'] == "/start":
     bot.sendMessage(chat_id, "Welcome to @DeezloaderRMX_bot")
     bot.sendMessage(chat_id, "This bot has been created for download songs by a Spotify or Deezer link, by an artist and song name or by an audio or voice message")
     bot.sendPhoto(chat_id, open("example.jpg", "rb"), caption="The bot commands can find here")
    elif content_type == "text" and msg['text'] == "/link":
     bot.sendMessage(chat_id, "Insert the link to download the music or album from spotify or deezer")
     stage[chat_id] = 1
    elif content_type == "text" and msg['text'] != "/link" and msg['text'] != "/name" and stage[chat_id] == 1:
     music = msg['text']
     threading.Thread(target=Link1, args=(music, chat_id)).start()
    elif content_type == "text" and msg['text'] == "/name":
     bot.sendMessage(chat_id, "Insert the artist's name:")
     stage[chat_id] = 2
    elif content_type == "text" and msg['text'] != "/link" and msg['text'] != "/name" and stage[chat_id] == 2:
     artist[chat_id] = msg['text']
     bot.sendMessage(chat_id, "Insert the name song:")
     stage[chat_id] = 3
    elif content_type == "text" and msg['text'] != "/link" and msg['text'] != "/name" and stage[chat_id] == 3:
     song = msg['text']
     threading.Thread(target=Name1, args=(artist[chat_id], song, chat_id)).start()
    elif content_type == "voice" or content_type == "audio":
     audio = msg[content_type]['file_id']
     threading.Thread(target=Audio, args=(audio, chat_id)).start()
def start2(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    try:
        stage[chat_id]
    except KeyError:
        stage[chat_id] = 0
    if content_type == "text" and msg['text'] == "/start":
     bot.sendMessage(chat_id, "Welcome to @DeezloaderRMX_bot")
     bot.sendMessage(chat_id, "This bot has been created for download songs by a Spotify or Deezer link, by an artist and song name or by an audio or voice message")
     bot.sendPhoto(chat_id, open("example.jpg", "rb"), caption="The bot commands can find here")
    elif content_type == "text" and msg['text'] == "/link":
     bot.sendMessage(chat_id, "Insert the link to download the music or album from spotify or deezer")
     stage[chat_id] = 1
    elif content_type == "text" and msg['text'] != "/link" and msg['text'] != "/name" and stage[chat_id] == 1:
     music = msg['text']
     print(msg)
     try:
        if users[chat_id] == 2:
         bot.sendMessage(chat_id, "Wait to finish and resend the " + content_type + ", did you thought that you could download how much songs did you want? :)")
        else:
            users[chat_id] += 1
            threading.Thread(target=Link1, args=(music, chat_id)).start()
     except KeyError:
        users[chat_id] = 1
        threading.Thread(target=Link1, args=(music, chat_id)).start()
    elif content_type == "text" and msg['text'] == "/name":
     bot.sendMessage(chat_id, "Insert the artist's name:")
     stage[chat_id] = 2
    elif content_type == "text" and msg['text'] != "/link" and msg['text'] != "/name" and stage[chat_id] == 2:
     artist[chat_id] = msg['text']
     bot.sendMessage(chat_id, "Insert the name song:")
     stage[chat_id] = 3
    elif content_type == "text" and msg['text'] != "/link" and msg['text'] != "/name" and stage[chat_id] == 3:
     song = msg['text']
     print(artist[chat_id])
     print(msg)
     try:
        if users[chat_id] == 2:
         bot.sendMessage(chat_id, "Wait to finish and resend the " + content_type + ", did you thought that you could download how much songs did you want? :)")
        else:
            users[chat_id] += 1
            threading.Thread(target=Name1, args=(artist[chat_id], song, chat_id)).start()
     except KeyError:
        users[chat_id] = 1
        threading.Thread(target=Name1, args=(artist[chat_id], song, chat_id)).start()
    elif content_type == "voice" or content_type == "audio":
     audio = msg[content_type]['file_id']
     threading.Thread(target=Audio, args=(audio, chat_id)).start()
try:
   while True:
       print("1):Free")
       print("2):Strict")
       print("3):Exit")
       ans = input("Choose:")
       if ans == "3":
        break
       elif ans != "1" or ans != "2" or ans != "3":
        if ans == "1":
         bot.message_loop({
                           "chat": start1,
                           "callback_query": download
                          })
        elif ans == "2":
         bot.message_loop({
                           "chat": start2,
                           "callback_query": download
                          }) 
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