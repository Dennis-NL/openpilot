import pytest

from openpilot.iqpilot.common.geo_regions import METRIC_REGION, UNKNOWN_REGION, region_for_position, region_is_metric

US_POINTS = [
  (47.6062, -122.3321, "Seattle"),
  (42.3314, -83.0458, "Detroit"),
  (42.8864, -78.8784, "Buffalo"),
  (25.7617, -80.1918, "Miami"),
  (29.7604, -95.3698, "Houston"),
  (32.7157, -117.1611, "San Diego"),
  (34.0522, -118.2437, "Los Angeles"),
  (61.2181, -149.9003, "Anchorage"),
  (58.3019, -134.4197, "Juneau"),
  (64.8378, -147.7164, "Fairbanks"),
  (21.3069, -157.8583, "Honolulu"),
  (18.4655, -66.1057, "San Juan"),
  (13.4757, 144.7489, "Guam"),
  (44.9778, -93.2650, "Minneapolis"),
  (40.7128, -74.0060, "New York"),
  (41.8781, -87.6298, "Chicago"),
  (31.7900, -106.4300, "El Paso"),
  (26.2034, -98.2300, "McAllen"),
  (44.8016, -68.7712, "Bangor"),
  (48.7519, -122.4787, "Bellingham"),
  (46.8772, -96.7898, "Fargo"),
  (48.6023, -93.4093, "International Falls"),
  (46.4953, -84.3453, "Sault Ste. Marie MI"),
  (47.1211, -88.5694, "Houghton"),
  (41.6528, -83.5379, "Toledo"),
  (42.1370, -83.1930, "Trenton MI"),
  (39.7392, -104.9903, "Denver"),
  (33.4484, -112.0740, "Phoenix"),
  (30.3322, -81.6557, "Jacksonville"),
  (42.3601, -71.0589, "Boston"),
  (38.9072, -77.0369, "Washington DC"),
]

GB_POINTS = [
  (51.5074, -0.1278, "London"),
  (54.5973, -5.9301, "Belfast"),
  (55.8642, -4.2518, "Glasgow"),
  (51.4816, -3.1791, "Cardiff"),
  (51.4545, -2.5879, "Bristol"),
  (53.4084, -2.9916, "Liverpool"),
  (53.4808, -2.2426, "Manchester"),
  (55.9533, -3.1883, "Edinburgh"),
  (52.4862, -1.8904, "Birmingham"),
  (53.8008, -1.5491, "Leeds"),
  (57.4778, -4.2247, "Inverness"),
  (57.1497, -2.0943, "Aberdeen"),
  (56.4620, -2.9707, "Dundee"),
  (58.6373, -3.0689, "John o' Groats"),
  (54.1509, -4.4814, "Douglas"),
  (49.1858, -2.1064, "St Helier"),
  (55.0000, -7.3200, "Derry"),
  (54.3438, -7.6315, "Enniskillen"),
  (54.1751, -6.3402, "Newry"),
  (54.4783, -8.0906, "Belleek"),
  (54.5973, -7.3095, "Omagh"),
  (55.2053, -6.6570, "Portrush"),
  (58.2090, -6.3890, "Stornoway"),
  (58.9809, -2.9605, "Kirkwall"),
  (60.1546, -1.1494, "Lerwick"),
  (50.7184, -3.5339, "Exeter"),
  (50.3755, -4.1427, "Plymouth"),
  (52.6309, 1.2974, "Norwich"),
  (54.9783, -1.6178, "Newcastle"),
  (51.8642, -2.2382, "Gloucester"),
  (52.4140, -4.0810, "Aberystwyth"),
  (51.6214, -3.9436, "Swansea"),
  (50.6938, -1.3040, "Newport IoW"),
]

LR_POINTS = [
  (6.3005, -10.7969, "Monrovia"),
  (4.3750, -7.7169, "Harper"),
  (6.9956, -9.4722, "Gbarnga"),
  (6.0667, -8.1333, "Zwedru"),
  (8.4219, -9.7478, "Voinjama"),
  (5.8808, -10.0467, "Buchanan"),
  (5.0100, -9.0400, "Greenville"),
  (7.3500, -8.7200, "Ganta"),
]

