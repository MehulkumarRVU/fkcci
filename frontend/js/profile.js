// PocketCoach AI - Profile Management Module
const API_URL = 'http://localhost:8080';

// Check authentication
const token = localStorage.getItem('token');
if (!token) {
    window.location.href = 'login.html';
}

// Setup logout button
document.getElementById('logoutBtn').addEventListener('click', (e) => {
    e.preventDefault();
    localStorage.removeItem('token');
    localStorage.removeItem('athlete');
    window.location.href = 'login.html';
});

// Load profile data
async function loadProfile() {
    try {
        const response = await fetch(`${API_URL}/api/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to load profile');
        }

        const athlete = await response.json();
        localStorage.setItem('athlete', JSON.stringify(athlete));

        // Display profile information
        document.getElementById('profileUsername').textContent = athlete.username;
        document.getElementById('profileEmail').textContent = athlete.email;
        const linkedSports = Array.isArray(athlete.linked_sports) && athlete.linked_sports.length > 0
            ? athlete.linked_sports
            : [athlete.sport_type];

        document.getElementById('profileSport').textContent = 
            athlete.sport_type === 'table_tennis' ? '🏓 Table Tennis' : '🥊 Boxing';
        document.getElementById('profileLinkedSports').textContent = linkedSports
            .map((sport) => sport === 'table_tennis' ? '🏓 Table Tennis' : '🥊 Boxing')
            .join(', ');
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
        document.getElementById('linkBoxing').checked = linkedSports.includes('boxing');
        document.getElementById('linkTableTennis').checked = linkedSports.includes('table_tennis');
        document.getElementById('updateActiveSport').value = athlete.sport_type;

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
        const response = await fetch(`${API_URL}/api/sessions/stats/summary`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

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
        const response = await fetch(`${API_URL}/api/auth/profile`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                height: height ? parseFloat(height) : null,
                weight: weight ? parseFloat(weight) : null,
                training_frequency_per_week: trainingFrequency ? parseInt(trainingFrequency) : 0
            })
        });

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

    const linkedSports = [];
    if (document.getElementById('linkBoxing').checked) {
        linkedSports.push('boxing');
    }
    if (document.getElementById('linkTableTennis').checked) {
        linkedSports.push('table_tennis');
    }

    if (linkedSports.length === 0) {
        showAlert('Select at least one connected sport', 'error');
        return;
    }

    if (!linkedSports.includes(activeSport)) {
        showAlert('Active sport must be one of your connected sports', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/api/auth/profile`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                linked_sports: linkedSports,
                sport_type: activeSport,
                skill_level: skillLevel,
                dominant_hand: dominantHand
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update preferences');
        }

        const athlete = await response.json();
        localStorage.setItem('athlete', JSON.stringify(athlete));

        showAlert('Training preferences updated successfully!', 'success');
        loadProfile();

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

function getScoreClass(score) {
    if (score >= 90) return 'excellent';
    if (score >= 75) return 'good';
    if (score >= 60) return 'average';
    return 'poor';
}

// Load profile on page load
loadProfile();

console.log('Profile module loaded');
