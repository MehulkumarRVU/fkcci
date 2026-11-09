// PocketCoach AI - Shared authentication utilities
const AUTH_API_URL = window.POCKETCOACH_API_URL || (
    window.location.port === '3000' || window.location.port === '5500'
        ? `${window.location.protocol}//${window.location.hostname}:8080`
        : ''
);

function getAuthToken() {
    return localStorage.getItem('token');
}

function getRefreshToken() {
    return localStorage.getItem('refresh_token');
}

function clearAuthStorage() {
    localStorage.removeItem('token');
    localStorage.removeItem('athlete');
    localStorage.removeItem('refresh_token');
}

let logoutInProgress = false;

async function logout() {
    if (logoutInProgress) return;
    logoutInProgress = true;

    const refreshToken = getRefreshToken();
    let revocationFailed = false;
    if (refreshToken) {
        try {
            const response = await fetch(`${AUTH_API_URL}/api/auth/logout`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken })
            });
            if (!response.ok) {
                throw new Error(`Logout token revocation failed (${response.status})`);
            }
        } catch (error) {
            console.error('Could not revoke the server refresh token:', error);
            revocationFailed = true;
        }
    }

    clearAuthStorage();
    if (revocationFailed) {
        window.alert('The server could not revoke this session. Its refresh token may remain valid until it expires.');
    }
    window.location.href = 'login.html';
}

function handleUnauthorized() {
    clearAuthStorage();
    window.location.href = 'login.html';
}

let refreshTokenRequest = null;

async function refreshAccessToken() {
    if (refreshTokenRequest) {
        return refreshTokenRequest;
    }

    const refreshToken = getRefreshToken();
    if (!refreshToken) return false;

    refreshTokenRequest = (async () => {
        try {
            const response = await fetch(`${AUTH_API_URL}/api/auth/token/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            if (!response.ok) return false;

            const data = await response.json();
            localStorage.setItem('token', data.access_token);
            if (data.refresh_token) {
                localStorage.setItem('refresh_token', data.refresh_token);
            }
            return true;
        } catch (err) {
            console.error('Error refreshing access token:', err);
            return false;
        }
    })().finally(() => {
        refreshTokenRequest = null;
    });
    return refreshTokenRequest;
}

async function fetchWithAuth(url, options = {}) {
    const headers = new Headers(options.headers || {});
    const token = getAuthToken();
    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    }

    if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json');
    }

    const response = await fetch(url, { ...options, headers });
    // Only 401 means "your credentials are invalid/expired" - 403 means
    // "you're authenticated but not authorized for this specific resource"
    // (wrong role, don't own it, etc.), a legitimate business-logic
    // rejection that should flow back to the caller as a normal error, not
    // force-log-out a perfectly valid session.
    if (response.status === 401) {
        if (await refreshAccessToken()) {
            const retryHeaders = new Headers(options.headers || {});
            retryHeaders.set('Authorization', `Bearer ${getAuthToken()}`);
            if (options.body && !(options.body instanceof FormData) && !retryHeaders.has('Content-Type')) {
                retryHeaders.set('Content-Type', 'application/json');
            }
            return fetch(url, { ...options, headers: retryHeaders });
        }
        handleUnauthorized();
    }
    return response;
}

function requireAuth() {
    if (!getAuthToken()) {
        handleUnauthorized();
        return false;
    }
    return true;
}

// Downloads a protected (auth-required) file, e.g. a PDF report. A plain
// <a href> can't carry the Authorization header these endpoints need, so
// this fetches the response as a Blob and triggers the download via a
// temporary object URL instead.
async function downloadFile(url, filename) {
    const response = await fetchWithAuth(url);
    if (!response.ok) {
        throw new Error(`Download failed (${response.status})`);
    }
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(objectUrl);
}

// Auto-wires every .password-toggle-btn on the page (login, signup, and
// reset-password forms) to show/hide its paired password field - one
// generic listener instead of per-page duplication.
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.password-toggle-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
            const input = document.getElementById(btn.dataset.toggleFor);
            if (!input) return;
            const showing = input.type === 'text';
            input.type = showing ? 'password' : 'text';
            btn.textContent = showing ? '👁️' : '🙈';
            btn.setAttribute('aria-label', showing ? 'Show password' : 'Hide password');
        });
    });
});

document.addEventListener('click', (event) => {
    if (!(event.target instanceof Element)) return;
    const logoutButton = event.target.closest('#logoutBtn');
    if (!logoutButton) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    void logout();
}, true);

window.getAuthToken = getAuthToken;
window.refreshAccessToken = refreshAccessToken;
window.fetchWithAuth = fetchWithAuth;
window.handleUnauthorized = handleUnauthorized;
window.logout = logout;
window.requireAuth = requireAuth;
window.downloadFile = downloadFile;
