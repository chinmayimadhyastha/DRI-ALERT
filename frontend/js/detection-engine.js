class DetectionEngine {
    constructor() {
        this.EAR_THRESHOLD = 0.21; // Eyes closed threshold
        this.MAR_THRESHOLD = 0.6; // Yawn threshold
        this.EYE_CLOSED_FRAMES = 15; // Frames before alert (approx 1.5 sec)
        this.YAWN_FRAMES = 10;
        this.eyeClosedCounter = 0;
        this.yawnCounter = 0;
        this.totalBlinks = 0;
        this.totalYawns = 0;
        console.log('🔍 Detection Engine initialized');
        console.log(`📊 Thresholds: EAR=${this.EAR_THRESHOLD}, MAR=${this.MAR_THRESHOLD}`);
    }

    calculateEAR(eye) {
    // Get eye landmarks (face-api.js format: array of {x, y} objects)
    // Correct indices for 68-point model
    const p1 = eye[1]; // Upper eyelid
    const p2 = eye[5]; // Lower eyelid
    const p3 = eye[2]; // Upper eyelid middle
    const p4 = eye[4]; // Lower eyelid middle
    const p5 = eye[0]; // Left corner
    const p6 = eye[3]; // Right corner
    
    // Calculate vertical distances
    const vertical1 = Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2));
    const vertical2 = Math.sqrt(Math.pow(p4.x - p3.x, 2) + Math.pow(p4.y - p3.y, 2));
    
    // Calculate horizontal distance
    const horizontal = Math.sqrt(Math.pow(p6.x - p5.x, 2) + Math.pow(p6.y - p5.y, 2));
    
    // EAR formula
    const ear = (vertical1 + vertical2) / (2.0 * horizontal);
    return ear;
}

    calculateMAR(mouth) {
        // Get mouth landmarks
        const p1 = mouth[13]; // Upper lip center
        const p2 = mouth[19]; // Lower lip center
        const p3 = mouth[14]; // Upper lip
        const p4 = mouth[18]; // Lower lip
        const p5 = mouth[0]; // Left corner
        const p6 = mouth[6]; // Right corner

        // Calculate vertical distances
        const vertical1 = Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2));
        const vertical2 = Math.sqrt(Math.pow(p4.x - p3.x, 2) + Math.pow(p4.y - p3.y, 2));

        // Calculate horizontal distance
        const horizontal = Math.sqrt(Math.pow(p6.x - p5.x, 2) + Math.pow(p6.y - p5.y, 2));

        // MAR formula
        const mar = (vertical1 + vertical2) / (2.0 * horizontal);
        return mar;
    } // FIX: Added missing closing brace

    analyzeFrame(detection) {
        if (!detection || !detection.landmarks) {
            return {
                status: 'no_face',
                ear: 0,
                mar: 0,
                drowsinessScore: 0,
                riskLevel: 'None',
                message: 'No face detected'
            };
        }

        // Get landmarks
        const leftEye = detection.landmarks.getLeftEye();
        const rightEye = detection.landmarks.getRightEye();
        const mouth = detection.landmarks.getMouth();

        // Calculate ratios
        const leftEAR = this.calculateEAR(leftEye);
        const rightEAR = this.calculateEAR(rightEye);
        const ear = (leftEAR + rightEAR) / 2.0;
        const mar = this.calculateMAR(mouth);

        // Initialize result
        let status = 'normal';
        let riskLevel = 'Low';
        let drowsinessScore = 0;
        let message = 'Driver alert';
        let alertTriggered = false;

        // Check for closed eyes
        if (ear < this.EAR_THRESHOLD) {
            this.eyeClosedCounter++;
            if (this.eyeClosedCounter >= this.EYE_CLOSED_FRAMES) {
                status = 'drowsy';
                riskLevel = 'High';
                drowsinessScore = 90;
                message = '⚠️ DROWSINESS DETECTED! Eyes closed for too long!';
                alertTriggered = true;
            } else {
                status = 'warning';
                riskLevel = 'Medium';
                drowsinessScore = 50;
                message = '⚠️ Warning: Eyes closing';
            }
        } else {
            // Eyes are open
            if (this.eyeClosedCounter >= 3) {
                this.totalBlinks++;
                console.log(`👁️ Blink detected! Total: ${this.totalBlinks}`);
            }
            this.eyeClosedCounter = 0;
        }

        // Check for yawning
        if (mar > this.MAR_THRESHOLD) {
            this.yawnCounter++;
            if (this.yawnCounter >= this.YAWN_FRAMES) {
                if (status !== 'drowsy') {
                    status = 'yawning';
                    riskLevel = 'Medium';
                    drowsinessScore = Math.max(drowsinessScore, 60);
                    message = '😮 YAWN DETECTED!';
                }
                this.totalYawns++;
                this.yawnCounter = 0;
                console.log(`😮 Yawn detected! Total: ${this.totalYawns}`);
            }
        } else {
            this.yawnCounter = 0;
        }

        // Log current values every 30 frames
        if (Math.random() < 0.03) {
            console.log(`📊 EAR: ${ear.toFixed(3)}, MAR: ${mar.toFixed(3)}, Status: ${status}`);
        }

        return {
            status,
            ear: ear.toFixed(3),
            mar: mar.toFixed(3),
            drowsinessScore,
            riskLevel,
            message,
            alertTriggered,
            blinks: this.totalBlinks,
            yawns: this.totalYawns,
            eyeClosedFrames: this.eyeClosedCounter
        };
    } // FIX: Added missing closing brace

    reset() {
        this.eyeClosedCounter = 0;
        this.yawnCounter = 0;
        this.totalBlinks = 0;
        this.totalYawns = 0;
    }
}

// Make it globally available
window.DetectionEngine = DetectionEngine;
