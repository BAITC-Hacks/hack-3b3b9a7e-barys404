"""Server-owned scope for the first release: national or one exact hospital."""
from dataclasses import dataclass


@dataclass(frozen=True)
class DataScope:
    hospital_name: str | None

    def apply(self, filters):
        result = dict(filters)
        if self.hospital_name is not None:
            if result.get("hospital_mo") not in (None, self.hospital_name):
                raise ValueError("Requested hospital is outside the data scope")
            result["hospital_mo"] = self.hospital_name
        return result
