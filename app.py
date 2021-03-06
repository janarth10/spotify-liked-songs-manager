import datetime
import json
import math
import requests

import spotipy
from spotipy.oauth2 import SpotifyOAuth


MY_USER_ID = "janarth.96"
SPOTIFY_CREDENTIALS_PATH = "/Users/newdev/Hive/Development/personal_projects/spotify-liked-songs-manager/configs/spotify_credentials.json"

TOP10_PLAYLISTS_BASE_NAME = 'TOP10_'
AUTH_REDIRECT_URI = 'http://127.0.0.1:9090'

# https://developer.spotify.com/documentation/general/guides/authorization/scopes/
SCOPES = [
	# Listening History scopes
	'user-top-read', # get TOP 50 tracks in last 4 months

	# Playlists scopes
	'playlist-modify-private',
	'playlist-read-private',
	'playlist-modify-public',
]


# --------------------------- Core features ------------------------------------

def discover_top10_weekly():
	"""
	Only able to fetch top X songs in last 4 weeks. solution

	1. 1st execution - save top 10 
	2. Subsequent executions
		fetch 50 (max) songs.
		remove songs from last 10 executions.
		if any left over, save to new playlist
	
	Use cron to run this weekly

	Not removing Liked Songs in this feature because I want to see what I'm listening to every week,
	including songs that I've already liked.

	Example response data 
	https://developer.spotify.com/documentation/web-api/reference/#/operations/get-users-top-artists-and-tracks
	"""

	CHUNK_SIZE = 50
	NUM_TOP_SONGS_TO_SAVE = 10
	DISCOVER_TIME_RANGE = 'short_term' # spotify returns top songs over 4 weeks, 6 months, or all time
	print('\n\nDISCOVER Top10 songs')

	# TOP10_Dec-26-2021
	top10_weekly_playlist_name = TOP10_PLAYLISTS_BASE_NAME + datetime.datetime.utcnow().astimezone().strftime('%b-%d-%Y')
	spotify_client = get_spotify_client()

	# get top 50 songs in last 4 weeks
	top50_resp_json = spotify_client.current_user_top_tracks(limit=CHUNK_SIZE, time_range=DISCOVER_TIME_RANGE)
	current_top50_track_uris_set = {x['uri'] for x in top50_resp_json['items']}

	# remove existing top10 songs
	for uri in get_uris_in_top10s_iterator():
		current_top50_track_uris_set = current_top50_track_uris_set - {uri}

	# if we have any new tracks in the top50, create a new top10 playlist for them
	if current_top50_track_uris_set:
		new_top10_playlist = spotify_client.user_playlist_create(
			user=MY_USER_ID,
			name=top10_weekly_playlist_name,
		)
		print(f"creating new playlist {new_top10_playlist['name']}")

		spotify_client.playlist_add_items(
			playlist_id=new_top10_playlist['id'],
			items=list(current_top50_track_uris_set)[:NUM_TOP_SONGS_TO_SAVE] 
		)
	print(f"DISCOVER Top10 added {len(list(current_top50_track_uris_set)[:NUM_TOP_SONGS_TO_SAVE])}")


