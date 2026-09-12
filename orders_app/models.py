from django.contrib.auth.models import User
from django.db import models

from offers_app.models import OfferDetail


class Order(models.Model):
    """A placed order, storing a frozen snapshot of the OfferDetail it was created from.

    The order intentionally does not reference OfferDetail via a ForeignKey:
    later edits to the original offer must not retroactively change an order
    a customer already placed.
    """

    class Status(models.TextChoices):
        """Possible lifecycle states of an order."""

        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    customer_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_orders')
    business_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='business_orders')

    title = models.CharField(max_length=255)
    revisions = models.IntegerField()
    delivery_time_in_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list)
    offer_type = models.CharField(max_length=10, choices=OfferDetail.OfferType.choices)

    status = models.CharField(max_length=15, choices=Status.choices, default=Status.IN_PROGRESS)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        """Return a human-readable representation of the order."""
        return f'Order #{self.id}: {self.title} ({self.status})'