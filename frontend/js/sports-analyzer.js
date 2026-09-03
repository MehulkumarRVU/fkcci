// PocketCoach AI - Sports Analyzer Module (Client-side)
// Provides basic angle calculations and feedback formatting

class SportsAnalyzer {
    constructor(sportType, sessionType = 'drill', dominantHand = 'right', skillLevel = 'beginner') {
        this.sportType = sportType;
        this.sessionType = sessionType;
        this.dominantHand = (dominantHand || 'right').toLowerCase() === 'left' ? 'left' : 'right';
        this.skillLevel = skillLevel || 'beginner';
        this.feedbackHistory = [];
        this.scoreHistory = [];
        this.techniqueHistory = [];
        this.balanceHistory = [];
        // Downsampled {landmarks, timestamp} buffer sent to
        // /api/analysis/analyze at session end for real, backend-computed
        // technique/balance/reaction scores instead of a client-only average.
        this.poseBuffer = [];
        this.lastBufferedAt = 0;
        this.bufferIntervalMs = 500;
        this.maxBufferSize = 600;
    }

    // Dominant-side landmark indices (MediaPipe Pose layout).
    dominantIndices() {
        return this.dominantHand === 'left'
            ? { shoulder: 11, elbow: 13, wrist: 15 }
            : { shoulder: 12, elbow: 14, wrist: 16 };
    }

    addPoseSample(landmarksArray, timestamp) {
        if (timestamp - this.lastBufferedAt < this.bufferIntervalMs) return;
        this.lastBufferedAt = timestamp;
        this.poseBuffer.push({ landmarks: landmarksArray, timestamp: timestamp / 1000 });
        if (this.poseBuffer.length > this.maxBufferSize) {
            this.poseBuffer.shift();
        }
    }

