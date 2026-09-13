import django_filters

from reviews_app.models import Review


class ReviewFilter(django_filters.FilterSet):
    """Supports filtering the review list by business user or reviewer."""

    business_user_id = django_filters.NumberFilter(field_name='business_user_id')
    reviewer_id = django_filters.NumberFilter(field_name='reviewer_id')

    class Meta:
        model = Review
        fields = ['business_user_id', 'reviewer_id']
