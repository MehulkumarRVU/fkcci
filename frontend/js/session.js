// PocketCoach AI - Session Management Module
const API_URL = 'http://localhost:8080';

requireAuth();

// Global variables
let athlete = null;

// Initialize
async function init() {
    athlete = JSON.parse(localStorage.getItem('athlete'));

    if (athlete && athlete.sport_type) {
        await refreshAthleteFromServer();
    } else {
        try {
            const authResponse = await fetchWithAuth(`${API_URL}/api/auth/me`);
            if (!authResponse.ok) {
                throw new Error('Unable to refresh athlete profile');
            }
            athlete = await authResponse.json();
            localStorage.setItem('athlete', JSON.stringify(athlete));
        } catch (error) {
            window.location.href = 'login.html';
            return;
        }
    }

    if (!athlete || !athlete.sport_type) {
        window.location.href = 'login.html';
        return;
    }

    // Setup logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('token');
            localStorage.removeItem('athlete');
            sessionStorage.removeItem('activeSession');
            window.location.href = 'login.html';
        });
    }

    // Load available skills
    await loadSkills();

    // Setup session form
    const sessionSetupForm = document.getElementById('sessionSetupForm');
    if (sessionSetupForm) {
        sessionSetupForm.addEventListener('submit', startSession);
    }
}

// Load available skills for the athlete's sport
async function loadSkills() {
    const skillSelect = document.getElementById('skillSelect');

    if (!skillSelect) {
        return;
    }

    try {
        let response = await fetch(`${API_URL}/api/skills/?sport_type=${athlete.sport_type}`);
        if (!response.ok) {
            throw new Error('Failed to fetch skills');
        }

        let skills = await response.json();

        if (!Array.isArray(skills) || skills.length === 0) {
            const seedResponse = await fetch(`${API_URL}/api/skills/seed`, { method: 'POST' });
            if (!seedResponse.ok) {
                console.warn('Skill seed endpoint failed:', seedResponse.status, seedResponse.statusText);
            }
            response = await fetch(`${API_URL}/api/skills/?sport_type=${athlete.sport_type}`);
            if (!response.ok) {
                throw new Error('Failed to fetch skills after seeding');
            }
            skills = await response.json();
        }

        if (!Array.isArray(skills) || skills.length === 0) {
            skillSelect.innerHTML = '<option value="">No skills available for your sport</option>';
            skillSelect.disabled = true;
            alert(`No skills found for sport ${athlete.sport_type}. Please contact support or try again later.`);
            return;
        }

        skillSelect.disabled = false;
        skillSelect.innerHTML = '<option value="">Select a skill...</option>';

        skills.forEach(skill => {
            const option = document.createElement('option');
            option.value = skill.id;
            option.textContent = `${skill.name} (${skill.difficulty_level})`;
            option.dataset.skill = JSON.stringify(skill);
            skillSelect.appendChild(option);
        });

        if (skills.length === 0) {
            skillSelect.innerHTML = '<option value="">No skills available</option>';
            alert('No skills found for your sport. Please try again after backend restart.');
        }

    } catch (error) {
        console.error('Error loading skills:', error);
        skillSelect.innerHTML = '<option value="">Unable to load skills</option>';
        alert('Failed to load skills. Ensure backend is running on port 8080.');
    }
}

async function refreshAthleteFromServer() {
    try {
        const authResponse = await fetchWithAuth(`${API_URL}/api/auth/me`);
        if (!authResponse.ok) {
            throw new Error('Unable to refresh athlete profile');
        }
        const latestAthlete = await authResponse.json();
        if (latestAthlete && latestAthlete.sport_type) {
            athlete = latestAthlete;
            localStorage.setItem('athlete', JSON.stringify(athlete));
        }
    } catch (error) {
        console.warn('Could not refresh athlete profile:', error);
    }
}

// Start training session
async function startSession(e) {
    e.preventDefault();

    const sessionType = document.getElementById('sessionType').value;
    const skillSelect = document.getElementById('skillSelect');
    const selectedOption = skillSelect.options[skillSelect.selectedIndex];

    if (!sessionType) {
        alert('Please select a session type');
        return;
    }
    
    if (!selectedOption.dataset.skill) {
        alert('Please select a skill');
        return;
    }

    const selectedSkill = JSON.parse(selectedOption.dataset.skill);
    const submitButton = e.target.querySelector('button[type="submit"]');
    if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = 'Starting Session...';
    }

    try {
        // Create session in backend
        const response = await fetchWithAuth(`${API_URL}/api/sessions/`, {
            method: 'POST',
            body: JSON.stringify({
                sport_type: athlete.sport_type,
                session_type: sessionType
            })
        });

        if (!response.ok) {
            let detail = 'Failed to create session';
            try {
                const errorData = await response.json();
                if (typeof errorData.detail === 'string') {
                    detail = errorData.detail;
                }
            } catch {
                // Ignore parse errors and keep fallback detail
            }

            if (response.status === 401 || response.status === 403) {
                handleUnauthorized();
                return;
            }
            throw new Error(detail);
        }

        if (!response.ok) {
            let detail = 'Failed to create session';
            try {
                const errorData = await response.json();
                if (typeof errorData.detail === 'string') {
                    detail = errorData.detail;
                }
            } catch {
                // Ignore parse errors and keep fallback detail
            }

            if (response.status === 401 || response.status === 403) {
                localStorage.removeItem('token');
                localStorage.removeItem('athlete');
                sessionStorage.removeItem('activeSession');
                alert('Your login session has expired. Please login again.');
                window.location.href = 'login.html';
                return;
            }

            throw new Error(detail);
        }

        const createdSession = await response.json();

        sessionStorage.setItem('activeSession', JSON.stringify({
            session: createdSession,
            skill: selectedSkill,
            sessionType,
            startedAt: Date.now()
        }));

        window.location.href = 'session-live.html';

    } catch (error) {
        console.error('Error starting session:', error);
        alert(error.message || 'Failed to start session');
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = 'Start Training Session';
        }
    }
}

// Initialize on load
init();

console.log('Session module loaded');
