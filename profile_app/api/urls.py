from django.urls import path
from .views import ProfileDetailView, BusinessProfileListView, CustomerProfileListView

urlpatterns = [
    path('profile/<int:pk>/', ProfileDetailView.as_view(), name='profile-detail'),
    path('profiles/business/', BusinessProfileListView.as_view(),name='profile-business-list'),
    path('', CustomerProfileListView.as_view(),name='profile-customer-list'),
]
