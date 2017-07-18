import kombu

DEBUG = False

SECRET_KEY = 'secret key for testing'

INSTALLED_APPS = [
    'idm_broker.apps.IDMBrokerConfig',
    'idm_broker.tests.test_app.apps.TestAppConfig',
]

DJANGO_ALLOWED_HOSTS = ['localhost']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

BROKER_HOSTNAME = 'localhost'
BROKER_SSL = False
BROKER_VHOST = ''
BROKER_USERNAME = 'guest'
BROKER_PASSWORD = 'guest'
BROKER_TRANSPORT = 'memory'
BROKER_PREFIX = 'idm_broker.test.'
CELERY_BROKER_URL = 'memory://localhost/idm-auth-celery'

IDM_BROKER = {
    'CONSUMERS': [{
        'queues': [kombu.Queue('test.queue', exchange=kombu.Exchange('test.exchange', type='topic'), routing_key='#')],
        'tasks': ['idm_broker.tests.tasks.test_task'],
    }],
}

ROOT_URLCONF = 'idm_broker.tests.test_app.urls'

API_BASE = 'http://example.org/'