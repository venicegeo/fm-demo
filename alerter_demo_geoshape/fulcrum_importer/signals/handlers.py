from django.db.models.signals import post_save
from django.dispatch import receiver
from fulcrum_importer.models import Feature
from django.core.cache import cache
from fulcrum_importer.mapping import get_geojson


@receiver(post_save, sender=Feature)
def push_features(sender, instance, **kwargs):
    print("UPDATING FEATURES!")
    layer = instance.layer
    updated_features = cache.get("updated_features")
    if not updated_features:
        updated_features = {}
    updated_features[layer.layer_name] = get_geojson(layer.layer_name)
    cache.set("updated_features",updated_features)