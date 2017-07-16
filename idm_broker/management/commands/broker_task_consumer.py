import logging
from optparse import OptionParser

from argparse import ArgumentParser
from django.core.management import BaseCommand

from idm_broker.consumer import BrokerTaskConsumer


class Command(BaseCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)

    def handle(self, *args, **options):
        if options['verbosity'] > 1:
            logging.basicConfig(level=logging.DEBUG)

        daemon = BrokerTaskConsumer()
        daemon()