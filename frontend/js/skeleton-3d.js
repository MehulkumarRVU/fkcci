// PocketCoach AI - Live 3D Skeleton Avatar ("Digital Twin")
//
// Renders the athlete's real-time pose as a mirrored 3D skeleton using
// MediaPipe's x,y,z,visibility landmarks. MediaPipe has always computed the
// z (depth) coordinate and pose-detection.js's landmarksToArray() already
// forwards it to the backend, but nothing anywhere consumed it - all
// drawing/analysis was 2D-only. This is purely additive: it doesn't touch
// the existing 2D canvas drawing or local/backend analysis pipeline.

const SKELETON_BONES = [
    [11, 12], [11, 13], [13, 15], [12, 14], [14, 16],
    [11, 23], [12, 24], [23, 24], [23, 25], [25, 27], [24, 26], [26, 28],
];

const THREE_CDN_URL = 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js';

function loadThreeJs() {
    if (window.THREE) return Promise.resolve();
    if (loadThreeJs._promise) return loadThreeJs._promise;
    loadThreeJs._promise = new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = THREE_CDN_URL;
        script.onload = () => resolve();
        script.onerror = () => reject(new Error('Failed to load three.js'));
        document.head.appendChild(script);
    });
    return loadThreeJs._promise;
}

class Skeleton3D {
    constructor(container) {
        this.container = container;
        this.ready = false;
        this.active = false;
        this.joints = [];
        this.bones = [];
    }

    async init() {
        if (this.ready) return;
        await loadThreeJs();
        const THREE = window.THREE;
        const width = this.container.clientWidth || 480;
        const height = this.container.clientHeight || 360;

        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0b1220);
        this.camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
        this.camera.position.set(0, 0, 3.2);

        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(width, height);
        this.container.innerHTML = '';
        this.container.appendChild(this.renderer.domElement);

        this.scene.add(new THREE.AmbientLight(0xffffff, 0.8));
        const point = new THREE.PointLight(0xffffff, 0.6);
        point.position.set(2, 2, 3);
        this.scene.add(point);

        const jointGeometry = new THREE.SphereGeometry(0.035, 12, 12);
        for (let i = 0; i < 33; i++) {
            const material = new THREE.MeshStandardMaterial({ color: 0x22c55e });
            const mesh = new THREE.Mesh(jointGeometry, material);
            mesh.visible = false;
            this.scene.add(mesh);
            this.joints.push(mesh);
        }

        SKELETON_BONES.forEach(() => {
            const material = new THREE.LineBasicMaterial({ color: 0x60a5fa, linewidth: 2 });
            const geometry = new THREE.BufferGeometry().setFromPoints([
                new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 0, 0)
            ]);
            const line = new THREE.Line(geometry, material);
            line.visible = false;
            this.scene.add(line);
            this.bones.push(line);
        });

        this.ready = true;
        this._renderLoop();
    }

    _renderLoop() {
        requestAnimationFrame(() => this._renderLoop());
        if (this.renderer) {
            this.renderer.render(this.scene, this.camera);
        }
    }

    _toVector3(landmark) {
        const THREE = window.THREE;
        // MediaPipe: x,y normalized [0,1] image space (y-down), z roughly
        // hip-depth-relative (same order of magnitude as x). Mapped into a
        // centered, y-up, mirrored (front-facing) three.js scene.
        const x = -(landmark.x - 0.5) * 2.2;
        const y = -(landmark.y - 0.5) * 2.2;
        const z = -(landmark.z || 0) * 2.2;
        return new THREE.Vector3(x, y, z);
    }

    updateFromLandmarks(landmarks) {
        if (!this.ready || !this.active || !landmarks) return;

        for (let i = 0; i < this.joints.length && i < landmarks.length; i++) {
            const lm = landmarks[i];
            const visible = (lm.visibility || 0) > 0.5;
            this.joints[i].visible = visible;
            if (visible) {
                this.joints[i].position.copy(this._toVector3(lm));
            }
        }

        SKELETON_BONES.forEach(([a, b], idx) => {
            const line = this.bones[idx];
            const la = landmarks[a];
            const lb = landmarks[b];
            const visible = la && lb && (la.visibility || 0) > 0.5 && (lb.visibility || 0) > 0.5;
            line.visible = visible;
            if (visible) {
                const pa = this._toVector3(la);
                const pb = this._toVector3(lb);
                const positions = line.geometry.attributes.position;
                positions.setXYZ(0, pa.x, pa.y, pa.z);
                positions.setXYZ(1, pb.x, pb.y, pb.z);
                positions.needsUpdate = true;
            }
        });
    }

    // Color-codes joints from server-computed deviations (ideal-form
    // overlay, Phase 6): { landmarkIndex: "low"|"medium"|"high" }. Reuses
    // the backend's deviation computation instead of re-implementing
    // range-check logic in JS - avoids the client/server threshold drift
    // that happened before this refactor.
    renderDeviation(deviations) {
        if (!this.ready || !deviations) return;
        Object.entries(deviations).forEach(([jointIndex, severity]) => {
            const idx = parseInt(jointIndex, 10);
            const joint = this.joints[idx];
            if (!joint) return;
            const color = severity === 'high' ? 0xef4444 : severity === 'medium' ? 0xf59e0b : 0x22c55e;
            joint.material.color.set(color);
        });
    }

    resetDeviationColors() {
        this.joints.forEach((joint) => joint.material.color.set(0x22c55e));
    }

    show() {
        this.active = true;
        this.container.style.display = 'block';
    }

    hide() {
        this.active = false;
        this.container.style.display = 'none';
    }

    isActive() {
        return this.active;
    }
}

console.log('Skeleton 3D module loaded');
