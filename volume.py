from pycaw.utils import AudioUtilities


class AudioController:
    def __init__(self, process_name):
        self.process_name = process_name
        self.unmute()
        self.muted = False

    def mute(self):
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            interface = session.SimpleAudioVolume
            if session.Process and session.Process.name() == self.process_name:
                interface.SetMute(1, None)

    def unmute(self):
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            interface = session.SimpleAudioVolume
            if session.Process and session.Process.name() == self.process_name:
                interface.SetMute(0, None)

    def toggle_mute(self):
        if self.muted:
            self.muted = False
            self.unmute()
        else:
            self.muted = True
            self.mute()
