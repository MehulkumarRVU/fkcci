// PocketCoach AI - Sports Analyzer Module (Client-side)
// Provides basic angle calculations and feedback formatting

class SportsAnalyzer {
    constructor(sportType, sessionType = 'drill') {
        this.sportType = sportType;
        this.sessionType = sessionType;
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
        const racketSports = ['table_tennis', 'badminton', 'tennis', 'pickleball', 'squash'];
        const combatSports = ['boxing', 'kickboxing', 'muay_thai', 'karate', 'taekwondo', 'judo', 'bjj', 'wrestling', 'fencing'];
        const courtSports = ['basketball', 'volleyball', 'handball'];
        const fitnessSports = ['ai_gym_coach', 'stretching', 'mobility_training', 'rehabilitation', 'home_workouts', 'calisthenics'];

        if (this.sportType === 'boxing') {
            this.analyzeBoxingLocal(landmarks, skillName, feedback);
        } else if (this.sportType === 'table_tennis') {
            this.analyzeTableTennisLocal(landmarks, skillName, feedback);
        } else if (this.sportType === 'badminton') {
            this.analyzeBadmintonLocal(landmarks, skillName, feedback);
        } else if (racketSports.includes(this.sportType)) {
            this.analyzeRacketLocal(landmarks, skillName, feedback);
        } else if (combatSports.includes(this.sportType)) {
            this.analyzeCombatLocal(landmarks, skillName, feedback);
        } else if (courtSports.includes(this.sportType)) {
            this.analyzeCourtLocal(landmarks, skillName, feedback);
        } else if (this.sportType === 'indoor_archery') {
            this.analyzeArcheryLocal(landmarks, skillName, feedback);
        } else if (fitnessSports.includes(this.sportType)) {
            this.analyzeFitnessLocal(landmarks, skillName, feedback);
        }

        this.applySessionTypeFocus(landmarks, skillName, feedback);

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

    analyzeBadmintonLocal(landmarks, skillName, feedback) {
        const leftWrist = landmarks[15];
        const rightWrist = landmarks[16];
        const leftElbow = landmarks[13];
        const rightElbow = landmarks[14];

        if (leftWrist && rightWrist && leftElbow && rightElbow) {
            if (skillName.toLowerCase().includes('smash') || skillName.toLowerCase().includes('clear')) {
                const leftArmAngle = this.calculateAngle(landmarks[11], leftElbow, leftWrist);
                const rightArmAngle = this.calculateAngle(landmarks[12], rightElbow, rightWrist);
                if (leftArmAngle < 140 && rightArmAngle < 140) {
                    feedback.push('✅ Good racket extension for powerful badminton shots');
                } else {
                    feedback.push('⚠️ Extend your arm more for better shuttle contact');
                }
            }

            if (skillName.toLowerCase().includes('net') || skillName.toLowerCase().includes('drop')) {
                if (rightWrist && rightElbow && rightWrist.y < rightElbow.y) {
                    feedback.push('✅ Nice wrist control for delicate net play');
                } else {
                    feedback.push('⚠️ Keep your racket hand higher for net precision');
                }
            }
        }
    }

    analyzeRacketLocal(landmarks, skillName, feedback) {
        // Generic racket-sport checks: stance, knee bend, racket extension
        this.analyzeTableTennisLocal(landmarks, skillName, feedback);
        // reuse badminton extension logic for racket extension checks
        try {
            this.analyzeBadmintonLocal(landmarks, skillName, feedback);
        } catch (e) {
            // ignore
        }
    }

    analyzeCombatLocal(landmarks, skillName, feedback) {
        // Basic guard and hip rotation checks for striking arts
        const leftWrist = landmarks[15];
        const rightWrist = landmarks[16];
        const leftShoulder = landmarks[11];
        const rightShoulder = landmarks[12];

        if (leftWrist && rightWrist && leftShoulder && rightShoulder) {
            const avgShoulderY = (leftShoulder.y + rightShoulder.y) / 2;
            if (leftWrist.y > avgShoulderY + 0.12 || rightWrist.y > avgShoulderY + 0.12) {
                feedback.push('❌ Keep your hands higher to protect your head');
            } else {
                feedback.push('✅ Good guard position');
            }
        }

        // Hip rotation hint (simple)
        const leftHip = landmarks[23];
        const rightHip = landmarks[24];
        if (leftHip && rightHip) {
            const hipDiff = Math.abs(leftHip.x - rightHip.x);
            if (hipDiff < 0.05) {
                feedback.push('⚠️ Try rotating your hips more for power');
            }
        }
    }

    analyzeCourtLocal(landmarks, skillName, feedback) {
        // Jump/landing and knee bend checks useful for basketball/volleyball/handball
        this.analyzeTableTennisLocal(landmarks, skillName, feedback);
        const leftKnee = landmarks[25];
        const rightKnee = landmarks[26];
        if (leftKnee && rightKnee && leftKnee.visibility > 0.5 && rightKnee.visibility > 0.5) {
            const kneeDiff = Math.abs(leftKnee.y - rightKnee.y);
            if (kneeDiff > 0.08) {
                feedback.push('⚠️ Uneven leg bend — try to land evenly');
            }
        }
    }

    analyzeArcheryLocal(landmarks, skillName, feedback) {
        // Simple alignment check for archery stance and draw
        const leftShoulder = landmarks[11];
        const rightShoulder = landmarks[12];
        const nose = landmarks[0];
        if (leftShoulder && rightShoulder && nose) {
            const midShoulderX = (leftShoulder.x + rightShoulder.x) / 2;
            const eyeOffset = Math.abs(nose.x - midShoulderX);
            if (eyeOffset > 0.06) {
                feedback.push('⚠️ Aim alignment off — try to square your shoulders to target');
            } else {
                feedback.push('✅ Good alignment towards target');
            }
        }
    }

    analyzeFitnessLocal(landmarks, skillName, feedback) {
        // Generic fitness checks: spine straightness, knee bend, range of motion
        const leftShoulder = landmarks[11];
        const rightShoulder = landmarks[12];
        const leftHip = landmarks[23];
        const rightHip = landmarks[24];
        if (leftShoulder && rightShoulder && leftHip && rightHip) {
            const shoulderMid = (leftShoulder.y + rightShoulder.y) / 2;
            const hipMid = (leftHip.y + rightHip.y) / 2;
            if (Math.abs(shoulderMid - hipMid) > 0.35) {
                feedback.push('⚠️ Keep your torso upright and avoid excessive lean');
            } else {
                feedback.push('✅ Good torso posture');
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
