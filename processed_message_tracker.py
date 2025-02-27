import time

class ProcessedMessageTracker:
    def __init__(self, max_message_age=300):
        self.processed_messages = {}
        self.MAX_MESSAGE_AGE = max_message_age

    def should_process_message(self, message_id, timestamp):
        return not self.is_message_processed(message_id) and not self.is_message_expired(timestamp)

    def is_message_processed(self, message_id):
        if message_id not in self.processed_messages:
            return False
        current_time = int(time.time())
        timestamp, _ = self.processed_messages[message_id]
        processed = current_time - timestamp <= self.MAX_MESSAGE_AGE
        if processed:
            print("Ignoring message - already processed")
        return processed

    def mark_message_as_processed(self, message_id, timestamp):
        self.processed_messages[message_id] = (timestamp, True)

    def cleanup_processed_messages(self):
        current_time = int(time.time())
        expired_ids = [message_id for message_id, (timestamp, _) in self.processed_messages.items() if
                       current_time - timestamp > self.MAX_MESSAGE_AGE]

        for message_id in expired_ids:
            del self.processed_messages[message_id]

    def is_message_expired(self, timestamp):
        current_time = int(time.time())
        expired = current_time - timestamp > self.MAX_MESSAGE_AGE
        if expired:
            print("Ignoring message - too old")
        return expired
