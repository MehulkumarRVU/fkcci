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

let poseDetector = null;
let consecutiveGoodFrames = 0;
let cameraReady = false;

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

    const statusEl = document.getElementById('visibilityStatus');

    if (ratio >= READY_RATIO_THRESHOLD) {
        consecutiveGoodFrames++;
        statusEl.textContent = consecutiveGoodFrames >= CONSECUTIVE_GOOD_FRAMES_REQUIRED
            ? "Looking good! You're ready to start."
            : 'Hold that position...';
    } else {
        consecutiveGoodFrames = 0;
        statusEl.textContent = visibleCount < 4
            ? 'Body not detected. Step back so the camera can see you fully.'
            : 'Move so your shoulders, hips, and knees are all visible.';
    }

    updateReadyButton();
}

function updateReadyButton() {
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
