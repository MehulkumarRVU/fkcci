// PocketCoach AI - Camera & Equipment Pre-Session Check
const API_URL = 'http://localhost:8080';

requireAuth();

// Same 10 key landmarks + 0.5 visibility threshold used by
// sports-analyzer.js's analyzeLocally() local visibility check, kept
// consistent rather than reinvented.
const KEY_LANDMARK_INDICES = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26];
const VISIBILITY_THRESHOLD = 0.5;
const READY_RATIO_THRESHOLD = 0.8;
const CONSECUTIVE_GOOD_FRAMES_REQUIRED = 15;

const AUTO_START_GRACE_MS = 1500;

let poseDetector = null;
let consecutiveGoodFrames = 0;
let consecutivePerfectFrames = 0;
let cameraReady = false;
let autoStartTriggered = false;

async function initPrecheck() {
    const activeSessionRaw = sessionStorage.getItem('activeSession');
    if (!activeSessionRaw) {
        window.location.href = 'session.html';
        return;
    }

    document.getElementById('logoutBtn').addEventListener('click', (e) => {
        e.preventDefault();
        localStorage.removeItem('token');
        localStorage.removeItem('athlete');
        sessionStorage.removeItem('activeSession');
        window.location.href = 'login.html';
    });

    document.getElementById('startCameraBtn').addEventListener('click', startCamera);
    document.getElementById('readyBtn').addEventListener('click', () => {
        window.location.href = 'session-live.html';
    });

    const toggleIsolateBtn = document.getElementById('toggleIsolateBtn');
    if (toggleIsolateBtn) {
        toggleIsolateBtn.addEventListener('click', () => {
            const enabled = !poseDetector.isolateSubject;
            poseDetector.setIsolateSubject(enabled);
            toggleIsolateBtn.textContent = enabled
                ? '🫥 Isolate Subject: On'
                : '🫥 Isolate Subject (Hide Background)';
        });
    }

    poseDetector = new PoseDetector();
    await poseDetector.initialize(
        document.getElementById('webcam'),
        document.getElementById('poseCanvas')
    );
    poseDetector.setOnResultsCallback(onPoseResults);
}

async function startCamera() {
    const startBtn = document.getElementById('startCameraBtn');
    startBtn.disabled = true;
    startBtn.textContent = 'Starting...';

    const started = await poseDetector.startCamera();

    if (!started) {
        startBtn.disabled = false;
        startBtn.textContent = 'Start Camera';
        showTroubleshooting('Unable to access your camera. Check that camera permissions are granted to this site, and that no other app is using the camera.');
        return;
    }

    cameraReady = true;
    startBtn.textContent = 'Camera Running';
    document.getElementById('visibilityStatus').textContent = 'Position yourself so your full body is visible...';
    hideTroubleshooting();

    startFpsPolling();
}

function startFpsPolling() {
    setInterval(() => {
        if (!poseDetector || !poseDetector.isRunning) return;
        document.getElementById('fpsDisplay').textContent = poseDetector.getFPS();
        const video = document.getElementById('webcam');
        if (video.videoWidth) {
            document.getElementById('resolutionDisplay').textContent = `${video.videoWidth}x${video.videoHeight}`;
        }
    }, 500);
}

function onPoseResults(landmarks) {
    const visibleCount = KEY_LANDMARK_INDICES.filter(idx =>
        landmarks[idx] && landmarks[idx].visibility > VISIBILITY_THRESHOLD
    ).length;
    const ratio = visibleCount / KEY_LANDMARK_INDICES.length;
    const percent = Math.round(ratio * 100);

    const progressEl = document.getElementById('visibilityProgress');
    progressEl.style.width = `${percent}%`;
    progressEl.textContent = `${percent}%`;
    progressEl.style.backgroundColor = ratio >= READY_RATIO_THRESHOLD ? 'var(--success-color, #22c55e)' : '';

    if (ratio >= READY_RATIO_THRESHOLD) {
        consecutiveGoodFrames++;
    } else {
        consecutiveGoodFrames = 0;
    }

    if (ratio === 1) {
        consecutivePerfectFrames++;
    } else {
        consecutivePerfectFrames = 0;
    }

    // Once auto-start has fired, leave its message and the disabled
    // button alone - later frames (which keep arriving during the grace
    // period) would otherwise overwrite the "starting automatically"
    // message back to the regular ready/hold-position text.
    if (autoStartTriggered) return;

    const statusEl = document.getElementById('visibilityStatus');
    if (ratio >= READY_RATIO_THRESHOLD) {
        statusEl.textContent = consecutiveGoodFrames >= CONSECUTIVE_GOOD_FRAMES_REQUIRED
            ? "Looking good! You're ready to start."
            : 'Hold that position...';
    } else {
        statusEl.textContent = visibleCount < 4
            ? 'Body not detected. Step back so the camera can see you fully.'
            : 'Move so your shoulders, hips, and knees are all visible.';
    }

    if (consecutivePerfectFrames >= CONSECUTIVE_GOOD_FRAMES_REQUIRED) {
        triggerAutoStart();
        return;
    }

    updateReadyButton();
}

function triggerAutoStart() {
    autoStartTriggered = true;
    const statusEl = document.getElementById('visibilityStatus');
    statusEl.textContent = 'Perfect visibility — starting automatically…';

    const readyBtn = document.getElementById('readyBtn');
    readyBtn.textContent = 'Starting automatically…';
    readyBtn.disabled = true;

    setTimeout(() => {
        window.location.href = 'session-live.html';
    }, AUTO_START_GRACE_MS);
}

function updateReadyButton() {
    if (autoStartTriggered) return;

    const readyBtn = document.getElementById('readyBtn');
    const isReady = cameraReady && consecutiveGoodFrames >= CONSECUTIVE_GOOD_FRAMES_REQUIRED;

    readyBtn.disabled = !isReady;
    if (!cameraReady) {
        readyBtn.textContent = 'Start your camera first';
    } else if (!isReady) {
        readyBtn.textContent = 'Waiting for clear view...';
    } else {
        readyBtn.textContent = "I'm Ready - Start Session";
    }
}

function showTroubleshooting(message) {
    const card = document.getElementById('troubleshootingCard');
    document.getElementById('troubleshootingMessage').textContent = message;
    card.classList.remove('hidden');
}

function hideTroubleshooting() {
    document.getElementById('troubleshootingCard').classList.add('hidden');
}

initPrecheck();

console.log('Session precheck module loaded');
