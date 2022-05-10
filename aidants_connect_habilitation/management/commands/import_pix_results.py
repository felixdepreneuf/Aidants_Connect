from django.core.management.base import BaseCommand

from aidants_connect_habilitation.tasks import import_pix_results


class Command(BaseCommand):
    help = "Gets test PIX results and update database"

    def handle(self, *args, **options):
        import_pix_results()
