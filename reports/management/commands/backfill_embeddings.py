from django.core.management.base import BaseCommand
from reports.models import Item
from reports.embeddings import compute_text_embedding


class Command(BaseCommand):
    help = "Backfill text embeddings for items that don't have one yet"

    def handle(self, *args, **kwargs):
        items = Item.objects.filter(text_embedding__isnull=True)
        count = items.count()
        self.stdout.write(f"Backfilling {count} items...")

        for item in items:
            item.text_embedding = compute_text_embedding(item.description)
            item.save(update_fields=["text_embedding"])
            self.stdout.write(f"  Item {item.id}: done")

        self.stdout.write(self.style.SUCCESS(f"Backfilled {count} items."))