// PocketCoach AI - Profile Management Module
const API_URL = 'http://localhost:8080';

requireAuth();

// Setup logout button
const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        handleUnauthorized();
    });
}

// Load profile data
async function loadProfile() {
    try {
        const response = await fetchWithAuth(`${API_URL}/api/auth/me`);

        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                return handleUnauthorized();
            }
            throw new Error('Failed to load profile');
        }

        if (!response.ok) {
            throw new Error('Failed to load profile');
        }

        const athlete = await response.json();
        localStorage.setItem('athlete', JSON.stringify(athlete));

        // Display profile information
        document.getElementById('profileUsername').textContent = athlete.username;
        document.getElementById('profileEmail').textContent = athlete.email;
        const linkedSports = Array.isArray(athlete.linked_sports)
            ? athlete.linked_sports
            : typeof athlete.linked_sports === 'string' && athlete.linked_sports.trim().length > 0
                ? athlete.linked_sports.split(',').map(s => s.trim()).filter(Boolean)
                : [];

        const sportDisplay = (sport) => {
            const mapping = {
                table_tennis: '🏓 Table Tennis',
                boxing: '🥊 Boxing',
                badminton: '🏸 Badminton',
                tennis: '🎾 Tennis',
                pickleball: '🥎 Pickleball',
                squash: '🏓 Squash',
                kickboxing: '🥊 Kickboxing',
                muay_thai: '🦵 Muay Thai',
                karate: '🥋 Karate',
                taekwondo: '🥋 Taekwondo',
                judo: '🥋 Judo',
                bjj: '🥋 BJJ',
                wrestling: '🤼 Wrestling',
                fencing: '🤺 Fencing',
                basketball: '🏀 Basketball',
                volleyball: '🏐 Volleyball',
                handball: '🤾 Handball',
                indoor_archery: '🏹 Indoor Archery',
                ai_gym_coach: '🏋️ AI Gym Coach',
                stretching: '🤸 Stretching',
                mobility_training: '🦴 Mobility Training',
                rehabilitation: '🩺 Rehabilitation',
                home_workouts: '🏠 Home Workouts',
                calisthenics: '💪 Calisthenics'
            };
            return mapping[sport] || sport;
        };

        document.getElementById('profileSport').textContent = sportDisplay(athlete.sport_type);
        const linkedSportsInfo = document.getElementById('profileLinkedSportsInfo');
        if (linkedSportsInfo) {
            linkedSportsInfo.innerHTML = linkedSports
                .map(sport => `<option value="${sport}">${sportDisplay(sport)}</option>`)
                .join('');
        }
        document.getElementById('profileSkillLevel').textContent = athlete.skill_level;
        document.getElementById('profileDominantHand').textContent = athlete.dominant_hand;
        document.getElementById('profileMembership').textContent = athlete.membership_tier.toUpperCase();
        document.getElementById('profileCreatedAt').textContent = formatDate(athlete.created_at);
        
        const perfRating = Math.round(athlete.performance_rating);
        const perfElement = document.getElementById('profilePerformance');
        perfElement.textContent = perfRating;
        perfElement.className = 'score-display ' + getScoreClass(perfRating);
        perfElement.style.fontSize = '1.5rem';
        perfElement.style.margin = '0';

        // Fill form fields
        document.getElementById('updateHeight').value = athlete.height || '';
        document.getElementById('updateWeight').value = athlete.weight || '';
        document.getElementById('updateTrainingFrequency').value = athlete.training_frequency_per_week || 0;
        document.getElementById('updateSkillLevel').value = athlete.skill_level;
        document.getElementById('updateDominantHand').value = athlete.dominant_hand;

        const activeSportSelect = document.getElementById('updateActiveSport');
        if (activeSportSelect) {
            updateActiveSportOptions(activeSportSelect, linkedSports, athlete.sport_type, sportDisplay, false);
        }

        const allSports = [
            'table_tennis', 'boxing', 'badminton', 'tennis', 'pickleball', 'squash',
            'kickboxing', 'muay_thai', 'karate', 'taekwondo', 'judo', 'bjj', 'wrestling',
            'fencing', 'basketball', 'volleyball', 'handball', 'indoor_archery',
            'ai_gym_coach', 'stretching', 'mobility_training', 'rehabilitation',
            'home_workouts', 'calisthenics'
        ];

        const connectedSportsMenu = document.getElementById('linkedSportsMenu');
        if (connectedSportsMenu) {
            connectedSportsMenu.innerHTML = allSports
                .map(sport => `
                    <label class="dropdown-option">
                        <input type="checkbox" name="linked_sports" value="${sport}" ${linkedSports.includes(sport) ? 'checked' : ''}>
                        ${sportDisplay(sport)}
                    </label>
                `)
                .join('');
        }

        updateLinkedSportsToggleText(linkedSports);

        const dropdownToggle = document.getElementById('linkedSportsToggle');
        const dropdownWrapper = document.getElementById('profileLinkedSportsDropdown');
        if (dropdownToggle && dropdownWrapper) {
            dropdownToggle.addEventListener('click', () => {
                dropdownWrapper.classList.toggle('open');
            });
        }

        document.addEventListener('click', (event) => {
            if (!dropdownWrapper?.contains(event.target)) {
                dropdownWrapper?.classList.remove('open');
            }
        });

        const linkedSportsCheckboxes = document.querySelectorAll('#linkedSportsMenu input[type="checkbox"]');
        linkedSportsCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                const selectedSports = Array.from(linkedSportsCheckboxes)
                    .filter(cb => cb.checked)
                    .map(cb => cb.value);

                updateLinkedSportsToggleText(selectedSports);
                updateActiveSportOptions(activeSportSelect, selectedSports, activeSportSelect.value, sportDisplay, true);
            });
        });

        // Load statistics
        loadStatistics();
        loadDigitalTwin();

        // Coach connection is an athlete-side concept (coaches manage
        // requests/invite codes from admin.html instead).
        if (athlete.role === 'athlete') {
            document.getElementById('coachConnectionCard').classList.remove('hidden');
            loadCoachConnection();
        }

    } catch (error) {
        console.error('Error loading profile:', error);
        showAlert('Failed to load profile data', 'error');
    }
}

