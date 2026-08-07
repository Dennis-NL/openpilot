# IQ.Pilot User Changelog

This changelog is written for everyday drivers and focuses on what you will notice on the road, as well as changes under-the-hood.

## IQ.Pilot 1.0c


**Navigate on IQ.Pilot**

Navigate on IQ.Pilot is here. Search for a destination, pick from route alternatives, and let IQ.Pilot guide you turn by turn with live rerouting when you miss an exit. Along with on-screen-maps, you can see your position, the route, and upcoming turns all at once without leaving the driving view. Speed, turn, and highway exit handling are route-aware, so IQ.Pilot knows what's coming before you do. Mapbox is included at no cost to you for enhanced online map data and routing. On supported vehicles, Navigate on IQ.Pilot will command turn signals automatically based on the route. Map Curve speed control pulls limit data from OpenStreetMaps when offline and Mapbox when available.

When approaching a highway exit, IQ.Pilot now initiates the lane change toward the exit. If your car has Blind Spot Monitoring (BSM), it can perform the lane change fully automatically, there's no blinker nudge required. Without BSM, you confirm with a brief blinker push and IQ.Pilot takes it from there.

**Speed Limit Control (SLC)**

IQ.Pilot can now read and act on speed limits from your car's dash, Mapbox, TomTom, HERE, (included at no cost to our users!) and offline maps. You pick what mode you want in settings: display only, warn you when you're over, or actually adjust your cruise speed. You also pick which source wins when they disagree (dash, Mapbox, map data, highest, or lowest reported limit). There's a look ahead setting so IQ.Pilot can start reacting to an upcoming speed change before you hit the sign to decelerate to the limit before crossing into the new speed limit. 

SLC can now also raise your cruise speed automatically when the speed limit increases, not just lower it. Toggle "confirm higher speed limit" off to enable this, SLC will adjust up to a higher accepted limit with a small prompt, without any confirmation input needed.

**Camera Alerts (Speed Cameras, Red Light Cameras, and Surveillance / ALPR Cameras)**

IQ.Pilot now detects upcoming speed cameras, red light cameras, and ALPR/surveillance cameras (including Flock Safety cameras) sourced from OpenStreetMap's and alerts you before you reach them. Each camera type has its own toggle so you can pick what you want to be warned about. Speed cameras can also trigger a speed reduction to the limit when detected if enabled. Camera data is sourced from OSM and is updated periodically.

**Direct Flock / ALPR Camera Detection (Bluetooth & WiFi)**

Beyond map data, IQ.Pilot can now spot Flock Safety and similar ALPR cameras directly over the air by their Bluetooth and WiFi signatures as you approach them. Because it's sensing the actual hardware rather than relying on a map, this works anywhere, including fully offline and even for cameras that haven't been mapped yet, so you get a heads-up the moment one is nearby. When IQ.Pilot picks up a camera directly, that live detection takes priority over map data, so you see a single clear "Flock Camera Detected" alert instead of a duplicate. It shares the same Flock camera alert toggle, runs quietly in the background only when that's enabled, and is built to stay out of the way of your Bluetooth (phone link, game controllers) and WiFi connections.

**IQ.Dynamic and Driving Behavior**

In IQ.Dynamic blended mode, when IQ.Pilot sees a stop light ahead, and the model agrees you need to stop, and there's no lead car to track, it will now commit (force) to stopping on its own, no lead car required. Gas pedal overrides it instantly. The stop prediction horizon is adjustable in IQ.Dynamic settings. Behavior for curves, low-speed driving, stopped leads, speed-limit fallbacks, and vision-based stops is now configurable. On-device IQ.Dynamic tuning is accessible by double-tapping IQ.Dynamic in longitudinal mode selection.

Force Stops now include "Smooth Stops" under the same toggle thank's to SpysyWeeb! With Force Stops on, all stops including model predicted stops at signs and lights now use the smooth landing law, so every stop settles gently rather than dropping in hard. The minimum force stop distance slider enforces minimum distance when configured.

IQ.Dynamic on supported Volkswagen platforms including MQB, and PQ now support blending OEM Stock Radar ACC with IQ.Dynamic to allow for a blended longitudinal experience while maintaining E2E IQ.Pilot functionality. 

**Driving Models**

IQ.Pilot updated to a new default driving model, `Pop!`

