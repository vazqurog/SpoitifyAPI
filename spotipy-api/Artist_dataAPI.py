from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json
"""
These are some fuck ass custom functions I made from an indian tutorial
before realizing i can just use the spotify(py) API's
"""
# loads in the dotenv file with client id and secret
load_dotenv()

client_id = "98fdb15739b24fe59809623392d0bc75"
client_secret = "6925b16806fb4c5285e0ad8200ff6254"

def get_token():
    # Get the token from the 
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"

    }
    data = {"grant_type" : "client_credentials"} 
    result = post(url, headers=headers, data=data)
    print("Raw result content\n",result.content)

    # Debugging information
    """print("Status Code:", result.status_code)
    print("Response Content:", result.content)"""

    if result.status_code != 200:
        print("Failed to get token", result.status_code, result.text)
        token = None
    else:
        json_result = json.loads(result.content)
        print("Succesfullt loaded JSON content")
        token = json_result["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization" : "Bearer " + token}

def search_for_artist(token, artist_id):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={artist_id}&type=artist&limit=1"

    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["artists"]["items"]
    if len(json_result) == 0:
        print(f"No such artist exsist.")
        return None
    
    return json_result[0]

def get_songs_by_artist(token,artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["tracks"]
    return json_result

def get_album_by_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums?country=US"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["items"]
    return json_result



def get_artists_genres(token, artist_id):
    url = (f"https://api.spotify.com/v1/artists/{artist_id}")
    headers = get_auth_header(token)
    results = get(url, headers=headers)
    json_results = json.loads(results.content)['genres']
    genre_list = json_results
    
    return genre_list


token = get_token()

result = search_for_artist(token, "Los Originales Del Bajio")
artist_id = result["id"]
songs = get_songs_by_artist(token, artist_id)
albums = get_album_by_artist(token, artist_id)
genres = get_artists_genres(token, artist_id)
"""
print(f"\t{result['name']} Top 10 Songs\n")
for idx, song in enumerate(songs):
    print(f"{idx + 1}. {song['name']}")
print()

print(f"\t{result['name']} Albums\n")
for idx, album in enumerate(albums):
    print(f"{idx + 1}. {album['name']}")
print()

print(f"")
"""

