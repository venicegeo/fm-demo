from django.db.models.signals import post_save
from django.dispatch import receiver
from piazza_consumer.models import Alert


@receiver(post_save, sender=Alert)
def update_json(sender, instance, **kwargs):
    print "SIGNAL!"
    alerts = Alert.objects.all().order_by('alert_date')
    with open('demo_app.json','wb') as alert_file:
        text = ""
        for alert in alerts:
            text += str(alert.alert_date) + " " + alert.alert_msg + "\n"
        alert_file.write(text)