def discover_recently_played():
	"""
		Intention - Discovering songs I forgot to save

		Everything returned by this api was listened to for >30seconds, so I
		PROBABLY liked it. 

		1. If it's in my liked songs, I probably queued it myself -> don't save it
		2. If it's in my TOP10 playlists, probably queued myself -> don't save it

		What's left?

		1. songs from Spotify's recommended
		2. listening to Spotify featured playlist
		3. Went looking for new songs
		4. Went looking for songs I USED to listen to

		all of which, I forgot to save after listening.

		Issue: can easily get cluttered, especially if I leave Spotify running 
		while I'm not around.
	"""

	MIN_PLAYLIST_SIZE = 7 # on avg 7 * 3m per song, at least a playlist of 21m
	FTS_BOT_PLAYLIST_ID = '5U55HdTVoOnEK9zls6Hnup' # ID for playlist FTS Bot - hope this id doesnt change
	print("\n\nDISCOVER recently played songs")

	last_50_recently_played_uris = set(get_50_recently_played_uris())

	# remove liked songs
	for uri in get_liked_songs_uris_iterator():
		last_50_recently_played_uris = last_50_recently_played_uris - {uri}

	# remove top10 songs
	for uri in get_uris_in_top10s_iterator():
		last_50_recently_played_uris = last_50_recently_played_uris - {uri}

	# don't save songs already in the playlist
	for uri in get_uris_for_playlist_iterator(playlist_id=FTS_BOT_PLAYLIST_ID):
		last_50_recently_played_uris = last_50_recently_played_uris - {uri}

	# create playlist if we've discovered enough songs
	if len(last_50_recently_played_uris) >= MIN_PLAYLIST_SIZE:
		spotify_client = get_spotify_client()
		spotify_client.playlist_add_items(
			playlist_id=FTS_BOT_PLAYLIST_ID,
			items=list(last_50_recently_played_uris)
		)
	print(f"DISCOVER Recently Played added {len(last_50_recently_played_uris)}")


def group_liked_songs_by_audio_features():
	"""
	group liked songs into playlists based on audio features.
	- [ ] learn how to visualize this data and find patterns
		- [ ] how to use python (numpy?) to do this
		- [ ] V1 can I find patterns just by looking?
		- [ ] V2 find patterns algorithmically with human assistance
		- [ ] V3 find patterns with 0 assistance? probably unnecssary
	- [ ] given patterns, group liked songs

	"""

	# VERY BASIC v1, to hit my deadline for v1 lol
	# collecting groups of songs with same speechiness up to 2 decimals, and the list is 
	#	over 7 songs
	CHUNK_SIZE = 50
	MIN_PLAYLIST_SIZE = 7 # on avg 7 * 3m per song, at least a playlist of 21m
	NUM_DECIMALS_TO_CHECK = 2 # collecting groups of songs with same speechiness up to 2 decimals

	print("\n\nDISCOVER Liked Songs Grouper")

	from collections import defaultdict
	feature_stats_aggregation = {
		# 'energy': defaultdict(list),
		# 'tempo': defaultdict(list),
		'speechiness': defaultdict(list),
		# 'instrumentalness': defaultdict(list),
		# 'liveness': defaultdict(list),
	}

	audio_features = []
	uris_chunk = []
	spotify_client = get_spotify_client()
	for uri in get_liked_songs_uris_iterator():
		uris_chunk.append(uri)
		if len(uris_chunk) == CHUNK_SIZE:
			audio_features.extend(spotify_client.audio_features(tracks=uris_chunk))
			uris_chunk = []

	if uris_chunk:
		audio_features.extend(spotify_client.audio_features(tracks=uris_chunk))

	for audio_feature in audio_features:
		for key, _ in feature_stats_aggregation.items():
			feature_stats_aggregation[key][round(audio_feature[key], NUM_DECIMALS_TO_CHECK)].append(audio_feature['uri'])

	for speech_level, uris in feature_stats_aggregation['speechiness'].items():
		if len(uris) >= MIN_PLAYLIST_SIZE:
			playlist = spotify_client.user_playlist_create(
				user=MY_USER_ID,
				name=f"{speech_level}_speechy",
			)
			print(f"creating new playlist {playlist['name']}")
			print(f"adding {len(uris)} songs!")

			spotify_client.playlist_add_items(
				playlist_id=playlist['id'],
				items=uris
			)


# --------------------------- helpers ------------------------------------------


