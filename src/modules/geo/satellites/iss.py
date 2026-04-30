from ..base_satellite import BaseSatellite

from src.infra.nats.core_manager import CoreNATSManager


class ISS(BaseSatellite):
    def __init__(self, nats: CoreNATSManager):
        super().__init__(name="ISS", nats=nats, interval=0.5)
        self.norad_id = 25544
