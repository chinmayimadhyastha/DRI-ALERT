document.addEventListener("DOMContentLoaded", function () {
    console.log("🚀 Monitor Starting...");

    // CORRECT - Use consistent key
    const session = localStorage.getItem('driAlertsession');
    if (!session) {
        alert("Please login first!");
        window.location.href = "driAlert-complete.html";
        return;
    }

    try {
        const sessionData = JSON.parse(session);
        console.log("✅ Logged in as:", sessionData.user?.email);
    } catch (e) {
        alert("Invalid session!");
        window.location.href = "driAlert-complete.html";
        return;
    }

    initMonitor();
});

function initMonitor() {
    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas");
    const ctx = canvas.getContext("2d");
    const startBtn = document.getElementById("start-btn");
    const stopBtn = document.getElementById("stop-btn");
    const statusText = document.getElementById("status");
    const earDisplay = document.getElementById("ear-value");
    const marDisplay = document.getElementById("mar-value");
    const blinkDisplay = document.getElementById("blink-count");
    const yawnDisplay = document.getElementById("yawn-count");
    const alertBox = document.getElementById("alert-box");

    let isMonitoring = false;
    let stream = null;
    let animationId = null;

    // Detection thresholds
    const MAR_THRESHOLD = 0.6;
    const EYE_CLOSURE_THRESHOLD = 0.21;
    const DROWSY_FRAMES = 90;

    // State tracking
    let eyeClosedFrames = 0;
    let yawnFrames = 0;
    let totalBlinks = 0;
    let totalYawns = 0;
    let sessionStart = Date.now();
    let frameCount = 0;
    let lastSave = 0;
    let lastBeep = 0;
    let lastBackendCall = 0;

    if (!sessionStorage.getItem("monitor_session_id")) {
        sessionStorage.setItem("monitor_session_id", "session_" + Date.now());
    }

    // Fast distance calculation
    function fastDistance(p1, p2) {
        const dx = p2.x - p1.x, dy = p2.y - p1.y;
        return Math.sqrt(dx * dx + dy * dy);
    }

    // Calculate Eye Aspect Ratio
    function calculateEAR(eye) {
        const v1 = fastDistance(eye[1], eye[5]);
        const v2 = fastDistance(eye[2], eye[4]);
        const h = fastDistance(eye[0], eye[3]);
        return (v1 + v2) / (2.0 * h);
    }

    // Calculate Mouth Aspect Ratio
    function calculateMAR(mouth) {
        const v1 = fastDistance(mouth[13], mouth[19]);
        const v2 = fastDistance(mouth[14], mouth[18]);
        const h = fastDistance(mouth[0], mouth[6]);
        return (v1 + v2) / (2.0 * h);
    }

    // Update UI with detection results
    function updateUI(ear, mar, status) {
        if (earDisplay) earDisplay.textContent = ear.toFixed(3);
        if (marDisplay) marDisplay.textContent = mar.toFixed(3);
        if (statusText) statusText.textContent = status;
        if (blinkDisplay) blinkDisplay.textContent = totalBlinks;
        if (yawnDisplay) yawnDisplay.textContent = totalYawns;

        if (alertBox) {
            if (status === "DROWSY") {
                alertBox.style.display = "block";
                alertBox.style.background = "rgba(239, 68, 68, 0.95)";
                alertBox.textContent = "⚠️ DROWSINESS DETECTED!";
            } else if (status === "WARNING") {
                alertBox.style.display = "block";
                alertBox.style.background = "rgba(245, 158, 11, 0.95)";
                alertBox.textContent = "⚠️ Eyes closing...";
            } else if (status === "YAWNING") {
                alertBox.style.display = "block";
                alertBox.style.background = "rgba(59, 130, 246, 0.95)";
                alertBox.textContent = "😴 Yawn detected!";
            } else {
                alertBox.style.display = "none";
            }
        }
    }

    // Play alert beep
    function playBeep() {
        const now = Date.now();
        if (now - lastBeep < 1000) return;
        lastBeep = now;

        try {
            const audio = new (window.AudioContext || window.webkitAudioContext)();
            const osc = audio.createOscillator();
            const gain = audio.createGain();
            osc.connect(gain);
            gain.connect(audio.destination);
            osc.frequency.value = 800;
            gain.gain.setValueAtTime(0.3, audio.currentTime);
            osc.start();
            osc.stop(audio.currentTime + 0.2);
            console.log("🔊 BEEP!");
        } catch (e) {
            console.log("Beep failed");
        }
    }

    // Show home button
    function showHomeButton() {
        let homeBtn = document.getElementById("home-btn");
        if (!homeBtn) {
            homeBtn = document.createElement("button");
            homeBtn.id = "home-btn";
            homeBtn.innerHTML = "🏠 Back to Home";
            homeBtn.style.cssText = "position:fixed;bottom:30px;right:30px;padding:15px 30px;font-size:18px;font-weight:bold;color:white;background:linear-gradient(135deg,#667eea 0,#764ba2 100%);border:none;border-radius:12px;cursor:pointer;box-shadow:0 4px 15px rgba(0,0,0,0.3);z-index:10000;";
            homeBtn.onclick = () => window.location.href = "driAlert-complete.html";
            document.body.appendChild(homeBtn);
        }
        homeBtn.style.display = "block";
    }

    // Hide home button
    function hideHomeButton() {
        const homeBtn = document.getElementById("home-btn");
        if (homeBtn) homeBtn.style.display = "none";
    }

    // Process frame with backend detection
    async function processFrameWithBackend(imageData) {
        try {
            // Get token from session
            const session = localStorage.getItem('driAlertsession');
            let token = null;
            
            if (session) {
                try {
                    const sessionData = JSON.parse(session);
                    token = sessionData.token;
                } catch (e) {
                    console.log('No valid session');
                }
            }
            
            // Build headers
            const headers = {
                'Content-Type': 'application/json'
            };
            
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
            
            const response = await fetch('http://localhost:5000/api/detection/process-frame', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ frame: imageData })
            });
            
            const result = await response.json();
            
            // LOG THE DETECTION RESULTS
            console.log('🔍 Backend Detection:', {
                EAR: result.earvalue,
                MAR: result.marvalue,
                Score: result.sleepscore,
                Status: result.status,
                BlinkCount: result.blink_count,
                EyeClosureFrames: result.eye_closure_frames,
                Debug: result.debug_info
            });
            
            return result;
        } catch (error) {
            console.error('❌ Backend detection error:', error);
            return null;
        }
    }

    // Start monitoring
    async function startMonitoring() {
        if (isMonitoring) return;
        console.log('🚀 Starting...');

        try {
            hideHomeButton();
            
            // Check camera permission first
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Camera not supported in this browser');
            }

            // Request camera access
            stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: 640,
                    height: 480,
                    frameRate: 30,
                    facingMode: 'user'
                }
            });
            
            video.srcObject = stream;
            await video.play();

            // Load face detection models
            console.log('📦 Loading models...');
            await Promise.all([
                faceapi.nets.tinyFaceDetector.loadFromUri('https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js/weights'),
                faceapi.nets.faceLandmark68Net.loadFromUri('https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js/weights')
            ]);
            console.log('✅ Models loaded!');

            isMonitoring = true;
            if (startBtn) startBtn.disabled = true;
            if (stopBtn) stopBtn.disabled = false;

            // Reset counters
            eyeClosedFrames = 0;
            yawnFrames = 0;
            totalBlinks = 0;
            totalYawns = 0;
            sessionStart = Date.now();
            frameCount = 0;

            console.log('✅ Monitoring ACTIVE!');
            detectLoop();

        } catch (e) {
            console.error('❌ Error:', e);
            
            // Specific error messages
            if (e.name === 'NotAllowedError') {
                alert('❌ Camera access denied. Please allow camera permissions.');
            } else if (e.name === 'NotFoundError') {
                alert('❌ No camera found. Please connect a camera.');
            } else if (e.message.includes('not supported')) {
                alert('❌ Your browser does not support camera access.');
            } else {
                alert('❌ Camera error: ' + e.message);
            }
            
            showHomeButton();
        }
    }

    // Main detection loop
    function detectLoop() {
        if (!isMonitoring) return;

        faceapi
            .detectSingleFace(video, new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.5 }))
            .withFaceLandmarks()
            .then(async detection => {
                if (detection) {
                    const leftEye = detection.landmarks.getLeftEye();
                    const rightEye = detection.landmarks.getRightEye();
                    const mouth = detection.landmarks.getMouth();

                    const ear = (calculateEAR(leftEye) + calculateEAR(rightEye)) / 2.0;
                    const mar = calculateMAR(mouth);
                    let status = "ALERT";

                    // Eye closure detection
                    if (ear < EYE_CLOSURE_THRESHOLD) {
                        eyeClosedFrames++;
                        if (eyeClosedFrames % 30 === 0) {
                            playBeep();
                        }

                        if (eyeClosedFrames >= DROWSY_FRAMES) {
                            status = "DROWSY";
                        } else if (eyeClosedFrames >= 15) {
                            status = "WARNING";
                        }
                    } else {
                        if (eyeClosedFrames >= 1 && eyeClosedFrames < 10) {
                            totalBlinks++;
                        }
                        eyeClosedFrames = 0;
                    }

                    // Yawn detection
                    if (mar > MAR_THRESHOLD) {
                        yawnFrames++;
                        if (yawnFrames === 8) {
                            status = "YAWNING";
                            totalYawns++;
                            playBeep();
                        }
                    } else {
                        yawnFrames = 0;
                    }

                    frameCount++;

                    // Call backend every 1 second for detailed detection
                    const now = Date.now();
                    if (now - lastBackendCall > 1000) {
                        lastBackendCall = now;
                        
                        try {
                            const tempCanvas = document.createElement('canvas');
                            tempCanvas.width = video.videoWidth;
                            tempCanvas.height = video.videoHeight;
                            const tempCtx = tempCanvas.getContext('2d');
                            tempCtx.drawImage(video, 0, 0);
                            const imageData = tempCanvas.toDataURL('image/jpeg', 0.7);

                            // Call backend detection (run in background)
                            processFrameWithBackend(imageData).then(backendResult => {
                                if (backendResult) {
                                    console.log('📊 Comparison - Backend EAR:', backendResult.earvalue, '| Frontend EAR:', ear.toFixed(3));
                                }
                            }).catch(e => console.log('Backend call error:', e));
                            
                        } catch (e) {
                            console.log('Backend call skipped:', e.message);
                        }
                    }

                    // Save detection data
                    if (status === "DROWSY" || status === "WARNING" || status === "YAWNING") {
                        if (now - lastSave > 3000) {
                            lastSave = now;
                            const s = localStorage.getItem("driAlertsession");
                            
                            if (s) {
                                try {
                                    const d = JSON.parse(s);
                                    
                                    // Capture image safely
                                    let capturedImage = null;
                                    try {
                                        const ic = document.createElement('canvas');
                                        ic.width = 320;
                                        ic.height = 240;
                                        const ictx = ic.getContext('2d', { willReadFrequently: true });
                                        ictx.drawImage(video, 0, 0, 320, 240);
                                        capturedImage = ic.toDataURL("image/jpeg", 0.5);
                                    } catch (e) {
                                        console.log("Image capture failed, saving without image");
                                    }

                                    console.log(`💾 Saving ${status} detection for ${d.user?.email}...`);
                                    
                                    // Send in background
                                    setTimeout(() => {
                                        fetch("http://localhost:5000/api/auth/save-detection", {
                                            method: "POST",
                                            headers: {
                                                "Content-Type": "application/json",
                                                "Authorization": `Bearer ${d.token}`
                                            },
                                            body: JSON.stringify({
                                                driver_name: d.user?.email,
                                                eye_aspect_ratio: parseFloat(ear.toFixed(3)),
                                                mouth_aspect_ratio: parseFloat(mar.toFixed(3)),
                                                drowsiness_score: status === "DROWSY" ? 0.9 : 0.6,
                                                risk_level: status === "DROWSY" ? "High" : "Medium",
                                                status: status === "DROWSY" ? "Drowsy" : "Alert",
                                                alert_triggered: status === "DROWSY",
                                                eye_closure_duration: (eyeClosedFrames * 0.033).toFixed(2),
                                                session_id: sessionStorage.getItem("monitor_session_id"),
                                                session_duration: Math.floor((now - sessionStart) / 1000),
                                                total_detections: frameCount,
                                                blink_count: totalBlinks,
                                                yawn_count: totalYawns,
                                                image_data: capturedImage,
                                                timestamp: new Date().toISOString()
                                            })
                                        })
                                        .then(r => r.ok ? console.log("✅ Detection SAVED!") : console.log("❌ Save failed:", r.status))
                                        .catch(e => console.log("❌ Save error:", e));
                                    }, 100);
                                } catch (parseError) {
                                    console.error("Session parse error:", parseError);
                                }
                            }
                        }
                    }

                    // Draw visualization
                    if (frameCount % 2 === 0) {
                        canvas.width = video.videoWidth;
                        canvas.height = video.videoHeight;
                        ctx.drawImage(video, 0, 0);
                        faceapi.draw.drawDetections(canvas, detection);
                        faceapi.draw.drawFaceLandmarks(canvas, detection);
                    }

                    updateUI(ear, mar, status);
                } else {
                    updateUI(0, 0, "NO FACE");
                    eyeClosedFrames = 0;
                }

                if (isMonitoring) {
                    animationId = requestAnimationFrame(detectLoop);
                }
            })
            .catch(err => {
                console.error("Detection error:", err);
                if (isMonitoring) {
                    animationId = requestAnimationFrame(detectLoop);
                }
            });
    }

    // Stop monitoring
    function stopMonitoring() {
        console.log("⏹️ Stopping monitoring...");
        isMonitoring = false;
        if (animationId) cancelAnimationFrame(animationId);
        if (stream) stream.getTracks().forEach(t => t.stop());
        if (video) video.srcObject = null;
        if (startBtn) startBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = true;
        if (alertBox) alertBox.style.display = "none";
        showHomeButton();
    }

    // Event listeners
    if (startBtn) startBtn.addEventListener("click", startMonitoring);
    if (stopBtn) stopBtn.addEventListener("click", stopMonitoring);

    console.log("✅ Monitor initialized and ready!");
    showHomeButton();
}
