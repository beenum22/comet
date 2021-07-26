import logging

logger = logging.getLogger(__name__)


class ChangeLog(object):

    def __init__(self, type='keepachangelog'):
        self.type = type
