// PocketCoach AI - Pricing Page Module
const API_URL = 'http://localhost:8080';

requireAuth();

const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        handleUnauthorized();
    });
}

async function loadCurrentTier() {
    try {
        const response = await fetchWithAuth(`${API_URL}/api/auth/me`);
        if (!response.ok) return;
        const athlete = await response.json();

        const label = document.getElementById('currentTierLabel');
        label.textContent = (athlete.membership_tier || 'free').toUpperCase();

        if (athlete.role === 'coach') {
            const adminLink = document.getElementById('adminLink');
            if (adminLink) adminLink.style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading current tier:', error);
    }
}

loadCurrentTier();

console.log('Pricing module loaded');
