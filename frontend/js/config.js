// frontend/config.js
const API_CONFIG = {
    BASE_URL: 'http://localhost:5000',
    ENDPOINTS: {
        AUTH: {
            LOGIN: '/api/auth/login',
            REGISTER: '/api/auth/register',
            ADMIN_LOGIN: '/api/auth/admin-login',
            SAVE_DETECTION: '/api/auth/save-detection'
        },
        DETECTION: {
            PROCESS_FRAME: '/api/detection/process-frame',
            SET_ACTIVE: '/api/detection/user/set-active'
        }
    }
};

// Helper function to build full URL
function getApiUrl(endpoint) {
    return `${API_CONFIG.BASE_URL}${endpoint}`;
}
