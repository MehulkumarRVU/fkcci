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
let skeleton3D = null;
let isPaused = false;
let pausedAccumulatedMs = 0;
let pauseStartedAt = null;
let repCounter = null;
let audioCoachingEnabled = false;
let lastSpokenText = null;
let lastSpokenAt = 0;
const AUDIO_MIN_GAP_MS = 4000;

// Live score display is driven only by real backend analysis (never the
// client-side "immediate feedback" heuristic, which starts at 100 and only
// subtracts for detected problems - a neutral idle pose triggers no
// problem checks and so reads as a high score despite no real technique
// having been performed). A small rolling window of the last few backend
// responses is averaged before display too, since single frames are noisy
// (MediaPipe landmark jitter can flip a threshold check frame to frame)
// and looked like "random numbers" without it.
const LIVE_SCORE_WINDOW = 5;
const LIVE_SCORE_MIN_SAMPLES = 2;
let liveScoreSamples = { overall: [], technique: [], reaction: [], balance: [] };

// Warn before an accidental tab close/refresh loses an in-progress
// session - no per-frame data is persisted to the backend mid-session, so
// a hard refresh would lose the in-memory score/pose buffers.
window.addEventListener('beforeunload', (e) => {
    if (sessionStorage.getItem('activeSession')) {
        e.preventDefault();
        e.returnValue = '';
    }
});

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
    document.getElementById('pauseBtn').addEventListener('click', togglePause);
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
    sportsAnalyzer = new SportsAnalyzer(athlete.sport_type, sessionType, athlete.dominant_hand, athlete.skill_level);
    skeleton3D = new Skeleton3D(document.getElementById('skeleton3dContainer'));

    repCounter = new RepCounter(athlete.sport_type, currentSkill.name, athlete.dominant_hand);
    repCounter.setTargetReps(activeSession.targetReps || null);
    if (repCounter.hasCounter()) {
        document.getElementById('liveCountCard').classList.remove('hidden');
        document.getElementById('liveCountLabel').textContent = repCounter.getLabel();
        updateLiveCountDisplay();
    }

    const toggle3dBtn = document.getElementById('toggle3dBtn');
    if (toggle3dBtn) {
        toggle3dBtn.addEventListener('click', toggle3dView);
    }

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

    const toggleAudioBtn = document.getElementById('toggleAudioBtn');
    if (toggleAudioBtn) {
        toggleAudioBtn.addEventListener('click', toggleAudioCoaching);
    }

    await poseDetector.initialize(
        document.getElementById('webcam'),
        document.getElementById('poseCanvas')
    );

    startSessionTimer();
    setCameraStatus('Starting camera and pose detection...');
    await startCamera();
}

async function toggle3dView() {
    const toggle3dBtn = document.getElementById('toggle3dBtn');
    const videoEl = document.getElementById('webcam');
    const canvasEl = document.getElementById('poseCanvas');

    if (skeleton3D.isActive()) {
        skeleton3D.hide();
        videoEl.style.display = '';
        canvasEl.style.display = '';
        toggle3dBtn.textContent = '🧍 Show Digital Twin (3D Skeleton)';
        return;
    }

    toggle3dBtn.disabled = true;
    toggle3dBtn.textContent = 'Loading 3D view...';
    try {
        await skeleton3D.init();
        videoEl.style.display = 'none';
        canvasEl.style.display = 'none';
        skeleton3D.show();
        toggle3dBtn.textContent = '📷 Show Camera View';
    } catch (error) {
        console.error('Failed to load 3D skeleton view:', error);
        alert('Could not load the 3D Digital Twin view.');
        toggle3dBtn.textContent = '🧍 Show Digital Twin (3D Skeleton)';
    } finally {
        toggle3dBtn.disabled = false;
    }
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

function togglePause() {
    if (isPaused) {
        resumeSession();
    } else {
        pauseSession();
    }
}

function pauseSession() {
    isPaused = true;
    pauseStartedAt = Date.now();

    if (sessionTimer) {
        clearInterval(sessionTimer);
        sessionTimer = null;
    }

    document.getElementById('pauseBtn').textContent = '▶️ Resume';
    const badge = document.getElementById('pausedBadge');
    badge.classList.remove('hidden');
    badge.style.display = 'flex';
    setCameraStatus('Session paused. Analysis and scoring are on hold.');

    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
    }
}

