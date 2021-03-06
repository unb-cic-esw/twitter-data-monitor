from app import app
import json
from flask import jsonify
from modules.twitter_user import TwitterUser
from app.models import ActorReport, TweetReport, Actor, RelationReport, TLRelationReport
from app import db

@app.route('/test')
def test_route():
	return "hello world"

@app.route('/api/actors')
def api_get_actors():
	data = {}
	politicians = []
	actors_count = 0
	actors = Actor.query.all()
	for actor in actors:
		actors_count += 1
		politicians.append(actor.username)
	data['code'] = '200'
	data['message'] = 'Success'
	data['length'] = actors_count
	data['actors'] = politicians

	return jsonify(data)

@app.route('/api/actors/datetime')
def api_get_actors_datetime():
	data = {}
	dates = []
	length = 0
	reports = ActorReport.query.all()
	for report in reports:
		dates.append(report.date)

	data['dates'] = list(set(dates))
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
		all_actors_collection_dates.append(actorreport.date)

	all_actors_collection_dates = list(set(all_actors_collection_dates))

	actor = Actor.query.filter_by(username=username).first()
	if not actor:
		data = {'code': '400', 'message': 'Bad Request', 'details': 'Invalid username.'}
		return jsonify(data)


	tweets_collection_dates = []
	tweetreports = TweetReport.query.filter_by(actor_id= actor.id)
	for tweetreport in tweetreports:
		tweets_collection_dates.append(tweetreport.date)

	tweets_collection_dates = list(set(tweets_collection_dates))

	if date == None :
		user = TwitterUser(actor.id)
		if user.existence == False :
			data = {'code': '400', 'message': 'Bad Request', 'details': 'Invalid username.'}
			return jsonify(data)
		else:
			if user.username != actor.username:
				Actor.query.filter_by(id=actor.id).update(dict(username=user.username))
				db.session.commit()
			data = {'code': '200', 'message':'Success', 'username': user.username, 'name': user.name, 'followers_count': user.followers_count, 'tweets_count': user.tweets_count, 'following_count': user.following_count, 'likes_count': user.likes_count, 'tweets_collection_dates': tweets_collection_dates, 'actor_collection_dates': all_actors_collection_dates}
			return jsonify(data)
	else:
		# What to do if there's multiple records for the same date?
		reports = ActorReport.query.filter_by(date=date)

		if reports.count()==0:
			data = {'code': '500', 'message': 'Internal Server Error', 'details': 'Sorry, no data for specific date.'}
			return jsonify(data)

		data = {}
		for report in reports:
			lines = report.csv_content.decode().split('\n')
			for line in lines:
				aux = line.split(';')
				try:
					if len(aux)>5 and actor.id == aux[0]:
						hour_data = {'date': date, 'username': aux[2], 'name': aux[1], 'followers_count': aux[3], 'tweets_count': aux[6], 'following_count': aux[4], 'likes_count': aux[5] }
						data[report.hour]=hour_data
				except:
					pass
		if data:
			data['code']= '200'
			data['message']='Success',
			return jsonify(data)

		data = {'code': '400', 'message': 'Bad Request', 'details': 'Sorry. No data for specific date.'}
		return jsonify(data)


@app.route('/api/actor/<username>/<date>/tweets')
def api_get_actor_account_date_tweets(username,date):

	actor = Actor.query.filter_by(username=username).first()
	if not actor:
		data = {'code': '400', 'message': 'Bad Request', 'details': 'Invalid username.'}
		return jsonify(data)

	data = {}
	report = TweetReport.query.filter_by(actor_id= actor.id).filter_by(date = date).first()

	if not report:
		data = {'code': '400', 'message': 'Bad Request', 'details': 'Sorry. No data for specific date.'}
		return jsonify(data)
	else:
		content = report.csv_content.decode()
		content = content.split('\n')
		data['tweets'] = []
		for line in content[1:]:
			try:
				aux_line = line.split(';')
				data['tweets'].append({'date': aux_line[0], 'text': aux_line[1], 'rt_author': aux_line[2], 'retweets': aux_line[3], 'likes': aux_line[4], 'hashtags': aux_line[5], 'mention':aux_line[6] })
			except:
				pass

		data['code'] = '200'
		data['message'] = 'Success'
		return jsonify(data)

@app.route('/api/relations')
def api_get_relations():
	data = {}
	available_dates = []
	relations = RelationReport.query.all()
	if not relations:
		data = {'code': '400', 'message': 'Bad Request', 'details': 'Sorry, no information was found.'}
		return jsonify(data)

	for relation in relations:
		available_dates.append(relation.date)

	data['dates'] = list(set(available_dates))
	data['code'] = '200'
	data['message'] = 'Success'
	return jsonify(data)

@app.route('/api/relations/<date>')
def api_get_relations_actor(date):
	data = {}

	relations = RelationReport.query.filter_by(date=date)
	if not relations.first():
		data = {'code': '400', 'message': 'Bad Request', 'details': 'Sorry, no information was found.'}
		return jsonify(data)

	for relation in relations:
		data[relation.hour]={}
		lines = relation.csv_content.decode().split('\n')
		for line in lines[1:]:
			aux_line = line.split(';')
			if len(aux_line)>2:
				data[relation.hour][aux_line[0]]=[]
		for line in lines[1:]:
			aux_line = line.split(';')
			if len(aux_line)>2:
				data[relation.hour][aux_line[0]].append({aux_line[1]:aux_line[2]})

	data['code'] = '200'
	data['message'] = 'Success'
	return jsonify(data)
