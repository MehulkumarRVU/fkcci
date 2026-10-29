// PocketCoach AI - Main Application Logic
const API_URL = window.POCKETCOACH_API_URL || (
    window.location.port === '3000' || window.location.port === '5500'
        ? `${window.location.protocol}//${window.location.hostname}:8080`
        : ''
);

// Helper function to check authentication
function isAuthenticated() {
    return localStorage.getItem('token') !== null;
}

// Helper function to get auth headers
function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

// Helper function to show alerts
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

    // Auto-remove after 5 seconds
    setTimeout(() => {
        alertContainer.innerHTML = '';
    }, 5000);
}

// Redirect to login if not authenticated
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = 'pages/login.html';
        return false;
    }
    return true;
}

// Format date helper
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Format time duration helper
function formatDuration(minutes) {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
        return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
}

// Get score color class
function getScoreClass(score) {
    if (score >= 90) return 'excellent';
    if (score >= 75) return 'good';
    if (score >= 60) return 'average';
    return 'poor';
}

// Get sport display name
function getSportDisplayName(sportType) {
    const map = {
        boxing: '🥊 Boxing',
        table_tennis: '🏓 Table Tennis',
        gym: '🏋️ Gym',
        badminton: '🏸 Badminton',
        stretching: '🤸 Stretching',
        mobility_training: '🦴 Mobility Training',
        rehabilitation: '🩺 Rehabilitation',
        home_workouts: '🏠 Home Workouts',
        calisthenics: '💪 Calisthenics'
    };
    return map[sportType] || sportType;
}

function getSportIcon(sportType) {
    const map = {
        boxing: '🥊',
        table_tennis: '🏓',
        gym: '🏋️',
        badminton: '🏸',
        stretching: '🤸',
        mobility_training: '🦴',
        rehabilitation: '🩺',
        home_workouts: '🏠',
        calisthenics: '💪'
    };
    return map[sportType] || '🏅';
}

// Full sport catalog for the landing page's "more sports" grid, grouped
// the same way as the backend's registry (backend/app/sports_registry.py)
// - table_tennis/boxing/badminton get their own detailed cards above and
// are excluded here.
const MORE_SPORT_CATEGORIES = [{
    category: 'Training categories',
    sports: [
        { key: 'boxing', name: 'Boxing', icon: '🥊' },
        { key: 'table_tennis', name: 'Table Tennis', icon: '🏓' },
        { key: 'gym', name: 'Gym', icon: '🏋️' },
        { key: 'badminton', name: 'Badminton', icon: '🏸' },
        { key: 'stretching', name: 'Stretching', icon: '🤸' },
        { key: 'mobility_training', name: 'Mobility Training', icon: '🦴' },
        { key: 'rehabilitation', name: 'Rehabilitation', icon: '🩺' },
        { key: 'home_workouts', name: 'Home Workouts', icon: '🏠' },
        { key: 'calisthenics', name: 'Calisthenics', icon: '💪' },
    ],
}];

function renderMoreSportsGrid() {
    const container = document.getElementById('moreSportsContainer');
    if (!container) return;

    container.innerHTML = MORE_SPORT_CATEGORIES.map(({ category, sports }) => `
        <h3 class="mb-2 mt-4">${category}</h3>
        <div class="grid grid-3 gap-2">
            ${sports.map(({ name, icon }) => `
                <a href="pages/login.html" class="card" style="text-align: center; text-decoration: none; color: inherit; display: block;">
                    <div style="font-size: 1.75rem;">${icon}</div>
                    <div style="font-weight: 500; margin-top: 0.25rem;">${name}</div>
                </a>
            `).join('')}
        </div>
    `).join('');
}

document.addEventListener('DOMContentLoaded', renderMoreSportsGrid);

console.log('PocketCoach AI - App initialized');
