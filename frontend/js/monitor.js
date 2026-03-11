document.addEventListener("DOMContentLoaded", function() {
  console.log("Monitor Starting...");
  
  // Check for valid session
  const sessionStr = localStorage.getItem('driAlertsession');
  if (!sessionStr) {
    console.error("No session found");
    alert("Please login first!");
    window.location.href = "index.html";
    return;
  }
  
  let sessionData = null;
  try {
    sessionData = JSON.parse(sessionStr);
    console.log("Session data:", sessionData);
  } catch (e) {
    console.error("Invalid session JSON:", e);
    alert("Invalid session! Please login again.");
    localStorage.removeItem('driAlertsession');
    window.location.href = "index.html";
    return;
  }
  
  // Check if session has required fields
  if (!sessionData.user || !sessionData.token) {
    console.error("Session missing user or token:", sessionData);
    alert("Invalid session! Please login again.");
    localStorage.removeItem('driAlertsession');
    window.location.href = "index.html";
    return;
  }
  
  console.log("✅ Logged in as:", sessionData.user.email);
  initMonitor();
});

function initMonitor() {
    
    const detectionManager = new DetectionEventManager();

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

    const MAR_THRESHOLD = 0.6;
    const EYE_CLOSURE_THRESHOLD = 0.25;
    const DROWSY_FRAMES = 90;
    // Threshold constants for drowsiness detection  
    // EAR below this = eyes closed
    const MOUTH_OPENING_THRESHOLD = 0.6;  // MAR above this = yawning
    const CONSECUTIVE_FRAMES_THRESHOLD = 3;  // Frames needed to trigger alert
    const YAWN_THRESHOLD = 0.6;  // Same as mouth opening

    let eyeClosedFrames = 0;
    let yawnFrames = 0;
    let totalBlinks = 0;
    let totalYawns = 0;
    let sessionStart = Date.now();
    let frameCount = 0;
    let lastSave = 0;
    let lastBeep = 0;
    let lastBackendCall = 0;
    let lastBackendEAR = null;
    let lastHeartbeat = 0;

    // ✅ ADD THIS
    let latestDetectionData = {
        ear: 0,
        mar: 0,
        drowsinessScore: 0,
        alertTriggered: false,
        eyeClosureDuration: 0,
        yawnDuration: 0
    };

    if (!sessionStorage.getItem("monitor_session_id")) {
        sessionStorage.setItem("monitor_session_id", "session_" + Date.now());
    }

    function fastDistance(p1, p2) {
        const dx = p2.x - p1.x, dy = p2.y - p1.y;
        return Math.sqrt(dx * dx + dy * dy);
    }

    function calculateEAR(eye) {
        const v1 = fastDistance(eye[1], eye[5]);
        const v2 = fastDistance(eye[2], eye[4]);
        const h = fastDistance(eye[0], eye[3]);
        return (v1 + v2) / (2.0 * h);
    }

    function calculateMAR(mouth) {
        const v1 = fastDistance(mouth[13], mouth[19]);
        const v2 = fastDistance(mouth[14], mouth[18]);
        const h = fastDistance(mouth[0], mouth[6]);
        return (v1 + v2) / (2.0 * h);
    }

    function updateUI(ear, mar, status) {
    const earDisplay = document.getElementById('ear-value');
    const marDisplay = document.getElementById('mar-value');
    const blinkDisplay = document.getElementById('blink-count');
    const yawnDisplay = document.getElementById('yawn-count');
    const alertBox = document.getElementById('alert-box');
    const safetyStatus = document.getElementById('safety-status');
    const totalDetections = document.getElementById('total-detections');
    const alertCount = document.getElementById('alert-count');
    
    if (earDisplay) earDisplay.textContent = ear.toFixed(3);
    if (marDisplay) marDisplay.textContent = mar.toFixed(3);
    if (blinkDisplay) blinkDisplay.textContent = totalBlinks;
    if (yawnDisplay) yawnDisplay.textContent = totalYawns;
    if (totalDetections) totalDetections.textContent = frameCount;
    
    if (alertBox) {
        if (status === 'DROWSY') {
            alertBox.classList.add('active');
            alertBox.innerHTML = '<h3><i class="fas fa-exclamation-triangle"></i> DROWSINESS DETECTED!</h3><p>Please take a break immediately for your safety.</p>';
            if (safetyStatus) {
                safetyStatus.textContent = 'DANGER';
                safetyStatus.style.color = '#ef4444';
            }
            if (alertCount) alertCount.textContent = parseInt(alertCount.textContent) + 1;
        } else if (status === 'WARNING') {
            alertBox.classList.add('active');
            alertBox.innerHTML = '<h3><i class="fas fa-exclamation-triangle"></i> WARNING</h3><p>Eyes closing detected. Stay alert!</p>';
            alertBox.style.background = 'linear-gradient(135deg, #f59e0b, #d97706)';
            if (safetyStatus) {
                safetyStatus.textContent = 'WARNING';
                safetyStatus.style.color = '#f59e0b';
            }
        } else if (status === 'YAWNING') {
            alertBox.classList.add('active');
            alertBox.innerHTML = '<h3><i class="fas fa-tired"></i> YAWN DETECTED</h3><p>You may be feeling tired. Consider taking a break.</p>';
            alertBox.style.background = 'linear-gradient(135deg, #3b82f6, #2563eb)';
            if (safetyStatus) {
                safetyStatus.textContent = 'CAUTION';
                safetyStatus.style.color = '#3b82f6';
            }
        } else {
            alertBox.classList.remove('active');
            if (safetyStatus) {
                safetyStatus.textContent = 'SAFE';
                safetyStatus.style.color = '#10b981';
            }
        }
    }
}

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

    function hideHomeButton() {
        const homeBtn = document.getElementById("home-btn");
        if (homeBtn) homeBtn.style.display = "none";
    }

    async function processFrameWithBackend(imageData) {
        try {
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

            const headers = {'Content-Type': 'application/json'};
            if (token) headers['Authorization'] = `Bearer ${token}`;

            const response = await fetch('http://localhost:5000/api/detection/process-frame', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ frame: imageData })
            });

            const result = await response.json();
            console.log('🔍 Backend:', result.earvalue?.toFixed(3));
            return result;
        } catch (error) {
            console.error('❌ Backend error:', error);
            return null;
        }
    }

    async function startMonitoring() {
        if (isMonitoring) return;
        console.log('🚀 Starting...');

        try {
            hideHomeButton();

            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Camera not supported in this browser');
            }

            stream = await navigator.mediaDevices.getUserMedia({
                video: {width: 640, height: 480, frameRate: 30, facingMode: 'user'}
            });

            video.srcObject = stream;
            await video.play();
            
            // Wait for video to be fully loaded with proper dimensions
            await new Promise(resolve => {
                if (video.videoWidth > 0) {
                    resolve();
                } else {
                    video.addEventListener('loadedmetadata', resolve, { once: true });
                }
            });

            console.log('📦 Loading models...');

            await Promise.all([
                faceapi.nets.tinyFaceDetector.loadFromUri('https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js/weights'),
                faceapi.nets.faceLandmark68Net.loadFromUri('https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js/weights')
            ]);
            console.log('✅ Models loaded!');

            isMonitoring = true;
            if (startBtn) startBtn.disabled = true;
            if (stopBtn) stopBtn.disabled = false;
            
            // ✅ ADD THESE LINES:
            if (startBtn) startBtn.style.display = 'none';
            if (stopBtn) stopBtn.style.display = 'flex';
            if (window.updateMonitoringStatus) window.updateMonitoringStatus(true);
            
            // Update overlay badges
            const videoStatus = document.getElementById('video-status');
            const detectionStatus = document.getElementById('detection-status');
            if (videoStatus) videoStatus.textContent = 'Camera Active';
            if (detectionStatus) detectionStatus.textContent = 'Detecting...';
            
            // Reset counters
            eyeClosedFrames = 0;
            yawnFrames = 0;
            totalBlinks = 0;
            totalYawns = 0;
            sessionStart = Date.now();
            frameCount = 0;
            
            console.log("✅ Monitoring ACTIVE!");
            detectLoop();
        
        } catch (e) {
            console.error('❌ Error:', e);

            if (e.name === 'NotAllowedError') {
                alert('❌ Camera access denied. Please allow camera permissions.');
            } else if (e.name === 'NotFoundError') {
                alert('❌ No camera found. Please connect a camera.');
            } else if (e.message.includes('not supported')) {
                alert('❌ Your browser does not support camera access.');
            } else {
                alert('❌ Camera error: ' + e.message);
            }

            //showHomeButton();
        }
    }

    function detectLoop() {
    if (!isMonitoring) return;

    faceapi
        .detectSingleFace(video, new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.5 }))
        .withFaceLandmarks()
        .then(async (detection) => {
            if (detection) {
                const leftEye = detection.landmarks.getLeftEye();
                const rightEye = detection.landmarks.getRightEye();
                const mouth = detection.landmarks.getMouth();

                const frontendEar = (calculateEAR(leftEye) + calculateEAR(rightEye)) / 2.0;
                const mar = calculateMAR(mouth);
                let status = "ALERT";
                let earToUse = frontendEar;

                // Get backend EAR every second
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
                        const backendResult = await processFrameWithBackend(imageData);
                        if (backendResult && backendResult.earvalue !== undefined) {
                            lastBackendEAR = backendResult.earvalue;
                            earToUse = lastBackendEAR;
                        }
                    } catch (e) {
                        // Backend skip, using frontend
                    }
                } else if (lastBackendEAR !== null) {
                    earToUse = lastBackendEAR;
                }

                if (now - lastHeartbeat > 5000) {
                    lastHeartbeat = now;
                    sendHeartbeat();
                }

                // Eye closure detection
                if (earToUse < EYE_CLOSURE_THRESHOLD) {
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
                    if (eyeClosedFrames > 0) {
                        if (eyeClosedFrames >= 1 && eyeClosedFrames <= 10) {
                            totalBlinks++;
                        }
                        eyeClosedFrames = 0;
                    }
                }

                // Yawn detection
                if (mar > MOUTH_OPENING_THRESHOLD) {
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

                 // ✅ UPDATE latest detection data
        latestDetectionData = {
            ear: earToUse,
            mar: mar,
            drowsinessScore: status === "DROWSY" ? 90 : status === "WARNING" ? 50 : status === "YAWNING" ? 60 : 0,
            alertTriggered: status === "DROWSY",
            eyeClosureDuration: eyeClosedFrames / 30,
            yawnDuration: yawnFrames / 8
        };

                // ✅ ADD THIS CODE HERE ✅
                // Save high-risk detections to database immediately
            if (status === "DROWSY" && typeof DetectionEventManager !== 'undefined') {
                const detectionManager = new DetectionEventManager();
                detectionManager.saveDetection({
                    ear: earToUse,
                    mar: mar,
                    drowsinessScore: 90,
                    alertTriggered: true,
                    eyeClosureDuration: eyeClosedFrames / 30,
                    yawnDuration: 0
                }, canvas).catch(err => {
                    console.error('❌ Failed to save high-risk detection:', err);
                });
            }
            // ✅ END OF NEW CODE ✅

                // ===== CORRECTED DRAWING SECTION =====
                // Get CURRENT display dimensions (in case window resized)
                const displayWidth = video.clientWidth;
                const displayHeight = video.clientHeight;

                // ALWAYS update canvas to match current display size
                canvas.width = displayWidth;
                canvas.height = displayHeight;

                // Clear canvas
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                // Resize detection to match display
                const displaySize = { width: displayWidth, height: displayHeight };
                const resizedDetections = faceapi.resizeResults(detection, displaySize);

                // Draw resized detection
                faceapi.draw.drawDetections(canvas, resizedDetections);
                faceapi.draw.drawFaceLandmarks(canvas, resizedDetections);

                updateUI(earToUse, mar, status);
            } else {
                updateUI(0, 0, "NO FACE");
                eyeClosedFrames = 0;
            }

            // Continue loop
            if (isMonitoring) {
                animationId = requestAnimationFrame(detectLoop);
            }
        })
        .catch(err => {
            console.error("Detection error:", err);
            // Continue loop even on error
            if (isMonitoring) {
                animationId = requestAnimationFrame(detectLoop);
            }
        });
}

    function stopMonitoring() {
        console.log("⏹️ Stopping monitoring...");

        // ✅ SAVE WITH REAL DATA - Use latestDetectionData
    if (typeof DetectionEventManager !== 'undefined') {
        const detectionManager = new DetectionEventManager();
        detectionManager.saveDetection(latestDetectionData, canvas).then(result => {
            if (result) {
                console.log('✅ Session saved to database:', result);
            }
        }).catch(err => {
            console.error('❌ Failed to save session:', err);
        });
    }
  
  notifyStopMonitoring(); // Notify backend
  isMonitoring = false;
  
  if (animationId) cancelAnimationFrame(animationId);
  if (stream) {
    stream.getTracks().forEach(t => t.stop());
  }
      if (video) video.srcObject = null;
    
    // ✅ CLEAR CANVAS AFTER A SHORT DELAY to allow save to complete
    setTimeout(() => {
        if (canvas && ctx) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            canvas.width = 0;
            canvas.height = 0;
        }
    }, 500);  // Wait 500ms for save to complete
  
  // ✅ Update UI to show stopped state
  if (startBtn) {
    startBtn.style.display = 'flex';
    startBtn.disabled = false;
  }
  if (stopBtn) {
    stopBtn.style.display = 'none';
    stopBtn.disabled = true;
  }
  if (alertBox) alertBox.classList.remove('active');
  
  // ✅ Update status indicators
  if (window.updateMonitoringStatus) {
    window.updateMonitoringStatus(false);
  }
  
  // Update overlay badges
  const videoStatus = document.getElementById('video-status');
  const detectionStatus = document.getElementById('detection-status');
  if (videoStatus) videoStatus.textContent = 'Camera Off';
  if (detectionStatus) detectionStatus.textContent = 'Not Monitoring';
  
  // showHomeButton(); // Commented out - we don't want the purple button
}

    if (startBtn) startBtn.addEventListener("click", startMonitoring);
    if (stopBtn) stopBtn.addEventListener("click", stopMonitoring);

    console.log("✅ Monitor initialized and ready!");
    //showHomeButton();

    function sendHeartbeat() {
    const session = localStorage.getItem('driAlertsession');
    if (!session) return;
    
    try {
        const data = JSON.parse(session);
        fetch('http://localhost:5000/api/detection/user/heartbeat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${data.token}`
            }
        }).then(r => {
            if (r.ok) {
                console.log('💓 Heartbeat sent');
            }
        }).catch(e => console.log('Heartbeat skip'));
    } catch (e) {
        console.log('Heartbeat parse error');
    }
}

function notifyStopMonitoring() {
    const session = localStorage.getItem('driAlertsession');
    if (!session) return;
    
    try {
        const data = JSON.parse(session);
        fetch('http://localhost:5000/api/detection/user/stop-monitoring', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${data.token}`
            }
        }).then(r => {
            if (r.ok) {
                console.log('🛑 Stop monitoring notified');
            }
        }).catch(e => console.log('Stop notify failed'));
    } catch (e) {}
}

}
