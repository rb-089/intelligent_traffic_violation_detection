from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import OverspeedIncident

@receiver(post_save, sender=OverspeedIncident)
def send_overspeed_notification(sender, instance, created, **kwargs):
    if created:  # Only send email for newly created incidents
        vehicle = instance.vehicle
        owner = vehicle.owner

        # Email content
        subject = "Traffic Overspeeding Violation Alert"
        message = (
            f"Dear {owner.name},\n\n"
            f"We detected your vehicle (Number Plate: {vehicle.vehicle_number}) "
            f"traveling at {instance.speed} km/h, which exceeds the speed limit.\n"
            f"Location: {instance.location}\n"
            f"Time: {instance.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Please ensure compliance with traffic rules to avoid further penalties.\n\n"
            f"Best regards,\nTraffic Violation Monitoring Team"
        )

        # Send email
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,  # Sender email from settings
                [owner.email],  # Recipient email
                fail_silently=False,  # Raise exceptions on failure
            )
            print(f"Notification sent to {owner.email}")
        except Exception as e:
            print(f"Error sending email: {e}")
