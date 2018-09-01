import threading

from core.manager import ServiceManager
from webservices.settings import TRADING_SERVICES


class Corethread(threading.Thread):
    def run(self):
        ServiceManager().initialise_services(TRADING_SERVICES)