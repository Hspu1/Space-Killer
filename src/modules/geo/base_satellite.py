from dataclasses import dataclass, field
import asyncio

from sgp4.api import Satrec


@dataclass(slots=True)
class BaseSatellite:
    name: str
    norad_id: int = field(init=False, default=None)
    satrec: Satrec = field(init=False, default=None)
    is_ready: asyncio.Event = field(default_factory=asyncio.Event, repr=False)
    
    def set_tle(self, l1: str, l2: str) -> bool:
        try:
            self.satrec = Satrec.twoline2rv(l1, l2)
            if self.satrec.error == 0:
                self.norad_id = self.satrec.satnum
                self.is_ready.set()
                return True
            return False
        except Exception:
            return False