IQ.Pilot also has the latest bleeding-edge models, as always, including the latest TobyRL model, NoPP model, DeeperRL model, DeepRLv3/4/5 models, OP Model 16 Deep, and all future RL models as they are released.

IQ.Pilot maintains supports for all legacy models like `Notre Dame (v1/3)`, `FarmVille`, `WD40`, etc.

**Dashcam, Live View, and Alerts**

- WebSSH now connects in under 15 seconds and connects the first time, every time.
- Live View in the Konn3kt app now processes full-resolution HDR input from the Comma 4 driver camera for a noticeably sharper, and more accurate picture. Live View performance was optimized, and microphone audio (one way) streaming is now included.
- You can fully disable dashcam recording from the Konn3kt app. Turning it off stops all recording, no logs, no video, no audio, full stop.
- Audible alerts now ramp in volume smoothly instead of cutting in abruptly for enhanced auditory alerts. 
- On-road live streaming, with Two-Way Audio streaming from your IQ.Pilot devices camera feed live through the Konn3kt app. Onroad choppiness fixed, keyframe-on-demand enabled for instant camera switches, and variable network-condition-adaptive bitrate.
- Konn3kt can now take a snapshot from any camera (road, driver, or wide) on-demand, both onroad and offroad, and returns it as a JPEG instantly for a glance. 

**Volkswagen**

Volkswagen support got a significant overhaul:

- Lateral and longitudinal tuning greatly improved.
- Accelerator override behavior now matches stock feel.
- MQB SnG handling improved for supported non-EPB ACC FtS vehicles.
- IQ.Pilot now supports all VW PQ and MQB CC-only and (A)CC-less cars, including CC-only PQ cars without an ADAS gateway.
- Volkswagen Passat B7 (PQ) with TRW450 now supports Stop-and-Go.
- Volkswagen MEB/MQBevo now only go on-road when in Drive and no longer in Park for 15 minutes after parking the car.
- Added Passat (PQ) model year ECU fingerprint.
- Konn3kt can now check EPS compatibility and LKAS coding status on VW MQB vehicles with a comma power. 
- Konn3kt can enable LKAS coding on supported VW MQB vehicles with EPS that didn't ship with factory LKAS with a comma power.
- Volkswagen MQB/PQ now supports full Radar Blending with IQ.Dynamic for an enhanced E2E + Highway experience. (limited by OEM ACC minimum speed)

**Volkswagen MEB and MQBevo**

IQ.Pilot now **officially** supports the Volkswagen MEB and MQBevo platforms! Including the ID.4, ID.3, ID.5, and Golf MK8 through model year 2025, as long as you have a compatible camera or gateway harness. Both LKAS and ACC are supported. This is the foundation of the `release-meb` branch, which is auto-synced from `release` and tailored specifically for these platforms.

**Toyota/Lexus**

Support added for Stop-and-Go and SDSU for Toyota/Lexus vehicles.

**Hyundai/Kia**

Fingerprint coverage expanded to cover more Hyundai/Kia variants that were previously unrecognized, and proper CAN-FD handling for newer HKG.

**UI — Comma 4 (mici)**

The Comma 4's offroad UI has been completely redesigned and has had major performance optimizations, it contains the same settings that BIG UI contains on Comma 3x/3 devices. 

**UI — Comma 3x and Comma 3 (tizi/tici)**

The tizi/tici (Comma 3x and Comma 3) onroad and offroad UI has been fully redesigned as well, matching the new IQ.Pilot design language with a brand new home screen, status bar, settings menu's, and should be a much better experience.

**UI Improvements**

IQ.Pilot's on-road UI got a number of improvements:

- The Steering Assistance border now has a lower portion that distinguishes lateral only engagement from full engagement.
- IQLong Personality can now be cycled on-road by tapping the driver-monitoring icon on BIG UI devices. The icon color reflects the currently selected personality as well as an on screen current profile confirmation. 
- IQLong mode IQ.Standard has been renamed to IQ.Chill to lessen confusion on long modes.
- IQLong mode can now be cycled on-road by tapping the nucleus icon in the top right corner on BIG UI devices. The icon changes to reflect IQ.Chill/Dynamic/Pilot.
- Fixed augmented road view calibration showing invalid calibration data on the model path / tracked lane lines by refreshing the matrix cache correctly for calibration to properly update on startup with Navigation enabled.
- Live Konn3kt accent color sync: whatever color you pick in the Konn3kt app flows to your device UI instantly. 
- Revamped Branch switcher to properly switch branches, and updater has had bugfixes to fix install issues where the device claims to have updated but has not actually updated. 


