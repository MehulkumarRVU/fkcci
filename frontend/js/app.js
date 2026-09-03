// PocketCoach AI - Main Application Logic
const API_URL = 'http://localhost:8080';

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
    return map[sportType] || sportType;
}

function getSportIcon(sportType) {
    const map = {
        table_tennis: '🏓',
        boxing: '🥊',
        badminton: '🏸',
        tennis: '🎾',
        pickleball: '🥎',
        squash: '🏓',
        kickboxing: '🥊',
        muay_thai: '🦵',
        karate: '🥋',
        taekwondo: '🥋',
        judo: '🥋',
        bjj: '🥋',
        wrestling: '🤼',
        fencing: '🤺',
        basketball: '🏀',
        volleyball: '🏐',
        handball: '🤾',
        indoor_archery: '🏹',
        ai_gym_coach: '🏋️',
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
const MORE_SPORT_CATEGORIES = [
    {
        category: 'Racket Sports',
        sports: [
            { key: 'tennis', name: 'Tennis', icon: '🎾' },
            { key: 'pickleball', name: 'Pickleball', icon: '🥎' },
            { key: 'squash', name: 'Squash', icon: '🏓' },
        ],
    },
    {
        category: 'Combat & Martial Arts',
        sports: [
            { key: 'kickboxing', name: 'Kickboxing', icon: '🥊' },
            { key: 'muay_thai', name: 'Muay Thai', icon: '🦵' },
            { key: 'karate', name: 'Karate', icon: '🥋' },
            { key: 'taekwondo', name: 'Taekwondo', icon: '🥋' },
            { key: 'judo', name: 'Judo', icon: '🥋' },
            { key: 'bjj', name: 'Brazilian Jiu-Jitsu', icon: '🥋' },
            { key: 'wrestling', name: 'Wrestling', icon: '🤼' },
            { key: 'fencing', name: 'Fencing', icon: '🤺' },
            { key: 'wwe', name: 'WWE', icon: '🤼' },
        ],
    },
    {
        category: 'Court & Team Sports',
        sports: [
            { key: 'basketball', name: 'Basketball', icon: '🏀' },
            { key: 'volleyball', name: 'Volleyball', icon: '🏐' },
            { key: 'handball', name: 'Handball', icon: '🤾' },
            { key: 'football', name: 'Football', icon: '⚽' },
            { key: 'baseball', name: 'Baseball', icon: '⚾' },
            { key: 'cricket', name: 'Cricket', icon: '🏏' },
            { key: 'hockey', name: 'Hockey', icon: '🏒' },
            { key: 'ice_hockey', name: 'Ice Hockey', icon: '🏒' },
            { key: 'kabaddi', name: 'Kabaddi', icon: '🏅' },
        ],
    },
    {
        category: 'Precision & Fitness',
        sports: [
            { key: 'indoor_archery', name: 'Indoor Archery', icon: '🏹' },
            { key: 'ai_gym_coach', name: 'AI Gym Coach', icon: '🏋️' },
            { key: 'stretching', name: 'Stretching', icon: '🤸' },
            { key: 'mobility_training', name: 'Mobility Training', icon: '🦴' },
            { key: 'rehabilitation', name: 'Rehabilitation', icon: '🩺' },
            { key: 'home_workouts', name: 'Home Workouts', icon: '🏠' },
            { key: 'calisthenics', name: 'Calisthenics', icon: '💪' },
            { key: 'weight_lifting', name: 'Weight Lifting', icon: '🏋️' },
            { key: 'gymnastics', name: 'Gymnastics', icon: '🤸' },
            { key: 'shooting', name: 'Shooting', icon: '🎯' },
            { key: 'swimming', name: 'Swimming', icon: '🏊' },
            { key: 'formula1', name: 'Formula 1', icon: '🏎️' },
            { key: 'motogp', name: 'MotoGP', icon: '🏍️' },
        ],
    },
];

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
