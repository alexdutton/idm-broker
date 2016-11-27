from django.conf import settings
from kombu import Connection
from kombu.pools import connections

#import pdb;pdb.set_trace()
connection = connections[Connection(hostname=settings.BROKER_HOSTNAME,
                                    ssl=settings.BROKER_SSL,
                                    virtual_host=settings.BROKER_VHOST,
                                    userid=settings.BROKER_USERNAME,
                                    password=settings.BROKER_PASSWORD,
                                    transport=settings.BROKER_TRANSPORT)]
broker_prefix = settings.BROKER_PREFIX