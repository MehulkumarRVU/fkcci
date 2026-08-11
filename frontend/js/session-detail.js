// PocketCoach AI - Session Detail / Replay Module
const API_URL = 'http://localhost:8080';
requireAuth();

// Mirrors backend/app/pose_engine/shared/utils.py PoseUtils.LANDMARKS - the
// landmark-index -> name mapping isn't otherwise exposed over the API, so
// joint_summary's integer-string keys need this to become human-readable.
const LANDMARK_NAMES = {
    0: 'Nose', 2: 'Left Eye', 5: 'Right Eye', 7: 'Left Ear', 8: 'Right Ear',
    11: 'Left Shoulder', 12: 'Right Shoulder', 13: 'Left Elbow', 14: 'Right Elbow',
    15: 'Left Wrist', 16: 'Right Wrist', 23: 'Left Hip', 24: 'Right Hip',
    25: 'Left Knee', 26: 'Right Knee', 27: 'Left Ankle', 28: 'Right Ankle',
};

function getSessionIdFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const id = params.get('id');
    return id ? parseInt(id, 10) : null;
}

function getSportIcon(sportType) {
    if (sportType === 'table_tennis') return '🏓';
    if (sportType === 'boxing') return '🥊';
    if (sportType === 'badminton') return '🏸';
    return '🏅';
}

function scoreOrNA(value) {
    return value === null || value === undefined ? 'N/A' : Math.round(value);
}

async function loadSessionDetail() {
    const sessionId = getSessionIdFromUrl();
    if (!sessionId) {
        showNotFound();
        return;
    }

    try {
        const response = await fetchWithAuth(`${API_URL}/api/sessions/${sessionId}`);
        if (!response.ok) {
            showNotFound();
            return;
        }
        const session = await response.json();
        renderSession(session);

        document.getElementById('downloadSessionPdfBtn').addEventListener('click', async (e) => {
            const btn = e.currentTarget;
            btn.disabled = true;
            const originalText = btn.textContent;
            btn.textContent = 'Generating...';
            try {
                await downloadFile(`${API_URL}/api/reports/session/${sessionId}/pdf`, `session_${sessionId}_report.pdf`);
            } catch (error) {
                console.error('Error downloading session report:', error);
                alert('Failed to download report');
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
            }
        });

        await loadSessionNotes(session);

    } catch (error) {
        console.error('Error loading session:', error);
        showNotFound();
    }
}

function showNotFound() {
    document.getElementById('loadingState').classList.add('hidden');
    document.getElementById('notFoundState').classList.remove('hidden');
}

function renderSession(session) {
    document.getElementById('loadingState').classList.add('hidden');
    document.getElementById('sessionContent').classList.remove('hidden');

    document.getElementById('sessionTitle').textContent =
        `${getSportIcon(session.sport_type)} ${session.skill_name || session.sport_type} - ${session.session_type.replace('_', ' ')}`;
    document.getElementById('sessionMeta').textContent =
        `${new Date(session.start_time).toLocaleString()} - ${session.duration_minutes} min - ${session.is_completed ? 'Completed' : 'In Progress'} (scoring ${session.scoring_version || 'v1'})`;

    document.getElementById('scorePerformance').textContent = scoreOrNA(session.performance_score);
    document.getElementById('scoreTechnique').textContent = scoreOrNA(session.technique_accuracy);
    document.getElementById('scoreReaction').textContent = scoreOrNA(session.reaction_score);
    document.getElementById('scoreBalance').textContent = scoreOrNA(session.balance_score);

    renderJointBreakdown(session.joint_summary);
    renderAnalysisDetails(session.session_data);
}

