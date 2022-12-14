# DeezSpot_bot
- A new bot is avalaible here [DeezSpot_bot](https://t.me/DeezSpot_bot). ENJOY :)

# Disclaimer

- I am not responsible for the usage of this program by other people.
- I do not recommend you doing this illegally or against Deezer's terms of service.
- This project is licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)

* ### PYTHON VERSION SUPPORTED ###
	![Python >= 3.9](https://img.shields.io/badge/python-v%3E=3.9-blue)

* ### OS Supported ###
	![Linux Support](https://img.shields.io/badge/Linux-Support-brightgreen.svg)
	![macOS Support](https://img.shields.io/badge/macOS-Support-brightgreen.svg)
	![Windows Support](https://img.shields.io/badge/Windows-Support-brightgreen.svg)

# SET UP

## Configurations

  ### bot_settings.py

  Go and modify [bot_settings.py](https://github.com/An0nimia/DeezSpot_bot/blob/master/configs/bot_settings.py)

  ![Image](https://github.com/An0nimia/DeezSpot_bot/blob/master/photos/screen_1.png)

  - Read the code comments
  - Add your chat_id to root_ids
  - Modify the bunker_channel variable with your channel id (the others one are optional, but suggested. YES you should create 3 channels :))
  - Be sure that in the channel you have setted the bot as admin, you have setted the right permissions and you added as admin also your user bot(personal account) as admin in the channel ALSO IT WON'T WORK
  - If you don't know how to get chat id send messages to him [@JsonDumpBot](https://t.me/JsonDumpBot)

  ### .deez_settings.ini


  Go and modify [.deez_settings.ini](https://github.com/An0nimia/DeezSpot_bot/blob/master/.deez_settings.ini)

  - mail, password, token(arl) are deezer credentials used for login
  - the pyrogram api_id & api_hash can be created [here](https://my.telegram.org/auth?to=apps)
  - for create a telegram bot look [here](https://t.me/BotFather)
  - for acrcloud key, secret, host look at [acrcloud](https://docs.acrcloud.com/tutorials/recognize-music) (NOW YOU CAN LEAVE HOST VAR EMPTY IF YOU DON'T WANT TO USE IT)

  ### .set_configs.py
  
  Go and modify [set_configs.py](https://github.com/An0nimia/DeezSpot_bot/blob/master/configs/set_configs.py)
  
  If you don't want to login with arl, which expire, log with normal credentials & delete line 35

## INSTALLATION WITH DOCKER

### Be sure you made all the configurations as explained above

Let create a volume

    docker volume create deezspot_disk

Build the image

    docker build -t deezspot .

Run the container
  
    docker run -v deezspot_disk:/app --rm -it deezspot bash
    python deez_bot.py

  ### OR  
    docker run -v deezspot_disk:/app --rm -it deezspot python deez_bot.py

Detach the container

    Press (CTRL + P) + (CTRL + Q) as explained here https://stackoverflow.com/questions/19688314/how-do-you-attach-and-detach-from-dockers-process

Attach the container

    docker attach <container_id> # you can find it with docker ps

## INSTALLATION NORMAL

Let create a own env

    pip install virtualenv

To install it just type this command

    git clone https://github.com/An0nimia/DeezSpot_bot.git && cd DeezSpot_bot && virtualenv bot_env && source bot_env/bin/activate && pip3 install -r req.txt

# START IT

## First method

```bash
python3 deez_bot.py
```

## OR

If you know how tmux works

```bash
tmux new -s deez_bot
```

then when you are inside just type

```bash
python3 deez_bot.py 1
```
