// PocketCoach AI - Pose Detection Module
// This module handles MediaPipe Pose detection

class PoseDetector {
    constructor() {
        this.pose = null;
        this.camera = null;
        this.isRunning = false;
        this.onResultsCallback = null;
        this.videoElement = null;
        this.canvasElement = null;
        this.canvasCtx = null;
        this.lastFrameTime = Date.now();
        this.fps = 0;
        // Opt-in background segmentation ("subject isolation") - off by
        // default since it's WASM-heavy and changes the whole visual.
        this.isolateSubject = false;
    }

    async initialize(videoElement, canvasElement) {
        this.videoElement = videoElement;
        this.canvasElement = canvasElement;
        this.canvasCtx = canvasElement.getContext('2d');

        // Initialize MediaPipe Pose
        this.pose = new Pose({
            locateFile: (file) => {
                return `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`;
            }
        });

        this.pose.setOptions({
            // 2 = MediaPipe's most accurate (heaviest) landmark model - was
            // 1 (the mid-tier model), traded for a real accuracy gain since
            // this runs on the browser's GPU/WASM path, not a constrained
            // mobile CPU.
            modelComplexity: 2,
            smoothLandmarks: true,
            enableSegmentation: true,
            smoothSegmentation: true,
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5
        });

        this.pose.onResults((results) => this.onResults(results));
        
        console.log('Pose detector initialized');
    }

    async startCamera() {
        if (this.isRunning) return;

        let stream = null;
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            });

            this.videoElement.srcObject = stream;
            this.videoElement.muted = true;
            this.videoElement.setAttribute('playsinline', 'true');
            this.videoElement.setAttribute('autoplay', 'true');
            
            await new Promise((resolve) => {
                this.videoElement.onloadedmetadata = () => {
                    resolve();
                };
            });

            await this.videoElement.play();

            this.canvasElement.width = this.videoElement.videoWidth;
            this.canvasElement.height = this.videoElement.videoHeight;

            this.isRunning = true;
            this.detectFrame();
            
            console.log('Camera started');
            return true;

        } catch (error) {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
            if (this.videoElement) {
                this.videoElement.srcObject = null;
            }
            console.error('Error starting camera:', error);
            alert('Unable to access camera. Please ensure camera permissions are granted.');
            return false;
        }
    }

    stopCamera() {
        this.isRunning = false;

        if (this.videoElement && this.videoElement.srcObject) {
            const tracks = this.videoElement.srcObject.getTracks();
            tracks.forEach(track => track.stop());
            this.videoElement.srcObject = null;
        }

        // Clear canvas
        if (this.canvasCtx) {
            this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
        }

        console.log('Camera stopped');
    }

    async detectFrame() {
        if (!this.isRunning) return;

        if (this.videoElement.readyState === this.videoElement.HAVE_ENOUGH_DATA) {
            await this.pose.send({ image: this.videoElement });
        }

        requestAnimationFrame(() => this.detectFrame());
    }

    onResults(results) {
        // Calculate FPS
        const now = Date.now();
        this.fps = Math.round(1000 / (now - this.lastFrameTime));
        this.lastFrameTime = now;

        // Clear canvas
        this.canvasCtx.save();
        this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);

        // Subject isolation: paint an opaque composite (person over a
        // solid backdrop) that covers the raw <video> element sitting
        // beneath this canvas - off by default, toggled via setIsolateSubject.
        if (this.isolateSubject && results.segmentationMask) {
            this.drawSubjectIsolation(results);
        }

        // Draw pose landmarks if detected
        if (results.poseLandmarks) {
            this.drawLandmarks(results.poseLandmarks);
            this.drawConnections(results.poseLandmarks);
        }

        this.canvasCtx.restore();

        // Call callback with results
        if (this.onResultsCallback && results.poseLandmarks) {
            this.onResultsCallback(results.poseLandmarks);
        }
    }

    drawSubjectIsolation(results) {
        const ctx = this.canvasCtx;
        const w = this.canvasElement.width;
        const h = this.canvasElement.height;

        // Keep only the person: draw the segmentation mask, then use it
        // as an alpha mask to composite in the matching video frame.
        ctx.drawImage(results.segmentationMask, 0, 0, w, h);
        ctx.globalCompositeOperation = 'source-in';
        ctx.drawImage(results.image, 0, 0, w, h);

        // Solid backdrop behind the isolated person, replacing the
        // original background.
        ctx.globalCompositeOperation = 'destination-over';
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(0, 0, w, h);

        ctx.globalCompositeOperation = 'source-over';
    }

    setIsolateSubject(enabled) {
        this.isolateSubject = enabled;
    }

    drawLandmarks(landmarks) {
        // Draw individual landmarks as circles
        landmarks.forEach((landmark, index) => {
            if (landmark.visibility > 0.5) {
                const x = landmark.x * this.canvasElement.width;
                const y = landmark.y * this.canvasElement.height;

                this.canvasCtx.beginPath();
                this.canvasCtx.arc(x, y, 5, 0, 2 * Math.PI);
                this.canvasCtx.fillStyle = '#00ff00';
                this.canvasCtx.fill();
            }
        });
    }

    drawConnections(landmarks) {
        // Define pose connections (simplified)
        const connections = [
            [11, 12], // Shoulders
            [11, 13], [13, 15], // Left arm
            [12, 14], [14, 16], // Right arm
            [11, 23], [12, 24], // Torso
            [23, 24], // Hips
            [23, 25], [25, 27], // Left leg
            [24, 26], [26, 28], // Right leg
        ];

        this.canvasCtx.strokeStyle = '#00ff00';
        this.canvasCtx.lineWidth = 3;

        connections.forEach(([startIdx, endIdx]) => {
            const start = landmarks[startIdx];
            const end = landmarks[endIdx];

            if (start.visibility > 0.5 && end.visibility > 0.5) {
                const startX = start.x * this.canvasElement.width;
                const startY = start.y * this.canvasElement.height;
                const endX = end.x * this.canvasElement.width;
                const endY = end.y * this.canvasElement.height;

                this.canvasCtx.beginPath();
                this.canvasCtx.moveTo(startX, startY);
                this.canvasCtx.lineTo(endX, endY);
                this.canvasCtx.stroke();
            }
        });
    }

    setOnResultsCallback(callback) {
        this.onResultsCallback = callback;
    }

    getFPS() {
        return this.fps;
    }

    // Convert landmarks to simple format for API
    landmarksToArray(landmarks) {
        return landmarks.map(lm => ({
            x: lm.x,
            y: lm.y,
            z: lm.z,
            visibility: lm.visibility
        }));
    }

    getLandmarkQuality(landmarks) {
        const keyIndices = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28];
        const valid = keyIndices.filter(index => {
            const landmark = landmarks[index];
            return landmark
                && Number.isFinite(landmark.x)
                && Number.isFinite(landmark.y)
                && Number.isFinite(landmark.z)
                && landmark.visibility >= 0.5;
        }).length;
        return {
            coverage: valid / keyIndices.length,
            reliable: valid / keyIndices.length >= 0.5
        };
    }
}

console.log('Pose detection module loaded');
