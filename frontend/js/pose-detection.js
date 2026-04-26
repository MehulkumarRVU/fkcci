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
            modelComplexity: 1,
            smoothLandmarks: true,
            enableSegmentation: false,
            smoothSegmentation: false,
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5
        });

        this.pose.onResults((results) => this.onResults(results));
        
        console.log('Pose detector initialized');
    }

    async startCamera() {
        if (this.isRunning) return;

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
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
            console.error('Error starting camera:', error);
            alert('Unable to access camera. Please ensure camera permissions are granted.');
            return false;
        }
    }

    stopCamera() {
        if (!this.isRunning) return;

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
}

console.log('Pose detection module loaded');
