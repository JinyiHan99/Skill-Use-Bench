import csv
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.products.models import Product, PriceHistory


class Command(BaseCommand):
    help = 'Export price change history for the last N days to a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('output', type=str, help='Output CSV file path')
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to look back (default: 30)',
        )
        parser.add_argument(
            '--product',
            type=str,
            help='Filter by product slug',
        )

    def handle(self, *args, **options):
        output_path = options['output']
        days = options['days']
        product_slug = options.get('product')

        since = timezone.now() - timedelta(days=days)

        queryset = PriceHistory.objects.filter(changed_at__gte=since)
        if product_slug:
            queryset = queryset.filter(product__slug=product_slug)

        queryset = queryset.select_related('product', 'changed_by')

        if not queryset.exists():
            self.stdout.write(self.style.WARNING('No price changes found.'))
            return

        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Product', 'Old Price', 'New Price', 'Changed At', 'Changed By'])

            for entry in queryset:
                writer.writerow([
                    entry.product.name,
                    entry.old_price,
                    entry.new_price,
                    entry.changed_at.isoformat(),
                    entry.changed_by.email if entry.changed_by else 'system',
                ])

        self.stdout.write(
            self.style.SUCCESS(f'Exported {queryset.count()} price changes to {output_path}')
        )
