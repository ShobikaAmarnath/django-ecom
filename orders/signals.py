from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from .models import Order

@receiver(post_save, sender=Order)
def send_order_status_email(sender, instance, created, **kwargs):
    """
    Triggered whenever an Order is updated.
    """
    if not created:  # Only when updating an existing order
        # If status is Paid, send confirmation email
        if instance.status == "Paid":
            mail_subject = f"Payment Verified for Order #{instance.order_number}"
            message = render_to_string("orders/order_received_email.html", {
                "user": instance.user,
                "order": instance,
                "payment_confirmed": True,  # Tells template to show "payment verified" section
            })
            to_email = instance.user.email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.content_subtype = "html"
            send_email.send()
