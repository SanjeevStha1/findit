from django.core.management.base import BaseCommand
from reports.models import ItemImage
from reports.embeddings import compute_image_embedding


class Command(BaseCommand):
    help = "Backfill image embeddings for ItemImages that don't have one yet"

    def handle(self, *args, **kwargs):
        images = ItemImage.objects.filter(image_embedding__isnull=True)
        count = images.count()
        self.stdout.write(f"Backfilling {count} images...")

        for img in images:
            img.image_embedding = compute_image_embedding(img.image_url)
            img.save(update_fields=["image_embedding"])
            self.stdout.write(f"  Image {img.id}: done")

        self.stdout.write(self.style.SUCCESS(f"Backfilled {count} images."))