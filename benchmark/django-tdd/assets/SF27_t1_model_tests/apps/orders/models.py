from django.db import models
from django.conf import settings
from django.utils import timezone


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.user.email}"

    def confirm(self):
        """Mark order as confirmed. Only pending orders can be confirmed."""
        if self.status != 'pending':
            raise ValueError(f"Cannot confirm order with status '{self.status}'")
        self.status = 'confirmed'
        self.save(update_fields=['status', 'updated_at'])

    def ship(self):
        """Mark order as shipped. Only confirmed orders can be shipped."""
        if self.status != 'confirmed':
            raise ValueError(f"Cannot ship order with status '{self.status}'")
        self.status = 'shipped'
        self.shipped_at = timezone.now()
        self.save(update_fields=['status', 'shipped_at', 'updated_at'])

    def deliver(self):
        """Mark order as delivered. Only shipped orders can be delivered."""
        if self.status != 'shipped':
            raise ValueError(f"Cannot deliver order with status '{self.status}'")
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at', 'updated_at'])

    def cancel(self):
        """Cancel order. Only pending or confirmed orders can be cancelled."""
        if self.status not in ('pending', 'confirmed'):
            raise ValueError(f"Cannot cancel order with status '{self.status}'")
        self.status = 'cancelled'
        self.save(update_fields=['status', 'updated_at'])

    @property
    def is_cancellable(self):
        return self.status in ('pending', 'confirmed')

    @property
    def days_since_order(self):
        return (timezone.now() - self.created_at).days


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=255)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    @property
    def line_total(self):
        return self.product_price * self.quantity
