#!/usr/bin/python3

from io import BytesIO

import matplotlib as mpl
mpl.use("agg")

from datetime import datetime
import matplotlib.pyplot as plt
from calendar import month_abbr
from configs.customs import bot_name
import matplotlib.dates as months_dates
from helpers.db_help import select_users_settings_date, select_dwsongs_top_downloaders

__locator = months_dates.MonthLocator()
__fmt = months_dates.DateFormatter("%b")
__many = 10

__manies = [
	a
	for a in range(1, 11)
]

def __get_data_users():
	num_of_months = len(month_abbr)
	datetime_months = []
	nums_users_per_month = []
	now = datetime.now()
	c_year = str(now.year)

	for n_month in range(1, num_of_months):
		c_month_name = month_abbr[n_month]

		if n_month < 10:
			c_month = f"0{n_month}"
		else:
			c_month = str(n_month)

		data = select_users_settings_date(c_month, c_year)
		l_data = len(data)
		nums_users_per_month.append(l_data)
		datetime_month = datetime.strptime(c_month_name, "%b")
		datetime_months.append(datetime_month)

	return datetime_months, nums_users_per_month

def create_graph_users() -> BytesIO:
	datetime_months, nums_users_per_month = __get_data_users()

	plt.plot(
		datetime_months, nums_users_per_month,
		marker = "o"
	)

	plt.title(f"{bot_name} users", fontweight = "bold")
	plt.xlabel("Months")
	plt.ylabel("Users")
	plt.legend(["Users"])

	x = plt.gca().xaxis
	x.set_major_locator(__locator)
	x.set_major_formatter(__fmt)
	x.grid()

	y = plt.gca().yaxis
	y.grid()

	for c_date, num_users in zip(datetime_months, nums_users_per_month):
		plt.text(c_date, num_users, num_users)

	buf = BytesIO()
	plt.savefig(buf)
	buf.seek(0)
	plt.close()

	return buf

def get_data_downloaders():
	data = select_dwsongs_top_downloaders(__many)
	users = []
	nums_downloads = []

	for user, num_downloads in data:
		users.append(user)
		nums_downloads.append(num_downloads)

	return users, nums_downloads

def create_graph_top_downloaders() -> BytesIO:
	users, nums_downloads = get_data_downloaders()

	plt.stem(__manies, nums_downloads)
	plt.title(f"{bot_name} top downloaders", fontweight = "bold")
	plt.xlabel("Users")
	plt.ylabel("Downloads")
	plt.legend(["Downloads"])
	plt.xticks(__manies)

	x = plt.gca().xaxis
	x.grid()

	y = plt.gca().yaxis
	y.grid()

	for num, num_downloads in zip(__manies, nums_downloads):
		plt.text(num, num_downloads, num_downloads)

	buf = BytesIO()
	plt.savefig(buf)
	buf.seek(0)
	plt.close()

	return buf