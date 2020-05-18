
from django.apps import AppConfig


class StationsConfig(AppConfig):
    name = 'stations'
    verbose_name = 'Paperwaves'

    def ready(self):
        import stations.signals # noqa
