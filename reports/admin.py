from django.contrib import admin
from .models import Category, Item, ItemImage
from .models import Claim
from .models import Match
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "type", "is_read", "created_at"]
    list_filter = ["type", "is_read"]

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ["id", "lost_item", "found_item", "score", "status", "created_at"]
    list_filter = ["status"]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ["id", "report_type", "category", "status", "user", "created_at"]
    list_filter = ["report_type", "status", "category"]


@admin.register(ItemImage)
class ItemImageAdmin(admin.ModelAdmin):
    list_display = ["id", "item", "uploaded_at"]

@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ["id", "item", "claimant", "status", "created_at"]
    list_filter = ["status"]