// PocketCoach AI - Public "Try the Demo" Page
// No auth required - pure client-side pose detection + local scoring,
// nothing is sent to the backend or saved anywhere.

let detector = null;
let analyzer = null;
let fpsTimer = null;

const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const sportTypeSelect = document.getElementById('sportType');

startBtn.addEventListener('click', async () => {
    detector = new PoseDetector();
    analyzer = new SportsAnalyzer(sportTypeSelect.value);

    await detector.initialize(
        document.getElementById('webcam'),
        document.getElementById('poseCanvas')
    );

    const success = await detector.startCamera();

    if (success) {
        startBtn.classList.add('hidden');
        stopBtn.classList.remove('hidden');

        detector.setOnResultsCallback(onPoseResults);

        if (fpsTimer) clearInterval(fpsTimer);
        fpsTimer = setInterval(() => {
            document.getElementById('fps').textContent = detector.getFPS();
        }, 1000);

        setStatus('Camera active - detecting pose...', 'alert-success');
    } else {
        setStatus('Unable to access camera. Check browser permissions and try again.', 'alert-error');
    }
});

stopBtn.addEventListener('click', () => {
    if (detector) {
        detector.stopCamera();
        startBtn.classList.remove('hidden');
        stopBtn.classList.add('hidden');
        setStatus('Camera stopped.', 'alert-info');
    }
    if (fpsTimer) {
        clearInterval(fpsTimer);
        fpsTimer = null;
    }
});

sportTypeSelect.addEventListener('change', () => {
    analyzer = new SportsAnalyzer(sportTypeSelect.value);
});

function setStatus(text, alertClass) {
    const el = document.getElementById('landmarkStatus');
    el.textContent = text;
    el.className = `alert ${alertClass}`;
}

function onPoseResults(landmarks) {
    const visibleLandmarks = landmarks.filter((lm) => lm.visibility > 0.5);
    document.getElementById('visibleCount').textContent = visibleLandmarks.length;

    const avgConfidence = landmarks.reduce((sum, lm) => sum + lm.visibility, 0) / landmarks.length;
    document.getElementById('confidence').textContent = `${Math.round(avgConfidence * 100)}%`;

    const analysis = analyzer.analyzeLocally(landmarks, 'Demo');

    const scoreElement = document.getElementById('demoScore');
    scoreElement.textContent = Math.round(analysis.score);
    scoreElement.className = `score-display ${getScoreClass(analysis.score)}`;

    document.getElementById('demoFeedback').innerHTML = analyzer.formatFeedback(analysis.feedback);
}

function getScoreClass(score) {
    if (score >= 90) return 'excellent';
    if (score >= 75) return 'good';
    if (score >= 60) return 'average';
    return 'poor';
}

console.log('Demo page loaded');
