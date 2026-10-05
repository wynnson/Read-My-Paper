class ReadMyPaperError(Exception):
    """Base class for user-facing application errors."""


class InvalidPaperId(ReadMyPaperError):
    pass


class PaperNotFound(ReadMyPaperError):
    pass


class PaperAlreadyExists(ReadMyPaperError):
    pass


class InvalidManifest(ReadMyPaperError):
    pass


class InvalidVoiceId(ReadMyPaperError):
    pass


class VoiceNotFound(ReadMyPaperError):
    pass


class VoiceAlreadyExists(ReadMyPaperError):
    pass


class PlaybackFailed(ReadMyPaperError):
    pass
