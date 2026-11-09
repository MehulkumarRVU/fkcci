# Physical Device and Camera Validation Report

Assessment date: 2026-11-08.

No physical Android phone, iPhone, iPad, or desktop webcam was available for
this validation. Device behavior is therefore **NOT TESTED**, not passed.

## Manual test matrix

| Device/browser | Camera access | Permissions | Orientation/background | Full session | Status |
|---|---|---|---|---|---|
| Android phone / Chrome | Front + rear camera | Grant/deny | Rotate, background/resume | Signup through logout | NOT TESTED |
| iPhone / Safari | Front + rear camera | Grant/deny | Rotate, background/resume | Signup through logout | NOT TESTED |
| iPad / Safari | Front + rear camera | Grant/deny | Rotate, background/resume | Signup through logout | NOT TESTED |
| Desktop / Chrome / webcam | Select camera | Grant/deny/disconnect | Resize, reconnect | Signup through logout | NOT TESTED |

## Checklist and evidence to collect

For each device/browser/version and HTTPS origin, record camera initialization
time, achieved FPS, pose-tracking reliability/loss recovery, memory, permission
errors, disconnect recovery, orientation changes, background/resume behavior,
session completion, results persistence, and logout. Try good/poor lighting,
low network, camera in use, denied permissions, and a device rotation while
tracking. Do not record identifiable video without separate consent.

The current frontend calls `getUserMedia`, requests 1280x720, initializes
MediaPipe Pose, tracks reliability state, and stops media tracks on explicit
camera stop. Camera startup/device-specific behavior and recovery on mobile
Safari/Chrome remain to be verified on hardware. Browser camera access requires
HTTPS except localhost.

Status: **NOT TESTED** — checklist prepared; no device result is claimed.
