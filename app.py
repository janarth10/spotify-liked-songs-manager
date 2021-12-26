import requests
import datetime


user_id = "janarth.96"
base_url = "https://api.spotify.com/v1/"
# url = f"https://api.spotify.com/v1/users/me/playlists"
access_token = "BQCr5tLF5qcST16T9zNxTfQ7kWNgZTh9QGMGt5rxa2y2cwS2UKAOwZ4ffJ6SAgW56NcvDWXXgg-YiJNmnhFaswVjadRKkGjPtqwcLK8rLuki1VxgyvJGsi3LzvIGftzHr1jEAIaQJhDpNzgPeqzT-0W63Sz25FoHguwa23_E1FR016ScQL_Iuco4dajjum6wNRiEFwgb8pBreQZz1w9un5Wl_LMQgRo"

def spotify_get_request(endpoint, params={}):
	resp = requests.get(
		base_url+endpoint,
		headers={"Authorization": f"Bearer {access_token}" },
		params=params
	)
	if not resp.ok:
		raise(Exception(resp.text))

	return resp.json()

def spotify_post_request(endpoint, request_json={}):
	resp = requests.post(
		base_url+endpoint,
		headers={"Authorization": f"Bearer {access_token}" },
		json=request_json
	)
	if not resp.ok:
		raise(Exception(resp.text))

	return resp.json()


def save_top_10_weekly():
	"""
	Only able to fetch top X songs in last 4 weeks. solution

	1. 1st execution - save top 10 
	2. Subsequent executions
		fetch 50 (max) songs.
		remove songs from last 10 executions.
		if any left over, save to new playlist
	
	Use cron to run this weekly

	todos
	- need to get access_token everytime this fn runs, with permissions to create, read, users_top
	- add cron to correct folder on Macbook
	- create first playlist manually
	- run script to make sure 2nd week playlist doesn't have any from first

	"""

	PLAYLIST_NAME_BASE = 'TOP10_'
	USERS_TOP_API = 'me/top/tracks'
	# TOP10_Dec-26-2021
	# TODO - this is wrong timezone
	top_10_weekly_playlist_name = PLAYLIST_NAME_BASE + datetime.datetime.utcnow().astimezone().strftime('%b-%d-%Y')

	# TODO - get new token

	resp_json = spotify_get_request(
		endpoint=USERS_TOP_API,
		params={'limit': 50, 'time_range': 'short_term'}
	)
	track_uris = [x['uri'] for x in resp_json['items']]

	print(track_uris)

	# find previous top10s and filter out by URIs
	
	# resp_json = spotify_get_request(f"users/{user_id}/playlists")

	# filter for playlist w names starting with 'TOP10_'
	# only look at last 10 playlists if we have more than 10 TOP10_s
	# playlist['tracks'] = {'href': 'https://api.spotify.com/v1/playlists/4a0Ev1qmduIWdcHmtKfPlX/tracks', 'total': 2}
	# if total > 1 -> request url and get `old_track_uris`. Do a set difference

	# with leftover tracks in `track_uris`
	# 1. create new playlist -> save ID
	# 2. spotify_post_request(f"playlists/{new_playlist_id}/tracks", {'uris': track_uris})

save_top_10_weekly()