// Detection Event Manager for DriAlert
class DetectionEventManager {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.sessionStart = Date.now();
        this.detectionCount = 0;
        this.totalBlinks = 0;
        this.totalYawns = 0;
        this.isOnline = navigator.onLine;
        this.offlineQueue = [];

        // Listen for online/offline events
        window.addEventListener('online', () => this.syncOfflineData());
        window.addEventListener('offline', () => this.isOnline = false);

        console.log('🔍 Detection Event Manager initialized');
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    async saveDetection(detectionData, canvas = null) {
        try {
            // Capture image from canvas
            let imageData = null;
            if (canvas) {
                imageData = canvas.toDataURL('image/jpeg', 0.7);
            }

            const eventData = {
                driver_name: this.getDriverName(),
                eye_aspect_ratio: detectionData.ear || 0,
                mouth_aspect_ratio: detectionData.mar || 0,
                eye_closure_duration: detectionData.eyeClosureDuration || 0,
                yawn_duration: detectionData.yawnDuration || 0,
                drowsiness_score: detectionData.drowsinessScore || 0,
                risk_level: this.calculateRiskLevel(detectionData),
                alert_triggered: detectionData.alertTriggered || false,
                head_pose: detectionData.headPose || {},
                blink_count: ++this.totalBlinks,
                yawn_count: detectionData.isYawning ? ++this.totalYawns : this.totalYawns,
                session_id: this.sessionId,
                session_duration: (Date.now() - this.sessionStart) / 1000,
                total_detections: ++this.detectionCount,
                location: await this.getLocation(),
                image_data: imageData
            };

            if (this.isOnline) {
                const result = await this.sendToServer(eventData);
                return result;
            } else {
                this.offlineQueue.push(eventData);
                console.log('📱 Stored detection offline for later sync');
                return { event_id: 'offline_' + Date.now() };
            }
        } catch (error) {
            console.error('❌ Error saving detection:', error);
            return null;
        }
    }

    async sendToServer(eventData) {
    const token = this.getAuthToken();
    
    if (!token) {
        console.error('No authentication token found');
        return null;
    }
    
    const response = await fetch('http://localhost:5000/api/auth/save-detection', {
        method: 'POST',
        mode: 'cors', // ADD THIS
        credentials: 'include', // ADD THIS
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(eventData)
    });
    
    if (response.ok) {
        const result = await response.json();
        console.log('✅ Detection saved:', result.eventid);
        
        if (eventData.risklevel === 'High') {
            this.showRiskNotification(eventData);
        }
        return result;
    } else {
        console.error('Failed to save detection:', response.statusText);
        throw new Error('Failed to save detection');
    }
}

    calculateRiskLevel(data) {
        const ear = data.ear || 0;
        const mar = data.mar || 0;
        const drowsinessScore = data.drowsinessScore || 0;
        const eyeClosureDuration = data.eyeClosureDuration || 0;

        if (ear < 0.15 || eyeClosureDuration > 3.0 || drowsinessScore > 0.8) {
            return "High";
        }

        if (ear < 0.2 || eyeClosureDuration > 1.5 || drowsinessScore > 0.5 || mar > 0.5) {
            return "Medium";
        }

        return "Low";
    }

    getDriverName() {
        const session = localStorage.getItem('driAlert_session') || localStorage.getItem('driAlert_admin_session');
        if (session) {
            const data = JSON.parse(session);
            return data.user?.email || 'Unknown Driver';
        }
        return 'Unknown Driver';
    }

    getAuthToken() {
        const session = localStorage.getItem('driAlert_session') || localStorage.getItem('driAlert_admin_session');
        if (session) {
            const data = JSON.parse(session);
            return data.token;
        }
        return null;
    }

    async getLocation() {
        try {
            if ('geolocation' in navigator) {
                return new Promise((resolve) => {
                    navigator.geolocation.getCurrentPosition(
                        (position) => {
                            resolve({
                                latitude: position.coords.latitude,
                                longitude: position.coords.longitude,
                                accuracy: position.coords.accuracy
                            });
                        },
                        () => resolve({ latitude: null, longitude: null, accuracy: null }),
                        { timeout: 5000, enableHighAccuracy: false }
                    );
                });
            }
        } catch (error) {
            console.log('Location not available:', error);
        }
        return { latitude: null, longitude: null, accuracy: null };
    }

    showRiskNotification(eventData) {
        // Create high-risk notification
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('⚠️ High Risk Drowsiness Detected!', {
                body: `Driver: ${eventData.driver_name}\nScore: ${eventData.drowsiness_score}`,
                icon: '/path/to/icon.png',
                badge: '/path/to/badge.png'
            });
        }

        // FIX: Completed in-page notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(239, 68, 68, 0.4);
            font-weight: 600;
            max-width: 300px;
            animation: slideIn 0.3s ease;
        `;
        
        notification.innerHTML = `
            <div style="font-size: 18px; margin-bottom: 8px;">⚠️ High Risk Alert</div>
            <div style="font-size: 14px; opacity: 0.9;">
                Driver: ${eventData.driver_name}<br>
                Drowsiness Score: ${Math.round(eventData.drowsiness_score * 100)}%
            </div>
        `;

        document.body.appendChild(notification);

        // Remove after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }

    async syncOfflineData() {
        if (this.offlineQueue.length === 0) return;

        console.log(`🔄 Syncing ${this.offlineQueue.length} offline detections...`);
        this.isOnline = true;

        const queue = [...this.offlineQueue];
        this.offlineQueue = [];

        for (const eventData of queue) {
            try {
                await this.sendToServer(eventData);
            } catch (error) {
                console.error('Failed to sync:', error);
                this.offlineQueue.push(eventData);
            }
        }
    }
}

// Make it globally available
window.DetectionEventManager = DetectionEventManager;
