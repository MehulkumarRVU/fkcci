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
    return sportType === 'table_tennis' ? '🏓 Table Tennis' : '🥊 Boxing';
}

console.log('PocketCoach AI - App initialized');
