#!/usr/bin/env python3

import sqlite3
import random

from config import Config

class DB:
	def __init__(self):
		self.conn = sqlite3.connect(Config.DBFILE)
		self.c = self.conn.cursor()

	def getVideoFile(self, name):
		self.c.execute("SELECT path from {}".format(name))
		result = self.c.fetchall()
		if result:
			return random.choice(result)[0]
		else:
			return None

if __name__ == '__main__':
	db = DB()
	video = db.getVideoFile("regularshow")
	if video:
		print(video)

	video = db.getVideoFile("regularshow")
	if video:
		print(video)