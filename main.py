import atexit
import os
import time
from datetime import datetime

from spotify_client import SpotifyClient

# sleep constants (in seconds)
SLEEP_BETWEEN_REQUESTS = 1
SLEEP_FOR_204 = 15
SLEEP_FOR_DEFAULT = 5


def exit_handler(controller):
    try:
        controller.unmute()
    except Exception:
        pass


def get_current_time():
    return datetime.now().strftime('%H:%M:%S')


def print_to_terminal(prefix, text, suffix):
    print(f"(at {get_current_time()}) [{prefix}] {text} [{suffix}]")


def print_track_info(name, artists, release_year, is_local):
    prefix = ""
    if is_local:
        prefix = "LOCAL"
    else:
        prefix = release_year

    print_to_terminal(
        prefix=prefix,
        text=name,
        suffix=f"by {artists}"
    )


def print_error_info(error_text, text, sleep_for):
    print_to_terminal(
        prefix=error_text,
        text=text,
        suffix=f"Waiting {sleep_for} seconds"
    )
    time.sleep(sleep_for - SLEEP_BETWEEN_REQUESTS)


def main():
    spotify = SpotifyClient()
    atexit.register(exit_handler, spotify.audio_controller)
    os.system('cls')

    track_info = None
    track_history = [None]
    last_played_was_ad = False

    while True:
        api_info = spotify.get_track()
        track_info = api_info['track_info']
        response_info = api_info['response_info']

        status_code = response_info['status_code']

        if status_code == 200:
            if track_info['currently_playing_type'] == 'track':
                if last_played_was_ad:
                    last_played_was_ad = False
                    spotify.toggle_mute()

                if track_info != track_history[-1]:
                    track_history.append(track_info)
                    print_track_info(
                        name=track_info['name'],
                        artists=track_info['artists'],
                        release_year=track_info['release_year'],
                        is_local=track_info['is_local']
                    )

            elif track_info['currently_playing_type'] == 'ad':
                if not last_played_was_ad:
                    last_played_was_ad = True
                    spotify.toggle_mute()

        elif status_code == 204:
            print_error_info(
                error_text=f"c{status_code}",
                text="No song info. Try playing a song on Spotify.",
                sleep_for=SLEEP_FOR_204
            )
        elif status_code in [429, 503]:
            retry_after = response_info['retry_after']

            if retry_after == None:
                retry_after = SLEEP_FOR_DEFAULT

            print_error_info(
                error_text=f"c{status_code}",
                text="Too Many Requests / Service Unavailable",
                sleep_for=retry_after
            )
        else:
            print_error_info(
                error_text=f"c{status_code}",
                text="Request is not OK.",
                sleep_for=SLEEP_FOR_DEFAULT
            )

        time.sleep(SLEEP_BETWEEN_REQUESTS)


if __name__ == '__main__':
    main()
