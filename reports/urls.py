from django.urls import path
from .views import CategoryListView, ItemImageCreateView, ItemListCreateView, ItemDetailView, cloudinary_signature
from .views import (
    CategoryListView,
    ItemListCreateView,
    ItemDetailView,
    ItemImageCreateView,
    cloudinary_signature,
    RegisterView,
)
from .views import ClaimCreateView, MyClaimsView, ReceivedClaimsView, ClaimUpdateView
from .views import get_matches_for_item
from .views import NotificationListView, NotificationMarkReadView
from .views import MyItemsView
from .views import mark_all_notifications_read
from .views import resolve_item

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("items/", ItemListCreateView.as_view(), name="item-list-create"),
    path("items/<int:pk>/", ItemDetailView.as_view(), name="item-detail"),
    path("items/<int:item_id>/images/", ItemImageCreateView.as_view(), name="item-image-create"),
    path("cloudinary-signature/", cloudinary_signature, name="cloudinary-signature"),
    path("register/", RegisterView.as_view(), name="register"),
    path("items/<int:item_id>/claim/", ClaimCreateView.as_view(), name="claim-create"),
    path("claims/mine/", MyClaimsView.as_view(), name="claims-mine"),
    path("claims/received/", ReceivedClaimsView.as_view(), name="claims-received"),
    path("claims/<int:pk>/", ClaimUpdateView.as_view(), name="claim-update"),
    path("items/<int:item_id>/matches/", get_matches_for_item, name="item-matches"),
    path("notifications/", NotificationListView.as_view(), name="notifications-list"),
    path("notifications/<int:pk>/mark-read/", NotificationMarkReadView.as_view(), name="notification-mark-read"),
    path("items/mine/", MyItemsView.as_view(), name="items-mine"),
    path("notifications/mark-all-read/", mark_all_notifications_read, name="notifications-mark-all-read"),
    path("items/<int:item_id>/resolve/", resolve_item, name="item-resolve"),
]
