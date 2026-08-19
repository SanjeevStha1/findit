from django.urls import path
from .views import CategoryListView, ItemImageCreateView, ItemListCreateView, ItemDetailView, cloudinary_signature

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("items/", ItemListCreateView.as_view(), name="item-list-create"),
    path("items/<int:pk>/", ItemDetailView.as_view(), name="item-detail"),
    path("cloudinary-signature/", cloudinary_signature, name="cloudinary-signature"),
    path("items/<int:item_id>/images/", ItemImageCreateView.as_view(), name="item-image-create"),
]