import importlib
import json
import re
import threading
from pathlib import Path

from confluent_kafka import Producer
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from models_handler import get_disticnt_tag_army
import routing_roles as routing_roles


class KafkaRouter:
    def __init__(self, kafka_host: str, config_path: str):
        self.producer = Producer({'bootstrap.servers': kafka_host})
        self.config_path = config_path
        self.channel_configs = []
        self._load_config()
        self._start_watcher()
        self.chars_to_remove = [',', '.', '/', '<', '>', '?', "'", '"', ';', ':', ']',
                                '[', '{', '}', '\\', '/', '+', '=', '_', '-', ')', '(',
                                '*', '&', '^', '%', '$', '#', '@', '!', '~', '`', 'ٰ', '‌',
                                'ٔ', 'ٔ', 'ء', '؟', '؛', '«', '»', 'ّ', 'َ', 'ِ', 'ُ', 'ً',
                                'ٍ', 'ٌ', 'ْ', '`', '!', '٬', '٫', 'ریال', '٪', '×',
                                '،', '،', 'ـ', '_', '|']

    def _load_config(self):
        importlib.reload(routing_roles)
        self.channel_configs = routing_roles.config
        print("🔄 KafkaRouter config reloaded")

    def _start_watcher(self):
        class ReloadHandler(FileSystemEventHandler):
            def __init__(self, router):
                self.router = router

            def on_modified(self, event):
                if Path(event.src_path).name == "routing_roles.py":
                    print("🔁 Detected change in routing_roles.py. Reloading KafkaRouter config...")
                    self.router._load_config()

        observer = Observer()
        handler = ReloadHandler(self)
        observer.schedule(handler, path=str(Path(self.config_path).parent), recursive=False)
        threading.Thread(target=observer.start, daemon=True).start()

    def match_channels(self, message: str):
        result = []
        message = message.replace('\u200c', ' ')
        for ch in self.chars_to_remove:
            message = message.replace(ch, '')

        for channel in self.channel_configs:
            roles = channel['roles']
            target_channel_id = channel['channel_id']
            matched_roles = []
            for role in roles:
                must_pass = all(re.search(rf'(^|\s){word}($|\s)', message) for word in role['must']) if role['must'] else True
                should_pass = any(re.search(rf'(^|\s){word}($|\s)', message) for word in role['should']) if role['should'] else True
                must_not_fail = not any(re.search(rf'(^|\s){word}($|\s)', message) for word in role['must_not']) if role['must_not'] else True

                if must_pass and should_pass and must_not_fail:
                    matched_roles.append(role)

            if matched_roles:
                result.append({
                    'channel_id': target_channel_id,
                    'matched_roles': matched_roles
                })
        return result

    def route_message(self, message_obj):
        content = message_obj['content']
        matchs = self.match_channels(content)
        target_channels = [item['channel_id'] for item in matchs]
        print(f"🔍 Matching channels for message: {target_channels}", flush=True)

        if matchs:
            for channel in matchs:
                message = message_obj['message']
                channel_id = channel['channel_id']
                if channel_id in [-1002680845262, -1002778743721]:
                    tag = get_disticnt_tag_army(message=message_obj['content'])['result']
                    if message_obj['resource'] == 'instagram':
                        message += f"📑 <b>دسته بندی:</b> {tag}\n"
                    else:
                        message += f"📑 *دسته بندی: **{tag}*\n"
                musts = []
                if channel['matched_roles']:
                    for roles in channel['matched_roles']:
                        if 'lable' in roles.keys():
                            musts.extend(roles['lable'])
                        else:
                            musts.extend(roles['must'])
                if musts:
                    musts = list(set(musts))
                    musts = '-'.join(musts)
                    if message_obj['resource'] == 'instagram':
                        message += f"📑 <b>کلیدواژه:</b> {musts}\n"
                    else:
                        message += f"📑 *کلیدواژه: **{musts}*\n"
                self.producer.produce(str(channel_id), json.dumps(
                    {
                        'channel_id': channel_id,
                        'content': message_obj['content'],
                        'message': message,
                        'resource': message_obj['resource'],
                    }
                ).encode("utf-8"))
                self.producer.flush()
                print(f"✅ Routed message to topic {channel_id}")
        else:
            print("❌ No matching topic found")
        
        return [match['channel_id'] for match in matchs]
