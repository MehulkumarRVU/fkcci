// PocketCoach AI - Authentication Module
const API_URL = 'http://localhost:8080';

// Toggle between login and signup forms
const showSignupLink = document.getElementById('showSignupLink');
const showLoginLink = document.getElementById('showLoginLink');
const loginForm = document.getElementById('loginForm');
const signupForm = document.getElementById('signupForm');

if (showSignupLink) {
    showSignupLink.addEventListener('click', (e) => {
        e.preventDefault();
        loginForm.classList.add('hidden');
        signupForm.classList.remove('hidden');
    });
}

if (showLoginLink) {
    showLoginLink.addEventListener('click', (e) => {
        e.preventDefault();
        signupForm.classList.add('hidden');
        loginForm.classList.remove('hidden');
    });
}

// Handle account type toggle
const accountTypeSelect = document.getElementById('accountType');
const athleteFields = document.getElementById('athleteFields');

if (accountTypeSelect) {
    accountTypeSelect.addEventListener('change', (e) => {
        if (e.target.value === 'coach') {
            // Hide athlete-specific fields for coaches
            athleteFields.style.display = 'none';
            // Make sport/skill fields not required
            document.getElementById('sportType').required = false;
            document.getElementById('skillLevel').required = false;
            document.getElementById('dominantHand').required = false;
        } else {
            // Show athlete fields and make them required
            athleteFields.style.display = 'block';
            document.getElementById('sportType').required = true;
            document.getElementById('skillLevel').required = true;
            document.getElementById('dominantHand').required = true;
        }
    });
}

// Login Form Handler
const loginFormElement = document.getElementById('loginFormElement');
if (loginFormElement) {
    loginFormElement.addEventListener('submit', async (e) => {
        e.preventDefault();

        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;

        try {
            // Create URLSearchParams for OAuth2 password flow
            const formData = new URLSearchParams();
            formData.append('grant_type', 'password');
            formData.append('username', username);
            formData.append('password', password);

            console.log('auth.js login payload:', formData.toString());

            const response = await fetch(`${API_URL}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: formData.toString()
            });

            const responseText = await response.text();
            console.log('auth.js login response status:', response.status, 'body:', responseText);

            if (!response.ok) {
                let errorMessage = 'Login failed';
                try {
                    const errorData = JSON.parse(responseText);
                    errorMessage = errorData.detail || errorMessage;
                } catch (parseError) {
                    errorMessage = responseText || errorMessage;
                }
                throw new Error(errorMessage);
            }

            const data = JSON.parse(responseText);
            
            // Store token and refresh token
            localStorage.setItem('token', data.access_token);
            if (data.refresh_token) {
                localStorage.setItem('refresh_token', data.refresh_token);
            }

            // Get athlete info
            const athleteResponse = await fetch(`${API_URL}/api/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${data.access_token}`
                }
            });

            if (athleteResponse.ok) {
                const athlete = await athleteResponse.json();
                localStorage.setItem('athlete', JSON.stringify(athlete));
            }

            // Show success and redirect
            showAlert('Login successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1000);

        } catch (error) {
            showAlert(error.message, 'error');
        }
    });
}

// Signup Form Handler
const signupFormElement = document.getElementById('signupFormElement');
if (signupFormElement) {
    signupFormElement.addEventListener('submit', async (e) => {
        e.preventDefault();

        const accountType = document.getElementById('accountType').value;
        const email = document.getElementById('signupEmail').value;
        const username = document.getElementById('signupUsername').value;
        const password = document.getElementById('signupPassword').value;

        try {
            let response;
            console.log('auth.js signup payload:', {
                accountType,
                email,
                username,
                password,
                sportType: document.getElementById('sportType').value,
                skillLevel: document.getElementById('skillLevel').value,
                dominantHand: document.getElementById('dominantHand').value,
                height: document.getElementById('height').value,
                weight: document.getElementById('weight').value,
            });

            if (accountType === 'coach') {
                // Coach signup
                response = await fetch(`${API_URL}/api/auth/signup-coach`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email,
                        username,
                        password
                    })
                });
            } else {
                // Athlete signup
                const sportType = document.getElementById('sportType').value;
                const skillLevel = document.getElementById('skillLevel').value;
                const dominantHand = document.getElementById('dominantHand').value;
                const height = document.getElementById('height').value;
                const weight = document.getElementById('weight').value;

                response = await fetch(`${API_URL}/api/auth/signup`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email,
                        username,
                        password,
                        sport_type: sportType,
                        skill_level: skillLevel,
                        dominant_hand: dominantHand,
                        height: height ? parseFloat(height) : null,
                        weight: weight ? parseFloat(weight) : null
                    })
                });
            }

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Signup failed');
            }

            // Show success message
            const accountTypeDisplay = accountType === 'coach' ? 'Coach' : 'Athlete';
            showAlert(`${accountTypeDisplay} account created successfully! Please login.`, 'success');

            // Switch to login form
            setTimeout(() => {
                signupForm.classList.add('hidden');
                loginForm.classList.remove('hidden');
                // Pre-fill username
                document.getElementById('loginUsername').value = username;
            }, 1500);

        } catch (error) {
            showAlert(error.message, 'error');
        }
    });
}

// Show alert helper
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

async function refreshAccessToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
        return false;
    }

    try {
        const response = await fetch(`${API_URL}/api/auth/token/refresh`, {
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
    } catch (error) {
        console.error('Error refreshing access token:', error);
        return false;
    }
}

async function fetchWithAuth(url, options = {}) {
    const headers = new Headers(options.headers || {});
    const token = localStorage.getItem('token');
    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    }

    if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json');
    }

    const response = await fetch(url, { ...options, headers });
    if (response.status === 401) {
        if (await refreshAccessToken()) {
            const retryHeaders = new Headers(options.headers || {});
            retryHeaders.set('Authorization', `Bearer ${localStorage.getItem('token')}`);
            if (options.body && !(options.body instanceof FormData) && !retryHeaders.has('Content-Type')) {
                retryHeaders.set('Content-Type', 'application/json');
            }
            return fetch(url, { ...options, headers: retryHeaders });
        }
        handleUnauthorized();
    }
    return response;
}

function handleUnauthorized() {
    localStorage.removeItem('token');
    localStorage.removeItem('athlete');
    localStorage.removeItem('refresh_token');
    window.location.href = 'login.html';
}

// Check if already logged in
// Check if already logged in
if (localStorage.getItem('token')) {
    // If on login page and already authenticated, only redirect when we
    // also have the athlete info. If athlete info is missing, attempt
    // to fetch it from the backend and populate localStorage first.
    if (window.location.pathname.includes('login.html')) {
        const athleteStr = localStorage.getItem('athlete');
        if (athleteStr) {
            window.location.href = 'dashboard.html';
        } else {
            // try to populate athlete info from the backend
            fetchWithAuth(`${API_URL}/api/auth/me`)
            .then(res => {
                if (!res.ok) throw new Error('Not authenticated');
                return res.json();
            })
            .then(data => {
                localStorage.setItem('athlete', JSON.stringify(data));
                window.location.href = 'dashboard.html';
            })
            .catch(() => {
                // Token invalid or fetch failed — clear token and remain on login
                localStorage.removeItem('token');
                localStorage.removeItem('athlete');
                localStorage.removeItem('refresh_token');
            });
        }
    }
}

console.log('Auth module loaded');

