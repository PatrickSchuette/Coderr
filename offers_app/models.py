from django.contrib.auth.models import User
from django.db import models


class Offer(models.Model):
    """A service offer created by a business user, made up of several OfferDetail tiers."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offers')
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='offer_images/', blank=True, null=True)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        """Return a human-readable representation of the offer."""
        return f'{self.title} ({self.user.username})'


class OfferDetail(models.Model):
    """A single pricing tier (basic/standard/premium) belonging to an Offer."""

    class OfferType(models.TextChoices):
        BASIC = 'basic', 'Basic'
        STANDARD = 'standard', 'Standard'
        PREMIUM = 'premium', 'Premium'

    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='details')
    title = models.CharField(max_length=255)
    revisions = models.IntegerField()
    delivery_time_in_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list)
    offer_type = models.CharField(max_length=10, choices=OfferType.choices)

    class Meta:
        ordering = ['price']

    def __str__(self) -> str:
        """Return a human-readable representation of the offer detail."""
        return f'{self.offer.title} - {self.offer_type}'
