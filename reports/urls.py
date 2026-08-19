from django.urls import path
from .views import CategoryListView, ItemListCreateView, ItemDetailView

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("items/", ItemListCreateView.as_view(), name="item-list-create"),
    path("items/<int:pk>/", ItemDetailView.as_view(), name="item-detail"),
]