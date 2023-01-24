import base64
import hashlib
import secrets
import requests
import urllib.parse
import webbrowser
import json
import os


class Token:
    def __init__(self):
        self.client_id = None
        self.refresh_token = None
        self.access_token = None
        self.file_path = ".cache"

        if not self.load_from_file():
            self.client_id = str(input("Type your 'client_id': "))

    def load_from_file(self):
        try:
            with open(self.file_path) as f:
                cache = json.load(f)
                self.client_id = cache['client_id']
                self.refresh_token = cache['refresh_token']
        except OSError as e:
            print(f"Error: {self.file_path} - {e.strerror}")
            return False
        else:
            return True

    def save_to_file(self):
        cache = {
            'client_id': self.client_id,
            'refresh_token': self.refresh_token
        }

        with open(self.file_path, 'w') as f:
            f.write(json.dumps(cache, indent=4, sort_keys=True))

    def delete_file(self):
        try:
            print(f"Existing '{self.file_path}' is deleted..")
            os.remove(self.file_path)
        except OSError as e:
            print(f"Error: {self.file_path} - {e.strerror}")
            return False
        else:
            return True


class Auth:
    def __init__(self):
        self.token = Token()

        if self.token.refresh_token == None:
            self.first_auth()
        elif self.token.access_token == None:
            self.refresh_access_token()

    def first_auth(self):
        # common parameters
        redirect_uri = 'http://localhost:8888/callback/'
        code_verifier = secrets.token_urlsafe(48)  # 64-character long random string
        code_challenge_byte = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge_byte).rstrip(b'=').decode('ascii')

        # getting the 'authorization_code'
        scope = 'user-read-currently-playing'
        state = secrets.token_urlsafe(12)  # 16-character long random string

        auth_url = 'https://accounts.spotify.com/authorize'
        auth_query = {
            'client_id': self.token.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'state': state,
            'scope': scope,
            'code_challenge_method': 'S256',
            'code_challenge': code_challenge
        }
        urlencoded_auth_query = urllib.parse.urlencode(auth_query)
        full_auth_url = f"{auth_url}?{urlencoded_auth_query}"

        webbrowser.open_new(full_auth_url)
        redirected_url = str(input("Enter the URL you were redirected to after authentication: "))
        redirected_url_components = urllib.parse.urlparse(redirected_url)
        redirected_url_query = urllib.parse.parse_qs(redirected_url_components.query)

        try:
            redirect_state = redirected_url_query['state'][0]
        except KeyError:
            raise SystemError("Wrong redirected url.")

        if state != redirect_state:
            raise SystemExit("The original 'state' parameter and the redirected 'state' parameter do not match!")

        try:
            authorization_code = redirected_url_query['code'][0]
        except KeyError:
            auth_error = redirected_url_query['error'][0]
            raise SystemExit(f"An error occurred while authenticating: {auth_error}")

        # getting 'access_token' and 'refresh_token'
        response = requests.post(
            url='https://accounts.spotify.com/api/token',
            params={
                'grant_type': 'authorization_code',
                'code': authorization_code,
                'redirect_uri': redirect_uri,
                'client_id': self.token.client_id,
                'code_verifier': code_verifier
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )

        if response.status_code != 200:
            request_error = response.text
            raise SystemExit("An error occurred while requesting access token: "
                             f"HTTP Status Code {response.status_code}"
                             f"\n{request_error}")

        response_json = response.json()
        self.token.access_token = response_json['access_token']
        self.token.refresh_token = response_json['refresh_token']
        self.token.save_to_file()

    def refresh_access_token(self):
        response = requests.post(
            url='https://accounts.spotify.com/api/token',
            params={
                'grant_type': 'refresh_token',
                'refresh_token': self.token.refresh_token,
                'client_id': self.token.client_id
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )

        if response.status_code != 200:
            request_error = response.text
            print("An error occurred while requesting a refreshed access token: "
                  f"HTTP Status Code {response.status_code}"
                  f"\n{request_error}")

            if response.status_code == 400:
                request_error_json = response.json()

                if request_error_json['error_description'] == "Refresh token revoked" and self.token.delete_file():
                    self.first_auth()
                else:
                    raise SystemExit
        else:
            response_json = response.json()
            self.token.access_token = response_json['access_token']

            try:
                self.token.refresh_token = response_json['refresh_token']
                self.token.save_to_file()
            except KeyError:
                pass
