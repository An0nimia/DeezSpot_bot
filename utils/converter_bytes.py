#!/usr/bin/python3

def convert_bytes_to(size, b_format):
	b_formats = ["kb", "mb", "gb", "tb"]
	index = b_formats.index(b_format) + 1
	in_bytes = 1000 ** index
	size /= in_bytes

	return size