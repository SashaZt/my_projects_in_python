# shared_state.py
import asyncio
from queue import Queue


class SharedState:

    def __init__(self, db, api_key=None):
        self.db = db
        self.monitored_streams = {}  # {unique_id: task}
        self.gift_queue = Queue(maxsize=5000)
        self.processed_gift_ids = set()
        self.shutdown_event = asyncio.Event()

    def get_shutdown_event(self):
        return self.shutdown_event

    def get_monitored_streams(self):
        return self.monitored_streams
