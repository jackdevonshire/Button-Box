"""
In-process event bus and activity log.

Anything interesting that happens (button presses, actions running, errors, the box going on/offline) is published
here. Subscribers - the live event stream the web UI listens to - get every event immediately, and events marked for
the activity log are saved to the database by a background writer, so publishing never blocks the caller.
"""
import datetime
import json
import queue
import threading

MAX_ACTIVITY_ROWS = 2000
SUBSCRIBER_QUEUE_SIZE = 500


class EventBus:
    def __init__(self):
        self.__subscribers = set()
        self.__lock = threading.Lock()
        self.__activity_queue = queue.Queue()
        self.__app = None
        self.__db = None

    def start(self, app, db):
        # Import here, on the main thread - importing in the writer thread races the app's own imports
        from app.core.models import ActivityEntry

        self.__app = app
        self.__db = db
        threading.Thread(target=self.__activity_writer, args=(ActivityEntry,), name="activity-writer",
                         daemon=True).start()

    def subscribe(self):
        subscriber = queue.Queue(maxsize=SUBSCRIBER_QUEUE_SIZE)
        with self.__lock:
            self.__subscribers.add(subscriber)
        return subscriber

    def unsubscribe(self, subscriber):
        with self.__lock:
            self.__subscribers.discard(subscriber)

    def publish(self, event_type, data=None):
        message = {"type": event_type, "timestamp": datetime.datetime.now().isoformat(), "data": data or {}}
        with self.__lock:
            subscribers = list(self.__subscribers)
        for subscriber in subscribers:
            try:
                subscriber.put_nowait(message)
            except queue.Full:
                pass  # A stalled client - drop events rather than block the box

    def log(self, kind, title, detail=None, control=None, event=None):
        """Records an entry in the activity log and publishes it to live subscribers"""
        entry = {"kind": kind, "title": title, "detail": detail, "control": control, "event": event,
                 "timestamp": datetime.datetime.now()}
        print(f"[{kind}] {title}" + (f" - {detail}" if detail else ""))
        self.__activity_queue.put(entry)

    def __activity_writer(self, ActivityEntry):
        writes_since_prune = 0
        while True:
            entry = self.__activity_queue.get()
            try:
                with self.__app.app_context():
                    row = ActivityEntry(**entry)
                    self.__db.session.add(row)
                    self.__db.session.commit()
                    self.publish("activity", row.to_json())

                    writes_since_prune += 1
                    if writes_since_prune >= 100:
                        writes_since_prune = 0
                        self.__prune(ActivityEntry)
            except Exception as e:
                print(f"Activity Log - Failed to save entry: {e}")

    def __prune(self, ActivityEntry):
        cutoff = ActivityEntry.query.order_by(ActivityEntry.id.desc()).offset(MAX_ACTIVITY_ROWS).first()
        if cutoff:
            ActivityEntry.query.filter(ActivityEntry.id <= cutoff.id).delete()
            self.__db.session.commit()


def format_sse(message):
    return f"event: {message['type']}\ndata: {json.dumps(message)}\n\n"


event_bus = EventBus()
