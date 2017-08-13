import logging
from optparse import OptionParser

from argparse import ArgumentParser
from django.core.management import BaseCommand

import idm_broker.consumer


class Command(BaseCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)

    def handle(self, *args, **options):
        if options['verbosity'] > 1:
            logging.basicConfig(level=logging.DEBUG)

        daemon = idm_broker.consumer.BrokerTaskConsumer()
        daemon()