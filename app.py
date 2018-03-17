
from flask import Flask, Response, json, request, redirect, url_for, g
import hashlib
from urllib.parse import urlparse
from models import *

app = Flask(__name__)


STATUS = ["OK", "FAILED"]
STATUS_CODES = ["INVALID_URLS", "SHORT_URLS_NOT_FOUND", "BAD_DATA"]
sqlite_db = SqliteDatabase('urlShortened.db')

@app.before_request
def before_request():
	sqlite_db.connect()
	UrlMap.create_table()

@app.teardown_request
def teardown_request(exception):
	sqlite_db.close()

def cleaning():
	if UrlMap.table_exists():
		UrlMap.drop_table()
		UrlMap.create_table()

@app.route('/<string:hashUrl>/',methods = ["POST"])
def redirection(hashUrl):
	if hashUrl == "clean-urls":
		cleaning()
		resp = Response(json.dumps({}), status=200, mimetype='application/json')
		return resp
	else:
		urlPair = UrlMap.get(shortUrl = request.host + '/' + hashUrl)
		urlPair.update(count = urlPair.count + 1).execute()	
		return redirect(urlPair.longUrl,302)

@app.route('/fetch/<string:urltype>/',methods = ['POST'])
def urlHandler(urltype):

	def parseCheck(longUrls, host):
		invalidUrls = []
		hashedUrls = {}
		for longUrl in longUrls:
			parsedUrl = urlparse(longUrl)
			print(parsedUrl)
			if not parsedUrl.netloc:
				invalidUrls.append(longUrl)
			elif not invalidUrls:
				hash = hashlib.sha1(longUrl.encode("UTF-8")).hexdigest()
				hash = hash[:8]
				hashedUrls[longUrl] = host + '/' + hash
		return hashedUrls, invalidUrls

	def urlMapping(hashedUrls):
		for key, value in hashedUrls.items():
			UrlMap.get_or_create(longUrl = key, shortUrl = value)

	def fetchCount(shortUrl):
		urlPair = UrlMap.get_or_none(shortUrl = shortUrl)
		if urlPair:
			return urlPair.count
		else:
			return None

	def fetchLongUrls(shortUrls):
		invalidUrls = []
		hashedUrls = {}
		for shortUrl in shortUrls:
			urlPair = UrlMap.get_or_none(shortUrl = shortUrl)
			if not urlPair:
				invalidUrls.append(shortUrl)
			elif not invalidUrls:
				hashedUrls[shortUrl] = urlPair.longUrl
		return hashedUrls, invalidUrls

	response = {}
	response["status"] = STATUS[0]
	response["status_codes"] = []

	stat = 200
	req = request.get_json()

	if urltype == "short-url":
		hashedUrls, invalidUrls = parseCheck([req["long_url"]], request.host)

		if not invalidUrls:
			urlMapping(hashedUrls)
			response["short_url"] = list(hashedUrls.values())
		else:
			response['status'] = STATUS[1]
			response['status_codes'] = [STATUS_CODES[0]]

	elif urltype == "short-urls":	
		hashedUrls, invalidUrls = parseCheck(req["long_urls"], request.host)

		if not invalidUrls:
			urlMapping(hashedUrls)
			response["short_urls"] = hashedUrls
		else:
			response["invalid_urls"] = invalidUrls
			response['status'] = STATUS[1]
			response['status_codes'] = [STATUS_CODES[0]]

	elif urltype == 'count':
		count = fetchCount(req["short-url"])

		if count:
			response["count"] = count
		else:
			response['status'] = STATUS[1]
			response['status_codes'] = []

	elif urltype == "long-url":
		hashedUrls, invalidUrls = fetchLongUrls([req["short_url"]])

		if not invalidUrls:
			response["long_url"] = list(hashedUrls.values())
		else:
			response['status'] = STATUS[1]
			response['status_codes'] = [STATUS_CODES[1]]
	
	elif urltype == "long-urls":
		hashedUrls, invalidUrls = fetchLongUrls(req["short_urls"])

		if not invalidUrls:
			response["long_urls"] = hashedUrls
		else:
			response["invalid_urls"] = []
			response['status'] = STATUS[1]
			response['status_codes'] = [STATUS_CODES[1]]
	else:
		response['status'] = STATUS[1]
		response['status_codes'] = [STATUS_CODES[2]]
		stat = 404
		
	data = json.dumps(response)
	resp = Response(data, status=stat, mimetype='application/json')
	return resp

app.run(port = 5000)
