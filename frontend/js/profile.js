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

    } catch (error) {
        console.error('Error loading profile:', error);
        showAlert('Failed to load profile data', 'error');
    }
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
