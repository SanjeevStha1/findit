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
    private_notes = models.TextField(
        blank=True,
        help_text="Private details only you can see — use this to verify claims (e.g. serial number, exact contents)."
    )
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

class Claim(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="claims")
    claimant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="claims"
    )
    verification_answer = models.TextField(
        help_text="Claimant's proof/answer to verify ownership"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    handoff_details = models.TextField(
        blank=True,
        help_text="Contact info / instructions the finder provides upon approval (phone, meeting spot, etc.)"
    )

    def __str__(self):
        return f"Claim on Item {self.item_id} by {self.claimant}"

    class Meta:
        ordering = ["-created_at"]

class Match(models.Model):
    class Status(models.TextChoices):
        SUGGESTED = "suggested", "Suggested"
        CONFIRMED = "confirmed", "Confirmed"
        DISMISSED = "dismissed", "Dismissed"

    lost_item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="matches_as_lost")
    found_item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="matches_as_found")
    score = models.FloatField()
    score_breakdown = models.JSONField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SUGGESTED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-score"]
        unique_together = ["lost_item", "found_item"]  # don't duplicate the same pair

    def __str__(self):
        return f"Match: Lost#{self.lost_item_id} <-> Found#{self.found_item_id} ({self.score:.2f})"

class Notification(models.Model):
    class Type(models.TextChoices):
        MATCH = "match", "New Match"
        CLAIM_UPDATE = "claim_update", "Claim Update"
        SYSTEM = "system", "System"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.CharField(max_length=20, choices=Type.choices)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_item_id = models.IntegerField(null=True, blank=True)
    related_match_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.user}: {self.message[:40]}"