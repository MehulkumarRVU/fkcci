// PocketCoach AI - Shared pose-analysis thresholds (client-side)
//
// The backend (backend/app/pose_engine/) is authoritative - this file exists
// so the frontend's instant preliminary feedback uses the SAME numbers
// instead of independently-guessed ones that can silently drift out of sync
// (this happened before: the client's stance-width check used different
// thresholds than the backend's balance check and contradicted it live).
// Mirrors backend/app/pose_engine/shared/thresholds.py (balance ratios) and
// the per-sport analyzers' primary checks.

const PoseThresholds = {
    balance: {
        narrowRatio: 0.8,   // ankle_width < hip_width * narrowRatio -> too narrow
        wideRatio: 2.0,     // ankle_width > hip_width * wideRatio -> too wide
        levelDiff: 0.05,    // ankle y-difference beyond this -> uneven weight
    },
    tableTennis: {
        armExtension: { low: 130, high: 170 },
        kneeFlexion: { low: 140, high: 170 },
    },
    badminton: {
        armExtensionStrong: 150,
        armExtensionOk: 130,
        kneeBend: { low: 140, high: 170 },
    },
    boxing: {
        elbowTuck: { low: 60, high: 110 },
        punchFull: 160,
        punchPartial: 140,
        hookElbow: { low: 80, high: 100 },
    },
    racketGeneric: {
        armExtensionGood: 140,
        armExtensionOk: 120,
        kneeBend: { low: 130, high: 170 },
    },
    combatGeneric: {
        guardShoulderOffset: 0.0,   // wrists must be above avg shoulder y
        hipRotationMin: 0.08,
    },

    // Skill-level tolerance, mirroring backend shared/skill_profiles.py.
    // range_multiplier widens (>1) or narrows (<1) the acceptable range;
    // beginner gets the most slack, advanced the least.
    skillLevels: {
        beginner: { rangeMultiplier: 1.4 },
        intermediate: { rangeMultiplier: 1.0 },
        advanced: { rangeMultiplier: 0.7 },
    },

    widenRange(low, high, skillLevel) {
        const profile = this.skillLevels[(skillLevel || 'beginner').toLowerCase()] || this.skillLevels.beginner;
        const center = (low + high) / 2;
        const half = ((high - low) / 2) * profile.rangeMultiplier;
        return [center - half, center + half];
    },
};

if (typeof window !== 'undefined') {
    window.PoseThresholds = PoseThresholds;
}
