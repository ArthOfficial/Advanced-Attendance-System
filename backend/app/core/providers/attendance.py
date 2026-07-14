from abc import ABC, abstractmethod

# ponytail: plain registry dict, no factory class. A provider registers itself; QR arrives in Phase 2.
PROVIDERS: dict[str, "AttendanceProvider"] = {}


class AttendanceProvider(ABC):
    method: str  # "QR" | "FACE" | "RFID" | "NFC"

    @abstractmethod
    def validate_and_mark(self, db, payload):
        """Validate the attendance payload and persist an Attendance row. Returns it."""
        ...


def register_provider(provider: "AttendanceProvider") -> None:
    PROVIDERS[provider.method] = provider


def get_provider(method: str) -> "AttendanceProvider":
    return PROVIDERS[method]
