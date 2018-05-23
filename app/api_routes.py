from app import app
import json
from flask import jsonify
from modules.twitter_user import TwitterUser
from app.models import ActorReport, TweetReport
from app import db

@app.route('/api/actors')
def api_get_actors():
	data = {}
	politicians = []
	actors_count = 0
	actors = json.load(open("helpers/politicians.json"))
	for actor in actors:
		if actor['twitter_handle'] != "":
			actors_count += 1
			politicians.append(actor['twitter_handle'])
	data['code'] = '200'
	data['message'] = 'Success'
	data['length'] = actors_count
	data['actors'] = politicians

	return jsonify(data)

@app.route('/api/actors/datetime')
def api_get_actors_datetime():
	data = {}
	data['dates'] = []
	length = 0
	reports = ActorReport.query.all()
	for report in reports:
		data['dates'].append(report.date[0:10])

	data['code'] = '200'
	data['message'] = 'Success'
	return jsonify(data)

@app.route('/api/actor/<username>/', defaults={ 'date': None })
@app.route('/api/actor/<username>/<date>')
def api_get_actor_account_date(username,date):
	## If not specified date, API will return current values from Tweepy API.
	all_actors_collection_dates = []
	actorreports = ActorReport.query.all()
	for actorreport in actorreports:
		all_actors_collection_dates.append(actorreport.date[0:10])


	tweets_collection_dates = []
	tweetreports = TweetReport.query.filter_by(username= username)
	for tweetreport in tweetreports:
		tweets_collection_dates.append(tweetreport.date[0:10])

	if date == None :
		user = TwitterUser(username)
		if user.existence == False :
			data = {'code': '400', 'message': 'Bad Request', 'details': 'Invalid username.'}
			return jsonify(data)
		else:
			data = {'code': '200', 'message':'Success', 'username': user.username, 'name': user.name, 'followers_count': user.followers_count, 'tweets_count': user.tweets_count, 'following_count': user.following_count, 'likes_count': user.likes_count, 'tweets_collection_dates': tweets_collection_dates, 'all_actors_collection_dates': all_actors_collection_dates}
			return jsonify(data)
	else:
		# What to do if there's multiple records for the same date?
		try:
			reports = ActorReport.query.all()
			for auxreport in reports:
				if auxreport.date[0:10] == date:
					report = auxreport.csv_content.decode()
			lines = report.split('\n')		
		except:
			data = {'code': '500', 'message': 'Internal Server Error', 'details': 'Could not find CSV for specific date.'}
			return jsonify(data)
		else:
			for line in lines:
				aux = line.split(';')
				if len(aux)>1 and username.lower() == aux[1].lower():
					data = {'date': date, 'code': '200', 'message':'Success', 'username': aux[1], 'name': aux[0], 'followers_count': aux[2], 'tweets_count': aux[5], 'following_count': aux[3], 'likes_count': aux[4] }
					return jsonify(data)
			data = {'code': '400', 'message': 'Bad Request', 'details': 'Invalid username.'}
			return jsonify(data)

@app.route('/api/actor/<username>/<date>/tweets')
def api_get_actor_account_date_tweets(username,date):
	report = None
	data = {}
	tweets_report = TweetReport.query.filter_by(username= username)
	for tweetreport in tweets_report:
		if tweetreport.date[0:10] == date:
			report = tweetreport

	if report == None:
		data = {'code': '400', 'message': 'Bad Request', 'details': 'Invalid username or date.'}
		return jsonify(data)
	else:
		content = report.csv_content.decode()
		content = content.split('\n')
		data['tweets'] = []
		for line in content:
			try:
				aux_line = line.split(';')
				data['tweets'].append({'date': aux_line[0], 'text': aux_line[1], 'rt_author': aux_line[2], 'retweets': aux_line[3], 'likes': aux_line[4], 'hashtags': aux_line[5], 'mention':aux_line[6] })
			except:
				pass

		data['code'] = '200'
		data['message'] = 'Success'
		return jsonify(data)
