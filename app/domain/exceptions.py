class MeetingError(Exception):
    pass


class InvalidMeetingDurationError(MeetingError):
    pass


class MeetingNotFoundError(MeetingError):
    pass


class EmptyMeetingNameError(MeetingError):
    pass


class InvalidFilenameError(MeetingError):
    pass