**IQ.OS 4.9.1**

IQ.OS 4.9.1 is bundled with IQ.Pilot 1.0c. IQ.OS is available for all supported devices: Comma 3, Comma 3x, Comma 4, Konik A1/M, and Mr.One C3/C3 Lite. It's a lightweight OS based on Ubuntu 24.04, includes Bluetooth (BLE), has a much smaller install footprint, and is continuously optimized for IQ.Pilot.

- Konn3kt now stays online regardless of IQ.Pilot's status. If IQ.Pilot fails to boot, Konn3kt remains available so you can switch branches, SSH in, and recover remotely without a physical connection, including over cellular. 
- Bug causing konn3kt setup time on a fresh install dropped from ~30 minutes fixed, setup dropped down to ~10 seconds.
- Automatic LocalAPI configuration in Konn3kt.
- Fixed Upstream Comma 4/3x/3 AGNOS Wi-Fi driver crash causing random crashes while driving. 
- Fixed Comma 4 green-dot-matrix text aliasing issue.
- Fixed Comma 4 display calibration not showing for accurate colors.

**Updater: Pre-download Mode**

A new "Update Install Mode" setting in Software settings gives you control over how updates are applied:

- **Predownload Only** — updates download in the background but wait for you to confirm before installing. 
- **Predownload + Preinstall** — downloads and installs automatically on next boot, as it was before. 

**Konn3kt Services**

Konn3kt's WebApp has migrated to `app.konn3kt.com`

Connection stability between Konn3kt and IQ.Pilot (Konn3ktion) is greatly improved.

**eSIM**

eSIM detection, provisioning, and profile management groundwork is now built into the device. The app can detect whether your device has an embedded SIM, provision it, and manage profiles without a physical SIM swap. eSIM support requires a compatible data plan; Contact IQ.Pilot support in the discord for known working eSIM carriers and plans. Note: eSIM is experimental and generally requires a hotspot-style data plan or an MVNO that does not IMEI filter.

**Additional 1.0c Updates**

**Navigate on IQ.Pilot and Offline Maps**

- Added Home, Work, and Recent destination shortcuts, route cancellation, saved-destination management, and course-up map rotation.
- Added an interactive off-road map with panning and current-location display, plus on-screen maneuver artwork for turns, merges, forks, off-ramps, continuation instructions, and arrival.
- Added navigation-memory handling so important fork and exit guidance remains available when a model output briefly omits it.
- Added full offline routing through a packaged Valhalla runtime. Navigation can now operate without Mapbox or an active internet connection.
- Added simultaneous installation of multiple offline regions, including offline raster tiles for the displayed map as well as routing and road metadata.
- Added separate Online On-Screen Maps and Offline On-Screen Maps controls, resumable regional downloads, combined routing-and-tile download progress, automatic mapd v2 region recognition and missing-data restoration.
- Added a hosted regional tile-bundle service with a fallback source, background tile decoding, and bounded texture caching to keep map work off the UI render path.
- Reduced navigation CPU, GPU, and memory overhead so maps can remain open for long drives without competing with the driving model.

**IQ Speed Assist and Camera Alerts**

- Added the new IQ Speed Assist architecture, with TomTom data alongside dashboard, Mapbox, and offline OpenStreetMap sources.
- Added optional cruise-set-speed mirroring, percentage-based offset zones for low, medium, and higher speed ranges, and earlier, smoother upcoming-speed-limit reactions in the longitudinal cruise envelope.
- Added clearer on-road SLC source, state, pending-limit, and adaptation feedback.
- Added individual controls for speed, red-light, and Flock/ALPR alerts, plus optional speed-camera slowdown using the detected limit and a configurable safety factor.
- Added haptic speed-camera feedback on supported Hyundai, Kia, and Genesis vehicles.

**Construction Zone Assist**

- Added optional camera-based Construction Zone Assist, which detects bright-orange work-zone barrels and markers.
- Added an adjustable work-zone target speed (60 mph by default), plus daylight, road-speed, and active-zone checks to reduce unrelated reflective detections.
- Added lightweight processing designed to run alongside the driving and driver-monitoring models.

