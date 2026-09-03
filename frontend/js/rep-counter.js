// PocketCoach AI - Live Rep/Combo/Jump Counter (client-side)
// Mirrors the exact peak/trough state-machine logic already proven
// server-side in analyze_session() for these three sports, so the live
// count and the end-of-session server-computed count agree:
//   - backend/app/pose_engine/sports/ai_gym_coach_analyzer.py (estimated_reps)
//   - backend/app/pose_engine/sports/boxing_analyzer.py (combination_count)
//   - backend/app/pose_engine/sports/basketball_analyzer.py (estimated_jumps)
// Sports outside this set have no server-side count to match, so
// hasCounter() is false and no badge is shown - never a fabricated number.

function repCounterCalcAngle(a, b, c) {
    if (!a || !b || !c) return null;
    if ((a.visibility !== undefined && a.visibility < 0.5) ||
        (b.visibility !== undefined && b.visibility < 0.5) ||
        (c.visibility !== undefined && c.visibility < 0.5)) {
        return null;
    }
    const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
    let angle = Math.abs(radians * 180.0 / Math.PI);
    if (angle > 180.0) angle = 360 - angle;
    return angle;
}

class RepCounter {
    constructor(sportType, skillName, dominantHand = 'right') {
        this.sportType = sportType;
        this.skillNameLower = (skillName || '').toLowerCase();
        this.dominantHand = dominantHand === 'left' ? 'left' : 'right';
        this.mode = this._detectMode();

        // Squat/push-up rep state
        this.inDown = false;
        this.reps = 0;

        // Boxing combo state
        this.currentComboRun = 0;
        this.combos = 0;

        // Jump state - needs a 3-frame window to detect a local minimum
        this.kneeHeightBuffer = [];
        this.jumps = 0;

        // Optional athlete-declared goal, set via setTargetReps() - purely
        // a UI target, doesn't change the counting algorithms above.
        this.targetReps = null;
    }

    setTargetReps(target) {
        this.targetReps = target && target > 0 ? target : null;
    }

    goalReached() {
        return this.targetReps !== null && this.getCount() >= this.targetReps;
    }

    _detectMode() {
        if (this.sportType === 'ai_gym_coach') {
            const isPushUp = this.skillNameLower.includes('push');
            return isPushUp ? 'pushup' : 'squat';
        }
        if (this.sportType === 'boxing') return 'combo';
        if (this.sportType === 'basketball') return 'jump';
        return null;
    }

    hasCounter() {
        return this.mode !== null;
    }

    getLabel() {
        switch (this.mode) {
            case 'squat':
            case 'pushup': return '🔢 Reps';
            case 'combo': return '🥊 Combos';
            case 'jump': return '🏀 Jumps';
            default: return '';
        }
    }

    getCount() {
        switch (this.mode) {
            case 'squat':
            case 'pushup': return this.reps;
            case 'combo': return this.combos;
            case 'jump': return this.jumps;
            default: return 0;
        }
    }

    // landmarks: raw MediaPipe pose landmarks array (33 entries, {x,y,z,visibility})
    update(landmarks) {
        if (this.mode === 'squat' || this.mode === 'pushup') this._updateRep(landmarks);
        else if (this.mode === 'combo') this._updateCombo(landmarks);
        else if (this.mode === 'jump') this._updateJump(landmarks);
    }

    _updateRep(landmarks) {
        const angle = this.mode === 'pushup'
            ? repCounterCalcAngle(landmarks[11], landmarks[13], landmarks[15]) // left shoulder-elbow-wrist
            : repCounterCalcAngle(landmarks[23], landmarks[25], landmarks[27]); // left hip-knee-ankle
        if (angle === null) return;

        const [downThreshold, upThreshold] = this.mode === 'pushup' ? [100, 150] : [140, 160];
        if (angle < downThreshold && !this.inDown) {
            this.inDown = true;
        }
        if (angle >= upThreshold && this.inDown) {
            this.reps++;
            this.inDown = false;
        }
    }

    _updateCombo(landmarks) {
        const idx = this.dominantHand === 'left'
            ? { shoulder: 11, elbow: 13, wrist: 15 }
            : { shoulder: 12, elbow: 14, wrist: 16 };
        const angle = repCounterCalcAngle(landmarks[idx.shoulder], landmarks[idx.elbow], landmarks[idx.wrist]);

        if (angle === null) {
            this.currentComboRun = 0;
            return;
        }
        if (angle > 140) {
            this.currentComboRun++;
        } else {
            if (this.currentComboRun >= 2) this.combos++;
            this.currentComboRun = 0;
        }
    }

    _updateJump(landmarks) {
        const leftKnee = landmarks[25];
        const rightKnee = landmarks[26];
        if (!leftKnee || !rightKnee) return;

        this.kneeHeightBuffer.push((leftKnee.y + rightKnee.y) / 2);
        if (this.kneeHeightBuffer.length > 3) this.kneeHeightBuffer.shift();

        if (this.kneeHeightBuffer.length === 3) {
            const [prev, mid, next] = this.kneeHeightBuffer;
            if (mid < prev - 0.02 && mid < next - 0.02) {
                this.jumps++;
            }
        }
    }
}

console.log('Rep counter module loaded');
