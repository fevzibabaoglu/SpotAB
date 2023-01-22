import atexit
import os
import time
from datetime import datetime

from spotify_client import SpotifyClient


def exit_handler(controller):
    controller.unmute()


def print_track_info(name, artists, release_year, is_local):
    prefix = ""
    if is_local:
        prefix = "LOCAL"
    else:
        prefix = release_year

    track_info = f"(at {datetime.now().strftime('%H:%M:%S')}) [{prefix}] {name} [by {artists}]"
    print(track_info)


def main():
    spotify = SpotifyClient()
    atexit.register(exit_handler, spotify.audio_controller)
    os.system('cls')

    track_info = None
    track_history = [None]
    ad = False

    while True:
        track_info = spotify.get_track()

        if track_info['status_code'] == 200:
            if track_info['currently_playing_type'] == 'track':
                if ad:
                    ad = False
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
                if not ad:
                    ad = True
                    spotify.toggle_mute()

            else:
                print(
                    f"(at {datetime.now().strftime('%H:%M:%S')}) "
                    f"[Type: {track_info['currently_playing_type']}] "
                    "Currently playing type is not acceptable. "
                    "Waiting 5 seconds."
                )
                time.sleep(4)

        else:
            print(
                f"(at {datetime.now().strftime('%H:%M:%S')}) "
                f"[c{track_info['status_code']}] "
                "Request is not OK. "
                "Waiting 5 seconds."
            )
            time.sleep(4)

        time.sleep(1)


if __name__ == '__main__':
    main()
