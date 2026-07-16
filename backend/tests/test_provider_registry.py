import pytest

from app.core.providers import attendance as prov


class _Fake(prov.AttendanceProvider):
    method = "FAKE"  # must not clash with the real QR provider (shared registry)

    def validate_and_mark(self, db, payload):
        return "marked"


def test_register_and_get():
    p = _Fake()
    prov.register_provider(p)
    assert prov.get_provider("FAKE") is p


def test_get_unknown_raises():
    with pytest.raises(KeyError):
        prov.get_provider("FACE")


def test_cannot_instantiate_abstract():
    with pytest.raises(TypeError):
        prov.AttendanceProvider()
