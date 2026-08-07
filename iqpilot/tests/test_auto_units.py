from openpilot.common.params import Params
from openpilot.iqpilot.common.auto_units import CONFIRMATIONS, AutoUnits

SEATTLE = (47.6062, -122.3321)
BERLIN = (52.5200, 13.4050)
LONDON = (51.5074, -0.1278)


class StubAutoUnits(AutoUnits):
  def __init__(self, params):
    super().__init__(params)
    self.position = (0.0, 0.0, False)

  def _position(self):
    return self.position


def settle(auto_units, position, count=CONFIRMATIONS, start=0.0):
  auto_units.position = position
  for i in range(count):
    auto_units.update(now=start + i * 100.0)
  return start + count * 100.0


class TestAutoUnits:
  def setup_method(self):
    self.params = Params()
    self.params.put_bool("IQAutoUnits", True)
    self.params.remove("IQAutoUnitsRegion")
    self.params.put_bool("IsMetric", False)
    self.auto_units = StubAutoUnits(self.params)

  def test_no_fix_does_nothing(self):
    settle(self.auto_units, (0.0, 0.0, False))
    assert self.params.get("IQAutoUnitsRegion") is None
    assert not self.params.get_bool("IsMetric")

  def test_disabled_does_nothing(self):
    self.params.put_bool("IQAutoUnits", False)
    settle(self.auto_units, (*BERLIN, True))
    assert self.params.get("IQAutoUnitsRegion") is None
    assert not self.params.get_bool("IsMetric")

  def test_metric_region_switches_to_metric(self):
    settle(self.auto_units, (*BERLIN, True))
    assert self.params.get("IQAutoUnitsRegion") == "METRIC"
    assert self.params.get_bool("IsMetric")

  def test_mph_region_stays_imperial(self):
    settle(self.auto_units, (*SEATTLE, True))
    assert self.params.get("IQAutoUnitsRegion") == "US"
    assert not self.params.get_bool("IsMetric")

  def test_uk_stays_imperial(self):
    self.params.put_bool("IsMetric", True)
    settle(self.auto_units, (*LONDON, True))
    assert self.params.get("IQAutoUnitsRegion") == "GB"
    assert not self.params.get_bool("IsMetric")

  def test_border_crossing_switches_units(self):
    now = settle(self.auto_units, (*SEATTLE, True))
    assert not self.params.get_bool("IsMetric")

    settle(self.auto_units, (*BERLIN, True), start=now)
    assert self.params.get("IQAutoUnitsRegion") == "METRIC"
    assert self.params.get_bool("IsMetric")

  def test_manual_override_is_kept_within_a_region(self):
    now = settle(self.auto_units, (*SEATTLE, True))
    self.params.put_bool("IsMetric", True)

    settle(self.auto_units, (*SEATTLE, True), start=now)
    assert self.params.get_bool("IsMetric")

  def test_unconfirmed_region_is_not_applied(self):
    settle(self.auto_units, (*BERLIN, True), count=CONFIRMATIONS - 1)
    assert self.params.get("IQAutoUnitsRegion") is None
    assert not self.params.get_bool("IsMetric")

  def test_flapping_region_resets_confirmations(self):
    now = 0.0
    for position in (BERLIN, SEATTLE, BERLIN, SEATTLE):
      now = settle(self.auto_units, (*position, True), count=1, start=now)
    assert self.params.get("IQAutoUnitsRegion") is None
    assert not self.params.get_bool("IsMetric")

  def test_rate_limited(self):
    self.auto_units.position = (*BERLIN, True)
    for _ in range(CONFIRMATIONS * 4):
      self.auto_units.update(now=1.0)
    assert self.params.get("IQAutoUnitsRegion") is None
