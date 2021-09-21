#!/usr/bin/python3

from logging import ERROR, INFO
from utils.converter_bytes import convert_bytes_to
from telegram.constants import MAX_FILESIZE_DOWNLOAD

logs_path = "logs/"
log_downloads = f"{logs_path}downloads.log"
log_uploads = f"{logs_path}uploads.log"
log_telegram = f"{logs_path}telegram.log"

logger_names = [
	("telegram.ext.dispatcher", ERROR, log_telegram),
	("uploads", INFO, log_uploads),
	("downloads", ERROR, log_downloads)
]

warning_for_banning = 4
user_session = "my_account"
user_errors = None #put yours
bunker_channel = None #put yours
owl_channel = None #put yours
db_name = "deez_bot.db"
settings_file = ".deez_settings.ini"
root_ids = {1270777127}
output_songs = "Songs/"
output_shazam = "Records/"
recursive_quality = True
recursive_download = True
make_zip = True
method_save = 2
download_dir_max_size = 6 #GB
progress_status_rate = 15

supported_link = [
	"www.deezer.com", "open.spotify.com",
	"deezer.com", "spotify.com", "deezer.page.link"
]

time_sleep = 8
seconds_limits_album = 30000 #seconds
seconds_limits_track = 7200
upload_max_size_user = 2 #GB
max_song_per_playlist = 200
max_download_user = 3

recorded_file_max_size = int(
	convert_bytes_to(
		MAX_FILESIZE_DOWNLOAD, "mb"
	)
)
