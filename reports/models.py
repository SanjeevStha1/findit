from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models
from pgvector.django import VectorField


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Item(models.Model):
    class ReportType(models.TextChoices):
        LOST = "lost", "Lost"
        FOUND = "found", "Found"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        MATCHED = "matched", "Matched"
        CLAIMED = "claimed", "Claimed"
        RESOLVED = "resolved", "Resolved"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="items",
    )
    report_type = models.CharField(max_length=10, choices=ReportType.choices)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="items"
    )
    description = models.TextField()
    item_date = models.DateTimeField()

    # Exact location — used internally for accurate distance calculations
    location = gis_models.PointField(geography=True)

    # Fuzzed/rounded location — safe to expose publicly (privacy, NFR2)
    location_display = gis_models.PointField(geography=True)

    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.ACTIVE
    )

    # Reserved for Phase 11 (AI text matching) — not used yet
    text_embedding = VectorField(dimensions=384, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_report_type_display()}: {self.category} ({self.id})"

    class Meta:
        ordering = ["-created_at"]


class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="images")
    image_url = models.URLField()

    # Reserved for Phase 12 (AI image matching) — not used yet
    image_embedding = VectorField(dimensions=512, null=True, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for Item {self.item_id}"