// Coach connection: search+request or invite-code join, plus pending/connected state.
async function loadCoachConnection() {
    try {
        const response = await fetchWithAuth(`${API_URL}/api/coaches/me/connection-status`);
        if (!response.ok) return;
        const status = await response.json();

        const unconnectedEl = document.getElementById('coachConnUnconnected');
        const pendingEl = document.getElementById('coachConnPending');
        const connectedEl = document.getElementById('coachConnConnected');

        unconnectedEl.classList.add('hidden');
        pendingEl.classList.add('hidden');
        connectedEl.classList.add('hidden');

        if (status.connected_coach) {
            connectedEl.classList.remove('hidden');
            document.getElementById('connectedCoachName').textContent = status.connected_coach.username;
        } else if (status.pending_request) {
            pendingEl.classList.remove('hidden');
            document.getElementById('pendingCoachName').textContent =
                status.pending_request.coach ? status.pending_request.coach.username : `Coach #${status.pending_request.coach_id}`;
            pendingEl.dataset.requestId = status.pending_request.id;
        } else {
            unconnectedEl.classList.remove('hidden');
        }
    } catch (error) {
        console.error('Error loading coach connection status:', error);
    }
}

const coachSearchBtn = document.getElementById('coachSearchBtn');
if (coachSearchBtn) {
    coachSearchBtn.addEventListener('click', async () => {
        const q = document.getElementById('coachSearchInput').value.trim();
        const resultsEl = document.getElementById('coachSearchResults');
        try {
            const response = await fetchWithAuth(`${API_URL}/api/coaches/search?q=${encodeURIComponent(q)}`);
            if (!response.ok) throw new Error('Search failed');
            const coaches = await response.json();

            resultsEl.innerHTML = coaches.length === 0
                ? '<p style="color: var(--text-secondary);">No coaches found.</p>'
                : coaches.map(c => `
                    <div class="flex justify-between align-center" style="padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
                        <span>${c.username}</span>
                        <button class="btn btn-primary btn-small" data-coach-id="${c.id}">Request</button>
                    </div>
                `).join('');

            resultsEl.querySelectorAll('button[data-coach-id]').forEach(btn => {
                btn.addEventListener('click', async () => {
                    btn.disabled = true;
                    try {
                        const reqResp = await fetchWithAuth(`${API_URL}/api/coaches/${btn.dataset.coachId}/request`, {
                            method: 'POST',
                        });
                        if (!reqResp.ok) {
                            const err = await reqResp.json();
                            throw new Error(err.detail || 'Failed to send request');
                        }
                        showAlert('Connection request sent!', 'success');
                        await loadCoachConnection();
                    } catch (error) {
                        showAlert(error.message, 'error');
                        btn.disabled = false;
                    }
                });
            });
        } catch (error) {
            console.error('Error searching coaches:', error);
            resultsEl.innerHTML = '<p style="color: var(--danger-color);">Search failed.</p>';
        }
    });
}

