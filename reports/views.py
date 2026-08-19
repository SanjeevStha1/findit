from django.contrib.gis.geos import Point
from rest_framework import generics, permissions
from .models import Item, Category
from .serializers import ItemSerializer, CategorySerializer
from .utils import fuzz_point
from django.contrib.gis.measure import D  # D = Distance, a measurement helper
from django.contrib.gis.db.models.functions import Distance

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
                pass  # invalid params — ignore filter, return unfiltered results

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