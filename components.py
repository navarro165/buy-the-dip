import queue
import threading

import exchanges as ex


class CurrentTrends:
    def __init__(self, currency, public_client=None, poll_frequency=None, run_event=None):
        self.thread = None
        self.run_event = run_event
        self.poll_frequency = poll_frequency  # in secs
        self.was_joined = False
        self.currency = currency
        self.out_queue = queue.Queue()
        self.public_client = public_client

    def __enter__(self):
        self.thread = threading.Thread(target=ex.Coinbase.get_trends,
                                       args=(self.currency, self.out_queue),
                                       kwargs={"poll_frequency": self.poll_frequency, "run_event": self.run_event})
        self.thread.daemon = True
        self.thread.start()
        return self

    def join(self):
        self.thread.join()
        self.was_joined = True
        return self.out_queue.get()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if not self.was_joined:
            try:
                self.thread.join()
            except Exception as e:
                raise RuntimeError(f"Current trends process failed. Message: {e}")
