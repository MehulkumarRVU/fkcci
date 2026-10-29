// PocketCoach AI - Dashboard Module
// Previously this logic lived in an inline <script> block inside
// dashboard.html that was never properly closed before a second
// <script src="../js/auth-utils.js"> tag - the browser's HTML parser treats
// the literal "</script>" text as closing the first script wherever it
// appears, so that second include never registered as a real script tag.
// Extracted into its own file (matching every other page's pattern) and fixed.

const API_URL = window.POCKETCOACH_API_URL || (
    window.location.port === '3000' || window.location.port === '5500'
        ? `${window.location.protocol}//${window.location.hostname}:8080`
        : ''
);
requireAuth();

// Logout functionality
document.getElementById('logoutBtn').addEventListener('click', (e) => {
    e.preventDefault();
    handleUnauthorized();
});

// Load dashboard data
async function loadDashboard() {
    try {
        const athlete = JSON.parse(localStorage.getItem('athlete'));

        // Show admin link for coaches
        if (athlete && athlete.role === 'coach') {
            const adminLink = document.getElementById('adminLink');
            if (adminLink) {
                adminLink.style.display = 'block';
            }
        }

        // Display athlete info
        if (!athlete) {
            window.location.href = 'login.html';
            return;
        }

        document.getElementById('athleteName').textContent = athlete.username;
        const sportDisplay = getSportDisplay(athlete.sport_type);
        document.getElementById('athleteSport').textContent = sportDisplay;

        // Load session stats
        const statsResponse = await fetchWithAuth(`${API_URL}/api/sessions/stats/summary`);
        if (!statsResponse.ok) {
            throw new Error('Failed to load session stats');
        }
        const stats = await statsResponse.json();

        // Update stats
        document.getElementById('totalSessions').textContent = stats.total_sessions;
        document.getElementById('totalMinutes').textContent = stats.total_minutes;
        const scoreOrNA = (value) => value === null || value === undefined ? 'N/A' : value;
        document.getElementById('avgPerformance').textContent = scoreOrNA(stats.average_performance);
        document.getElementById('avgTechnique').textContent = scoreOrNA(stats.average_technique);
        // average_reaction is honestly null when no session in the summary
        // window had a measured reaction score - show "N/A" rather than
        // rendering the literal string "null" or coercing it to 0.
        const reactionDisplay = stats.average_reaction === null || stats.average_reaction === undefined
            ? 'N/A' : stats.average_reaction;
        document.getElementById('reactionScore').textContent = reactionDisplay;
        document.getElementById('balanceScore').textContent = scoreOrNA(stats.average_balance);

        // Update progress bars
        const reactionPct = stats.average_reaction === null || stats.average_reaction === undefined ? 0 : stats.average_reaction;
        document.getElementById('reactionProgress').style.width = `${reactionPct}%`;
        document.getElementById('reactionProgress').textContent =
            stats.average_reaction === null || stats.average_reaction === undefined ? 'N/A' : `${reactionPct}%`;
        const balancePct = stats.average_balance === null || stats.average_balance === undefined ? 0 : stats.average_balance;
        document.getElementById('balanceProgress').style.width = `${balancePct}%`;
        document.getElementById('balanceProgress').textContent =
            stats.average_balance === null || stats.average_balance === undefined ? 'N/A' : `${balancePct}%`;

        // Apply score colors
        if (stats.average_performance !== null && stats.average_performance !== undefined) {
            applyScoreColor('avgPerformance', stats.average_performance);
        }
        if (stats.average_reaction !== null && stats.average_reaction !== undefined) {
            applyScoreColor('reactionScore', stats.average_reaction);
        }
        if (stats.average_balance !== null && stats.average_balance !== undefined) {
            applyScoreColor('balanceScore', stats.average_balance);
        }

        // Load recent sessions
        await loadRecentSessions();

        // Load available skills
        await loadAvailableSkills(athlete.sport_type);

        // Load streak + achievements
        await loadGamification();

        // Load notes thread, only if this athlete has an assigned coach
        if (athlete.coach_id) {
            document.getElementById('coachNotesCard').classList.remove('hidden');
            await loadDashboardNotes(athlete.id);
        }

    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

async function loadDashboardNotes(athleteId) {
    const threadEl = document.getElementById('dashboardNotesThread');
    const sendBtn = document.getElementById('dashboardNoteSendBtn');
    const input = document.getElementById('dashboardNoteInput');
    if (!threadEl) return;

    async function refresh() {
        try {
            const response = await fetchWithAuth(`${API_URL}/api/notes/athlete/${athleteId}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const notes = await response.json();

            threadEl.innerHTML = notes.length === 0
                ? '<p style="color: var(--text-secondary);">No notes yet.</p>'
                : notes.map(n => `
                    <div class="note-bubble ${n.is_coach ? 'from-coach' : 'from-athlete'}">
                        <div class="note-meta">${n.author_username} (${n.is_coach ? 'Coach' : 'You'}) - ${new Date(n.created_at).toLocaleString()}</div>
                        <div class="note-message"></div>
                    </div>
                `).join('');

            const bubbles = threadEl.querySelectorAll('.note-message');
            notes.forEach((n, i) => { if (bubbles[i]) bubbles[i].textContent = n.message; });

            threadEl.scrollTop = threadEl.scrollHeight;
        } catch (error) {
            console.error('Error loading notes:', error);
            threadEl.innerHTML = '<p style="color: var(--danger-color);">Failed to load notes.</p>';
        }
    }

    if (sendBtn) {
        sendBtn.addEventListener('click', async () => {
            const message = input.value.trim();
            if (!message) return;
            sendBtn.disabled = true;
            try {
                const response = await fetchWithAuth(`${API_URL}/api/notes/athlete/${athleteId}`, {
                    method: 'POST',
                    body: JSON.stringify({ message }),
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
    }

    await refresh();
}

async function loadGamification() {
    try {
        const response = await fetchWithAuth(`${API_URL}/api/gamification/me`);
        if (!response.ok) return;

        const data = await response.json();
        document.getElementById('streakValue').textContent = data.current_streak;
        document.getElementById('longestStreakValue').textContent = data.longest_streak;

        const strip = document.getElementById('achievementsStrip');
        if (data.achievements.length === 0) {
            strip.innerHTML = '<p style="color: var(--text-secondary); margin: 0; font-size: 0.875rem;">No achievements yet - complete a session to start earning badges!</p>';
            return;
        }

        strip.innerHTML = data.achievements.map(a => `
            <span class="achievement-badge" title="${a.description}">
                <span class="icon">${a.icon}</span> ${a.name}
            </span>
        `).join('');

    } catch (error) {
        console.error('Error loading gamification data:', error);
    }
}

async function loadRecentSessions() {
    try {
        const response = await fetchWithAuth(`${API_URL}/api/sessions/?limit=5`);
        if (!response.ok) {
            throw new Error('Failed to load sessions');
        }
        const sessions = await response.json();

        const container = document.getElementById('recentSessions');

        if (sessions.length === 0) {
            container.innerHTML = '<div class="card"><p>No sessions yet. Start your first training session!</p></div>';
            return;
        }

        const scoreOrNA = (value) => value === null || value === undefined ? 'N/A' : value;
        container.innerHTML = sessions.map(session => `
            <a href="session-detail.html?id=${session.id}" class="card" style="display: block; color: inherit; text-decoration: none; cursor: pointer;">
                <div class="flex justify-between align-center">
                    <div>
                        <h4>${getSportIcon(session.sport_type)} ${session.session_type.replace('_', ' ').toUpperCase()}</h4>
                        <p style="color: var(--text-secondary);">${new Date(session.start_time).toLocaleDateString()} - ${session.duration_minutes} min</p>
                    </div>
                    <div class="text-right">
                        <div class="score-display ${getScoreClass(session.performance_score)}" style="font-size: 2rem;">
                            ${scoreOrNA(session.performance_score)}
                        </div>
                        <p style="font-size: 0.875rem; color: var(--text-secondary);">Performance</p>
                    </div>
                </div>
                <div class="grid grid-3 gap-2 mt-2">
                    <div>
                        <strong>Technique:</strong> ${scoreOrNA(session.technique_accuracy)}
                    </div>
                    <div>
                        <strong>Reaction:</strong> ${scoreOrNA(session.reaction_score)}
                    </div>
                    <div>
                        <strong>Balance:</strong> ${scoreOrNA(session.balance_score)}
                    </div>
                </div>
            </a>
        `).join('');

    } catch (error) {
        console.error('Error loading sessions:', error);
        document.getElementById('recentSessions').innerHTML =
            '<div class="alert alert-error">Failed to load sessions</div>';
    }
}

async function loadAvailableSkills(sportType) {
    try {
        const response = await fetch(`${API_URL}/api/skills/?sport_type=${sportType}`);
        const skills = await response.json();

        const container = document.getElementById('availableSkills');

        container.innerHTML = skills.map(skill => `
            <div class="card">
                <h4>${skill.name}</h4>
                <p style="color: var(--text-secondary); font-size: 0.875rem;">${skill.description || 'No description'}</p>
                <div class="mt-2">
                    <span class="badge badge-accent">${skill.difficulty_level}</span>
                    ${skill.primary_focus ? `<span class="badge badge-accent" style="margin-left: 0.5rem;">${skill.primary_focus}</span>` : ''}
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading skills:', error);
    }
}

function applyScoreColor(elementId, score) {
    const element = document.getElementById(elementId);
    element.className = 'score-display ' + getScoreClass(score);
}

function getScoreClass(score) {
    if (score === null || score === undefined) return 'unevaluable';
    if (score >= 90) return 'excellent';
    if (score >= 75) return 'good';
    if (score >= 60) return 'average';
    return 'poor';
}

function getSportDisplay(sportType) {
    if (sportType === 'table_tennis') return '🏓 Table Tennis';
    if (sportType === 'boxing') return '🥊 Boxing';
    if (sportType === 'badminton') return '🏸 Badminton';
    return sportType;
}

function getSportIcon(sportType) {
    if (sportType === 'table_tennis') return '🏓';
    if (sportType === 'boxing') return '🥊';
    if (sportType === 'badminton') return '🏸';
    return '🏅';
}

// Load dashboard on page load
loadDashboard();

console.log('Dashboard module loaded');
