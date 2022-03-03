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

## INSTALLATION

Let create a own env

    pip install virtualenv

To install it just type this command

    git clone https://github.com/An0nimia/DeezSpot_bot.git && cd DeezSpot_bot && virtualenv bot_env && source bot_env/bin/activate && pip3 install -r req.txt

## Configurations

  ### bot_settings.py

  Go and modify [bot_settings.py](https://github.com/An0nimia/DeezSpot_bot/blob/master/configs/bot_settings.py)

  ![Image](https://github.com/An0nimia/DeezSpot_bot/blob/master/photos/screen_1.png)

  - Read the code comments
  - If you don't know how to get chat id send messages to him [@JsonDumpBot](https://t.me/JsonDumpBot)

  ### .deez_settings.ini


  Go and modify [.deez_settings.ini](https://github.com/An0nimia/DeezSpot_bot/blob/master/.deez_settings.ini)

  - mail, password, token(arl) are deezer credentials used for login
  - the pyrogram api_id & api_hash can be created [here](https://my.telegram.org/auth?to=apps)
  - for create a telegram bot look [here](https://t.me/BotFather)
  - for acrcloud key, secret, host look at [acrcloud](https://docs.acrcloud.com/tutorials/recognize-music)

  ### .set_configs.py
  
  Go and modify [set_configs.py](https://github.com/An0nimia/DeezSpot_bot/blob/master/configs/set_configs.py)
  
  If you don't want to login with arl, which expire, log with normal credentials & delete line 35

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
