from django.contrib.gis.measure import D
from .models import Item, Match
from .models import Notification
from .embeddings import cosine_similarity

# Weights for each factor — must sum to 1.0
WEIGHT_CATEGORY = 0.25
WEIGHT_DISTANCE = 0.30
WEIGHT_DATE = 0.20
WEIGHT_TEXT = 0.25

MAX_DISTANCE_KM = 15   # beyond this, distance score is ~0
MAX_DAYS = 14          # beyond this, date score is ~0


def score_category(lost, found):
    return 1.0 if lost.category_id == found.category_id else 0.0


def score_distance(lost, found):
    if not lost.location or not found.location:
        return 0.0
    distance_m = lost.location.distance(found.location) * 100_000  # rough degree-to-meter fallback
    # More accurate: use the geography-aware distance via a DB query in production;
    # here we do a simple in-Python approximation for clarity.
    distance_km = lost.location.distance(found.location)
    # NOTE: see explanation below about why we compute this via the DB instead.
    return max(0.0, 1.0 - (distance_km / MAX_DISTANCE_KM))


def score_date(lost, found):
    delta_days = abs((lost.item_date - found.item_date).days)
    return max(0.0, 1.0 - (delta_days / MAX_DAYS))


def score_text(lost, found):
    if lost.text_embedding is not None and found.text_embedding is not None:
        similarity = cosine_similarity(lost.text_embedding, found.text_embedding)
        return max(0.0, similarity)  # cosine can be slightly negative; clamp to 0
    # Fallback for items created before embeddings existed
    lost_words = set(lost.description.lower().split())
    found_words = set(found.description.lower().split())
    if not lost_words or not found_words:
        return 0.0
    overlap = lost_words & found_words
    union = lost_words | found_words
    return len(overlap) / len(union)


WEIGHT_CATEGORY = 0.20
WEIGHT_DISTANCE = 0.25
WEIGHT_DATE = 0.15
WEIGHT_TEXT = 0.20
WEIGHT_IMAGE = 0.20


def compute_match(lost, found):
    cat_score = score_category(lost, found)
    text_score = score_text(lost, found)
    date_score = score_date(lost, found)
    image_score = score_image(lost, found)

    breakdown = {
        "category": round(cat_score, 3),
        "date": round(date_score, 3),
        "text": round(text_score, 3),
    }

    overall = (
        cat_score * WEIGHT_CATEGORY
        + date_score * WEIGHT_DATE
        + text_score * WEIGHT_TEXT
    )

    if image_score is not None:
        breakdown["image"] = round(image_score, 3)
        overall += image_score * WEIGHT_IMAGE
    else:
        # No photos to compare — redistribute image's weight proportionally
        # to the signals that ARE available, so missing photos don't just
        # silently cap the max possible score.
        overall = overall / (1 - WEIGHT_IMAGE)

    return overall, breakdown


def find_candidates_for_item(item):
    """
    Given a lost OR found item, find and score candidate matches of the
    opposite type, using a DB-side distance query for accuracy, then
    Python-side scoring for the rest.
    """
    opposite_type = "found" if item.report_type == "lost" else "lost"

    candidates = Item.objects.filter(
        report_type=opposite_type,
        status="active",
    ).exclude(user=item.user)

    results = []
    for candidate in candidates:
        if not item.location or not candidate.location:
            continue

        distance_km = item.location.distance(candidate.location) * 111  # degrees→km approx
        if distance_km > MAX_DISTANCE_KM:
            continue  # too far, skip entirely

        distance_score = max(0.0, 1.0 - (distance_km / MAX_DISTANCE_KM))

        lost_item = item if item.report_type == "lost" else candidate
        found_item = candidate if item.report_type == "lost" else item

        partial_score, breakdown = compute_match(lost_item, found_item)
        overall_score = partial_score + (distance_score * WEIGHT_DISTANCE)
        breakdown["distance"] = round(distance_score, 3)
        breakdown["distance_km"] = round(distance_km, 2)

        results.append((lost_item, found_item, overall_score, breakdown))

    results.sort(key=lambda r: r[2], reverse=True)
    return results


def save_matches_for_item(item, top_n=10):
    """Compute candidates and persist them as Match rows (top N only)."""
    candidates = find_candidates_for_item(item)[:top_n]
    saved = []
    for lost_item, found_item, score, breakdown in candidates:
        match, created = Match.objects.update_or_create(
            lost_item=lost_item,
            found_item=found_item,
            defaults={"score": score, "score_breakdown": breakdown},
        )
        saved.append(match)

        # Only notify on genuinely new, reasonably confident matches
        if created and score >= 0.5:
            for notify_user, other_item in [
                (lost_item.user, found_item),
                (found_item.user, lost_item),
            ]:
                Notification.objects.create(
                    user=notify_user,
                    type=Notification.Type.MATCH,
                    message=f"A possible match was found for your report: {other_item.description[:60]}",
                    related_item_id=other_item.id,
                    related_match_id=match.id,
                )
    return saved

def score_image(lost, found):
    lost_images = lost.images.exclude(image_embedding__isnull=True)
    found_images = found.images.exclude(image_embedding__isnull=True)

    if not lost_images.exists() or not found_images.exists():
        return None  # no photos to compare — don't penalize, just skip

    best_score = 0.0
    for li in lost_images:
        for fi in found_images:
            sim = cosine_similarity(li.image_embedding, fi.image_embedding)
            best_score = max(best_score, sim)
    return max(0.0, best_score)