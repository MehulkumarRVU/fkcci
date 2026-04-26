// Admin Dashboard JavaScript
const API_BASE_URL = 'http://localhost:8080/api';
let currentCoach = null;
let coachAthletes = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    const athlete = JSON.parse(localStorage.getItem('athlete') || '{}');

    if (!token || athlete.role !== 'coach') {
        window.location.href = '../index.html';
        return;
    }

    currentCoach = athlete;
    loadCoachSummary();
    loadAthletes();
});

/**
 * Load coach summary statistics
 */
async function loadCoachSummary() {
    try {
        const response = await fetch(`${API_BASE_URL}/analytics/coach/summary`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // Update summary cards
        document.getElementById('totalAthletes').textContent = data.total_athletes;
        document.getElementById('totalSessions').textContent = data.total_sessions_this_month;
        document.getElementById('avgPerformance').textContent = 
            data.avg_performance_across_athletes.toFixed(1) + '%';

        if (data.most_active_athlete) {
            document.getElementById('mostActive').textContent = 
                `${data.most_active_athlete.username} (${data.most_active_athlete.sessions})`;
        }

        // Display top performers
        displayTopPerformers(data.top_performers);
    } catch (error) {
        console.error('Error loading coach summary:', error);
        showAlert('Failed to load summary data', 'error');
    }
}

/**
 * Load all athletes coached by current coach
 */
async function loadAthletes() {
    try {
        const response = await fetch(`${API_BASE_URL}/analytics/coach/athletes`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        coachAthletes = await response.json();
        displayAthletes(coachAthletes);
    } catch (error) {
        console.error('Error loading athletes:', error);
        const container = document.getElementById('athletesContainer');
        container.innerHTML = `
            <div class="error-message">
                <strong>Error:</strong> Failed to load athletes. Please refresh the page.
            </div>
        `;
    }
}

/**
 * Display athletes in grid
 */
function displayAthletes(athletes) {
    const container = document.getElementById('athletesContainer');

    if (!athletes || athletes.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>📊 No athletes assigned to you yet.</p>
                <p style="font-size: 13px; margin-top: 10px;">Athletes will appear here once they're assigned to your account.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = athletes.map(athlete => `
        <div class="athlete-card">
            <div class="athlete-header">
                <h3>${athlete.username}</h3>
                <div class="info">
                    <span class="badge badge-${athlete.sport_type}">${athlete.sport_type}</span>
                    <span style="margin-left: 8px;">Level: ${athlete.skill_level}</span>
                </div>
            </div>
            <div class="athlete-body">
                <div class="athlete-stat">
                    <label>Email:</label>
                    <value>${athlete.email}</value>
                </div>
                <div class="athlete-stat">
                    <label>Total Sessions:</label>
                    <value id="sessions-${athlete.id}">-</value>
                </div>
                <div class="athlete-stat">
                    <label>Sports:</label>
                    <value>${athlete.linked_sports.join(', ')}</value>
                </div>
                <div class="athlete-stat">
                    <label>Joined:</label>
                    <value>${formatDate(athlete.created_at)}</value>
                </div>
            </div>
            <div class="athlete-footer">
                <button class="btn-view-details" onclick="viewAthleteDetails(${athlete.id})">
                    View Detailed Report
                </button>
            </div>
        </div>
    `).join('');

    // Load session counts for each athlete
    athletes.forEach(athlete => {
        loadAthleteMonthlyStats(athlete.id);
    });
}

/**
 * Load monthly stats for an athlete
 */
async function loadAthleteMonthlyStats(athleteId) {
    try {
        const response = await fetch(`${API_BASE_URL}/analytics/coach/athlete/${athleteId}/monthly-report`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });

        if (response.ok) {
            const data = await response.json();
            const element = document.getElementById(`sessions-${athleteId}`);
            if (element) {
                element.textContent = data.this_month_sessions;
            }
        }
    } catch (error) {
        console.error(`Error loading stats for athlete ${athleteId}:`, error);
    }
}

/**
 * Display top performers
 */
function displayTopPerformers(topPerformers) {
    const container = document.getElementById('topPerformersContainer');

    if (!topPerformers || topPerformers.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>📈 No performance data yet.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="top-performers">
            ${topPerformers.map((performer, index) => `
                <div class="performer-item">
                    <span class="performer-name">
                        ${index + 1}. ${performer.username}
                    </span>
                    <span class="performer-score">${performer.avg_performance.toFixed(1)}%</span>
                </div>
            `).join('')}
        </div>
    `;
}

/**
 * View detailed report for an athlete
 */
async function viewAthleteDetails(athleteId) {
    const modal = document.getElementById('detailModal');
    modal.classList.add('show');

    try {
        const response = await fetch(`${API_BASE_URL}/analytics/coach/athlete/${athleteId}/monthly-report`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        document.getElementById('modalAthleteTitle').textContent = `${data.athlete_username} - Monthly Report`;
        displayAthleteDetails(data);
    } catch (error) {
        console.error('Error loading athlete details:', error);
        document.getElementById('modalBody').innerHTML = `
            <div class="error-message">
                <strong>Error:</strong> Failed to load athlete details. Please try again.
            </div>
        `;
    }
}

/**
 * Display detailed athlete report in modal
 */
function displayAthleteDetails(report) {
    const stats = report.monthly_stats;

    const html = `
        <!-- Profile Section -->
        <div class="detail-section">
            <h3>👤 Athlete Profile</h3>
            <div class="stats-grid">
                <div class="stat-box">
                    <label>Skill Level</label>
                    <value>${report.skill_level}</value>
                </div>
                <div class="stat-box">
                    <label>Primary Sport</label>
                    <value>${report.sport_type}</value>
                </div>
                <div class="stat-box">
                    <label>All-Time Sessions</label>
                    <value>${report.total_sessions}</value>
                </div>
                <div class="stat-box">
                    <label>Performance Rating</label>
                    <value>${report.performance_rating.toFixed(1)}%</value>
                </div>
            </div>
        </div>

        <!-- Monthly Performance Section -->
        <div class="detail-section">
            <h3>📊 This Month's Performance (Past 30 Days)</h3>
            <div class="stats-grid">
                <div class="stat-box">
                    <label>Total Sessions</label>
                    <value>${stats.total_sessions}</value>
                </div>
                <div class="stat-box">
                    <label>Completed Sessions</label>
                    <value>${stats.completed_sessions}</value>
                </div>
                <div class="stat-box">
                    <label>Avg Performance</label>
                    <value>${stats.avg_performance_score.toFixed(1)}%</value>
                </div>
                <div class="stat-box">
                    <label>Training Hours</label>
                    <value>${stats.total_training_hours}h</value>
                </div>
            </div>

            <div class="stats-grid">
                <div class="stat-box">
                    <label>Technique Accuracy</label>
                    <value>${stats.avg_technique_accuracy.toFixed(1)}%</value>
                </div>
                <div class="stat-box">
                    <label>Reaction Score</label>
                    <value>${stats.avg_reaction_score.toFixed(1)}%</value>
                </div>
                <div class="stat-box">
                    <label>Balance Score</label>
                    <value>${stats.avg_balance_score.toFixed(1)}%</value>
                </div>
                <div class="stat-box">
                    <label>Highest Score</label>
                    <value>${stats.highest_performance.toFixed(1)}%</value>
                </div>
            </div>

            <div style="margin-top: 20px;">
                <strong>📈 Performance Range:</strong>
                <div style="margin-top: 8px; padding: 12px; background: #f8f9fa; border-radius: 6px;">
                    <div style="margin-bottom: 8px;">
                        <span style="color: #666;">Highest:</span> 
                        <span style="font-weight: bold; color: #28a745;">${stats.highest_performance.toFixed(1)}%</span>
                    </div>
                    <div>
                        <span style="color: #666;">Lowest:</span> 
                        <span style="font-weight: bold; color: #dc3545;">${stats.lowest_performance.toFixed(1)}%</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recent Sessions Section -->
        <div class="detail-section">
            <h3>📋 Recent Sessions</h3>
            ${report.recent_sessions.length > 0 ? `
                <table class="sessions-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Sport</th>
                            <th>Type</th>
                            <th>Duration</th>
                            <th>Performance</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${report.recent_sessions.map(session => `
                            <tr>
                                <td>${formatDate(session.start_time)}</td>
                                <td><span class="badge badge-${session.sport_type}">${session.sport_type}</span></td>
                                <td>${session.session_type}</td>
                                <td>${session.duration_minutes}m</td>
                                <td>
                                    <strong style="color: ${getScoreColor(session.performance_score)};">
                                        ${session.performance_score.toFixed(1)}%
                                    </strong>
                                </td>
                                <td>
                                    <span class="badge ${session.is_completed ? 'badge-completed' : 'badge-in-progress'}">
                                        ${session.is_completed ? 'Completed' : 'In Progress'}
                                    </span>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            ` : `
                <div class="empty-state">
                    <p>No sessions recorded yet.</p>
                </div>
            `}
        </div>

        <!-- Feedback Section -->
        <div class="detail-section">
            <h3>💡 Coaching Feedback</h3>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #667eea;">
                ${generateCoachingFeedback(stats)}
            </div>
        </div>
    `;

    document.getElementById('modalBody').innerHTML = html;
}

/**
 * Generate coaching feedback based on stats
 */
function generateCoachingFeedback(stats) {
    let feedback = [];

    // Performance feedback
    if (stats.avg_performance_score >= 85) {
        feedback.push('✅ Excellent performance! This athlete is one of your top performers.');
    } else if (stats.avg_performance_score >= 70) {
        feedback.push('👍 Good performance. Maintain the current training regime.');
    } else if (stats.avg_performance_score >= 50) {
        feedback.push('⚠️ Average performance. Consider increasing training frequency or intensity.');
    } else {
        feedback.push('❌ Below average performance. Recommend one-on-one coaching sessions.');
    }

    // Technique feedback
    if (stats.avg_technique_accuracy >= 80) {
        feedback.push('✅ Technique accuracy is excellent!');
    } else if (stats.avg_technique_accuracy < 60) {
        feedback.push('⚠️ Technique accuracy needs improvement. Focus on form drills.');
    }

    // Session frequency
    if (stats.total_sessions >= 8) {
        feedback.push('✅ Great commitment with ' + stats.total_sessions + ' training sessions.');
    } else if (stats.total_sessions < 4) {
        feedback.push('⚠️ Low training frequency. Encourage more regular practice.');
    }

    // Balance score
    if (stats.avg_balance_score >= 80) {
        feedback.push('✅ Balance and posture are excellent!');
    } else if (stats.avg_balance_score < 60) {
        feedback.push('⚠️ Balance score is below target. Include stability exercises in training.');
    }

    return feedback.map(f => `<div style="margin-bottom: 10px; padding: 10px; background: white; border-radius: 4px;">${f}</div>`).join('');
}

/**
 * Close detail modal
 */
function closeModal() {
    document.getElementById('detailModal').classList.remove('show');
}

/**
 * Get color based on score
 */
function getScoreColor(score) {
    if (score >= 80) return '#28a745';
    if (score >= 60) return '#ffc107';
    return '#dc3545';
}

/**
 * Format date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const alertClass = type === 'error' ? 'error-message' : 'success-message';
    const alert = document.createElement('div');
    alert.className = alertClass;
    alert.textContent = message;
    
    const container = document.querySelector('.container');
    container.insertBefore(alert, container.firstChild);
    
    setTimeout(() => alert.remove(), 5000);
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    const modal = document.getElementById('detailModal');
    if (e.target === modal) {
        closeModal();
    }
});