const joinInviteBtn = document.getElementById('joinInviteBtn');
if (joinInviteBtn) {
    joinInviteBtn.addEventListener('click', async () => {
        const code = document.getElementById('inviteCodeInput').value.trim();
        if (!code) return;
        joinInviteBtn.disabled = true;
        try {
            const response = await fetchWithAuth(`${API_URL}/api/coaches/join/${encodeURIComponent(code)}`, {
                method: 'POST',
            });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to join with that code');
            }
            showAlert('Connected with your coach!', 'success');
            await loadCoachConnection();
        } catch (error) {
            showAlert(error.message, 'error');
        } finally {
            joinInviteBtn.disabled = false;
        }
    });
}

const cancelRequestBtn = document.getElementById('cancelRequestBtn');
if (cancelRequestBtn) {
    cancelRequestBtn.addEventListener('click', async () => {
        const requestId = document.getElementById('coachConnPending').dataset.requestId;
        if (!requestId) return;
        cancelRequestBtn.disabled = true;
        try {
            const response = await fetchWithAuth(`${API_URL}/api/coaches/requests/${requestId}`, {
                method: 'DELETE',
            });
            if (!response.ok && response.status !== 204) throw new Error('Failed to cancel request');
            showAlert('Request cancelled.', 'success');
            await loadCoachConnection();
        } catch (error) {
            showAlert(error.message, 'error');
        } finally {
            cancelRequestBtn.disabled = false;
        }
    });
}

const leaveCoachBtn = document.getElementById('leaveCoachBtn');
if (leaveCoachBtn) {
    leaveCoachBtn.addEventListener('click', async () => {
        if (!confirm('Disconnect from your coach?')) return;
        leaveCoachBtn.disabled = true;
        try {
            const response = await fetchWithAuth(`${API_URL}/api/coaches/me/leave`, {
                method: 'POST',
            });
            if (!response.ok && response.status !== 204) throw new Error('Failed to disconnect');
            showAlert('Disconnected from coach.', 'success');
            await loadCoachConnection();
        } catch (error) {
            showAlert(error.message, 'error');
        } finally {
            leaveCoachBtn.disabled = false;
        }
    });
}

// Load statistics
async function loadStatistics() {
    try {
        const response = await fetchWithAuth(`${API_URL}/api/sessions/stats/summary`);

        if (response.ok) {
            const stats = await response.json();
            document.getElementById('statTotalSessions').textContent = stats.total_sessions;
            document.getElementById('statAvgPerformance').textContent = Math.round(stats.average_performance);
        }

    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// Update physical stats form
document.getElementById('updatePhysicalForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const height = document.getElementById('updateHeight').value;
    const weight = document.getElementById('updateWeight').value;
    const trainingFrequency = document.getElementById('updateTrainingFrequency').value;

    try {
        const response = await fetchWithAuth(`${API_URL}/api/auth/profile`, {
            method: 'PUT',
            body: JSON.stringify({
                height: height ? parseFloat(height) : null,
                weight: weight ? parseFloat(weight) : null,
                training_frequency_per_week: trainingFrequency ? parseInt(trainingFrequency) : 0
            })
        });

        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                return handleUnauthorized();
            }
            throw new Error('Failed to update physical stats');
        }

        if (!response.ok) {
            throw new Error('Failed to update physical stats');
        }

        const athlete = await response.json();
        localStorage.setItem('athlete', JSON.stringify(athlete));
        showAlert('Physical stats updated successfully!', 'success');
        loadProfile();

    } catch (error) {
        console.error('Error updating physical stats:', error);
        showAlert('Failed to update physical stats', 'error');
    }
});

