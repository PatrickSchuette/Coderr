from django.db.models import Avg
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from offers_app.models import Offer
from profile_app.models import Profile
from reviews_app.models import Review


class BaseInfoView(APIView):
    """Return aggregated platform statistics. Maps to /api/base-info/."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        """Compute and return review, rating, business, and offer counts."""
        review_count = Review.objects.count()
        average_rating = Review.objects.aggregate(average=Avg('rating'))['average'] or 0
        business_profile_count = Profile.objects.filter(type=Profile.ProfileType.BUSINESS).count()
        offer_count = Offer.objects.count()

        return Response({
            'review_count': review_count,
            'average_rating': round(average_rating, 1),
            'business_profile_count': business_profile_count,
            'offer_count': offer_count,
        })