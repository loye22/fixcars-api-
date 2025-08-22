import requests
from django.conf import settings

class OneSignalService:
    @staticmethod
    def send_notification(player_ids, message, heading="Notification", data=None):
        """Send notification using only App ID"""
        if not player_ids:
            return False
        
        notification_data = {
            "app_id": settings.ONESIGNAL_APP_ID,
            "include_player_ids": player_ids,
            "headings": {"en": heading},
            "contents": {"en": message},
            "data": data or {}
        }
        
        try:
            response = requests.post(
                "https://onesignal.com/api/v1/notifications",
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "Authorization": f"Basic {settings.ONESIGNAL_REST_API_KEY}"
                },
                json=notification_data
            )
            
            return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    def send_to_user(user_profile, message, heading="Notification", data=None):
        """Send notification to all devices of a user"""
        player_ids = list(user_profile.devices.filter(is_active=True)
                               .values_list('player_id', flat=True))
        
        if not player_ids:
            return False
            
        return OneSignalService.send_notification(player_ids, message, heading, data)
