from rest_framework import serializers
from .models import Item, ItemImage, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class ItemImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemImage
        fields = ["id", "image_url", "uploaded_at"]


class ItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    images = ItemImageSerializer(many=True, read_only=True)
    reported_by = serializers.CharField(source="user.username", read_only=True)

    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)

    # New: readable output fields, sourced from the fuzzed location only
    display_latitude = serializers.SerializerMethodField()
    display_longitude = serializers.SerializerMethodField()

    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            "id",
            "distance_km",
            "report_type",
            "category",
            "category_name",
            "description",
            "item_date",
            "status",
            "latitude",
            "longitude",
            "display_latitude",
            "display_longitude",
            "images",
            "reported_by",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]

    def get_distance_km(self, obj):
        if hasattr(obj, "distance") and obj.distance is not None:
            return round(obj.distance.km, 2)
        return None

    def get_display_latitude(self, obj):
        return obj.location_display.y if obj.location_display else None

    def get_display_longitude(self, obj):
        return obj.location_display.x if obj.location_display else None