from distributed.ray_base import RayAgent
from distributed.celery_base import celery_app, CeleryAgent


class RayAuditAgent(RayAgent):

    def process(self, msg):
        if msg.get("type") == "audit":
            event = msg["event"]
            self.logger.info(f"Audit event: {event}")
            # Extend for compliance, external logging, etc.


@celery_app.task(base=CeleryAgent, name="celery_audit_task")
def celery_audit_task(self, msg):
    if msg.get("type") == "audit":
        event = msg["event"]
        self.logger.info(f"Audit event: {event}")
        # Extend for compliance, external logging, etc.