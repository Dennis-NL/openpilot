#!/usr/bin/env python3
"""
canlived — live CAN bridge to konn3kt.

Streams the device's live CAN bus to the konn3kt server so it can be viewed remotely
in Cabana (via a local ZMQ proxy on the laptop). This is the remote analogue of running
`./cereal/messaging/bridge` locally: instead of re-publishing CAN over a LAN ZMQ socket,
canlived opens its OWN websocket to konn3kt and forwards the raw capnp `Event` frames.

It is deliberately a separate daemon (not part of hephaestusd's control websocket):
  * hephaestusd's send path fragments everything as TEXT frames through one queue, which
    cannot carry binary capnp and would head-of-line-block the control plane at 100Hz.
  * a dedicated socket means CAN traffic and control traffic never contend.

Lifecycle: the manager launches canlived only while the `CanLiveStreaming` param is set.
hephaestusd sets/clears that param via startCanLive/stopCanLive, which the konn3kt server
calls when the first viewer connects / the last viewer disconnects. So canlived runs only
during an active debug session — no idle connections, no battery/data cost otherwise.

Copyright © IQ.Lvbs, apart of Project Teal Lvbs, All Rights Reserved.
"""
import os
import threading

from websocket import ABNF, create_connection

import cereal.messaging as messaging
from openpilot.common.api import Api
from openpilot.common.params import Params
from openpilot.common.swaglog import cloudlog

# Cabana's live "Device" stream subscribes only to "can", so that's all we forward to
# match the local experience exactly. (sendcan/TX is not shown by the live device view.)
CAN_SERVICES = ["can"]

# Reconnect backoff bounds (seconds).
RECONNECT_MIN = 1.0
RECONNECT_MAX = 10.0


def _api_host() -> str:
  # Same host hephaestusd talks to; force the websocket scheme.
  host = os.getenv("HEPHAESTUS_HOST") or os.getenv("KONN3KT_API_HOST") or "wss://api-iqlabs.konn3kt.com"
  host = host.rstrip("/")
  if host.startswith("https://"):
    host = "wss://" + host[len("https://"):]
  elif host.startswith("http://"):
    host = "ws://" + host[len("http://"):]
  return host


def _stream_once(dongle_id: str, ws_uri: str, token: str, exit_event: threading.Event) -> None:
  """Open one websocket and pump CAN until it drops or we're asked to exit."""
  ws = create_connection(ws_uri, cookie="jwt=" + token, enable_multithread=True, timeout=30.0)
  cloudlog.info("canlived: connected to %s", ws_uri)
  try:
    # Blocking receive with a short timeout so we periodically re-check exit_event and
    # the socket stays responsive to shutdown even when the bus is quiet.
    socks = [messaging.sub_sock(s, conflate=False, timeout=100) for s in CAN_SERVICES]
    while not exit_event.is_set():
      got_any = False
      for sock in socks:
        while True:
          raw = sock.receive(non_blocking=True)
          if raw is None:
            break
          got_any = True
          # Forward the exact capnp Event bytes as a single binary frame. canlived owns
          # this socket, so there is no fragmentation/interleaving to worry about.
          ws.send_frame(ABNF.create_frame(raw, ABNF.OPCODE_BINARY, 1))
      if not got_any:
        # Nothing pending across any sub — yield briefly instead of busy-spinning.
        exit_event.wait(0.005)
  finally:
    try:
      ws.close()
    except Exception:
      pass


def main(exit_event: threading.Event | None = None) -> None:
  if exit_event is None:
    exit_event = threading.Event()

  params = Params()
  dongle_id = params.get("DongleId", encoding="utf-8")
  if not dongle_id:
    cloudlog.error("canlived: no DongleId, cannot stream")
    return

  api = Api(dongle_id)
  host = _api_host()
  ws_uri = f"{host}/ws/can/{dongle_id}"

  backoff = RECONNECT_MIN
  while not exit_event.is_set():
    try:
      token = api.get_token(expiry_hours=1)
      _stream_once(dongle_id, ws_uri, token, exit_event)
      backoff = RECONNECT_MIN  # clean disconnect, reset backoff
    except Exception as e:
      cloudlog.exception("canlived: stream error: %s", e)
      exit_event.wait(backoff)
      backoff = min(backoff * 2, RECONNECT_MAX)


if __name__ == "__main__":
  main()
