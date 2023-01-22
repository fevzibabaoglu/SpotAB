import base64
import urllib.parse
import requests
import webbrowser
import json


class Token:
    def __init__(self):
        self.client_id = None
        self.client_secret = None
        self.base64 = None
        self.refresh_token = None
        self.access_token = None

        if not self.load_from_file():
            self.get_ids()
            self.base64 = self.authorization_base64_encoder()

    def get_ids(self):
        self.client_id = str(input("Type your 'client_id': "))
        self.client_secret = str(input("Type your 'client_secret': "))

    def authorization_base64_encoder(self):
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_string_bytes = auth_string.encode("ascii")
        base64_bytes = base64.b64encode(auth_string_bytes)
        base64_string = base64_bytes.decode("ascii")
        return base64_string

    def load_from_file(self):
        file_path = f".cache"

        try:
            with open(file_path) as f:
                cache = json.load(f)
                self.refresh_token = cache['refresh_token']
                self.base64 = cache['base64']
        except FileNotFoundError:
            return False
        else:
            return True

    def save_to_file(self):
        file_path = f".cache"
        cache = {
            'refresh_token': self.refresh_token,
            'base64': self.base64
        }

        with open(file_path, 'w') as f:
            f.write(json.dumps(cache, indent=4, sort_keys=True))


class Auth:
    def __init__(self):
        self.token = Token()

        if self.token.refresh_token == None:
            self.first_auth()
        elif self.token.access_token == None:
            self.refresh_access_token()

    def first_auth(self):
        redirect_uri = 'http://localhost:8888/callback/'
        scope = 'user-read-currently-playing'

        # getting the authorization_code
        url = 'https://accounts.spotify.com/authorize'
        query = {
            'client_id': self.token.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': scope
        }
        urlencoded_query = urllib.parse.urlencode(query)

        full_url = f"{url}?{urlencoded_query}"
        webbrowser.open_new(full_url)

        redirected_url = str(input("Enter the URL you were redirected to: "))
        redirected_url_components = urllib.parse.urlparse(redirected_url)
        redirected_url_query = urllib.parse.parse_qs(redirected_url_components.query)
        code = ''.join(redirected_url_query['code'])

        # getting the tokens
        response = requests.post(
            url='https://accounts.spotify.com/api/token',
            params={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri
            },
            headers={
                'Authorization': f"Basic {self.token.base64}",
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )

        response_json = response.json()
        self.token.access_token = response_json['access_token']
        self.token.refresh_token = response_json['refresh_token']
        self.token.save_to_file()

    def refresh_access_token(self):
        response = requests.post(
            url='https://accounts.spotify.com/api/token',
            params={
                'grant_type': 'refresh_token',
                'refresh_token': self.token.refresh_token
            },
            headers={
                'Authorization': f"Basic {self.token.base64}",
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )

        response_json = response.json()
        self.token.access_token = response_json['access_token']