function renderJointBreakdown(jointSummary) {
    const container = document.getElementById('jointBreakdownContent');
    if (!jointSummary || Object.keys(jointSummary).length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary);">No per-joint data available for this session.</p>';
        return;
    }

    const rows = Object.entries(jointSummary).map(([landmarkIndex, counts]) => {
        const name = LANDMARK_NAMES[parseInt(landmarkIndex, 10)] || `Landmark ${landmarkIndex}`;
        const total = (counts.low || 0) + (counts.medium || 0) + (counts.high || 0);
        const highPct = total > 0 ? Math.round(((counts.high || 0) / total) * 100) : 0;
        const mediumPct = total > 0 ? Math.round(((counts.medium || 0) / total) * 100) : 0;
        return `
            <div class="flex justify-between align-center" style="padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
                <span>${name}</span>
                <span style="font-size: 0.85rem;">
                    <span style="color: var(--danger-color);">${counts.high || 0} high</span> &middot;
                    <span style="color: var(--warning-color);">${counts.medium || 0} medium</span> &middot;
                    <span style="color: var(--text-secondary);">${counts.low || 0} good</span>
                    ${total > 0 ? `(${highPct}% high, ${mediumPct}% medium)` : ''}
                </span>
            </div>
        `;
    }).join('');

    container.innerHTML = rows;
}

function renderAnalysisDetails(sessionData) {
    const card = document.getElementById('analysisDetailsCard');
    const content = document.getElementById('analysisDetailsContent');
    if (!sessionData || Object.keys(sessionData).length === 0) {
        card.classList.add('hidden');
        return;
    }

    const rows = [];
    if (sessionData.reaction_status) rows.push(['Reaction Status', sessionData.reaction_status]);
    if (sessionData.pose_confidence !== undefined) rows.push(['Pose Confidence', `${Math.round(sessionData.pose_confidence * 100)}%`]);
    if (sessionData.calibration_status) rows.push(['Calibration Engine', sessionData.calibration_status]);
    if (sessionData.frames_analyzed) rows.push(['Frames Analyzed', sessionData.frames_analyzed]);
    if (sessionData.skill_analyzed) rows.push(['Skill Analyzed', sessionData.skill_analyzed]);

    if (rows.length === 0) {
        card.classList.add('hidden');
        return;
    }

    content.innerHTML = rows.map(([label, value]) => `
        <div class="flex justify-between" style="padding: 0.35rem 0;">
            <span style="color: var(--text-secondary);">${label}</span>
            <span>${value}</span>
        </div>
    `).join('');
}

async function loadSessionNotes(session) {
    const threadEl = document.getElementById('sessionNotesThread');
    const sendBtn = document.getElementById('sessionNoteSendBtn');
    const input = document.getElementById('sessionNoteInput');

    async function refresh() {
        try {
            const response = await fetchWithAuth(`${API_URL}/api/notes/athlete/${session.athlete_id}?session_id=${session.id}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const notes = await response.json();

            threadEl.innerHTML = notes.length === 0
                ? '<p style="color: var(--text-secondary);">No notes for this session yet.</p>'
                : notes.map(n => `
                    <div class="note-bubble ${n.is_coach ? 'from-coach' : 'from-athlete'}">
                        <div class="note-meta">${n.author_username} (${n.is_coach ? 'Coach' : 'Athlete'}) - ${new Date(n.created_at).toLocaleString()}</div>
                        <div class="note-message"></div>
                    </div>
                `).join('');

            const bubbles = threadEl.querySelectorAll('.note-message');
            notes.forEach((n, i) => { if (bubbles[i]) bubbles[i].textContent = n.message; });

        } catch (error) {
            console.error('Error loading session notes:', error);
            threadEl.innerHTML = '<p style="color: var(--danger-color);">Failed to load notes.</p>';
        }
    }

    sendBtn.addEventListener('click', async () => {
        const message = input.value.trim();
        if (!message) return;
        sendBtn.disabled = true;
        try {
            const response = await fetchWithAuth(`${API_URL}/api/notes/athlete/${session.athlete_id}`, {
                method: 'POST',
                body: JSON.stringify({ message, session_id: session.id }),
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            input.value = '';
            await refresh();
        } catch (error) {
            console.error('Error posting note:', error);
        } finally {
            sendBtn.disabled = false;
        }
    });

    await refresh();
}

// Show admin link for coaches
document.addEventListener('DOMContentLoaded', () => {
    try {
        const athleteData = localStorage.getItem('athlete');
        if (athleteData) {
            const athlete = JSON.parse(athleteData);
            const adminLink = document.getElementById('adminLink');
            if (adminLink && athlete.role === 'coach') {
                adminLink.style.display = 'block';
            }
        }
    } catch (e) {
        console.error('Error showing admin link:', e);
    }

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            handleUnauthorized();
        });
    }
});

loadSessionDetail();

console.log('Session detail module loaded');
