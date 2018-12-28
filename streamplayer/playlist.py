#!/usr/bin/env python3

import json

from db import DB

class Entry:

	def __init__(self, data):
		self.db = DB()
		self.video = data["video"]
		self.logo = data["logo"]
		self.overlays = data["overlays"]

	def has_overlay(self):
		return len(self.overlays) > 0

	def has_logo(self):
		return self.logo != ""

	def get_overlays(self):
		return self.overlays

	def get_logo(self):
		return self.logo

	def get_video(self):
		if self.video["file"].endswith(".mp4"):
			return self.video["file"]
		else:
			return self.db.getVideoFile(self.video["file"])

	def get_video_size_x(self):
		return self.video["size"]["x"]

	def get_video_size_y(self):
		return self.video["size"]["y"]

	def get_video_pos_x(self):
		return self.video["position"]["x"]

	def get_video_pos_y(self):
		return self.video["position"]["y"]

	def __str__(self):
		return ', '.join(['{key}={value}'.format(key=key, value=self.__dict__.get(key)) for key in self.__dict__])


class Playlist:

	def __init__(self, fname):
		self.entries = []

		with open(fname) as f:
			file_input = json.load(f)

		for e in file_input:
			self.add_entry(e)

		self.next_entry = 0

	def __str__(self):
		return ', '.join(['{key}={value}'.format(key=key, value=self.__dict__.get(key)) for key in self.__dict__])

	def add_entry(self, data):
		self.entries.append(Entry(data))

	def get_next(self):
		try:
			return self.entries.pop(0)
		except IndexError:
			return None


if __name__ == "__main__":
	from config import Config
	playlist = Playlist(Config.PLAYLISTFILE)
	print(playlist)
	while True:
		next_entry = playlist.get_next()
		if not next_entry:
			break
		print(next_entry.get_video())