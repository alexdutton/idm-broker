from django.apps import AppConfig, apps


class TestAppConfig(AppConfig):
    name = 'idm_broker.tests.test_app'

    def ready(self):
        from . import models, serializers

        apps.get_app_config('idm_broker').register_notifications([
            {'serializer': serializers.PersonSerializer, 'exchange': 'person'},
            {'serializer': serializers.RobotSerializer, 'exchange': 'robot'},
        ])
        apps.get_app_config('idm_broker').register_related_notification(
            model=models.Robot,
            accessor=lambda robot: robot.owner
        )
