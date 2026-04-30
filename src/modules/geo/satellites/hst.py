from ..base_satellite import BaseSatellite
from src.infra.nats.core_manager import CoreNATSManager


class HST(BaseSatellite):
    def __init__(self, nats: CoreNATSManager):
        super().__init__(name="HST", nats=nats, interval=1.0)
        self.norad_id = 20580
