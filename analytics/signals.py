from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Insight, Anomaly, Metric
from core.realtime import broadcast_to_user_dashboards


def _broadcast(owner_id, entity: str, action: str, data: dict):
    if not owner_id:
        return
    payload = {'entity': entity, 'action': action}
    payload.update(data)
    broadcast_to_user_dashboards(owner_id, payload)


@receiver(post_save, sender=Insight)
def insight_created(sender, instance: Insight, created, **kwargs):
    dataset = getattr(instance, 'dataset', None)
    owner_id = dataset.owner_id if dataset else None
    _broadcast(owner_id, 'insight', 'created' if created else 'updated', {
        'id': instance.id,
        'title': instance.title,
        'insight_type': instance.insight_type,
        'created_at': instance.created_at.isoformat() if instance.created_at else None,
        'dataset_id': dataset.id if dataset else None,
    })


@receiver(post_save, sender=Anomaly)
def anomaly_created(sender, instance: Anomaly, created, **kwargs):
    dataset = getattr(instance, 'dataset', None)
    owner_id = dataset.owner_id if dataset else None
    _broadcast(owner_id, 'anomaly', 'created' if created else 'updated', {
        'id': instance.id,
        'description': instance.description,
        'severity': instance.severity,
        'status': instance.status,
        'detected_at': instance.detected_at.isoformat() if instance.detected_at else None,
        'dataset_id': dataset.id if dataset else None,
    })


@receiver(post_save, sender=Metric)
def metric_updated(sender, instance: Metric, created, **kwargs):
    dataset = getattr(instance, 'dataset', None)
    owner_id = dataset.owner_id if dataset else None
    _broadcast(owner_id, 'metric', 'created' if created else 'updated', {
        'id': instance.id,
        'name': instance.name,
        'value': instance.value,
        'updated_at': instance.updated_at.isoformat() if instance.updated_at else None,
        'dataset_id': dataset.id if dataset else None,
    })

