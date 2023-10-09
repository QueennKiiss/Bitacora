from notifypy import Notify

def create_critical_notification(title: str, message: str) -> None:
    """ Creates a notification with critical urgency"""

    notification = Notify()

    notification.title = title
    notification.message = message
    #notification.application_name = None
    #notification.audio = None
    #notification.icon = None
    notification.urgency = "critical"
    notification.send()

if __name__ == "__main__":
    create_critical_notification(
        title="Critical notification", 
        message="I am a critical notification standing forever up"
        )