// Update preferences form
document.getElementById('updatePreferencesForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const skillLevel = document.getElementById('updateSkillLevel').value;
    const dominantHand = document.getElementById('updateDominantHand').value;
    const activeSport = document.getElementById('updateActiveSport').value;

    const linkedSportsMenu = document.getElementById('linkedSportsMenu');
    const linkedSports = linkedSportsMenu
        ? Array.from(linkedSportsMenu.querySelectorAll('input[type="checkbox"]:checked')).map(option => option.value)
        : [];

    if (linkedSports.length === 0) {
        showAlert('Select at least one connected sport', 'error');
        return;
    }

    if (!linkedSports.includes(activeSport)) {
        showAlert('Active sport must be one of your connected sports', 'error');
        return;
    }

    try {
        const response = await fetchWithAuth(`${API_URL}/api/auth/profile`, {
            method: 'PUT',
            body: JSON.stringify({
                linked_sports: linkedSports,
                sport_type: activeSport,
                skill_level: skillLevel,
                dominant_hand: dominantHand
            })
        });

        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                return handleUnauthorized();
            }
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update preferences');
        }

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update preferences');
        }

        const athlete = await response.json();
        localStorage.setItem('athlete', JSON.stringify(athlete));

        showAlert('Training preferences updated successfully!', 'success');

        // Brief UX: disable submit and refresh profile after 1s
        const prefBtn = document.querySelector('#updatePreferencesForm button[type="submit"]');
        if (prefBtn) {
            prefBtn.disabled = true;
            const originalText = prefBtn.textContent;
            prefBtn.textContent = 'Updating...';
            setTimeout(async () => {
                await loadProfile();
                prefBtn.disabled = false;
                prefBtn.textContent = originalText;
            }, 1000);
        } else {
            // Fallback: refresh immediately
            setTimeout(() => loadProfile(), 1000);
        }

    } catch (error) {
        console.error('Error updating preferences:', error);
        showAlert('Failed to update preferences', 'error');
    }
});

const downloadProgressPdfBtn = document.getElementById('downloadProgressPdfBtn');
if (downloadProgressPdfBtn) {
    downloadProgressPdfBtn.addEventListener('click', async () => {
        downloadProgressPdfBtn.disabled = true;
        const originalText = downloadProgressPdfBtn.textContent;
        downloadProgressPdfBtn.textContent = 'Generating...';
        try {
            await downloadFile(`${API_URL}/api/reports/progress/pdf`, 'progress_report.pdf');
        } catch (error) {
            console.error('Error downloading progress report:', error);
            showAlert('Failed to download progress report', 'error');
        } finally {
            downloadProgressPdfBtn.disabled = false;
            downloadProgressPdfBtn.textContent = originalText;
        }
    });
}

// Digital Twin: score-over-time trend + recurring joint-deviation tendencies,
// aggregated server-side from real session history (backend
// app/services/profile_twin_service.py) - not recomputed here.
async function loadDigitalTwin() {
    try {
        const response = await fetchWithAuth(`${API_URL}/api/analytics/me/profile-twin`);
        if (!response.ok) return;

        const twin = await response.json();
        const emptyState = document.getElementById('twinEmptyState');
        const content = document.getElementById('twinContent');

        if (!twin.total_sessions || twin.score_trend.length === 0) {
            emptyState.classList.remove('hidden');
            content.classList.add('hidden');
            return;
        }

        emptyState.classList.add('hidden');
        content.classList.remove('hidden');

        const trendLabels = {
            improving: '📈 Improving',
            declining: '📉 Declining',
            stable: '➖ Stable',
            insufficient_data: 'Not enough data yet'
        };
        document.getElementById('twinTrendDirection').textContent = trendLabels[twin.trend_direction] || twin.trend_direction;

        drawTrendSparkline(document.getElementById('twinTrendCanvas'), twin.score_trend.map(p => p.score));

        const perSportEl = document.getElementById('twinPerSport');
        const sports = Object.entries(twin.per_sport || {});
        perSportEl.innerHTML = sports.length
            ? sports.map(([sport, stats]) => `
                <div class="flex justify-between" style="padding: 0.25rem 0; border-bottom: 1px solid var(--border-color);">
                    <span>${sport.replace(/_/g, ' ')}</span>
                    <span>${stats.avg_score.toFixed(1)} avg (${stats.session_count} sessions, ${stats.trend_direction})</span>
                </div>
            `).join('')
            : '<p style="color: var(--text-secondary);">No per-sport data yet.</p>';

        const tendenciesEl = document.getElementById('twinTendencies');
        const tendencies = twin.recurring_tendencies || [];
        tendenciesEl.innerHTML = tendencies.length
            ? tendencies.map(t => `<li>${t.joint}: ${t.high_count} high-deviation, ${t.medium_count} medium-deviation frames</li>`).join('')
            : '<li style="color: var(--text-secondary); list-style: none;">No recurring form issues detected yet - keep training to build this out.</li>';

    } catch (error) {
        console.error('Error loading digital twin:', error);
    }
}