METRIC_POINTS = [
  (49.2827, -123.1207, "Vancouver"),
  (48.4284, -123.3656, "Victoria"),
  (43.6532, -79.3832, "Toronto"),
  (42.3149, -83.0364, "Windsor"),
  (46.5136, -84.3358, "Sault Ste. Marie ON"),
  (42.9745, -82.4066, "Sarnia"),
  (43.2557, -79.8711, "Hamilton"),
  (42.9849, -81.2453, "London ON"),
  (45.5019, -73.5674, "Montreal"),
  (45.4765, -75.7013, "Gatineau"),
  (46.8139, -71.2080, "Quebec City"),
  (46.0878, -64.7782, "Moncton"),
  (44.6488, -63.5752, "Halifax"),
  (49.8951, -97.1384, "Winnipeg"),
  (51.0447, -114.0719, "Calgary"),
  (53.5461, -113.4938, "Edmonton"),
  (52.1332, -106.6700, "Saskatoon"),
  (50.6745, -120.3273, "Kamloops"),
  (32.5149, -117.0382, "Tijuana"),
  (31.7000, -106.4700, "Ciudad Juarez"),
  (25.6866, -100.3161, "Monterrey"),
  (27.5060, -99.5075, "Nuevo Laredo"),
  (19.4326, -99.1332, "Mexico City"),
  (53.3498, -6.2603, "Dublin"),
  (51.8985, -8.4756, "Cork"),
  (53.2707, -9.0568, "Galway"),
  (54.9503, -7.7345, "Letterkenny"),
  (54.0000, -6.4000, "Dundalk"),
  (54.2489, -6.9683, "Monaghan"),
  (54.2766, -8.4761, "Sligo"),
  (54.6538, -8.1096, "Donegal"),
  (52.5200, 13.4050, "Berlin"),
  (52.2297, 21.0122, "Warsaw"),
  (48.8566, 2.3522, "Paris"),
  (60.1699, 24.9384, "Helsinki"),
  (50.4501, 30.5234, "Kyiv"),
  (-33.8688, 151.2093, "Sydney"),
  (35.6762, 139.6503, "Tokyo"),
  (8.4844, -13.2299, "Freetown"),
  (7.8767, -11.1875, "Kenema"),
  (8.2783, -10.5733, "Kailahun"),
  (9.6412, -13.5784, "Conakry"),
  (7.7562, -8.8179, "Nzerekore"),
  (7.4125, -7.5539, "Man"),
  (5.3600, -4.0083, "Abidjan"),
]


@pytest.mark.parametrize("lat, lon, name", US_POINTS)
def test_us_positions(lat, lon, name):
  assert region_for_position(lat, lon) == "US", name


@pytest.mark.parametrize("lat, lon, name", GB_POINTS)
def test_gb_positions(lat, lon, name):
  assert region_for_position(lat, lon) == "GB", name


@pytest.mark.parametrize("lat, lon, name", LR_POINTS)
def test_lr_positions(lat, lon, name):
  assert region_for_position(lat, lon) == "LR", name


@pytest.mark.parametrize("lat, lon, name", METRIC_POINTS)
def test_metric_positions(lat, lon, name):
  assert region_for_position(lat, lon) == METRIC_REGION, name


@pytest.mark.parametrize("lat, lon", [(0.0, 0.0), (0.0, 0.00001), (91.0, 10.0), (10.0, 181.0)])
def test_invalid_positions(lat, lon):
  assert region_for_position(lat, lon) == UNKNOWN_REGION


def test_region_is_metric():
  assert not region_is_metric("US")
  assert not region_is_metric("GB")
  assert not region_is_metric("LR")
  assert region_is_metric(METRIC_REGION)
  assert not region_is_metric(UNKNOWN_REGION)
