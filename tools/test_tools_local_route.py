"""End-to-end check that cabana and jotpluggler can still load a route and decode CAN.

Uses a synthesized local route so it runs offline — the konn3kt API paths are covered
separately by tools/replay/tests/test_api.cc and the per-tool konn3kt tests.
"""
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

import cereal.messaging as messaging
from cereal import log

TOOLS_DIR = Path(__file__).parent
CABANA_BIN = TOOLS_DIR / "cabana" / "_cabana"
JOTPLUGGLER_BIN = TOOLS_DIR / "jotpluggler" / "jotpluggler"

DONGLE_ID = "0000000000000000"
TIMESTAMP = "2024-01-01--00-00-00"
ROUTE = f"{DONGLE_ID}|{TIMESTAMP}"


def write_rlog(path: Path, n_frames: int = 200):
  """A minimal but valid rlog: carParams once, then CAN frames at 100Hz."""
  with open(path, "wb") as f:
    cp = messaging.new_message('carParams')
    cp.carParams.carFingerprint = "TOYOTA_RAV4_TSS2"
    cp.carParams.brand = "toyota"
    f.write(cp.to_bytes())

    for i in range(n_frames):
      msg = messaging.new_message('can', 2)
      msg.logMonoTime = int(i * 1e7)
      for j, addr in enumerate((0x1D2, 0x260)):
        msg.can[j].address = addr
        msg.can[j].src = 0
        msg.can[j].dat = bytes([i % 256] * 8)
      f.write(msg.to_bytes())


@pytest.fixture(scope="module")
def local_route(tmp_path_factory):
  data_dir = tmp_path_factory.mktemp("routes")
  for seg in range(2):
    seg_dir = data_dir / f"{DONGLE_ID}|{TIMESTAMP}--{seg}"
    seg_dir.mkdir()
    write_rlog(seg_dir / "rlog")
  return data_dir


def run(cmd, timeout=180):
  env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
  return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env,
                        cwd=TOOLS_DIR.parent)


@pytest.mark.skipif(not JOTPLUGGLER_BIN.exists(), reason="jotpluggler not built")
def test_jotpluggler_renders_a_local_route(local_route, tmp_path):
  out = tmp_path / "plot.png"
  result = run([str(JOTPLUGGLER_BIN), "--data-dir", str(local_route),
                "--sync-load", "--output", str(out), ROUTE])
  assert result.returncode == 0, result.stdout + result.stderr
  assert out.is_file(), result.stdout + result.stderr
  # a blank/failed render still writes a file, so require real content
  assert out.stat().st_size > 5000, f"suspiciously small render: {out.stat().st_size} bytes"


@pytest.mark.skipif(not CABANA_BIN.exists(), reason="cabana not built")
def test_cabana_loads_a_local_route(local_route):
  # cabana has no headless render mode: on success it enters the Qt event loop and
  # never returns, so run it briefly and assert on what it logged before we kill it.
  # A load failure exits before the event loop and logs "failed to load route".
  env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
  proc = subprocess.Popen([str(CABANA_BIN), "--data_dir", str(local_route), "--no-vipc", ROUTE],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                          env=env, cwd=TOOLS_DIR.parent)
  loaded = f"loaded route {ROUTE} with 2 valid segments"
  lines = []
  deadline = time.monotonic() + 60
  try:
    while time.monotonic() < deadline:
      line = proc.stdout.readline()
      if not line:  # cabana exited, which means the load failed
        break
      lines.append(line)
      if loaded in line:
        break
  finally:
    proc.kill()
    proc.wait()
    proc.stdout.close()

  out = "".join(lines)
  assert "failed to load route" not in out, out
  assert "invalid route format" not in out, out
  assert loaded in out, out


@pytest.mark.skipif(not shutil.which("python3"), reason="no python3")
def test_replay_logreader_reports_load_stats(local_route):
  """LogReader gained download/decompress/parse instrumentation during the sync;
  jotpluggler's load-stats panel reads it."""
  header = (TOOLS_DIR / "replay" / "logreader.h").read_text()
  for accessor in ("compressed_size", "decompressed_size", "download_seconds",
                   "decompress_seconds", "parse_seconds"):
    assert f"{accessor}() const" in header


def test_can_capnp_field_matches_extractor_codegen():
  """jotpluggler's generated extractor reads busTimeDEPRECATED; if cereal is ever
  renamed to upstream's `deprecated` group this must be re-patched."""
  assert 'busTimeDEPRECATED' in log.CanData.schema.fields
  gen = (TOOLS_DIR / "jotpluggler" / "generate_event_extractors.py").read_text()
  assert "getBusTimeDEPRECATED()" in gen
