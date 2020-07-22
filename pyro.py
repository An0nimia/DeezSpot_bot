from pyrogram import Client

api_id = 1455634
api_hash = "3d41b573a565f4682d41712a99edd69a"

with Client("my_account", api_id, api_hash) as app:
    app.send_message("me", "Greetings from **Pyrogram**!")