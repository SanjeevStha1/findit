from django.contrib import admin
from .models import Category, Item, ItemImage
from .models import Claim

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