function resumeSession() {
    isPaused = false;
    if (pauseStartedAt) {
        pausedAccumulatedMs += Date.now() - pauseStartedAt;
        pauseStartedAt = null;
    }

    startSessionTimer();

    document.getElementById('pauseBtn').textContent = '⏸️ Pause';
    const badge = document.getElementById('pausedBadge');
    badge.classList.add('hidden');
    badge.style.display = 'none';
    setCameraStatus('Camera active. Pose detection is running.');
}

function toggleAudioCoaching() {
    audioCoachingEnabled = !audioCoachingEnabled;
    const btn = document.getElementById('toggleAudioBtn');
    btn.textContent = audioCoachingEnabled ? '🔊 Audio Coaching: On' : '🔊 Audio Coaching: Off';
    if (!audioCoachingEnabled && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
    }
}

// Speaks the top feedback message, throttled so it doesn't chatter
// constantly given analysis runs multiple times per second: only speaks
// when the message actually changed and at most once per
// AUDIO_MIN_GAP_MS.
function speakFeedback(feedbackList) {
    if (!audioCoachingEnabled || !feedbackList || feedbackList.length === 0) return;
    if (!('speechSynthesis' in window)) return;

    const text = feedbackList[0].replace(/[\u{1F300}-\u{1FAFF}☀-➿]/gu, '').trim();
    if (!text) return;

    const now = Date.now();
    if (text === lastSpokenText || now - lastSpokenAt < AUDIO_MIN_GAP_MS) return;

    lastSpokenText = text;
    lastSpokenAt = now;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(new SpeechSynthesisUtterance(text));
}

