import logging

from django.core.management.base import BaseCommand

from muxltiproducer import tasks


class Command(BaseCommand):
    help = "Synchronize data with the Mux API"

    def handle(self, *args, **options):
        logging.getLogger().setLevel(logging.INFO)
        if options["verbosity"] >= 3:
            logging.getLogger().setLevel(logging.DEBUG)
        tasks.synchronize.call_local()
