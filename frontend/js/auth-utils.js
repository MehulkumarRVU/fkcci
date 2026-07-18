// PocketCoach AI - Shared authentication utilities
const AUTH_API_URL = window.API_URL || 'http://localhost:8080';

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

function handleUnauthorized() {
    clearAuthStorage();
    window.location.href = 'login.html';
}

async function refreshAccessToken() {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
        return false;
    }

    try {
        const response = await fetch(`${AUTH_API_URL}/api/auth/token/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        if (!response.ok) {
            return false;
        }

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
    if (response.status === 401 || response.status === 403) {
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

window.getAuthToken = getAuthToken;
window.fetchWithAuth = fetchWithAuth;
window.handleUnauthorized = handleUnauthorized;
window.requireAuth = requireAuth;
