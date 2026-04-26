// PocketCoach AI - Sports Analyzer Module (Client-side)
// Provides basic angle calculations and feedback formatting

class SportsAnalyzer {
    constructor(sportType) {
        this.sportType = sportType;
        this.feedbackHistory = [];
        this.scoreHistory = [];
    }

    calculateAngle(a, b, c) {
        // Calculate angle between three points (a-b-c)
        const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
        let angle = Math.abs(radians * 180.0 / Math.PI);
        
        if (angle > 180.0) {
            angle = 360 - angle;
        }
        
        return angle;
    }

    calculateDistance(a, b) {
        return Math.sqrt(Math.pow(a.x - b.x, 2) + Math.pow(a.y - b.y, 2));
    }

    // Local analysis (for immediate visual feedback)
    analyzeLocally(landmarks, skillName) {
        const feedback = [];
        let score = 100;

        // Basic local checks (more detailed analysis is done server-side)
        
        // Check if all key landmarks are visible
        const keyIndices = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26];
        const visibleCount = keyIndices.filter(idx => 
            landmarks[idx] && landmarks[idx].visibility > 0.5
        ).length;

        if (visibleCount < keyIndices.length * 0.8) {
            feedback.push('⚠️ Move to ensure full body is visible');
            score -= 20;
        }

        // Check balance (ankle width)
        const leftAnkle = landmarks[27];
        const rightAnkle = landmarks[28];
        
        if (leftAnkle && rightAnkle && 
            leftAnkle.visibility > 0.5 && rightAnkle.visibility > 0.5) {
            
            const stanceWidth = Math.abs(leftAnkle.x - rightAnkle.x);
            
            if (stanceWidth < 0.1) {
                feedback.push('⚠️ Widen your stance for better balance');
                score -= 10;
            } else if (stanceWidth > 0.4) {
                feedback.push('⚠️ Stance too wide - bring feet closer');
                score -= 10;
            } else {
                feedback.push('✅ Good stance width');
            }
        }

        // Sport-specific checks
        if (this.sportType === 'boxing') {
            this.analyzeBoxingLocal(landmarks, skillName, feedback);
        } else if (this.sportType === 'table_tennis') {
            this.analyzeTableTennisLocal(landmarks, skillName, feedback);
        }

        return {
            score: Math.max(0, score),
            feedback: feedback
        };
    }

    analyzeBoxingLocal(landmarks, skillName, feedback) {
        // Check guard position
        const leftWrist = landmarks[15];
        const rightWrist = landmarks[16];
        const leftShoulder = landmarks[11];
        const rightShoulder = landmarks[12];

        if (leftWrist && rightWrist && leftShoulder && rightShoulder) {
            const avgShoulderY = (leftShoulder.y + rightShoulder.y) / 2;
            
            // Hands should be at or above shoulder level
            if (leftWrist.y > avgShoulderY + 0.1 || rightWrist.y > avgShoulderY + 0.1) {
                feedback.push('❌ Keep hands up - protect your face');
            }
        }
    }

    analyzeTableTennisLocal(landmarks, skillName, feedback) {
        // Check knee bend
        const leftHip = landmarks[23];
        const leftKnee = landmarks[25];
        const leftAnkle = landmarks[27];

        if (leftHip && leftKnee && leftAnkle && 
            leftHip.visibility > 0.5 && leftKnee.visibility > 0.5 && leftAnkle.visibility > 0.5) {
            
            const kneeAngle = this.calculateAngle(leftHip, leftKnee, leftAnkle);
            
            if (kneeAngle > 170) {
                feedback.push('⚠️ Bend your knees more for better reaction');
            }
        }
    }

    addFeedback(feedback, score) {
        this.feedbackHistory.push({
            feedback: feedback,
            score: score,
            timestamp: Date.now()
        });

        // Keep only last 100 entries
        if (this.feedbackHistory.length > 100) {
            this.feedbackHistory.shift();
        }

        this.scoreHistory.push(score);
        if (this.scoreHistory.length > 100) {
            this.scoreHistory.shift();
        }
    }

    getAverageScore() {
        if (this.scoreHistory.length === 0) return 0;
        const sum = this.scoreHistory.reduce((a, b) => a + b, 0);
        return Math.round(sum / this.scoreHistory.length);
    }

    getLatestFeedback(count = 5) {
        return this.feedbackHistory.slice(-count);
    }

    clearHistory() {
        this.feedbackHistory = [];
        this.scoreHistory = [];
    }

    // Format feedback for display
    formatFeedback(feedbackArray) {
        return feedbackArray.map(msg => {
            let feedbackClass = 'feedback-item';
            
            if (msg.includes('✅')) {
                feedbackClass += ' success';
            } else if (msg.includes('⚠️')) {
                feedbackClass += ' warning';
            } else if (msg.includes('❌')) {
                feedbackClass += ' error';
            }

            return `<div class="${feedbackClass}">${msg}</div>`;
        }).join('');
    }
}

console.log('Sports analyzer module loaded');