function onPoseResults(landmarks) {
    if (isPaused) return;

    const localAnalysis = sportsAnalyzer.analyzeLocally(landmarks, currentSkill.name);

    // Feedback tips (text) are still shown instantly - they're just
    // pass/fail hints, not a fabricated accuracy percentage. The numeric
    // score display is driven only by real backend analysis; see
    // sendToBackendForAnalysis().
    const feedbackPanel = document.getElementById('feedbackPanel');
    feedbackPanel.innerHTML = sportsAnalyzer.formatFeedback(localAnalysis.feedback);
    speakFeedback(localAnalysis.feedback);

    sportsAnalyzer.addFeedback(localAnalysis.feedback, localAnalysis.score);

    // Purely additive - doesn't touch the existing 2D drawing/local-analysis
    // path above, and no-ops until the user toggles the 3D view on.
    if (skeleton3D && skeleton3D.isActive()) {
        skeleton3D.updateFromLandmarks(landmarks);
    }

    if (repCounter && repCounter.hasCounter()) {
        repCounter.update(landmarks);
        updateLiveCountDisplay();
    }

    // Downsampled buffer used at session end for a real, backend-computed
    // technique/balance/reaction analysis of the whole session (not just a
    // client-side running average).
    sportsAnalyzer.addPoseSample(poseDetector.landmarksToArray(landmarks), Date.now());

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
            // The session may have been paused while this request was in
            // flight - discard a late response rather than updating the
            // score/feedback panel after the UI already shows "paused".
            if (isPaused) return;

            const analysis = await response.json();
            sportsAnalyzer.addServerResult(analysis);
            recordLiveScoreSample(analysis.score, analysis.technique_accuracy, analysis.reaction_score, analysis.balance_score);

            // Ideal-form overlay: color-codes the 3D skeleton's joints from
            // the backend's own deviation classification (reuses the
            // analyzer's real thresholds - not a second parallel JS copy).
            if (skeleton3D && skeleton3D.isActive() && analysis.deviations) {
                skeleton3D.renderDeviation(analysis.deviations);
            }

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

function updateLiveCountDisplay() {
    const valueEl = document.getElementById('liveCountValue');
    const bannerEl = document.getElementById('goalReachedBanner');
    const count = repCounter.getCount();

    valueEl.textContent = repCounter.targetReps !== null ? `${count} / ${repCounter.targetReps}` : count;

    if (repCounter.goalReached()) {
        bannerEl.classList.remove('hidden');
    }
}

function rollingAverage(samples, newValue) {
    if (typeof newValue === 'number') {
        samples.push(newValue);
        if (samples.length > LIVE_SCORE_WINDOW) samples.shift();
    }
    if (samples.length === 0) return null;
    return samples.reduce((a, b) => a + b, 0) / samples.length;
}

// Feeds one real backend analysis result into the rolling window and
// updates the live display once there's enough signal to show a number
// that isn't just a single noisy frame.
function recordLiveScoreSample(overall, technique, reaction, balance) {
    const smoothedOverall = rollingAverage(liveScoreSamples.overall, overall);
    const smoothedTechnique = rollingAverage(liveScoreSamples.technique, technique);
    const smoothedReaction = rollingAverage(liveScoreSamples.reaction, reaction ?? null);
    const smoothedBalance = rollingAverage(liveScoreSamples.balance, balance);

    if (liveScoreSamples.overall.length < LIVE_SCORE_MIN_SAMPLES) {
        document.getElementById('liveScoreStatus').textContent =
            `Analyzing your form... (${liveScoreSamples.overall.length}/${LIVE_SCORE_MIN_SAMPLES})`;
        return;
    }

    document.getElementById('liveScoreStatus').textContent = '';
    updateLiveScore(smoothedOverall, smoothedTechnique, smoothedReaction, smoothedBalance);
}

function updateLiveScore(overall, technique, reaction, balance) {
    document.getElementById('liveScore').textContent = Math.round(overall);
    document.getElementById('liveTechnique').textContent = Math.round(technique);
    document.getElementById('liveReaction').textContent = reaction === null ? 'N/A' : Math.round(reaction);
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
        const elapsed = Math.floor((Date.now() - sessionStartTime - pausedAccumulatedMs) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        document.getElementById('sessionDuration').textContent =
            `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }, 1000);
}

async function endSession() {
    if (!confirm('Are you sure you want to end this session?')) return;

    stopCamera();

    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
    }

    if (sessionTimer) {
        clearInterval(sessionTimer);
    }

    // Fold in any pause still in progress so it isn't dropped from the
    // excluded-time total when ending while paused.
    if (isPaused && pauseStartedAt) {
        pausedAccumulatedMs += Date.now() - pauseStartedAt;
        pauseStartedAt = null;
    }

    const durationMinutes = Math.floor((Date.now() - sessionStartTime - pausedAccumulatedMs) / 60000);
    const avgScore = sportsAnalyzer.getAverageScore();

    // Fallback values from real per-response server measurements tracked
    // throughout the session (used only if the full-session analysis below
    // can't run, e.g. an empty buffer or a network error) - never a
    // fabricated multiplier of one client-side average.
    const avgTechnique = sportsAnalyzer.getAverageTechnique();
    const avgBalance = sportsAnalyzer.getAverageBalance();

    let sessionUpdate = {
        end_time: new Date().toISOString(),
        duration_minutes: durationMinutes,
        is_completed: true,
        performance_score: avgScore,
        technique_accuracy: avgTechnique !== null ? avgTechnique : avgScore,
        balance_score: avgBalance !== null ? avgBalance : avgScore
    };

    // Full-session analysis: temporal smoothing, low-confidence frame
    // rejection, and a real event-based reaction_score (or an honest
    // "not_measured"/"insufficient_data" status instead of a guess).
    let serverDetailedCounts = null;
    const poseBuffer = sportsAnalyzer.getPoseBuffer();
    if (poseBuffer.length > 0) {
        try {
            const response = await fetchWithAuth(`${API_URL}/api/analysis/analyze`, {
                method: 'POST',
                body: JSON.stringify({
                    sport_type: athlete.sport_type,
                    skill_name: currentSkill.name,
                    pose_data: poseBuffer,
                    session_id: currentSession.id
                })
            });
            if (response.ok) {
                const analysis = await response.json();
                if (analysis.supported && analysis.overall_score !== null) {
                    sessionUpdate = {
                        ...sessionUpdate,
                        performance_score: analysis.overall_score,
                        technique_accuracy: analysis.technique_accuracy,
                        balance_score: analysis.balance_score,
                        // null when reaction_status isn't "measured" - stored
                        // as an honest missing value, never a fabricated number.
                        reaction_score: analysis.reaction_score,
                        session_data: {
                            reaction_status: analysis.reaction_status,
                            pose_confidence: analysis.pose_confidence,
                            calibration_status: analysis.calibration_status
                        },
                        joint_summary: (analysis.detailed_analysis && analysis.detailed_analysis.joint_deviation_summary) || null
                    };
                    serverDetailedCounts = (analysis.detailed_analysis && analysis.detailed_analysis.detailed) || null;
                } else if (analysis.supported === false) {
                    console.warn('Session analysis not supported for this sport:', analysis.reason);
                }
            }
        } catch (error) {
            console.warn('Full-session analysis failed, using running averages instead:', error);
        }
    }

    try {
        const response = await fetchWithAuth(`${API_URL}/api/sessions/${currentSession.id}`, {
            method: 'PUT',
            body: JSON.stringify(sessionUpdate)
        });

        if (!response.ok) throw new Error('Failed to update session');

        const savedSession = await response.json();
        sessionStorage.removeItem('activeSession');
        showSessionSummary(savedSession, serverDetailedCounts);
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

function showSessionSummary(session, serverDetailedCounts) {
    document.getElementById('summaryScore').textContent = Math.round(session.performance_score);
    document.getElementById('summaryTechnique').textContent = Math.round(session.technique_accuracy);
    document.getElementById('summaryReaction').textContent =
        session.reaction_score === null || session.reaction_score === undefined ? 'N/A' : Math.round(session.reaction_score);
    document.getElementById('summaryBalance').textContent = Math.round(session.balance_score);
    document.getElementById('summaryDuration').textContent = session.duration_minutes;

    const scoreDisplay = document.getElementById('summaryScore');
    scoreDisplay.className = 'score-display';
    if (session.performance_score >= 90) scoreDisplay.classList.add('excellent');
    else if (session.performance_score >= 75) scoreDisplay.classList.add('good');
    else if (session.performance_score >= 60) scoreDisplay.classList.add('average');
    else scoreDisplay.classList.add('poor');

    // Server-authoritative rep/combo/jump count, computed from the exact
    // same session pose buffer as the live client-side count - shown as
    // the "official" number, with the live count alongside it for
    // transparency about how closely the two matched during the session.
    if (repCounter && repCounter.hasCounter() && serverDetailedCounts) {
        const countKeyByMode = {
            squat: 'estimated_reps',
            pushup: 'estimated_reps',
            combo: 'combination_count',
            jump: 'estimated_jumps'
        };
        const serverCount = serverDetailedCounts[countKeyByMode[repCounter.mode]];
        if (serverCount !== undefined) {
            document.getElementById('summaryCountLabel').textContent = repCounter.getLabel().replace(/^\S+\s/, '');
            document.getElementById('summaryFinalCount').textContent = serverCount;
            document.getElementById('summaryLiveCount').textContent = repCounter.getCount();
            document.getElementById('summaryCountRow').classList.remove('hidden');
        }
    }

    document.getElementById('sessionSummary').classList.remove('hidden');
}

initLiveSession();

console.log('Live session module loaded');
