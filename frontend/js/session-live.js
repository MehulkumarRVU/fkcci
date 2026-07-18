// PocketCoach AI - Live Session Module
const API_URL = 'http://localhost:8080';

requireAuth();

let currentSession = null;
let currentSkill = null;
let poseDetector = null;
let sportsAnalyzer = null;
let sessionStartTime = null;
let sessionTimer = null;
let fpsTimer = null;
let athlete = null;
let sessionType = null;
let analysisFrameCount = 0;

function setCameraStatus(message, isError = false) {
    const statusEl = document.getElementById('cameraStatus');
    if (!statusEl) return;
    statusEl.textContent = message;
    statusEl.style.color = isError ? 'var(--danger-color)' : 'var(--text-secondary)';
}

async function initLiveSession() {
    athlete = JSON.parse(localStorage.getItem('athlete'));
    const activeSessionRaw = sessionStorage.getItem('activeSession');

    if (!athlete || !activeSessionRaw) {
        window.location.href = 'session.html';
        return;
    }

    const activeSession = JSON.parse(activeSessionRaw);
    currentSession = activeSession.session;
    currentSkill = activeSession.skill;
    sessionType = activeSession.sessionType;
    sessionStartTime = activeSession.startedAt || Date.now();

    document.getElementById('logoutBtn').addEventListener('click', (e) => {
        e.preventDefault();
        localStorage.removeItem('token');
        localStorage.removeItem('athlete');
        sessionStorage.removeItem('activeSession');
        window.location.href = 'login.html';
    });

    document.getElementById('endSessionBtn').addEventListener('click', endSession);
    const endSessionBtnSecondary = document.getElementById('endSessionBtnSecondary');
    if (endSessionBtnSecondary) {
        endSessionBtnSecondary.addEventListener('click', endSession);
    }
    document.getElementById('startCameraBtn').addEventListener('click', startCamera);
    document.getElementById('stopCameraBtn').addEventListener('click', stopCamera);
    document.getElementById('startNewSessionBtn').addEventListener('click', () => {
        sessionStorage.removeItem('activeSession');
        window.location.href = 'session.html';
    });

    document.getElementById('currentSkill').textContent = currentSkill.name;
    document.getElementById('currentSessionType').textContent = activeSession.sessionType.replace('_', ' ');
    document.getElementById('techniqueTips').innerHTML = `<p>${currentSkill.technique_tips || 'No tips available'}</p>`;
    document.getElementById('commonMistakes').textContent = currentSkill.common_mistakes || '-';
    document.getElementById('safetyWarning').textContent = currentSkill.safety_warning || 'None';

    const sessionModeMessage = document.getElementById('sessionModeMessage');
    if (sessionModeMessage) {
        sessionModeMessage.textContent = getSessionTypeHint(sessionType);
    }

    poseDetector = new PoseDetector();
    sportsAnalyzer = new SportsAnalyzer(athlete.sport_type, sessionType);

    await poseDetector.initialize(
        document.getElementById('webcam'),
        document.getElementById('poseCanvas')
    );

    startSessionTimer();
    setCameraStatus('Starting camera and pose detection...');
    await startCamera();
}

async function startCamera() {
    if (!poseDetector) return;

    const success = await poseDetector.startCamera();
    if (!success) {
        setCameraStatus('Unable to start camera. Click Start Camera and allow browser permission.', true);
        document.getElementById('startCameraBtn').classList.remove('hidden');
        document.getElementById('stopCameraBtn').classList.add('hidden');
        return;
    }

    document.getElementById('startCameraBtn').classList.add('hidden');
    document.getElementById('stopCameraBtn').classList.remove('hidden');
    setCameraStatus('Camera active. Pose detection is running.');

    poseDetector.setOnResultsCallback(onPoseResults);

    if (fpsTimer) {
        clearInterval(fpsTimer);
    }
    fpsTimer = setInterval(() => {
        document.getElementById('fpsDisplay').textContent = poseDetector.getFPS();
    }, 1000);
}

function stopCamera() {
    if (poseDetector) {
        poseDetector.stopCamera();
    }

    if (fpsTimer) {
        clearInterval(fpsTimer);
        fpsTimer = null;
    }

    document.getElementById('stopCameraBtn').classList.add('hidden');
    document.getElementById('startCameraBtn').classList.remove('hidden');
    setCameraStatus('Camera stopped. Click Start Camera to resume.');
}

function onPoseResults(landmarks) {
    const localAnalysis = sportsAnalyzer.analyzeLocally(landmarks, currentSkill.name);

    updateLiveScore(localAnalysis.score, localAnalysis.score, 0, localAnalysis.score);

    const feedbackPanel = document.getElementById('feedbackPanel');
    feedbackPanel.innerHTML = sportsAnalyzer.formatFeedback(localAnalysis.feedback);

    sportsAnalyzer.addFeedback(localAnalysis.feedback, localAnalysis.score);

    analysisFrameCount++;
    if (analysisFrameCount >= 30) {
        analysisFrameCount = 0;
        sendToBackendForAnalysis(landmarks);
    }
}