function drawTrendSparkline(canvas, scores) {
    if (!canvas || scores.length === 0) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    const padding = 10;
    const min = Math.min(...scores, 0);
    const max = Math.max(...scores, 100);
    const range = Math.max(max - min, 1);

    ctx.strokeStyle = '#2563eb';
    ctx.lineWidth = 2;
    ctx.beginPath();
    scores.forEach((score, i) => {
        const x = padding + (i / Math.max(scores.length - 1, 1)) * (width - padding * 2);
        const y = height - padding - ((score - min) / range) * (height - padding * 2);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();

    ctx.fillStyle = '#2563eb';
    scores.forEach((score, i) => {
        const x = padding + (i / Math.max(scores.length - 1, 1)) * (width - padding * 2);
        const y = height - padding - ((score - min) / range) * (height - padding * 2);
        ctx.beginPath();
        ctx.arc(x, y, 2.5, 0, 2 * Math.PI);
        ctx.fill();
    });
}

// Helper functions
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) return;

    const alertClass = type === 'success' ? 'alert-success' : 
                      type === 'error' ? 'alert-error' : 'alert-info';

    const alertHTML = `
        <div class="alert ${alertClass}">
            ${message}
        </div>
    `;

    alertContainer.innerHTML = alertHTML;

    setTimeout(() => {
        alertContainer.innerHTML = '';
    }, 5000);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function updateActiveSportOptions(selectElement, connectedSports, currentActiveSport, sportDisplay, showValidationAlert = true) {
    if (!selectElement) return;

    const selectedSports = Array.isArray(connectedSports) ? connectedSports : [];

    if (selectedSports.length === 0) {
        selectElement.innerHTML = '<option value="">Select a connected sport</option>';
        selectElement.value = '';
        selectElement.disabled = true;
        return;
    }

    selectElement.disabled = false;
    const optionsHtml = selectedSports
        .map(sport => `
            <option value="${sport}">${sportDisplay(sport)}</option>
        `)
        .join('');

    selectElement.innerHTML = optionsHtml;

    if (selectedSports.includes(currentActiveSport)) {
        selectElement.value = currentActiveSport;
    } else {
        selectElement.value = selectedSports[0];
        if (showValidationAlert) {
            showAlert('Active sport was updated to match your connected sports.', 'info');
        }
    }
}

function getScoreClass(score) {
    if (score >= 90) return 'excellent';
    if (score >= 75) return 'good';
    if (score >= 60) return 'average';
    return 'poor';
}

function updateLinkedSportsToggleText(selectedSports) {
    const toggle = document.getElementById('linkedSportsToggle');
    if (!toggle) return;

    if (!selectedSports || selectedSports.length === 0) {
        toggle.textContent = 'Select connected sports';
        return;
    }

    if (selectedSports.length === 1) {
        toggle.textContent = `${selectedSports.length} sport selected: ${selectedSports[0].replace('_', ' ')}`;
        return;
    }

    toggle.textContent = `${selectedSports.length} sports selected`;
}

function handleUnauthorized() {
    localStorage.removeItem('token');
    localStorage.removeItem('athlete');
    localStorage.removeItem('refresh_token');
    window.location.href = 'login.html';
}

// Load profile on page load
loadProfile();

console.log('Profile module loaded');
