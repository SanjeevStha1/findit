from django.contrib.gis.geos import Point
from rest_framework import generics, permissions
from .models import Item, Category
from .serializers import ClaimStatusUpdateSerializer, ItemSerializer, CategorySerializer
from .utils import fuzz_point
from django.contrib.gis.measure import D  # D = Distance, a measurement helper
from django.contrib.gis.db.models.functions import Distance
from .serializers import ItemImageSerializer
from .models import ItemImage
import time
import cloudinary.utils
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import RegisterSerializer
from django.contrib.auth.models import User
from .models import Claim
from .serializers import ClaimSerializer
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .matching import save_matches_for_item
from .models import Match
from rest_framework.decorators import api_view, permission_classes as perm_classes
from rest_framework.permissions import AllowAny
from .models import Notification
from .serializers import NotificationSerializer
from .models import Notification

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class NotificationMarkReadView(generics.UpdateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(is_read=True)

class MatchSerializerMixin:
    pass  # placeholder, we'll define the real serializer next


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def get_matches_for_item(request, item_id):
    item = Item.objects.get(pk=item_id)
    matches = save_matches_for_item(item)

    data = []
    for m in matches:
        other = m.found_item if item.report_type == "lost" else m.lost_item
        data.append({
            "match_id": m.id,
            "other_item_id": other.id,
            "other_item_description": other.description,
            "other_item_category": other.category.name,
            "score": round(m.score, 3),
            "score_breakdown": m.score_breakdown,
            "status": m.status,
        })
    return Response(data)

class ClaimCreateView(generics.CreateAPIView):
    serializer_class = ClaimSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        item = Item.objects.get(pk=self.kwargs["item_id"])
        if item.user == self.request.user:
            raise ValidationError("You cannot claim your own report.")
        serializer.save(claimant=self.request.user, item=item)



class MyClaimsView(generics.ListAPIView):
    """Claims the logged-in user has submitted (as a claimant)."""
    serializer_class = ClaimSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Claim.objects.filter(claimant=self.request.user)


class ReceivedClaimsView(generics.ListAPIView):
    """Claims submitted on items the logged-in user reported (as a finder)."""
    serializer_class = ClaimSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Claim.objects.filter(item__user=self.request.user)


class ClaimUpdateView(generics.UpdateAPIView):
    serializer_class = ClaimStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Claim.objects.filter(item__user=self.request.user)

    def perform_update(self, serializer):
        claim = serializer.save(resolved_at=timezone.now())
        Notification.objects.create(
            user=claim.claimant,
            type=Notification.Type.CLAIM_UPDATE,
            message=f"Your claim on '{claim.item.description[:60]}' was {claim.status}.",
            related_item_id=claim.item.id,
        )

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]  # public — anyone can see categories


class ItemListCreateView(generics.ListCreateAPIView):
    serializer_class = ItemSerializer

    def get_permissions(self):
        # Anyone can browse (GET); must be logged in to create (POST)
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = Item.objects.filter(status="active").select_related("category").prefetch_related("images")

        # --- Existing distance filter ---
        lat = self.request.query_params.get("lat")
        lng = self.request.query_params.get("lng")
        radius_km = self.request.query_params.get("radius_km")

        if lat and lng and radius_km:
            try:
                user_point = Point(float(lng), float(lat), srid=4326)
                radius = D(km=float(radius_km))
                queryset = queryset.filter(
                    location__distance_lte=(user_point, radius)
                ).annotate(
                    distance=Distance("location", user_point)
                ).order_by("distance")
            except (ValueError, TypeError):
                pass

        # --- New filters ---
        report_type = self.request.query_params.get("report_type")
        if report_type in ("lost", "found"):
            queryset = queryset.filter(report_type=report_type)

        category_id = self.request.query_params.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        date_from = self.request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(item_date__gte=date_from)

        date_to = self.request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(item_date__lte=date_to)

        return queryset

    def perform_create(self, serializer):
        lat = serializer.validated_data.pop("latitude")
        lng = serializer.validated_data.pop("longitude")
        point = Point(lng, lat, srid=4326)

        serializer.save(
            user=self.request.user,
            location=point,
            location_display=fuzz_point(point),  # ← now actually fuzzed
        )


class ItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ItemSerializer
    queryset = Item.objects.select_related("category").prefetch_related("images")

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]





@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cloudinary_signature(request):
    timestamp = int(time.time())
    params_to_sign = {"timestamp": timestamp}

    signature = cloudinary.utils.api_sign_request(
        params_to_sign, cloudinary.config().api_secret
    )

    return Response({
        "signature": signature,
        "timestamp": timestamp,
        "cloud_name": cloudinary.config().cloud_name,
        "api_key": cloudinary.config().api_key,
    })






class ItemImageCreateView(generics.CreateAPIView):
    serializer_class = ItemImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        item = Item.objects.get(pk=self.kwargs["item_id"], user=self.request.user)
        serializer.save(item=item)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]