    getPoseBuffer() {
        return this.poseBuffer;
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

        // Check balance (ankle width relative to hip width - mirrors backend
        // PoseUtils.analyze_balance so client and server feedback agree)
        const leftAnkle = landmarks[27];
        const rightAnkle = landmarks[28];
        const leftHip = landmarks[23];
        const rightHip = landmarks[24];

        if (leftAnkle && rightAnkle && leftHip && rightHip &&
            leftAnkle.visibility > 0.5 && rightAnkle.visibility > 0.5 &&
            leftHip.visibility > 0.5 && rightHip.visibility > 0.5) {

            const ankleWidth = Math.abs(leftAnkle.x - rightAnkle.x);
            const hipWidth = Math.abs(leftHip.x - rightHip.x);
            const bal = (typeof PoseThresholds !== 'undefined') ? PoseThresholds.balance : { narrowRatio: 0.8, wideRatio: 2.0 };

            if (hipWidth > 0 && ankleWidth < hipWidth * bal.narrowRatio) {
                feedback.push('⚠️ Widen your stance for better balance');
                score -= 10;
            } else if (hipWidth > 0 && ankleWidth > hipWidth * bal.wideRatio) {
                feedback.push('⚠️ Stance too wide - bring feet closer');
                score -= 10;
            } else {
                feedback.push('✅ Good stance width');
            }
        }

        // Sport-specific checks. motogp/formula1 are intentionally excluded -
        // seated/helmeted/vehicle-occluded activities aren't assessable via
        // webcam pose analysis (mirrors backend AnalyzerFactory.NOT_POSE_COACHABLE).
        const racketSports = ['table_tennis', 'badminton', 'tennis', 'pickleball', 'squash'];
        const combatSports = ['boxing', 'kickboxing', 'muay_thai', 'karate', 'taekwondo', 'judo', 'bjj', 'wrestling', 'fencing', 'kabaddi', 'wwe'];
        const courtSports = ['basketball', 'volleyball', 'handball', 'football', 'baseball', 'cricket', 'hockey', 'ice_hockey'];
        const archerySports = ['indoor_archery', 'shooting'];
        const fitnessSports = ['ai_gym_coach', 'weight_lifting', 'stretching', 'mobility_training', 'rehabilitation', 'home_workouts', 'calisthenics', 'gymnastics', 'swimming'];

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
        } else if (archerySports.includes(this.sportType)) {
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
        // Guard check applies regardless of which skill is being drilled.
        const leftWrist = landmarks[15];
        const rightWrist = landmarks[16];
        const leftShoulder = landmarks[11];
        const rightShoulder = landmarks[12];

        if (leftWrist && rightWrist && leftShoulder && rightShoulder) {
            const avgShoulderY = (leftShoulder.y + rightShoulder.y) / 2;
            if (leftWrist.y > avgShoulderY + 0.1 || rightWrist.y > avgShoulderY + 0.1) {
                feedback.push('❌ Keep hands up - protect your face');
            } else {
                feedback.push('✅ Good guard position');
            }
        }

        // Skill-specific checks - previously skillName was accepted but
        // never read, so every boxing skill (Jab, Cross, Hook, Uppercut...)
        // showed the exact same single guard-position message.
        const skill = (skillName || '').toLowerCase();
        const leftElbow = landmarks[13];
        const rightElbow = landmarks[14];
        // Jab/Cross/Hook/Uppercut/Slip all need the full arm chain (plus
        // shoulders) confidently visible - MediaPipe can drop a landmark on
        // partial occlusion, and calculateAngle throws on an undefined point.
        // Pivot/Footwork below only needs hips, so it's checked separately
        // rather than being gated behind arm visibility too.
        const armLandmarksReady = leftShoulder && rightShoulder && leftElbow && rightElbow && leftWrist && rightWrist;
        const needsArms = skill.includes('jab') || skill.includes('cross') || skill.includes('hook')
            || skill.includes('uppercut') || skill.includes('slip') || skill.includes('roll');

        if (needsArms && !armLandmarksReady) {
            // Not enough of the arm is visible to grade this skill this
            // frame - skip rather than risk a throw on a missing point.
        } else if (skill.includes('jab') || skill.includes('cross')) {
            const leftAngle = this.calculateAngle(leftShoulder, leftElbow, leftWrist);
            const rightAngle = this.calculateAngle(rightShoulder, rightElbow, rightWrist);
            const extension = Math.max(leftAngle, rightAngle);
            if (extension > 160) {
                feedback.push(`✅ Full extension on your ${skillName.toLowerCase()}`);
            } else if (extension > 140) {
                feedback.push(`⚠️ ${skillName} not fully extended - punch straighter through the target`);
            } else {
                feedback.push(`❌ ${skillName} too short - snap your arm fully out`);
            }
        } else if (skill.includes('hook')) {
            const leftAngle = this.calculateAngle(leftShoulder, leftElbow, leftWrist);
            const rightAngle = this.calculateAngle(rightShoulder, rightElbow, rightWrist);
            // Whichever elbow is closer to the ~90° hook bend is the hooking arm.
            const hookAngle = Math.abs(leftAngle - 90) < Math.abs(rightAngle - 90) ? leftAngle : rightAngle;
            if (hookAngle >= 80 && hookAngle <= 100) {
                feedback.push('✅ Good 90° elbow bend for your hook');
            } else if (hookAngle < 80) {
                feedback.push('⚠️ Hook elbow too tight - open up closer to a 90° bend');
            } else {
                feedback.push('⚠️ Hook elbow too wide - tuck in closer to a 90° bend');
            }
        } else if (skill.includes('uppercut')) {
            if (leftWrist.y < leftShoulder.y || rightWrist.y < rightShoulder.y) {
                feedback.push('✅ Good upward drive on your uppercut');
            } else {
                feedback.push('⚠️ Drive your uppercut upward through the target, not across');
            }
        } else if (skill.includes('slip') || skill.includes('roll')) {
            const nose = landmarks[0];
            const midShoulderX = (leftShoulder.x + rightShoulder.x) / 2;
            if (nose && Math.abs(nose.x - midShoulderX) > 0.05) {
                feedback.push('✅ Good head movement off the centerline');
            } else {
                feedback.push('⚠️ Move your head off centerline when slipping');
            }
        } else if (skill.includes('pivot') || skill.includes('footwork')) {
            const leftHip = landmarks[23];
            const rightHip = landmarks[24];
            if (leftHip && rightHip && Math.abs(leftHip.x - rightHip.x) < 0.12) {
                feedback.push('⚠️ Rotate your hips more through the pivot');
            } else {
                feedback.push('✅ Good hip rotation through the pivot');
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
            const t = (typeof PoseThresholds !== 'undefined') ? PoseThresholds.tableTennis.kneeFlexion : { high: 170 };

            if (kneeAngle > t.high) {
                feedback.push('⚠️ Bend your knees more for better reaction');
            }
        }
    }

    analyzeBadmintonLocal(landmarks, skillName, feedback) {
        // Racket arm resolved from the athlete's dominant hand instead of a
        // hardcoded side.
        const idx = this.dominantIndices();
        const shoulder = landmarks[idx.shoulder];
        const elbow = landmarks[idx.elbow];
        const wrist = landmarks[idx.wrist];
        const t = (typeof PoseThresholds !== 'undefined') ? PoseThresholds.badminton : { armExtensionOk: 140 };

        if (shoulder && elbow && wrist) {
            if (skillName.toLowerCase().includes('smash') || skillName.toLowerCase().includes('clear')) {
                const armAngle = this.calculateAngle(shoulder, elbow, wrist);
                if (armAngle >= (t.armExtensionOk || 130)) {
                    feedback.push('✅ Good racket extension for powerful badminton shots');
                } else {
                    feedback.push('⚠️ Extend your arm more for better shuttle contact');
                }
            }

            if (skillName.toLowerCase().includes('net') || skillName.toLowerCase().includes('drop')) {
                if (wrist.y < elbow.y) {
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

    // Appends a session-type-specific reminder. This was previously called
    // from analyzeLocally() but never defined, which threw on every frame
    // and silently broke live scoring/feedback entirely.
    applySessionTypeFocus(landmarks, skillName, feedback) {
        const hints = {
            drill: '🎯 Drill focus: repeat the motion cleanly, prioritize form over speed.',
            shadow: '🕺 Shadow focus: keep balance and control without impact.',
            sparring: '⚡ Sparring focus: watch your guard and reaction timing.',
            match_simulation: '🏆 Match focus: keep intensity and pacing realistic.'
        };
        const hint = hints[this.sessionType];
        if (hint) {
            feedback.push(hint);
        }
    }

    // Records a server-computed analysis result so session-end aggregates
    // (technique/balance) reflect real, independently measured values
    // instead of derivatives of a single local score.
    addServerResult(analysis) {
        if (typeof analysis.technique_accuracy === 'number') {
            this.techniqueHistory.push(analysis.technique_accuracy);
            if (this.techniqueHistory.length > 100) this.techniqueHistory.shift();
        }
        if (typeof analysis.balance_score === 'number') {
            this.balanceHistory.push(analysis.balance_score);
            if (this.balanceHistory.length > 100) this.balanceHistory.shift();
        }
    }

    getAverageTechnique() {
        if (this.techniqueHistory.length === 0) return null;
        const sum = this.techniqueHistory.reduce((a, b) => a + b, 0);
        return Math.round(sum / this.techniqueHistory.length);
    }

    getAverageBalance() {
        if (this.balanceHistory.length === 0) return null;
        const sum = this.balanceHistory.reduce((a, b) => a + b, 0);
        return Math.round(sum / this.balanceHistory.length);
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
