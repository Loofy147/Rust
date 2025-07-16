from distributed.ray_base import RayAgent
from distributed.celery_base import celery_app, CeleryAgent

class RayNotificationAgent(RayAgent):
    def process(self, msg):
        if msg.get("type") == "notify":
            content = msg["content"]
            self.logger.info(f"Notification: {content}")
            # Extend here for email/Slack integration

@celery_app.task(base=CeleryAgent, name="celery_notification_task")
def celery_notification_task(self, msg):
    if msg.get("type") == "notify":
        content = msg["content"]
        self.logger.info(f"Notification: {content}")
        # Extend here for email/Slack integration