// PocketCoach AI - Forgot Password Module
const API_URL = 'http://localhost:8080';

const forgotPasswordForm = document.getElementById('forgotPasswordForm');
if (forgotPasswordForm) {
    forgotPasswordForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = document.getElementById('forgotEmail').value;
        const submitBtn = forgotPasswordForm.querySelector('button[type="submit"]');
        submitBtn.disabled = true;

        try {
            await fetch(`${API_URL}/api/auth/password-reset/request`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
            });

            // Always show the same success state regardless of whether the
            // email was registered - the backend intentionally returns an
            // identical response either way to prevent account enumeration.
            document.getElementById('requestFormWrapper').classList.add('hidden');
            document.getElementById('requestSentState').classList.remove('hidden');
        } catch (error) {
            console.error('Error requesting password reset:', error);
            showAlert('Something went wrong. Please try again.', 'error');
            submitBtn.disabled = false;
        }
    });
}

function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) return;
    const alertClass = type === 'success' ? 'alert-success' : type === 'error' ? 'alert-error' : 'alert-info';
    alertContainer.innerHTML = `<div class="alert ${alertClass}">${message}</div>`;
    setTimeout(() => { alertContainer.innerHTML = ''; }, 5000);
}

console.log('Forgot password module loaded');