def get_spotify_client():
	# https://spotipy.readthedocs.io/en/2.19.0/#spotipy.oauth2.SpotifyOAuth

	web_api_creds = None
	with open(SPOTIFY_CREDENTIALS_PATH) as f:
		web_api_creds = json.load(f)['web']

	spotify_client = spotipy.Spotify(auth_manager=SpotifyOAuth(
		scope=SCOPES,
		client_id=web_api_creds['client_id'],
		client_secret=web_api_creds['client_secret'],
		redirect_uri=AUTH_REDIRECT_URI,
		open_browser=True,
	))
	return spotify_client


def get_uris_for_playlist_iterator(playlist_id, limit=float('inf')):
	"""
	limit - only return first x songs

	https://spotipy.readthedocs.io/en/2.19.0/#spotipy.client.Spotify.playlist_items
	https://developer.spotify.com/documentation/web-api/reference/#/operations/get-playlists-tracks
	"""
	CHUNK_SIZE = 50

	spotify_client = get_spotify_client()
	num_total_songs_to_return = min(
		spotify_client.playlist_items(playlist_id=playlist_id, limit=1)['total'],
		limit,
	)
	counter = 0

	for i in range(math.ceil(num_total_songs_to_return / CHUNK_SIZE)):
		resp_json = spotify_client.playlist_items(
			playlist_id=playlist_id,
			limit=CHUNK_SIZE,
			offset=CHUNK_SIZE*i,
		)
		for track in resp_json['items']:
			yield track['track']['uri']
			counter += 1
			if counter == limit:
				break


def get_50_recently_played_uris():
	# https://spotipy.readthedocs.io/en/2.19.0/#spotipy.client.Spotify.current_user_recently_played
	# https://developer.spotify.com/documentation/web-api/reference/#/operations/get-recently-played

	spotify_client = get_spotify_client()
	resp_json = spotify_client.current_user_recently_played(
		limit=50,
	)
	return [
		track['track']['uri']
		for track in resp_json['items']
	]

def get_liked_songs_uris_iterator():
	# https://spotipy.readthedocs.io/en/2.19.0/?highlight=top#spotipy.client.Spotify.current_user_saved_tracks
	# https://developer.spotify.com/documentation/web-api/reference/#/operations/get-users-saved-tracks

	CHUNK_SIZE = 50

	spotify_client = get_spotify_client()
	num_liked_songs = spotify_client.current_user_saved_tracks(limit=1)['total']
	for i in range(math.ceil(num_liked_songs / CHUNK_SIZE)):
		resp_json = spotify_client.current_user_saved_tracks(
			limit=CHUNK_SIZE,
			offset=CHUNK_SIZE*i,
		)
		for track in resp_json['items']:
			yield track['track']['uri']

def get_uris_in_top10s_iterator():
	# https://spotipy.readthedocs.io/en/2.19.0/#spotipy.client.Spotify.current_user_playlists
	# https://developer.spotify.com/documentation/web-api/reference/#/operations/get-a-list-of-current-users-playlists

	spotify_client = get_spotify_client()
	all_playlists_resp_json = spotify_client.current_user_playlists()
	top10_playlist_ids = [
		playlist['id'] for playlist in 
		all_playlists_resp_json['items'] 
		if playlist['name'][:len(TOP10_PLAYLISTS_BASE_NAME)] == TOP10_PLAYLISTS_BASE_NAME
	]

	# only look at last 10 playlists if we have more than 10 TOP10_s
	for playlist_id in top10_playlist_ids:
		for uri in get_uris_for_playlist_iterator(playlist_id=playlist_id):
			yield uri

def get_playlist_id_by_name(playlist_name):
	spotify_client = get_spotify_client()
	## JPTODO i have over 50 playlists, need an iterator to return everythin
	all_playlists_resp_json = spotify_client.current_user_playlists()
	playlist_ids = [
		playlist['id'] for playlist in 
		all_playlists_resp_json['items'] 
		if playlist['name'] == playlist_name
	]
	if playlist_ids:
		return playlist_ids[0]


# ------------ Main Code - running weekly on a cron ----------------------------

discover_top10_weekly()
discover_recently_played()
# group_liked_songs_by_audio_features()

