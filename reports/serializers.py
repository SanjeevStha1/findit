from rest_framework import serializers
from .models import Item, ItemImage, Category
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Claim
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "type", "message", "is_read", "related_item_id", "related_match_id", "created_at"]
        read_only_fields = ["id", "created_at"]

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

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )
        return user

class ClaimSerializer(serializers.ModelSerializer):
    claimant_username = serializers.CharField(source="claimant.username", read_only=True)
    item_description = serializers.CharField(source="item.description", read_only=True)

    class Meta:
        model = Claim
        fields = [
            "id", "item", "item_description", "claimant", "claimant_username",
            "verification_answer", "status", "created_at", "resolved_at",
        ]
        read_only_fields = ["id", "claimant", "item", "status", "created_at", "resolved_at"]

class ClaimStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Claim
        fields = ["id", "status", "resolved_at"]
        read_only_fields = ["id", "resolved_at"]