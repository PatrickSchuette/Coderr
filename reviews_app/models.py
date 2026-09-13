from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    """A customer's rating and comment for a business user's work.

    A reviewer may leave at most one review per business user, enforced
    at the database level via unique_together.
    """

    business_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('business_user', 'reviewer')
        ordering = ['-updated_at']

    def __str__(self) -> str:
        """Return a human-readable representation of the review."""
        return f'{self.reviewer.username} -> {self.business_user.username}: {self.rating}/5'