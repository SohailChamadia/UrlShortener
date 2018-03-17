from peewee import *

db = SqliteDatabase("urlShortened.db")

class UrlMap(Model):

	shortUrl = CharField(primary_key = True)
	longUrl = CharField()
	count = IntegerField(default = 0)

	class Meta:
		database = db