**IQ.Dynamic, Stops, and Longitudinal Control**

- Added separate IQ.Dynamic road-speed and lead-speed thresholds, configurable curve, low-speed, slower-lead, stopped-lead, and model-predicted-stop activation, and an adjustable model-stop prediction horizon.
- Added automatic Volkswagen stock-radar set-speed and following-gap synchronization when radar blending is enabled on supported PQ vehicles.
- Added an independent custom stopping-distance adjustment, smoother stopped-lead pull-away, and end-to-end launch assistance when the model predicts an opening path.
- Added dedicated departure chimes for an opening path and a pulling-away lead, Experimental Lead MPC, and end-to-end cruise convergence toward the selected speed as the road opens.
- Added configurable end-to-end set-speed selection using either a preset or the driver’s current target, per-platform stopping overrides, accelerator-override longitudinal control on supported vehicles, and predictive reactions to speed limits and curves.

**Steering, Lane Changes, and Environment View**

- Added an on-road Always-On Lateral control path for supported Hyundai LFA buttons and Bluetooth-controller commands for testing or controlling it in Joystick Mode.
- Added continuous lane changes while the blinker is held, while retaining driver confirmation for subsequent maneuvers.
- Added configurable model-action smoothing, angle-based lateral control, optional VW ALC torque blending, a dedicated Volkswagen PQ HCA7 torque controller, and live-learned curvature correction for supported Volkswagen MEB configurations.
- Added an optional Environment View that can replace the model scene and render 3D object boxes, a ground grid, lane lines, road edges, and the planned path.
- Added a precompiled Qualcomm IQ.Vision model and bandwidth-efficient camera preprocessing to reduce contention with the primary driving model.

**Driving Models and IQModeld**

- Added the unified IQModeld runtime and native bridge for current combined models and legacy split models.
- Added fused vision-and-policy execution for supported supercombo bundles, zero-copy camera-frame handling through the tinygrad runner, and unified combined-artifact, combined-split, fused, tinygrad, and ONNX runner support.
- Added current-model redownload, manifest refresh when published models change, a clear Driving Model Updating state, and engagement gating until the selected model is ready.

**Home, On-Road UI, and Visuals**

- Added dedicated Routes, Navigation, Video, and status surfaces, a selectable home-panel widget, 60 fps off-road BIG UI presentation, and device-specific frame pacing.
- Added Comma 4 anti-aliasing, augmented-road presentation, driver-camera orientation improvements, and an expanded status bar with temperature, vehicle state, Konn3kt status, and connected Wi-Fi network name.
- Added the installed IQ.OS version to Software settings, tappable branch information in the BIG UI header, smooth edge-swipe navigation, transitions, parallax, shadows, animated controls, and a seamless build-spinner-to-UI transition.
- Added a glowing primary-lead orb, IQ.Pilot teal and pink acceleration-bar styling, a top-bar Silent Mode bell, Night Mode display sleep after sunset, and screen recording through Konn3kt.

**Dashcam and Route Viewer**

- Increased qcamera resolution by 5× while balancing storage and upload use.
- Added crash-safe route writes, frequent durable checkpoints, power-loss preservation, and boot-time recovery for incomplete recordings.
- Added an on-device Routes screen with date, duration, camera availability, cloud-upload state, and local, uploading, uploaded, and cloud-only badges.
- Added local playback of road, wide, and driver video with synchronized audio; cloud-only route discovery and streaming through Konn3kt; and synchronized telemetry, model path, steering angle, driver-monitoring, vehicle speed, and cruise-set-speed overlays.
- Added qlog-only route visualization, fullscreen playback, auto-hiding controls, loading feedback, scrubbing, fast-forward speeds, hardware HEVC decode, local-time presentation, bounded playback buffering, and screen-awake behavior during playback.

**Live View, Audio, and WebSSH**

- Added a Live View indicator on the driving screen, dual-camera picture-in-picture streaming, and live model-path overlay while both the device and Konn3kt use cellular.
- Added instant keyframe requests, network-adaptive encoder bitrate, and full-resolution HDR driver-camera input on Comma 4.

**Konn3kt Services, Bluetooth, and Backup**

