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
            // Create FormData for OAuth2 password flow
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            const response = await fetch(`${API_URL}/api/auth/login`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Login failed');
            }

            const data = await response.json();
            
            // Store token
            localStorage.setItem('token', data.access_token);

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

// Check if already logged in
if (localStorage.getItem('token')) {
    // If on login page and already authenticated, redirect to dashboard
    if (window.location.pathname.includes('login.html')) {
        window.location.href = 'dashboard.html';
    }
}

console.log('Auth module loaded');
