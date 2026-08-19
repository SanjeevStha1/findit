import random
import math
from django.contrib.gis.geos import Point

# How far (in meters) the public-facing point can be shifted from the real one
FUZZ_RADIUS_METERS = 150


def fuzz_point(point: Point) -> Point:
    """
    Returns a new Point randomly offset from the input point by up to
    FUZZ_RADIUS_METERS, in a random direction. Used to hide a report's
    exact location from public view (NFR2 privacy requirement).
    """
    # Random distance (not always max, so it's not a predictable ring)
    distance_m = random.uniform(0, FUZZ_RADIUS_METERS)
    angle = random.uniform(0, 2 * math.pi)

    # Convert meters to approximate degrees offset
    # 1 degree latitude ≈ 111,320 meters (roughly constant)
    delta_lat = (distance_m * math.cos(angle)) / 111_320

    # 1 degree longitude varies with latitude (shrinks toward the poles)
    delta_lng = (distance_m * math.sin(angle)) / (
        111_320 * math.cos(math.radians(point.y))
    )

    fuzzed_lng = point.x + delta_lng
    fuzzed_lat = point.y + delta_lat

    return Point(fuzzed_lng, fuzzed_lat, srid=4326)