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

	Example response data 
	https://developer.spotify.com/documentation/web-api/reference/#/operations/get-users-top-artists-and-tracks
	"""

	CHUNK_SIZE = 50
	NUM_TOP_SONGS_TO_SAVE = 10
	DISCOVER_TIME_RANGE = 'short_term' # spotify returns top songs over 4 weeks, 6 months, or all time
	print('\n\n DISCOVER top10 songs')

	# TOP10_Dec-26-2021
	top10_weekly_playlist_name = TOP10_PLAYLISTS_BASE_NAME + datetime.datetime.utcnow().astimezone().strftime('%b-%d-%Y')
	spotify_client = get_spotify_client()

	# get top 50 songs in last 4 weeks
	top50_resp_json = spotify_client.current_user_top_tracks(limit=CHUNK_SIZE, time_range=DISCOVER_TIME_RANGE)
	current_top50_track_uris_set = {x['uri'] for x in top50_resp_json['items']}

	# get existing top10 playlists so we don't save same songs
	all_playlists_resp_json = spotify_client.current_user_playlists()
	top10_playlist_ids = [
		playlist['id'] for playlist in 
		all_playlists_resp_json['items'] 
		if playlist['name'][:len(TOP10_PLAYLISTS_BASE_NAME)] == TOP10_PLAYLISTS_BASE_NAME
	]

	for playlist_id in top10_playlist_ids:
		playlist_tracks_uri_set = {
			track['track']['uri'] for track in 
			spotify_client.playlist_items(
				playlist_id=playlist_id, 
				fields='items.track.uri'
			)['items']
		}
		current_top50_track_uris_set = current_top50_track_uris_set - playlist_tracks_uri_set

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
		print(f"Spotify cron added {len(list(current_top50_track_uris_set)[:NUM_TOP_SONGS_TO_SAVE])}")


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
	PLAYLIST_ID = '5U55HdTVoOnEK9zls6Hnup' # ID for playlist FTS Bot - hope this id doesnt change
	print("\n\nDISCOVER recently played songs")

	last_50_recently_played_uris = set(get_50_recently_played_uris())

	# remove liked songs
	for uri in get_liked_songs_uris_iterator():
		last_50_recently_played_uris = last_50_recently_played_uris - {uri}

	# remove top10 songs
	for uri in get_uris_in_top10s_iterator():
		last_50_recently_played_uris = last_50_recently_played_uris - {uri}


	# create playlist if we've discovered enough songs
	if len(last_50_recently_played_uris) > MIN_PLAYLIST_SIZE:
		spotify_client = get_spotify_client()
		spotify_client.playlist_add_items(
			playlist_id=PLAYLIST_ID,
			items=list(last_50_recently_played_uris)
		)
		print(f"Spotify cron added {len(last_50_recently_played_uris)}")


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
	pass




# --------------------------- helpers ------------------------------------------


def get_spotify_client():
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


def get_50_recently_played_uris():
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
	spotify_client = get_spotify_client()
	all_playlists_resp_json = spotify_client.current_user_playlists()
	top10_playlist_ids = [
		playlist['id'] for playlist in 
		all_playlists_resp_json['items'] 
		if playlist['name'][:len(TOP10_PLAYLISTS_BASE_NAME)] == TOP10_PLAYLISTS_BASE_NAME
	]

	# only look at last 10 playlists if we have more than 10 TOP10_s
	for playlist_id in top10_playlist_ids:
		for track in spotify_client.playlist_items(
			playlist_id=playlist_id, 
			fields='items.track.uri'
		)['items']:
			yield track['track']['uri']


# ------------ Main Code - running weekly on a cron ----------------------------

discover_top10_weekly()
discover_recently_played()