import datetime
import json
import requests

import spotipy
from spotipy.oauth2 import SpotifyOAuth


MY_USER_ID = "janarth.96"
SPOTIFY_CREDENTIALS_PATH = "/Users/newdev/Hive/Development/personal_projects/spotify-liked-songs-manager/configs/spotify_credentials.json"

SCOPES = [
	# Listening History scopes
	'user-top-read', # get TOP 50 tracks in last 4 months

	# Playlists scopes
	'playlist-modify-private',
	'playlist-read-private',
	'playlist-modify-public',
]

def get_spotify_client():
	# https://developer.spotify.com/documentation/general/guides/authorization/scopes/
	web_api_creds = None
	with open(SPOTIFY_CREDENTIALS_PATH) as f:
		web_api_creds = json.load(f)['web']

	spotify_client = spotipy.Spotify(auth_manager=SpotifyOAuth(
		scope=SCOPES,
		client_id=web_api_creds['client_id'],
		client_secret=web_api_creds['client_secret'],
		redirect_uri='http://127.0.0.1:9090',
		open_browser=True,
	))
	return spotify_client


def get_liked_songs():
	# https://spotipy.readthedocs.io/en/2.19.0/?highlight=top#spotipy.client.Spotify.current_user_saved_tracks
	pass

def save_top10_weekly():
	"""
	Only able to fetch top X songs in last 4 weeks. solution

	1. 1st execution - save top 10 
	2. Subsequent executions
		fetch 50 (max) songs.
		remove songs from last 10 executions.
		if any left over, save to new playlist
	
	Use cron to run this weekly
	"""

	PLAYLIST_NAME_BASE = 'TOP10_'
	# TOP10_Dec-26-2021
	# TODO - this is wrong timezone
	top10_weekly_playlist_name = PLAYLIST_NAME_BASE + datetime.datetime.utcnow().astimezone().strftime('%b-%d-%Y')

	spotify_client = get_spotify_client()
	top50_resp_json = spotify_client.current_user_top_tracks(limit=50, time_range='short_term')
	current_top50_track_uris_set = {x['uri'] for x in top50_resp_json['items']}
	print('\n\n')
	print(f"found {len(current_top50_track_uris_set)} top50s")

	all_playlists_resp_json = spotify_client.current_user_playlists()
	top10_playlist_ids = [
		playlist['id'] for playlist in 
		all_playlists_resp_json['items'] 
		if playlist['name'][:len(PLAYLIST_NAME_BASE)] == PLAYLIST_NAME_BASE
	]

	# only look at last 10 playlists if we have more than 10 TOP10_s
	for playlist_id in top10_playlist_ids[:10]:
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
			items=list(current_top50_track_uris_set)[:10] 
		)
		print(f"Spotify cron added {len(list(current_top50_track_uris_set)[:10])}")



# ------------ Main Code - running weekly on a cron ----------------------------
save_top10_weekly()