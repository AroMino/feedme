import time
import threading
import os
from src.pipeline import run as run_pipeline
from src.utils.llm import RateLimitError

class RSSScheduler:
    def __init__(self, interval_seconds=600):
        self.interval = interval_seconds
        self.thread = None
        self.stop_event = threading.Event()

    def _worker(self):
        print(f"🚀 [Scheduler] Background worker started. Interval: {self.interval}s")
        
        # Initial wait to let the server start up fully
        time.sleep(10)
        
        while not self.stop_event.is_set():
            try:
                run_pipeline()
                print(f"⏰ [Scheduler] Pipeline run complete. Sleeping for {self.interval}s...")
            except RateLimitError as e:
                print(f"🛑 [Scheduler] QUOTA REACHED: {e}")
                print(f"⏰ [Scheduler] Run aborted. Waiting {self.interval}s for next attempt...")
            except Exception as e:
                print(f"❌ [Scheduler] Error during pipeline run: {e}")
            
            # Wait for interval or stop event
            self.stop_event.wait(self.interval)

    def start(self):
        if self.thread is not None:
            return
        
        # Guard against double-start in Flask debug mode
        if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
            return

        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join()

# Singleton instance
scheduler = RSSScheduler()
