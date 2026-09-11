from django.urls import path
from rest_framework.routers import DefaultRouter

from offers_app.api.views import OfferDetailRetrieveView, OfferViewSet

router = DefaultRouter()
router.register('offers', OfferViewSet, basename='offer')

urlpatterns = router.urls + [
    path('offerdetails/<int:pk>/', OfferDetailRetrieveView.as_view(),name='offerdetail-detail')]
