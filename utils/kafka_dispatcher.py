import importlib
import json
import asyncio
import threading
from pathlib import Path

from confluent_kafka import Consumer, TopicPartition, OFFSET_END
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import utils.routing_roles as routing_roles


class Worker:
    pass


class KafkaDispatcher:
    def __init__(self, kafka_host: str, worker: Worker, config_path: str, group_id: str):
        self.kafka_host = kafka_host
        self.worker = worker
        self.group_id = group_id
        self.config_path = config_path
        self.consumer = None
        self.current_topics = set()

        # Initialize consumer and subscribe
        self._load_config_and_subscribe()

        # Start file watcher in a thread
        self._start_watcher()


    def _load_config_and_subscribe(self):
        importlib.reload(routing_roles)
        new_topics = {str(c["channel_id"]) for c in routing_roles.config}
        if new_topics != self.current_topics:
            self.current_topics = new_topics
            if self.consumer:
                self.consumer.unsubscribe()
                print("🔄 Unsubscribed from old topics")

            self.consumer = Consumer({
                'bootstrap.servers': self.kafka_host,
                'group.id': self.group_id,
                'auto.offset.reset': 'latest'
            })
            self.consumer.subscribe(list(self.current_topics))
            print(f"✅ Subscribed to topics: {self.current_topics}")

            # Wait for partition assignment and then seek to end
            self._seek_to_end_on_assignment()

    def _seek_to_end_on_assignment(self):
        # Poll once to trigger assignment
        self.consumer.poll(0)

        # Get assigned partitions
        partitions = self.consumer.assignment()
        if not partitions:
            print("⚠️ No partitions assigned yet, polling to get assignment...")
            # Poll until partitions assigned (with timeout to avoid infinite loop)
            for _ in range(10):
                self.consumer.poll(1)
                partitions = self.consumer.assignment()
                if partitions:
                    break

        if partitions:
            # Seek to end on all assigned partitions
            for p in partitions:
                self.consumer.seek(TopicPartition(p.topic, p.partition, OFFSET_END))
            print("➡️ Consumer seeked to end of all assigned partitions")
        else:
            print("❌ Could not get partition assignment to seek to end")

    def _start_watcher(self):
        class ReloadHandler(FileSystemEventHandler):
            def __init__(self, dispatcher):
                self.dispatcher = dispatcher

            def on_modified(self, event):
                if Path(event.src_path).name == "routing_roules.py":
                    print("🔁 Detected change in routing_roules.py. Reloading...")
                    self.dispatcher._load_config_and_subscribe()

        observer = Observer()
        handler = ReloadHandler(self)
        observer.schedule(handler, path=str(Path(self.config_path).parent), recursive=False)
        threading.Thread(target=observer.start, daemon=True).start()

    async def run(self):
        while True:
            msg = await asyncio.to_thread(self.consumer.poll, 1.0)
            if msg is None or msg.error():
                await asyncio.sleep(0.1)
                continue

            try:
                data = json.loads(msg.value().decode())
                await self.worker.send_message(
                    channel_id=data.get("channel_id"),
                    message=data.get("message"),
                    resource=data.get("resource", "default"),
                )
                await asyncio.to_thread(self.consumer.commit)
            except Exception as e:
                print("Error handling message:", e)
