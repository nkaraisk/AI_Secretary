FRAME_MS = 20 # Gives update() a precise contract: one call represents 20 milliseconds of audio.
START_MS = 60 # Three consecutive active frames start a turn. A single 20 ms click, or even two active frames followed by quiet, won’t start one.
END_MS = 600 # Gives the caller longer to pause between words.


class SpeechTurnDetector: # One detector will belong to one call.
    def __init__(self) -> None:
        self.speaking = False # Remembers the previous decision.
        # Measure consecutive time.
        self.active_ms = 0 # A quiet frame resets the active counter.
        self.quiet_ms = 0 # An active frame resets the quiet counter.

    def update(self, active: bool) -> str | None:
        if active:
            self.quiet_ms = 0
            self.active_ms += FRAME_MS

            if not self.speaking and self.active_ms >= START_MS:
                self.speaking = True
                return "speech_start"
        else:
            self.active_ms = 0
            self.quiet_ms += FRAME_MS

            if self.speaking and self.quiet_ms >= END_MS:
                self.speaking = False
                return "speech_end"

        return None