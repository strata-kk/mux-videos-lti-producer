from django.core.management.base import BaseCommand

from muxltiproducer import mux


class Command(BaseCommand):
    help = "Generate a Mux signing key"

    def handle(self, *args, **options):
        client = mux.get_url_signing_key_client()
        print(client.create_url_signing_key())
