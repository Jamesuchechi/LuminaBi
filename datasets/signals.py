from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Dataset
from dashboards.realtime import broadcast_to_user_dashboards


@receiver(post_save, sender=Dataset)
def dataset_changed(sender, instance: Dataset, created, **kwargs):
    """Broadcast dataset creation/updates to the owner's dashboard hub."""
    owner_id = instance.owner_id
    if not owner_id:
        return

    payload = {
        'entity': 'dataset',
        'action': 'created' if created else 'updated',
        'id': instance.id,
        'name': instance.name,
        'rows': instance.row_count,
        'cols': instance.col_count,
        'is_cleaned': instance.is_cleaned,
        'data_quality_score': instance.data_quality_score,
        'uploaded_at': instance.uploaded_at.isoformat() if instance.uploaded_at else None,
    }

    broadcast_to_user_dashboards(owner_id, payload)

