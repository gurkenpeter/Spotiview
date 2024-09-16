from flask import Flask, redirect, request, session, render_template, url_for, jsonify
import requests
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

# Spotify API Konfiguration
SPOTIFY_CLIENT_ID = 'ee79aef75d23416dbcfadae448a4d4c7'
SPOTIFY_CLIENT_SECRET = 'fc0883b75d9c44b8bda50fc6daa2b375'
SPOTIFY_REDIRECT_URI = 'http://localhost:5000/callback'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_API_BASE_URL = 'https://api.spotify.com/v1'

def get_spotify_auth_url():
    """Generiert die URL für die Spotify Authentifizierung."""
    scopes = 'user-read-currently-playing'
    auth_url = f"{SPOTIFY_AUTH_URL}?response_type=code&client_id={SPOTIFY_CLIENT_ID}&scope={scopes}&redirect_uri={SPOTIFY_REDIRECT_URI}"
    return auth_url


print("Spotify URL wird geladen - API wird vorbereitet")


def get_spotify_access_token(auth_code):
    """Holt ein Access Token von Spotify."""
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    }
    
    response = requests.post(SPOTIFY_TOKEN_URL, data=data)
    if response.status_code == 200:
        print("Spotify-JSON-Daten abgerufen")
        return response.json()
        
    else:
        print("Fehler beim Abrufen des Access Tokens:", response.json())
        return None

def refresh_spotify_access_token(refresh_token):
    """Erneuert das Access Token von Spotify."""
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    }
    
    response = requests.post(SPOTIFY_TOKEN_URL, data=data)
    if response.status_code == 200:
        return response.json()
    else:
        print("Fehler beim Erneuern des Access Tokens:", response.json())
        return None

def get_current_track(access_token):
    """Holt die aktuellen Musikinformationen von der Spotify API."""
    url = f"{SPOTIFY_API_BASE_URL}/me/player/currently-playing"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(url, headers=headers)
    print("Spotify API Response Status Code:", response.status_code)
    if response.status_code == 200:
        data = response.json()
        print("Spotify API Response JSON:", data)  # Debugging-Ausgabe
        if data.get('is_playing'):
            track_name = data['item']['name']
            artist_name = ', '.join([artist['name'] for artist in data['item']['artists']])
            album_cover_url = data['item']['album']['images'][0]['url']
            return track_name, artist_name, album_cover_url
        else:
            print("Es wird gerade keine Musik abgespielt.")
            return None, None, None
    else:
        print("Fehler beim Abrufen des aktuellen Titels:", response.json())
        return None, None, None

@app.route('/')
def index():
    """Startseite, die den aktuellen Track anzeigt oder zur Spotify Authentifizierung weiterleitet."""
    if 'access_token' in session:
        access_token = session['access_token']
        track_name, artist_name, album_cover_url = get_current_track(access_token)
        if track_name and artist_name:
            return render_template('index.html', track_name=track_name, artist_name=artist_name, album_cover_url=album_cover_url)
        else:
            return "Keine Musik wird aktuell abgespielt oder das Access Token ist abgelaufen. Bitte <a href='/login'>erneut anmelden</a>."
    else:
        return redirect(url_for('login'))

@app.route('/login')
def login():
    """Weiterleitung zur Spotify Authentifizierungsseite."""
    auth_url = get_spotify_auth_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    """Callback-Route für die Spotify Authentifizierung."""
    auth_code = request.args.get('code')
    token_info = get_spotify_access_token(auth_code)
    if token_info:
        session['access_token'] = token_info['access_token']    
        session['refresh_token'] = token_info['refresh_token']
        return redirect(url_for('index'))
    else:
        return "Fehler beim Abrufen des Spotify Access Tokens."

@app.route('/track_info')
def track_info():
    """Gibt die aktuellen Track-Informationen als JSON zurück."""
    if 'access_token' in session:
        access_token = session['access_token']
        track_name, artist_name, album_cover_url = get_current_track(access_token)
        return jsonify({
            'track_name': track_name,
            'artist_name': artist_name,
            'album_cover_url': album_cover_url
        })
    else:
        return jsonify({
            'track_name': None,
            'artist_name': None,
            'album_cover_url': None
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=false)

