import requests

from token_authorization import Auth
from volume import AudioController


class SpotifyClient:
    def __init__(self):
        self.auth = Auth()
        self.audio_controller = AudioController('Spotify.exe')

    def get_track(self):
        track_info = {
            'currently_playing_type': None,
            'name': None,
            'artists': None,
            'release_year': None,
            'is_local': None
        }
        response_info = {
            'status_code': None,
            'retry_after': None
        }
        api_info = {
            'track_info': track_info,
            'response_info': response_info
        }

        response = requests.get(
            url='https://api.spotify.com/v1/me/player/currently-playing',
            headers={
                'Authorization': f"Bearer {self.auth.token.access_token}"
            }
        )

        response_info['status_code'] = response.status_code

        if response.status_code in [429, 503]:
            try:
                response_info['retry_after'] = int(response.headers['Retry-After'])
            except KeyError:
                pass

        if response.status_code == 401:
            self.auth.refresh_access_token()
        elif response.status_code == 200:
            response_json = response.json()

            track_info['currently_playing_type'] = response_json['currently_playing_type']

            if response_json['currently_playing_type'] == 'track':
                track_info['is_local'] = response_json["item"]["is_local"]
                track_info['name'] = response_json['item']['name']

                artists = response_json["item"]["artists"]
                artists_names = ', '.join([artist['name'] for artist in artists])
                track_info['artists'] = artists_names

                if response_json["item"]["album"]["release_date_precision"] != None:
                    date = [None, None, None]  # YYYY, MM, DD format
                    release_date = response_json["item"]["album"]["release_date"].split('-')

                    for index, date_component in enumerate(release_date):
                        date[index] = date_component

                    track_info['release_year'] = date[0]

        return api_info

    def toggle_mute(self):
        self.audio_controller.toggle_mute()
