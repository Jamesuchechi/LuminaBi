"""
Helper utilities for broadcasting dashboard events over Channels.
Uses the in-memory channel layer configured in settings (no Redis required).
Migrated from dashboards app.
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_to_user_dashboards(user_id, payload: dict):
    """
    Send a payload to all dashboard hub subscribers for a user.
    The DashboardHubConsumer joins the `dashboard_user_<id>` group.
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    try:
        async_to_sync(channel_layer.group_send)(
            f'dashboard_user_{user_id}',
            {
                'type': 'dashboard_push',
                'payload': payload,
            },
        )
    except Exception:
        # Silent fail to avoid breaking request flow
        pass