- Added independent device services that stay available when IQ.Pilot is stopped or cannot enter its main UI, including OS-level recovery over Wi-Fi and cellular.
- Added a dedicated `iquploaderd` route-and-log uploader, automatic IQ.Pilot crash-log uploads, Volkswagen and Tesla odometer display, backup-and-restore services, encrypted backup archives, backup status, and Konn3kt RPC support for compatible Volkswagen coding and diagnostics.
- Added direct Bluetooth Low Energy control across comma 3, comma 3X, comma 4, Konik, and Mr.One hardware, including authenticated requests, replay protection, settings synchronization, automatic discovery and pairing, and fallback when internet connectivity is unavailable.
- Added BLE control for supported IQ.Pilot, vehicle, display, network, navigation, and driving settings; live propagation to active services; and setup-stage Wi-Fi scanning, Wi-Fi connection, network status, channel selection, install start, setup progress, and installation status.

**Volkswagen PQ and MQB**

- Added Always-On Lateral for ECAN, non-ECAN/ACAN, CC-only, and CC-less PQ configurations; SEAT Alhambra TRW460i Stop-and-Go with automatic resume; and Stop-and-Go for additional electronic-parking-brake configurations.
- Added MQB-A0 automatic resume and steering-lockout options, standstill handling for supported non-EPB ACC vehicles, and ACC-command suppression while braking.
- Added dedicated PQ radar engagement, cancellation, set-speed, acceleration, and following-gap management; automatic PQ EPS-patch detection; and patch-aware minimum-steering-speed handling.
- Added a PQ firmware tool with backup, dump upload, patch detection, programming, and recovery; persistent PQ LKAS coding over TP2.0/KWP; model-year ECU fingerprinting; expanded Passat identification; distance-button mapping; dashboard personality presentation; and continued MQB lateral control while cruise is faulted.
- Added stock lateral handoff when IQ.Pilot lateral is inactive, explicit Volkswagen readiness handling, and Volkswagen odometer persistence with cloud backup.

**Platform Support**

- Added MEB/MQBevo steering ratios, steering behavior, zero-speed steering where supported, ACC-HUD handling, and Drive/Park state handling. Supported configurations include ID.3, ID.4, ID.5, and Golf Mk8 through model year 2025.
- Added Honda-specific final-stopping deceleration control, Subaru Creep from Standstill, and guarded Tesla vehicle-bus parsing for supported harnesses.
- Added more Hyundai/Kia/Genesis CAN-FD and HDA2 handling, radar-track and corner-radar controls, Camera SCC and platform-specific cruise controls, Auto Cruise Control and Auto Engage, custom steering and steering-rate controls, lane-change steering-rate controls, and expanded parameter/fingerprint diagnostics.

**IQ.OS, Power, Network, and Recovery**

- Updated the bundled platform to IQ.OS 4.9.1, with device-specific boot and display support, Comma 4 display calibration, HDR camera and display-color support, USB 3 logging, USB link-error recovery, 2 GB compressed zram swap, and consistent startup runtime packaging.
- Added FastSleep deep standby, including five-minute idle entry after parking, low-voltage entry, staged voltage shutdown thresholds, suspension of high-power services, Konn3kt recovery connectivity during standby, voltage-aware power decisions, and immediate wake on ignition or charging.
- Added zero-touch Bluetooth onboarding, Konn3kt pairing-code presentation, IQ.OS update confirmation, Bluetooth game-controller support for Joystick Mode, and Bluetooth operation independent of the main IQ.Pilot process.
- Added a redesigned Network settings experience, explicit Wi-Fi Disconnect, cellular reconnection after APN changes, Comma 3X SIM electrical-probe recovery, and QR/manual eSIM activation with profile listing, refresh, enable, disable, and deletion.
- Added Force On-Road for a temporary ten-minute parked diagnostic session, an Update & Reboot recovery-screen action, and USB Storage mode.

**Updater, Reliability, and Performance**

- Added Konn3kt confirmation before IQ.OS updates, interrupted submodule/artifact-preparation recovery, precompiled release preparation for comma 3, comma 3X, and comma 4, and crash-screen update-and-reboot without entering the full UI.
- Added independent model, navigation, map, uploader, backup, and perception services; navigation/map recovery that does not block engagement; power-state coordination; startup parameter ownership and permission normalization; message-queue dead-reader cleanup; lower shared-memory use; and clearer build, process-state, and diagnostic output.
