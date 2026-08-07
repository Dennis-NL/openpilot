# Upstream sync plan — `tools/cabana` and `tools/jotpluggler`

Hand-port the current upstream (commaai/openpilot) versions of Cabana and jotpluggler into
iqpilot without losing konn3kt integration. iqpilot does not use comma connect: every route
list, route-file listing, JWT and live-CAN path goes through `api-iqlabs.konn3kt.com`, and the
DBC source is `iqdbc`, not `opendbc_repo`.

Reference clone used for this analysis: `/tmp/openpilot-upstream` @ `e7b1ee3a5`
("jp: fix segment range parsing", 2026-08-05).

---

## 1. Where we actually are

Baselines were established by blob-matching every iqpilot file against upstream history, not by
reading commit messages.

| Tool | iqpilot baseline | Upstream HEAD | Gap |
|---|---|---|---|
| `tools/cabana` | `bcdeec313` (2025-12-16, #36884) | `e7b1ee3a5` (2026-08-05) | **53 commits, ~8 months** |
| `tools/jotpluggler` | `61608db78` (2026-07-15, #38353) | `e7b1ee3a5` | **6 commits, ~3 weeks** |
| `tools/plotjuggler` | `a46ff01ca` (2026-01-19) | `e7b1ee3a5` | 14 commits (secondary scope) |

Cabana is the real work. jotpluggler was hand-ported in May–July 2026 (`4b68073c4`, `b26218e85`,
`2cd89a198`) and is nearly current — most of its files are **byte-identical** to upstream HEAD.

A critical structural fact: upstream moved the whole tree under a nested `openpilot/` package
(`#38219`/`#38220`/`#38223`, 2026-06-21) and moved the HAL to `common/hardware/` (`#38202`).
iqpilot has **not** adopted either. Every ported file needs a de-prefix pass:

- `#include "openpilot/cereal/..."` → `"cereal/..."`
- `#include "common/hardware/hw.h"` → `"system/hardware/hw.h"`
- `#include "json11/json11.hpp"` → `"third_party/json11/json11.hpp"`
- `repo_root() / "openpilot" / "tools" / ...` → `repo_root() / "tools" / ...`
- SCons nodes `#openpilot/common`, `#openpilot/cereal` → `#common`, `#cereal`
- `opendbc_repo/opendbc/dbc` → `iqdbc/dbc`; `#opendbc_repo` → `#iqdbc_repo`

---

## 2. konn3kt invariants — the contract the port must not break

These are the only genuinely IQ-owned surfaces. Everything else in both trees is upstream code we
are behind on. **Anything not on this list should be taken from upstream verbatim** (modulo §1).

### Cabana

| File | What is IQ-owned | Disposition |
|---|---|---|
| `utils/api.{cc,h}` | `CommaApi::BASE_URL = API_HOST ?: https://api-iqlabs.konn3kt.com`; RSA-signed device JWT; Qt `HttpRequest` | **Delete** — fold into `tools/replay/api.{cc,h}` (§3.A) |
| `streams/routes.{cc,h}` | konn3kt device list + route listing | Rewrite on upstream HEAD shape, konn3kt endpoints |
| `konn3kt_canproxy.py` | `canlived → konn3kt relay → local ZMQ → Cabana` proxy | Keep; must stay wired to the Device/ZMQ stream (§3.C) |
| `SConscript` | iqdbc paths, non-nested paths, `PrettyAction`, extra libs | Rebase onto upstream, re-apply IQ deltas |
| `mainwin.cc` | "Load DBC from commaai/**iqdbc**" menu | Re-apply rename only |
| `dbc/generate_dbc_json.py` | `from iqdbc.car import ...` | Re-apply rename only |
| `assets/assets.cc` (tracked) | bootstrap-icons LFS bypass | See §3.K |
| `dbc/car_fingerprint_to_dbc.json` (+`.log`) | tracked build product | Keep tracked |
| `.gitignore`, `README.md` | binary name, iqdbc, konn3kt route examples | Re-apply |

### jotpluggler

All IQ deltas are already carrying `// IQ.Pilot patch:` comments — preserve that convention.

| File | IQ patch |
|---|---|
| `SConscript` | `.venv` site-packages injection; `iqdbc.dbc.generator.generator.create_all()` instead of upstream `get_generated_dbcs()`; no `bootstrap_icons` module; explicit `avformat/avcodec/avutil/x264/yuv/z/bz2/zstd/curl/ssl/crypto` + `OpenCL`/`va`/`va-drm`/`drm`; `PrettyAction`; guards `imgui.MESA_DIR` existence |
| `icons.cc` | vendored `tools/jotpluggler/assets/bootstrap-icons.ttf` (third_party/bootstrap is LFS, TTF not checked in) |
| `common.cc` | iqpilot `common/util.h` has no `check_system`; inline `std::system` + stderr |
| `runtime.cc` | no `common/yuv.h`; vendored libyuv lacks `NV12ToABGR` → `NV12ToARGB` + `ARGBToABGR` |
| `sketch_layout.cc` | `PyDownloader::getRouteFiles` → `CommaApi2::httpGet(BASE_URL + "/v1/route/<name>/files")`; `androidLog` (cereal not renamed); iqdbc paths |
| `app.{cc,h}`, `layout.cc`, `layout_io.cc`, `map.cc`, `custom_series.cc` | path/include de-prefixing; `LogOrigin::Android`; iqdbc |
| `dbc.h` | empty-multiplex guard (`mux.empty() ? 0 : std::stoi(mux)`) — a genuine bugfix, **upstream this** |
| `generate_event_extractors.py` | `getBusTimeDEPRECATED()` (iqpilot cereal keeps a flat field, not upstream's `deprecated :group`) |
| `pluggle.py` | iqpilot-only launcher (upstream has none) |

---

## 3. Conflict matrix — upstream change vs konn3kt

### A. File downloading / API moved from C++ to Python (`#37497`, `#38430`) — **highest impact**

Upstream cabana HEAD calls `PyDownloader::getDevices()`, `getDeviceRoutes()`, `getRouteFiles()`
(`tools/replay/py_downloader.h`), which shell into `openpilot/tools/lib/`. iqpilot's replay has
**no** `py_downloader`; it keeps a C++/libcurl path in `tools/replay/api.{cc,h}`
(`CommaApi2::BASE_URL`, `create_token(use_jwt)`, `httpGet`). jotpluggler already bridges this gap
in `sketch_layout.cc` — **reuse that pattern**, don't invent a second one.

Resolution: extend `tools/replay/api.{cc,h}` with

```
std::string getDevices();                                   // GET /v1/me/devices/
std::string getDeviceRoutes(dongle_id, start_ms, end_ms, preserved);
                                                            // GET /v1/devices/<id>/routes_segments?start=&end=
                                                            // GET /v1/devices/<id>/routes/preserved
std::string getRouteFiles(route);                           // GET /v1/route/<name>/files   (already reachable via httpGet)
```

returning the same JSON shapes upstream's `PyDownloader` returns, then port upstream's `routes.cc`
verbatim with `PyDownloader::` → `CommaApi2::`. Upstream's HEAD `routes.cc` is already Qt-free
(json11 + `strptime`/`strftime` for the preserved-route ISO timestamps) — that code ports as-is.

Auth semantics to preserve: `create_token(!Hardware::PC())` — device RSA-JWT on device,
`~/.comma/auth.json` `access_token` on a PC. Upstream's Python path only ever does the latter.

Consequence: `tools/cabana/utils/api.{cc,h}` (Qt `QNetworkAccessManager` + duplicate JWT code)
**gets deleted**, which drops `Qt5Network` from the cabana link and converges with §3.B.

### B. de-Qt: `#37519`, `#37521`, `#37522`, `#37523`, `#38357`, `#38359`, `#38360`

The bulk of the 53-commit gap. `QString`→`std::string` through the DBC core, new Qt-free
`core/{can_data,color,message_id,settings}.h`, Qt/core split in `dbc/dbcqt.{cc,h}`, QtXml dropped
(bootstrap SVG symbol extraction hand-rolled in `utils/util.cc`), QtConcurrent dropped, QtSerialBus
dropped (SocketCAN now raw `linux/can` sockets, `#37553` excludes it on macOS).

**Zero konn3kt content.** Pure upstream adoption. It is also why almost every cabana file shows a
large diff — those are not IQ changes, they are upstream changes we lack.

Net effect on `SConscript`: `qt_modules` goes from
`["Widgets","Gui","Core","Network","Concurrent","DBus","Xml"]` → `["Widgets","Gui","Core"]`,
and `Qt5SerialBus` / `QtSerialBus` framework drop out.

### C. `--zmq` bridge path (`#38484`) — **breaks konn3kt_canproxy if ported blind**

Upstream HEAD `DeviceStream::start()` forks `cereal/messaging/bridge <addr> /"can/"` and
`streamThread()` then always subscribes on `127.0.0.1`. `bridge <ip> <whitelist>` is
`zmq_to_msgq` (see `cereal/messaging/bridge.cc:60`) — it ZMQ-subscribes from `<ip>` and republishes
to local msgq.

iqpilot's documented remote-CAN workflow is the opposite direction:
`konn3kt_canproxy.py` sets `ZMQ=1` and **publishes** capnp `Event` frames on a local ZMQ `can`
socket; the user then picks *Live → Device → ZMQ → 127.0.0.1*. Under upstream HEAD semantics that
forks a bridge which subscribes to the same loopback endpoint the proxy publishes on and
republishes into msgq, while cabana reads ZMQ — the proxy path stops being the thing cabana reads.

Resolution: keep the pre-`#38484` direct-attach semantics as an explicit IQ escape hatch. Port
upstream's bridge-forking code, but subscribe to `zmq_address` directly (no bridge fork) when the
stream is started in "attach to an existing ZMQ publisher" mode — either by treating loopback
addresses as attach-mode, or by adding a third radio button next to MSGQ/ZMQ. Mark it
`// IQ.Pilot patch:` and state why (konn3kt_canproxy). **This must be re-verified end-to-end on a
real device before the sync is called done** (§5.3).

### D. libyuv removed, `common/yuv.h` added (`#38306`)

jotpluggler already patches around this. Cabana's `cameraview.cc` does NV12 conversion too.
Decision: port `common/yuv.h` into iqpilot once, then **delete** the `runtime.cc` IQ patch and take
upstream's `cameraview.cc` verbatim. One-time cost, removes a recurring patch site.

### E. Vendored native deps via `comma-deps-*` wheels (`#37327`, `#37994`, `#37681`, `#38308`)

Upstream `SConstruct` now exports `ffmpeg_libs` and pulls capnproto/ffmpeg/zstd/zeromq/json11/
libusb/imgui/bootstrap-icons from pip wheels. iqpilot pins `imgui`/`libusb` from
`git.konn3kt.com/IQ.Lvbs/dependencies`, vendors json11 in `third_party/json11`, and has **no**
`bootstrap_icons` module and **no** `ffmpeg_libs` export.

Resolution: add an `ffmpeg_libs` list + `Export` to iqpilot's `SConstruct` mirroring upstream's
(`avformat avcodec swresample avutil` [+ `x264 z` [+ `va va-drm drm`]]) so both tool SConscripts can
take upstream's form nearly verbatim instead of hand-listing libs. Keep `third_party/json11`.
Do **not** chase the wheels.

### F. `androidLog` → `operatingSystemLog` (`#38209`)

iqpilot cereal still has `androidLog`. Keep the existing `sketch_layout.cc` / `app.h` IQ patch.
Renaming cereal is out of scope (it is a schema change with device-side blast radius).

### G. Tests: catch2 dropped (`#38408`), unittest conversion (`#38387`, `#38384`)

Upstream deleted `tools/cabana/tests/test_runner.cc` and split a deliberately Qt-free
`tests/test_dbc_core` target (objects built from the **base** env, linking no Qt — it exists
specifically to stop Qt creeping back into the DBC core). Adopt that shape; drop `test_runner.cc`.
jotpluggler gains `test_jotpluggler.py`.

### H. `cabana` launcher script + `_cabana` binary (`#37814`, `c02cf706a`, `05cf8023a`)

Upstream builds `Program('_cabana')` and ships `tools/cabana/cabana` as a bash launcher that
installs Qt if missing and runs `scons -u openpilot/tools/cabana/_cabana openpilot/cereal/messaging/bridge`.
iqpilot builds `Program('cabana')` — so `tools/cabana/cabana` is currently a **committed binary**.
Adopting upstream's split means: `.gitignore` `cabana` → `_cabana`, and the launcher's scons
targets de-prefixed to `tools/cabana/_cabana cereal/messaging/bridge`.

### I. `assets.cc` / bootstrap icons (`#37994`, `71290f380`, `15267e408`)

Upstream generates `assets/assets.cc` at build time (`rcc` over an `assets.generated.qrc` that
interpolates the packaged bootstrap-icons SVG path) and gitignores it. iqpilot tracks the generated
14.9k-line `assets.cc` because the icons package isn't available.

Recommended: vendor the bootstrap-icons **SVG** next to the already-vendored TTF
(`tools/jotpluggler/assets/bootstrap-icons.ttf`), add a tiny local shim module exposing
`SVG_PATH`/`TTF_PATH`, adopt upstream's generation, and untrack `assets.cc`. This also lets
jotpluggler's `icons.cc` IQ patch collapse back to upstream's `BOOTSTRAP_ICONS_TTF` define.
Acceptable fallback: keep tracking `assets.cc` and keep both patches.

---

## Status

**Phases 0–2 are done and landed.** Both tools are at upstream `e7b1ee3a5` (2026-08-05) with
konn3kt preserved. Departures from the plan as written, and what remains:

- §3.I resolved better than planned: `third_party/bootstrap/bootstrap-icons.svg` turned out to be
  **tracked already**, so upstream's build-time embedding was adopted as-is — no vendored SVG, and
  the 14.9k-line generated `assets.cc` is gone (it was never tracked; it was a gitignored build
  product).
- §3.D done both ways: `common/yuv.{cc,h}` ported, and `tools/replay/framereader.cc` moved off
  libyuv too, so the jotpluggler `runtime.cc` patch disappeared entirely.
- Unplanned dependency found during the port: upstream's `#38430` also added download/decompress/
  parse instrumentation to `LogReader`, which jotpluggler's load-stats panel reads. Ported into
  iqpilot's `LogReader` around its own FileReader/decompress steps (so decompress is timed
  separately, unlike upstream where the Python downloader does it inline).
- §3.C landed as a **three-mode** `DeviceStream` (`Msgq` / `Zmq` / `Bridge`) rather than an
  escape hatch. Upstream's ZMQ path forks a bridge that republishes to **msgq** while still
  setting `ZMQ=1` and subscribing over **ZMQ** — that combination reads nothing. Keeping the modes
  explicit preserves upstream's bridge convenience *and* the direct attach `konn3kt_canproxy.py`
  needs, and fixes that inconsistency. `--bridge <ip>` is a new flag.
- Also de-comma'd beyond the plan: jotpluggler's "Useradmin" / "comma connect" buttons became a
  single **konn3kt** link (`KONN3KT_APP_HOST`, default `https://konn3kt.com`, same
  `<dongle_id>/<log_id>` path shape `tools/lib/logreader.py` already parses).

### Phase 3 verification actually performed (macOS arm64, live konn3kt)

- **konn3kt API, live, real credentials** — every endpoint the port builds returns 200 with real
  data: `/v1/me/devices/` (2 devices), `/v1/devices/<id>/routes_segments?start=&end=` (1776
  routes), `/v1/devices/<id>/routes/preserved` (16), `/v1/route/<name>/files` (48 logs / 48 qlogs
  / 48 qcameras).
- **Real route in the real GUI** — `_cabana --qcam 0f53129ed44f6920|000001a5--07db1da02e` loaded
  **48 valid segments** and came up as a foreground Cocoa app (not offscreen).
- **Live CAN over the ZMQ attach** — a local publisher mimicking `konn3kt_canproxy.py` fed
  `_cabana --zmq 127.0.0.1`; cabana ingested **2179 CAN frames** and wrote them to
  `~/cabana_live_stream/.../rlog`. This is the exact path `#38484` would have broken.
- **Fixed while verifying:** `utils::icon()` painted a null QPixmap whenever an empty icon id was
  requested (`ToolButton("")` in `chartswidget.cc`), logging two `QPainter` warnings on every
  dark-theme macOS start. Pre-existing upstream bug, not a port regression; guarded here and worth
  upstreaming alongside the `dbc.h` mux fix.

**Still outstanding:**
- **Phase 3.3 (device half):** the konn3kt relay accepts the websocket and authorizes the stream,
  but `0f53129ed44f6920` emits no frames because `canlived` only runs while the `CanLiveStreaming`
  param is set. Needs a device with that enabled to close the loop.
- **Phase 3.5:** cabana has not been built for larch64.
- Charts/video widgets were not visually inspected — `screencapture` is blocked by macOS
  screen-recording permission for the terminal, so GUI rendering is evidenced by process state and
  the ingested-frame log rather than by a screenshot.

Tests added: `tools/replay/tests/test_api.cc` (konn3kt endpoint paths + error envelope),
`tools/cabana/test_cabana_konn3kt.py`, `tools/jotpluggler/test_jotpluggler.py`, and
`tools/test_tools_local_route.py` (synthesizes a local route and drives both tools headlessly).

## 4. Execution plan

Land each phase as its own commit. Build after every sub-step — do not batch §4.2.

### Phase 0 — infrastructure (no tool code)

0.1 `SConstruct`: add and `Export` `ffmpeg_libs`.
0.2 Port `common/yuv.h`; drop the `runtime.cc` libyuv patch.
0.3 Vendor bootstrap-icons SVG + local `bootstrap_icons` shim (`SVG_PATH`, `TTF_PATH`).
0.4 `tools/replay/api.{cc,h}`: add `getDevices()`, `getDeviceRoutes()`, `getRouteFiles()` against
    the konn3kt endpoints, matching upstream `PyDownloader` JSON shapes.

**Gate:** `scons -u -j8 tools/replay` clean; a scratch binary lists real devices from
`api-iqlabs.konn3kt.com` with both a device JWT and a PC `auth.json` token.

### Phase 1 — jotpluggler (6 commits; do first, it validates the whole pattern cheaply)

1.1 `3f49e2d33` thumbnail source — add `thumbnail.{cc,h}`; `common.h` `kSpecialItemSpecs` 5→6;
    `common.cc` `PaneKind::Thumbnail`; `layout_io.cc` `"thumbnail"`; `app.{cc,h}` `ThumbnailView`
    + `ThumbnailFrame`; `session.cc` `setThumbnails`. Re-apply the json11/path/`Android` patches.
1.2 `576de9c7e` build speedup — take upstream `generate_event_extractors.py` **wholesale**
    (iqpilot's copy has diverged: `event_base_slots`, `static_enums`, single-use scalar getters)
    and re-apply only the `getBusTimeDEPRECATED()` patch.
1.3 `e7b1ee3a5` segment-range parsing — empty-begin guard in `sketch_layout.cc`.
1.4 `6b47a5b6b` decompress-in-downloader — iqpilot has no `PyDownloader`; confirm the replay-side
    decompression path is unaffected (expected no-op).
1.5 `fef29ad22`/`911f07ee8` — add `test_jotpluggler.py`.

**Gate:** `scons -u -j8 tools/jotpluggler`; `./tools/jotpluggler/pluggle.py <konn3kt route>` opens,
thumbnails render, CAN series decode against iqdbc, a saved layout round-trips.

### Phase 2 — cabana (53 commits). Bottom-up, one layer per build.

2.1 **DBC core** — `dbc/{dbc,dbcfile,dbcmanager}.{cc,h}`, new `core/{can_data,color,message_id,settings}.h`,
    new `dbc/dbcqt.{cc,h}`. Re-apply iqdbc rename in `dbc/generate_dbc_json.py`.
2.2 **Streams** — `abstractstream`, `livestream`, `replaystream`, `pandastream`, `socketcanstream`
    (raw `linux/can`, macOS-excluded), `devicestream`. Re-apply the §3.C canproxy escape hatch.
2.3 **Routes** — port upstream HEAD `streams/routes.{cc,h}`, swap `PyDownloader::` → `CommaApi2::`.
    **Delete `utils/api.{cc,h}`.**
2.4 **Widgets** — `binaryview`, `historylog`, `videowidget`, `signalview`, `detailwidget`,
    `messageswidget`, `mainwin` (re-apply the iqdbc menu label), `streamselector`, `commands`,
    `settings`, `cameraview`, `chart/*`, `tools/*`, `utils/{util,export,elidedlabel}`.
2.5 **SConscript** — rebase on upstream; re-apply: non-nested paths, `iqdbc/dbc` +
    `#iqdbc_repo`, `PrettyAction` wrappers, `third_party/json11`, `ffmpeg_libs` from Phase 0.1.
    Qt modules collapse to `Widgets/Gui/Core` (+Charts).
2.6 **Tests** — adopt the Qt-free `tests/test_dbc_core` target; drop `tests/test_runner.cc`.
2.7 **Launcher** — adopt `cabana` bash script + `Program('_cabana')`; de-prefix its scons targets;
    fix `.gitignore` (`cabana` → `_cabana`, `*.generated.qrc`, `bootstrap_icons.cc`).

**Gate (each sub-step):** `scons -u -j8 tools/cabana` clean, no new warnings.

### Phase 3 — konn3kt verification (the part that actually proves the sync)

3.1 Remote-routes dialog against `api-iqlabs.konn3kt.com`: device list populates; all five periods
    (7d / 14d / 30d / 6mo / **Preserved**) return routes with correct start times and durations.
    Preserved uses ISO timestamps, the rest use `*_utc_millis` — both paths must be exercised.
3.2 Open a konn3kt route end-to-end: route-file listing, log download + decompression, qcam/fcam
    video, iqdbc DBC load, chart, CSV export.
3.3 **Remote live CAN:** `canlived` on device → konn3kt relay → `konn3kt_canproxy.py` on laptop →
    Cabana *Live → Device → ZMQ → 127.0.0.1*. Frames must decode. Per prior work this is the
    untested leg of the canlive feature — run it on `gutek-a1`.
3.4 Local live CAN: panda stream, MSGQ device stream, SocketCAN (Linux only).
3.5 larch64 device build, if cabana is still expected to build on-device.

### Phase 4 — plotjuggler (secondary, 14 commits)

Only `juggle.py`, `layouts/`, `README.md` diverge, and the only IQ delta is the `iqdbc.car.fingerprints`
import plus non-nested paths. Cheap; fold in after Phase 3 or skip.

---

## 5. Risks and rules

- **Don't batch Phase 2.** ~40 files change; a single "port everything then build" pass produces an
  unbisectable wall of link errors. One layer, one build.
- **`git add` only ported files.** The tree currently contains built artifacts (`*.o`, `*.a`,
  `moc_*.cc`, `tools/cabana/cabana`, `tools/jotpluggler/jotpluggler`,
  `generated_event_extractors.h`, `generated_dbcs/`). Never `git add -A` here.
- `dbc/car_fingerprint_to_dbc.json` is a tracked build product regenerated by scons — expect churn
  on every build; keep it tracked so cabana doesn't need iqdbc importable at runtime.
- Dropping `Qt5Network/Concurrent/DBus/Xml/SerialBus` changes the larch64 link set; verify the
  device build before assuming the SConscript is done.
- §3.C is the one place where a faithful upstream port actively regresses a konn3kt feature. If
  Phase 3.3 can't be run on hardware in this pass, **do not** land 2.2 with upstream's bridge fork
  as the only ZMQ path.
- Upstream candidate: the `dbc.h` empty-multiplex-indicator guard is a real upstream bug fix worth
  sending back.

## 6. Explicit non-goals

- Adopting upstream's nested `openpilot/` tree layout.
- Migrating iqpilot's replay to `PyDownloader` / `tools/lib` Python downloading.
- Renaming cereal `androidLog` → `operatingSystemLog`.
- Converging on the `comma-deps-*` pip wheels.

---

## Appendix A — cabana commits to port (`bcdeec313..e7b1ee3a5`, 53)

```
4cfdcea1d 2026-07-28 cabana: fix macOS build and --zmq bridge path (#38484)   <- §3.C
6b47a5b6b 2026-07-23 tools: decompress in the python downloader (#38430)      <- §3.A
75d590fb9 2026-07-21 replace catch2 tests for 20% faster builds (#38408)      <- §3.G
e124d6df9 2026-07-19 more dead code gc
a04c045cd 2026-07-17 cabana: de-Qt, part 3 (#38360)                           <- §3.B
5d23a78c7 2026-07-16 cabana: de-Qt, part 2 (#38359)                           <- §3.B
06a73f538 2026-07-16 cabana: de-Qt, part 1 (#38357)                           <- §3.B
39117a587 2026-07-08 remove submodule symlinks (#38312)
f283f6703 2026-07-08 Revert "try removing submodule symlinks (#38310)"
b827c0f55 2026-07-08 try removing submodule symlinks (#38310)
1e49eac4d 2026-07-08 rm libyuv (#38306)                                       <- §3.D
9877f6ac0 2026-07-08 ffmpeg: use shared libraries (#38308)                    <- §3.E
05cf8023a 2026-07-07 fix cabana                                               <- §3.H
c02cf706a 2026-07-07 fix cabana launch script                                 <- §3.H
5edc0bd89 2026-06-21 mv root dirs into nested openpilot (#38219)              <- §1 (de-prefix)
20e0f21b5 2026-06-21 prefix paths with openpilot (#38223)                     <- §1 (de-prefix)
37eda06c9 2026-06-21 move cereal/ into nested openpilot (#38220)              <- §1 (de-prefix)
bfd8d4868 2026-06-06 cabana: fix "seperated" typo in findsignal placeholders (#38142)
5408c86b7 2026-05-28 Cabana: Fixed internal typos and method casing (#38099)
15267e408 2026-05-11 cabana: gitignore generated file                         <- §3.I
bea893820 2026-05-10 use packaged bootstrap icons (#37994)                    <- §3.I
bd1c7f39e 2026-05-07 scons build cleanups (#37981)
0584a5f5e 2026-04-12 add bridge target to cabana run script (#37814)          <- §3.H
31e4fe55a 2026-03-22 tools: setup ffmpeg hwaccel (#37718)
a8b5c7450 2026-03-21 prep for imgui tools (#37712)
240e0036d 2026-03-20 macOS: fix build (#37686)
a68ea44af 2026-03-14 cabana: use vendored libusb from commaai/dependencies (#37681)  <- §3.E
5e7f5dd84 2026-03-14 replay/cabana: remove unused openssl dependency (#37680)
ee9da82aa 2026-03-13 cleanup build paths (#37667)
71290f380 2026-03-08 cabana: gitignore assets.cc                              <- §3.I
e42ee228c 2026-03-08 gitignore cleanups (#37615)
5e1a576f3 2026-03-07 cabana: exclude SocketCAN on macOS (#37553)              <- §3.B
0c452dbaf 2026-03-03 cabana: fix right pane width limitation (#37527)
06b2c68e0 2026-03-01 macOS: fix cabana builds (#37518)
3478ac133 2026-03-01 cabana: remove QtSerialBus (#37523)                      <- §3.B
ce04d25f7 2026-03-01 cabana: remove QtConcurrent (#37522)                     <- §3.B
0c7abf385 2026-03-01 cabana: remove QtXml (#37521)                            <- §3.B
0b9ab8bb9 2026-03-01 cabana: replace Qt types with stdlib (#37519)            <- §3.B (largest)
885658512 2026-02-28 new demo route (#37457)
e7cc70f3f 2026-02-28 consolidate file downloading from C++ to Python (#37497) <- §3.A
276713ddf 2026-02-27 add back bz2 support with vendored bzip2 (#37459)
238fca233 2026-02-25 tools: fix darwin compile errors (#37399)
8810948ec 2026-02-24 CI: ensure no brew (#37387)
76d084d87 2026-02-23 switch to system compilers (GCC on Linux, Apple Clang on macOS) (#37355)
f4a36f7f7 2026-02-22 rm cpp bz2 (#37332)
4bffe422e 2026-02-22 vendor capnproto and ffmpeg via dependencies repo (#37327)  <- §3.E
c98ba4ff4 2026-02-20 Qt is optional (#37295)
037e6e749 2026-02-17 cabana: fix crash when zmq address is used (#37222)
af1583cdf 2026-02-12 Reapply tgwarp w NV12 fix (#37168)
45099e7fc 2026-02-10 Revert tgwarp again (#37161)
667f3bb32 2026-02-07 Revert "revert tg calib and opencl cleanup (#37113)" (#37115)
51312afd3 2026-02-07 revert tg calib and opencl cleanup (#37113)
d5cbb89d8 2026-02-06 Remove all the OpenCL (#37105)
```

## Appendix B — jotpluggler commits to port (`61608db78..e7b1ee3a5`, 6)

```
e7b1ee3a5 2026-08-05 jp: fix segment range parsing
6b47a5b6b 2026-07-23 tools: decompress in the python downloader (#38430)
576de9c7e 2026-07-21 speed up jotpluggler build (#38406)
911f07ee8 2026-07-21 convert tests to unittest (#38387)
fef29ad22 2026-07-19 start porting tests to unittest style (#38384)
3f49e2d33 2026-07-18 jp: add thumbnail source (#38363)
```

## Appendix C — how the baselines were established

Blob-hash matching, not commit archaeology: for each iqpilot file, walk upstream history
newest-first and report the newest commit whose blob for that path is byte-identical. Files with no
match are IQ-modified or IQ-new; the minimum over the untouched files bounds the fork point.

```
cd /tmp/openpilot-upstream
git log --format='%H %ad %s' --date=short -30 -- openpilot/tools/cabana tools/cabana > /tmp/cab_commits.txt
for f in $(cd $LOCAL/tools/cabana && find . -type f \( -name '*.cc' -o -name '*.h' \) -not -name 'moc_*' | sed 's|^\./||' | sort); do
  h=$(git hash-object "$LOCAL/tools/cabana/$f") || continue
  while read -r c d rest; do
    b=$(git rev-parse "$c:openpilot/tools/cabana/$f" 2>/dev/null || git rev-parse "$c:tools/cabana/$f" 2>/dev/null)
    [ "$b" = "$h" ] && { echo "$f -> ${c:0:9} $d $rest"; break; }
  done < /tmp/cab_commits.txt
done
```

Cross-checked against the last upstream-authored commits in iqpilot's own history
(`bcdeec313 Reduce pub-sub memory usage by 10x (#36884)` for cabana) and against feature markers
(`virtual std::string routeName` first appears in `0b9ab8bb9`, 2026-03-01 — absent from iqpilot,
confirming the fork predates it).
