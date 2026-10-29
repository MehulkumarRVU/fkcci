// PocketCoach AI - Session Management Module
const API_URL = window.POCKETCOACH_API_URL || (
    window.location.port === '3000' || window.location.port === '5500'
        ? `${window.location.protocol}//${window.location.hostname}:8080`
        : ''
);

requireAuth();

// Global variables
let athlete = null;

// Session type options tailored per sport family - previously the dropdown
// offered the same 4 generic options (including "Sparring") regardless of
// sport, which made no sense for e.g. table tennis or archery.
const SESSION_TYPE_OPTIONS = {
    combat: [
        { value: 'drill', label: 'Drill Practice' },
        { value: 'shadow', label: 'Shadow Training' },
        { value: 'sparring', label: 'Sparring' },
        { value: 'match_simulation', label: 'Match Simulation' }
    ],
    racket: [
        { value: 'drill', label: 'Drill Practice' },
        { value: 'shadow', label: 'Shadow Practice (No Ball)' },
        { value: 'match_simulation', label: 'Match Play' }
    ],
    court: [
        { value: 'drill', label: 'Drill Practice' },
        { value: 'shadow', label: 'Shadow Practice' },
        { value: 'match_simulation', label: 'Game Simulation' }
    ],
    precision: [
        { value: 'drill', label: 'Technique Drill' },
        { value: 'match_simulation', label: 'Scoring Round' }
    ],
    fitness: [
        { value: 'drill', label: 'Form Practice' },
        { value: 'shadow', label: 'Light / Recovery Session' },
        { value: 'match_simulation', label: 'Full Intensity Workout' }
    ]
};

const SPORT_FAMILY = {
    table_tennis: 'racket', badminton: 'racket',
    boxing: 'combat',
    gym: 'fitness', stretching: 'fitness', mobility_training: 'fitness',
    rehabilitation: 'fitness', home_workouts: 'fitness', calisthenics: 'fitness'
};

// Mirrors rep-counter.js's RepCounter._detectMode() sport list - only
// these sports have a server-side count to cross-check against, so a
// target only makes sense for them.
const SPORTS_WITH_REP_COUNTER = ['gym', 'boxing'];

function updateTargetRepsVisibility(sportType) {
    const group = document.getElementById('targetRepsGroup');
    if (!group) return;
    group.classList.toggle('hidden', !SPORTS_WITH_REP_COUNTER.includes(sportType));
}

function populateSessionTypeOptions(sportType) {
    const select = document.getElementById('sessionType');
    if (!select) return;

    const family = SPORT_FAMILY[sportType] || 'court';
    const options = SESSION_TYPE_OPTIONS[family] || SESSION_TYPE_OPTIONS.court;

    select.innerHTML = '<option value="">Select session type...</option>' +
        options.map(opt => `<option value="${opt.value}">${opt.label}</option>`).join('');
}

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

    populateSessionTypeOptions(athlete.sport_type);
    updateTargetRepsVisibility(athlete.sport_type);

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
    setupAdaptiveOptions();

    // Setup session form
    const sessionSetupForm = document.getElementById('sessionSetupForm');
    if (sessionSetupForm) {
        sessionSetupForm.addEventListener('submit', startSession);
    }

    async function setupAdaptiveOptions() {
        const options = document.getElementById('adaptiveOptions');
        const modeInputs = document.querySelectorAll('input[name="trainingMode"]');
        if (!options || !modeInputs.length) return;
        const setVisibility = () => options.classList.toggle(
            'hidden',
            document.querySelector('input[name="trainingMode"]:checked').value !== 'adaptive'
        );
        modeInputs.forEach(input => input.addEventListener('change', setVisibility));
        try {
            const response = await fetch(`${API_URL}/api/adaptive/catalog?category=${encodeURIComponent(athlete.sport_type)}`);
            if (!response.ok) throw new Error('Unable to load adaptive exercises');
            const catalog = await response.json();
            const exerciseSelect = document.getElementById('adaptiveExercise');
            Object.entries(catalog.exercises || {}).forEach(([key, exercise]) => {
                const option = document.createElement('option');
                option.value = key;
                option.textContent = key.replaceAll('_', ' ');
                option.dataset.setups = JSON.stringify(exercise.setups);
                option.dataset.views = JSON.stringify(exercise.camera_views);
                exerciseSelect.appendChild(option);
            });
            const updateGuidance = () => {
                const selected = exerciseSelect.options[exerciseSelect.selectedIndex];
                const setups = selected ? JSON.parse(selected.dataset.setups) : [];
                document.getElementById('adaptiveSetup').innerHTML = setups.map(setup =>
                    `<option value="${setup}">${setup.replaceAll('_', ' ')}</option>`).join('');
                document.getElementById('adaptiveGuidance').textContent =
                    selected ? `Required upper-body landmarks: ${catalog.exercises[selected.value].required_landmarks.join(', ')}. Use a ${JSON.parse(selected.dataset.views).join(' or ')} view.` : '';
            };
            exerciseSelect.addEventListener('change', updateGuidance);
            updateGuidance();
        } catch (error) {
            console.error('Adaptive catalog error:', error);
            document.getElementById('adaptiveGuidance').textContent = 'Adaptive exercise options are unavailable. Please use Standard Training or try again later.';
        }
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
            const seedResponse = await fetchWithAuth(`${API_URL}/api/skills/seed`, { method: 'POST' });
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
    const targetRepsInput = document.getElementById('targetReps');
    const targetReps = targetRepsInput && targetRepsInput.value ? parseInt(targetRepsInput.value, 10) : null;
    const adaptiveMode = document.querySelector('input[name="trainingMode"]:checked')?.value === 'adaptive';
    const adaptive = adaptiveMode ? {
        setup: document.getElementById('adaptiveSetup').value,
        exercise: document.getElementById('adaptiveExercise').value,
        camera_view: document.getElementById('adaptiveCamera').value
    } : null;

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
                session_type: sessionType,
                skill_name: selectedSkill.name,
                adaptive
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

            if (response.status === 401) {
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

            if (response.status === 401) {
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
            targetReps: targetReps && targetReps > 0 ? targetReps : null,
            adaptive,
            startedAt: Date.now()
        }));

        window.location.href = 'session-precheck.html';

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
