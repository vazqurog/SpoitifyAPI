from flask import Flask, redirect, session, url_for, request, render_template
import os
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import spotipy
from spotipy.cache_handler import FlaskSessionCacheHandler
from Artist_dataAPI import get_artists_genres, get_token
import time
from dotenv import load_dotenv
# Creating the app with flask
app = Flask(__name__)

# Generates a 64 byte access-key for security measures within the app
app.config['SECRET_KEY'] = os.urandom(64)
load_dotenv()

# Client ID pulled from the spotify dev dashboard.
#FIXME make .env file for all this shit  
client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
redirect_uri = 'http://127.0.0.1:5000/callback'
scope = 'user-library-read' # a scope whoich allows us to access data
cache_handler = FlaskSessionCacheHandler(session) # Creates the cache handler

# Authentication manager, uses params to authenticate with API
sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    cache_handler=cache_handler,
    show_dialog=True # Presents spotify log in page (debugging)
)

# instance of the Spotify API that lets us interact with WebAPI
sp = Spotify(auth_manager=sp_oauth) 
    
# Endpoint that that receives our playlist 
@app.route('/') # how to define a route for a flask web app

def home():
    # Checks if user is logged in
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url() # Creates URL to log in page
        return redirect(auth_url)
    return redirect(url_for('genre_scores_liked_songs')) # 

# Endpoint that refreshes the token when it expires. (redirect URI)
@app.route('/callback')
def callback():
    #FIXME Use get_cached token according to spotify api idgaf tbh fix it later
    sp_oauth.get_access_token(request.args['code'])
    return redirect(url_for('genre_scores_liked_songs'))
    
# Endpoint that returns the users playlist
@app.route('/get_playlists')
def get_playlists():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url() # Creates URL to log in page
        return redirect(auth_url)
    
    # Users top tracks also included in the scope 
    playlist = sp.current_user_playlists()
    playlist_info = [(pl['name'], pl['external_urls']['spotify']) for pl in playlist['items']]
    playlist_html = '<br>'.join([f'{name}: {url}' for name, url in playlist_info])

    return playlist_html
# Endpoint that returns top tracks
@app.route('/get_tracks')
def get_tracks():

    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url() # Creates URL to log in page
        return redirect(auth_url)

    tracks = sp.current_user_top_tracks(limit=5, time_range="short_term")
    track_info = [(idx, tr['name'], [artist['name'] for artist in tr['artists']]) for idx, tr in enumerate(tracks['items'])]

    # Formats the data we have on a html sheet
    # <br> is a line break, seperates each execution apart by a line
    track_html = '<br>'.join(f"{idx + 1}. {name}: {', '.join(artists)}" for idx, name, artists in track_info)
    
    
    return track_html
    #return track_html

# Endpoint for genre scores based off user short,medium or long term history. limit=50
@app.route('/genre_scores_top_tracls')
def genre_scores_top_tracks():

    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    
    tracks = sp.current_user_top_tracks(limit=50, time_range="short_term")
    genre_score = {}
    # loops through track and artists objects for artists ID to find genres
    for tr in tracks['items']:
        for art in tr['artists']:
            artists_id = art["id"]
            genres_list = get_artists_genres(get_token() ,artists_id)

            for genre in genres_list:

                if genre not in genre_score.keys():

                    if len(genres_list) <= 0: # Handles empty list
                        print(f"No genres available for {art['name']}")
                     
                    elif len(genres_list) == 1: # handles list with length of 1
                        genre_score[genres_list[0]] = 1
                    
                    else: # handles all other lists
                        genre_score[genre] = 1
             
                else:
                    genre_score[genre] += 1

    sorted_genre_scores = dict(sorted(genre_score.items(), key=lambda item: item[1], reverse=True))
    
    return sorted_genre_scores

@app.route('/genre_scores_liked_songs')
def genre_scores_liked_songs():
    start_time = time.time()
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    
    genre_score = {}
    offset = 0
    limit = 50
    temp = sp.current_user_saved_tracks()
    total_tracks = temp['total']
    
    # While loop to bypass the limit=50 the set by API.
    while offset <= total_tracks:
        offset += 50
        tracks = sp.current_user_saved_tracks(limit=limit, offset=offset)
        # loops through track and artists objects for artists ID to find genres
        for tr in tracks['items']:
            for art in tr['track']['artists']:
                artists_id = art["id"]
                genres_list = get_artists_genres(get_token() ,artists_id)
                for genre in genres_list:
                    if genre not in genre_score.keys():

                        if len(genres_list) <= 0: # Handles empty list
                            print(f"No genres available for {art['name']}")
                        
                        elif len(genres_list) == 1: # handles list with length of 1
                            genre_score[genres_list[0]] = 1
                        
                        else: # handles all other lists
                            genre_score[genre] = 1
                
                    else:
                        genre_score[genre] += 1

    end_time = time.time()
    total_time = abs(start_time - end_time)

    print(f"\nRUNTIME: {total_time:.2f} seconds\n")
    sorted_genre_scores = sort_genre_score(genre_score, 0)
    print(sorted_genre_scores)
    return sorted_genre_scores

def sort_genre_score(genres:dict, offset:int):
    sorted_dict = dict()
    for k, v in genres.items():
        if v > offset:
            sorted_dict[k] = v
    return sorted_dict

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)