async function sendToBackendForAnalysis(landmarks) {
    try {
        const landmarksArray = poseDetector.landmarksToArray(landmarks);

        const response = await fetchWithAuth(`${API_URL}/api/analysis/realtime-feedback`, {
            method: 'POST',
            body: JSON.stringify({
                sport_type: athlete.sport_type,
                skill_name: currentSkill.name,
                landmarks: landmarksArray
            })
        });

        if (response.ok) {
            const analysis = await response.json();
            updateLiveScore(
                analysis.score,
                analysis.technique_accuracy,
                analysis.reaction_score || 0,
                analysis.balance_score
            );

            if (analysis.feedback && analysis.feedback.length > 0) {
                const feedbackPanel = document.getElementById('feedbackPanel');
                feedbackPanel.innerHTML += sportsAnalyzer.formatFeedback(analysis.feedback);
            }
        }
    } catch (error) {
        console.error('Error sending to backend:', error);
    }
}

function handleUnauthorized() {
    localStorage.removeItem('token');
    localStorage.removeItem('athlete');
    localStorage.removeItem('refresh_token');
    sessionStorage.removeItem('activeSession');
    window.location.href = 'login.html';
}

function updateLiveScore(overall, technique, reaction, balance) {
    document.getElementById('liveScore').textContent = Math.round(overall);
    document.getElementById('liveTechnique').textContent = Math.round(technique);
    document.getElementById('liveReaction').textContent = Math.round(reaction);
    document.getElementById('liveBalance').textContent = Math.round(balance);

    const scoreDisplay = document.getElementById('liveScore');
    scoreDisplay.className = 'score-display';
    if (overall >= 90) scoreDisplay.classList.add('excellent');
    else if (overall >= 75) scoreDisplay.classList.add('good');
    else if (overall >= 60) scoreDisplay.classList.add('average');
    else scoreDisplay.classList.add('poor');
}

function startSessionTimer() {
    sessionTimer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - sessionStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        document.getElementById('sessionDuration').textContent =
            `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }, 1000);
}

async function endSession() {
    if (!confirm('Are you sure you want to end this session?')) return;

    stopCamera();

    if (sessionTimer) {
        clearInterval(sessionTimer);
    }

    const durationMinutes = Math.floor((Date.now() - sessionStartTime) / 60000);
    const avgScore = sportsAnalyzer.getAverageScore();

    try {
        const response = await fetchWithAuth(`${API_URL}/api/sessions/${currentSession.id}`, {
            method: 'PUT',
            body: JSON.stringify({
                end_time: new Date().toISOString(),
                duration_minutes: durationMinutes,
                is_completed: true,
                performance_score: avgScore,
                technique_accuracy: avgScore,
                reaction_score: avgScore * 0.9,
                balance_score: avgScore * 0.95
            })
        });

        if (!response.ok) throw new Error('Failed to update session');

        await response.json();
        sessionStorage.removeItem('activeSession');
        window.location.href = 'dashboard.html';
    } catch (error) {
        console.error('Error ending session:', error);
        alert('Failed to save session data');
    }
}

function getSessionTypeHint(sessionType) {
    const hints = {
        drill: 'Drill sessions focus on repetition and technique refinement.',
        shadow: 'Shadow training emphasizes balance and movement without impact.',
        sparring: 'Sparring mode prioritizes guard, reaction, and positioning.',
        match_simulation: 'Match simulation emphasizes intensity and realistic pacing.'
    };
    return hints[sessionType] || 'Perform this session with the correct focus for your chosen mode.';
}

function showSessionSummary(session) {
    document.getElementById('summaryScore').textContent = Math.round(session.performance_score);
    document.getElementById('summaryTechnique').textContent = Math.round(session.technique_accuracy);
    document.getElementById('summaryReaction').textContent = Math.round(session.reaction_score);
    document.getElementById('summaryBalance').textContent = Math.round(session.balance_score);
    document.getElementById('summaryDuration').textContent = session.duration_minutes;

    const scoreDisplay = document.getElementById('summaryScore');
    scoreDisplay.className = 'score-display';
    if (session.performance_score >= 90) scoreDisplay.classList.add('excellent');
    else if (session.performance_score >= 75) scoreDisplay.classList.add('good');
    else if (session.performance_score >= 60) scoreDisplay.classList.add('average');
    else scoreDisplay.classList.add('poor');

    document.getElementById('sessionSummary').classList.remove('hidden');
}

initLiveSession();

console.log('Live session module loaded');
