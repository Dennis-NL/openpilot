#!/usr/bin/env python3
"""
Copyright © IQ.Lvbs, apart of Project Teal Lvbs, All Rights Reserved, licensed under https://konn3kt.com/tos

Verifies the vendored `mapd` routing binary authored by Jacob Pfeifer
(github.com/pfeiferj/mapd), built from the gitlvb teal/mapd fork against
teal/gomsgq. The only accepted binary is the checked-in one matching the pinned
hash; nothing is ever downloaded at runtime. Jacob's stock release build embeds
a 15-reader msgq header layout — on this fork (NUM_READERS=32) its registration
writes land inside other processes' reader slots, so a wrong binary is
quarantined rather than left where manager could start it.
"""
import hashlib
import os
import sys

from openpilot.common.basedir import BASEDIR
from openpilot.common.params import Params
from openpilot.common.spinner import Spinner
from openpilot.common.swaglog import cloudlog
from openpilot.iqpilot.iq_maps import VENDOR_MAPD_PATH
import openpilot.system.sentry as sentry

VENDOR_RELEASE_TAG = "v2.0.6-iq1"

_VERSION_PARAM = "MapdVersion"
_HASH_FILE = os.path.join(BASEDIR, "iqpilot", "iq_maps", "tests", "mapd_hash")
QUARANTINE_PATH = VENDOR_MAPD_PATH + ".quarantined"


def sha256_of_file(path: str) -> str:
  """Hex SHA-256 digest of a file on disk."""
  digest = hashlib.sha256()
  with open(path, "rb") as handle:
    for block in iter(lambda: handle.read(1 << 20), b""):
      digest.update(block)
  return digest.hexdigest()


def stamp_vendor_version(version: str, params: Params | None = None) -> None:
  (params or Params()).put(_VERSION_PARAM, version)


class VendorMapdInstaller:
  def __init__(self, spinner_ref: Spinner | None = None, params: Params | None = None):
    self._spinner = spinner_ref
    self._params = params if params is not None else Params()

  def get_installed_version(self) -> str:
    return str(self._params.get(_VERSION_PARAM) or "")

  def verify(self) -> bool:
    """True iff the on-disk binary matches the pinned hash; quarantines a wrong one."""
    expected = self._expected_hash()
    if not expected:
      cloudlog.error("iq_maps: pinned mapd hash missing, vendor binary cannot be verified")
      return False

    if not os.path.isfile(VENDOR_MAPD_PATH):
      # the binary is a tracked file: the updater/bundle restores it
      self._say("Offline maps engine missing; it will be restored by the next update.")
      self._params.remove(_VERSION_PARAM)
      return False

    try:
      current = sha256_of_file(VENDOR_MAPD_PATH)
    except OSError:
      cloudlog.exception("iq_maps: vendor mapd unreadable")
      return False

    if current == expected:
      stamp_vendor_version(VENDOR_RELEASE_TAG, self._params)
      try:
        os.remove(QUARANTINE_PATH)
      except OSError:
        pass
      self._say(f"Offline maps engine verified [{VENDOR_RELEASE_TAG}]")
      return True

    # a foreign binary — e.g. a stock release download from the retired fetch
    # path — must never run: quarantine it where manager can't start it
    cloudlog.error(f"iq_maps: vendor mapd hash {current[:12]} != pinned {expected[:12]}, quarantining")
    self._say("Offline maps engine failed verification; quarantined until the next update.")
    try:
      os.replace(VENDOR_MAPD_PATH, QUARANTINE_PATH)
    except OSError:
      cloudlog.exception("iq_maps: vendor mapd quarantine failed")
      return False
    self._params.remove(_VERSION_PARAM)
    try:
      raise RuntimeError(f"vendor mapd hash mismatch quarantined: {current}")
    except RuntimeError as exc:
      sentry.init(sentry.SentryProject.SELFDRIVE)
      sentry.capture_exception(exc)
    return False

  def _expected_hash(self) -> str:
    try:
      with open(_HASH_FILE) as f:
        return f.read().strip()
    except OSError:
      return ""

  def _say(self, text: str) -> None:
    if self._spinner is not None:
      self._spinner.update(text)


if __name__ == "__main__":
  spinner = Spinner()
  ok = VendorMapdInstaller(spinner).verify()
  spinner.close()
  sys.exit(0 if ok else 1)
