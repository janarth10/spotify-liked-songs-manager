import requests


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


uris_to_copy = ['spotify:track:0NeBH6OPQMBJMcmhRoCUmv', 'spotify:track:294pxweq9pggAO32OQVgYw']
# new_playlist_name = 'robot_playlist'
# create_playlist_resp = spotify_post_request(f"users/{user_id}/playlists", {'name': new_playlist_name})


resp_json = spotify_get_request(f"users/{user_id}/playlists")
playlist_names = [(x['id'], x['name']) for x in resp_json['items']]
import pdb; pdb.set_trace()
print(playlist_names)


spotify_post_request(f"playlists/{new_playlist_id}/tracks", {'uris': track_uris})