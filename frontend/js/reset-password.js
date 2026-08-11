// PocketCoach AI - Reset Password Module
const API_URL = 'http://localhost:8080';

function getTokenFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('token');
}

const token = getTokenFromUrl();
const resetPasswordForm = document.getElementById('resetPasswordForm');

if (!token) {
    document.getElementById('missingTokenState').classList.remove('hidden');
    resetPasswordForm.classList.add('hidden');
}

if (resetPasswordForm) {
    resetPasswordForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        if (newPassword !== confirmPassword) {
            showAlert('Passwords do not match', 'error');
            return;
        }

        const submitBtn = resetPasswordForm.querySelector('button[type="submit"]');
        submitBtn.disabled = true;

        try {
            const response = await fetch(`${API_URL}/api/auth/password-reset/confirm`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token, new_password: newPassword }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to reset password');
            }

            resetPasswordForm.classList.add('hidden');
            document.getElementById('resetSuccessState').classList.remove('hidden');
        } catch (error) {
            console.error('Error resetting password:', error);
            showAlert(error.message, 'error');
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

console.log('Reset password module loaded');
