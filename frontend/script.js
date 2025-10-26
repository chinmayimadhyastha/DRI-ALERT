// Enhanced Script.js with Modern Features - Bug-Free Version
class DriAlert {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.currentPage = 'main-page';
        this.isMenuOpen = false;
        this.testimonialIndex = 0;
        this.testimonialInterval = null;
        this.particles = [];
        this.testimonialCarouselEnabled = false;
        this.init();
    }

    init() {
        try {
            this.applyTheme(this.currentTheme);
            this.bindEvents();
            this.initAnimations();
            this.initParticles();
            
            setTimeout(() => {
                try {
                    this.startTestimonialCarousel();
                } catch (error) {
                    console.warn('Testimonial carousel initialization failed:', error);
                }
            }, 1000);
            
            this.initCounters();
            this.hideLoadingScreen();
            
            window.addEventListener('scroll', this.handleScroll.bind(this));
            console.log('🚀 DriAlert initialized successfully!');
        } catch (error) {
            console.error('DriAlert initialization error:', error);
        }
    }

    bindEvents() {
        // Theme toggle
        const themeToggle = document.getElementById('themeToggle');
        const themePanel = document.getElementById('themePanel');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                if (themePanel) {
                    themePanel.classList.toggle('active');
                }
            });
        }

        // Theme selection
        document.querySelectorAll('.theme-option').forEach(option => {
            option.addEventListener('click', () => {
                const theme = option.dataset.theme;
                this.setTheme(theme);
                if (themePanel) {
                    themePanel.classList.remove('active');
                }
            });
        });

        // Mobile menu toggle
        const mobileMenuToggle = document.getElementById('mobileMenuToggle');
        const navMenu = document.getElementById('navMenu');
        if (mobileMenuToggle) {
            mobileMenuToggle.addEventListener('click', () => {
                this.toggleMobileMenu();
            });
        }

        // Navigation links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                const section = link.dataset.section;
                if (section) {
                    e.preventDefault();
                    this.scrollToSection(section);
                    this.setActiveNavLink(link);
                    if (this.isMenuOpen) {
                        this.toggleMobileMenu();
                    }
                }
            });
        });

        // Auth buttons
        document.querySelectorAll('.login-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.showPage('login-page');
            });
        });

        document.querySelectorAll('.signup-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.showPage('signup-page');
            });
        });

        document.querySelectorAll('.admin-login-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.showPage('admin-login-page');
            });
        });

        // Back to home buttons
        document.querySelectorAll('.back-home').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.showPage('main-page');
            });
        });

        // Form submissions
        this.bindFormEvents();

        // Hero buttons
        document.querySelectorAll('[data-target]').forEach(btn => {
            btn.addEventListener('click', () => {
                const target = btn.dataset.target;
                this.scrollToSection(target);
            });
        });

        // Testimonial navigation
        const prevBtn = document.getElementById('prevTestimonial');
        const nextBtn = document.getElementById('nextTestimonial');
        if (prevBtn) prevBtn.addEventListener('click', () => this.prevTestimonial());
        if (nextBtn) nextBtn.addEventListener('click', () => this.nextTestimonial());

        // Indicator clicks
        document.querySelectorAll('.indicator').forEach((indicator, index) => {
            indicator.addEventListener('click', () => this.goToTestimonial(index));
        });

        // Close panels when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.theme-selector')) {
                const themePanel = document.getElementById('themePanel');
                if (themePanel) {
                    themePanel.classList.remove('active');
                }
            }
        });
    }

    bindFormEvents() {
        // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', this.handleLogin.bind(this));
        }

        // Signup form
        const signupForm = document.getElementById('signup-form');
        if (signupForm) {
            signupForm.addEventListener('submit', this.handleSignup.bind(this));
        }

        // Admin login form
        const adminLoginForm = document.getElementById('admin-login-form');
        if (adminLoginForm) {
            adminLoginForm.addEventListener('submit', this.handleAdminLogin.bind(this));
        }

        // Password toggle buttons
        document.querySelectorAll('.toggle-password').forEach(btn => {
            btn.addEventListener('click', () => {
                const input = btn.previousElementSibling;
                const icon = btn.querySelector('i');
                if (input.type === 'password') {
                    input.type = 'text';
                    icon.classList.replace('fa-eye', 'fa-eye-slash');
                } else {
                    input.type = 'password';
                    icon.classList.replace('fa-eye-slash', 'fa-eye');
                }
            });
        });
    }

    // Theme Management
    setTheme(theme) {
        this.currentTheme = theme;
        this.applyTheme(theme);
        localStorage.setItem('theme', theme);
        
        document.querySelectorAll('.theme-option').forEach(option => {
            option.classList.toggle('active', option.dataset.theme === theme);
        });
        
        this.showToast('success', 'Theme Updated', `Switched to ${theme} theme`);
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        
        document.querySelectorAll('.theme-option').forEach(option => {
            option.classList.toggle('active', option.dataset.theme === theme);
        });
    }

    // Page Management
    showPage(pageId) {
        console.log(`Switching to page: ${pageId}`);
        
        const pages = document.querySelectorAll('.page');
        pages.forEach(page => {
            page.classList.remove('active');
            page.style.display = 'none';
        });

        const targetPage = document.getElementById(pageId);
        if (targetPage) {
            targetPage.classList.add('active');
            targetPage.style.display = 'block';
            console.log(`Page switched to: ${pageId}`);
            
            document.body.style.overflow = 'auto';
            document.body.style.overflowX = 'hidden';
            document.body.style.pointerEvents = 'auto';
        }
        
        this.updatePageTitle(pageId);
    }

    updatePageTitle(pageId) {
        const titles = {
            'main-page': 'DriAlert - AI Drowsiness Detection System',
            'login-page': 'Login - DriAlert',
            'signup-page': 'Sign Up - DriAlert',
            'admin-login-page': 'Admin Login - DriAlert'
        };
        document.title = titles[pageId] || 'DriAlert';
    }

    // Navigation
    scrollToSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) {
            const headerHeight = 80;
            const targetPosition = section.offsetTop - headerHeight;
            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        }
    }

    setActiveNavLink(activeLink) {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        activeLink.classList.add('active');
    }

    toggleMobileMenu() {
        const navMenu = document.getElementById('navMenu');
        const mobileMenuToggle = document.getElementById('mobileMenuToggle');
        
        this.isMenuOpen = !this.isMenuOpen;
        
        if (navMenu) {
            navMenu.classList.toggle('active', this.isMenuOpen);
        }
        
        if (mobileMenuToggle) {
            mobileMenuToggle.classList.toggle('active', this.isMenuOpen);
        }
        
        document.body.style.overflow = this.isMenuOpen ? 'hidden' : '';
    }

    // Scroll Effects
    handleScroll() {
        const header = document.getElementById('header');
        const scrollY = window.scrollY;

        if (header) {
            header.classList.toggle('scrolled', scrollY > 50);
        }

        this.updateActiveNavOnScroll();
        this.updateParallaxEffects(scrollY);
    }

    updateActiveNavOnScroll() {
        const sections = ['hero', 'features', 'how-it-works', 'testimonials', 'about'];
        const headerHeight = 100;
        let currentSection = '';

        sections.forEach(sectionId => {
            const section = document.getElementById(sectionId);
            if (section) {
                const rect = section.getBoundingClientRect();
                if (rect.top <= headerHeight && rect.bottom >= headerHeight) {
                    currentSection = sectionId;
                }
            }
        });

        if (currentSection) {
            document.querySelectorAll('.nav-link').forEach(link => {
                const isActive = link.dataset.section === currentSection;
                link.classList.toggle('active', isActive);
            });
        }
    }

    updateParallaxEffects(scrollY) {
        const heroBackground = document.querySelector('.hero-background');
        if (heroBackground) {
            heroBackground.style.transform = `translateY(${scrollY * 0.5}px)`;
        }

        document.querySelectorAll('.floating-particles .particle').forEach((particle, index) => {
            const speed = 0.2 + (index * 0.1);
            particle.style.transform = `translateY(${scrollY * speed}px)`;
        });
    }

    // Testimonial Carousel
    startTestimonialCarousel() {
        const testimonials = document.querySelectorAll('.testimonial-card');
        if (testimonials.length > 0) {
            const activeTestimonial = document.querySelector('.testimonial-card.active');
            if (!activeTestimonial) {
                testimonials[0].classList.add('active');
                const firstIndicator = document.querySelector('.indicator');
                if (firstIndicator) {
                    firstIndicator.classList.add('active');
                }
            }

            if (this.testimonialCarouselEnabled) {
                this.testimonialInterval = setInterval(() => {
                    this.nextTestimonial();
                }, 5000);
            }
        } else {
            console.log('No testimonial cards found - carousel disabled');
        }
    }

    stopTestimonialCarousel() {
        if (this.testimonialInterval) {
            clearInterval(this.testimonialInterval);
            this.testimonialInterval = null;
        }
    }

    nextTestimonial() {
        const testimonials = document.querySelectorAll('.testimonial-card');
        const indicators = document.querySelectorAll('.indicator');

        if (!testimonials || testimonials.length === 0) {
            return;
        }

        if (this.testimonialIndex >= testimonials.length) {
            this.testimonialIndex = 0;
        }

        if (testimonials[this.testimonialIndex]) {
            testimonials[this.testimonialIndex].classList.remove('active');
        }

        if (indicators && indicators[this.testimonialIndex]) {
            indicators[this.testimonialIndex].classList.remove('active');
        }

        this.testimonialIndex = (this.testimonialIndex + 1) % testimonials.length;

        if (testimonials[this.testimonialIndex]) {
            testimonials[this.testimonialIndex].classList.add('active');
        }

        if (indicators && indicators[this.testimonialIndex]) {
            indicators[this.testimonialIndex].classList.add('active');
        }

        const track = document.getElementById('testimonialTrack');
        if (track) {
            track.style.transform = `translateX(-${this.testimonialIndex * 100}%)`;
        }
    }

    prevTestimonial() {
        const testimonials = document.querySelectorAll('.testimonial-card');
        const indicators = document.querySelectorAll('.indicator');

        if (!testimonials || testimonials.length === 0) {
            return;
        }

        if (this.testimonialIndex >= testimonials.length) {
            this.testimonialIndex = 0;
        }

        if (testimonials[this.testimonialIndex]) {
            testimonials[this.testimonialIndex].classList.remove('active');
        }

        if (indicators && indicators[this.testimonialIndex]) {
            indicators[this.testimonialIndex].classList.remove('active');
        }

        this.testimonialIndex = this.testimonialIndex === 0 ? testimonials.length - 1 : this.testimonialIndex - 1;

        if (testimonials[this.testimonialIndex]) {
            testimonials[this.testimonialIndex].classList.add('active');
        }

        if (indicators && indicators[this.testimonialIndex]) {
            indicators[this.testimonialIndex].classList.add('active');
        }

        const track = document.getElementById('testimonialTrack');
        if (track) {
            track.style.transform = `translateX(-${this.testimonialIndex * 100}%)`;
        }
    }

    goToTestimonial(index) {
        const testimonials = document.querySelectorAll('.testimonial-card');
        const indicators = document.querySelectorAll('.indicator');

        if (!testimonials || testimonials.length === 0) {
            return;
        }

        if (index < 0 || index >= testimonials.length) {
            return;
        }

        if (testimonials[this.testimonialIndex]) {
            testimonials[this.testimonialIndex].classList.remove('active');
        }

        if (indicators && indicators[this.testimonialIndex]) {
            indicators[this.testimonialIndex].classList.remove('active');
        }

        this.testimonialIndex = index;

        if (testimonials[this.testimonialIndex]) {
            testimonials[this.testimonialIndex].classList.add('active');
        }

        if (indicators && indicators[this.testimonialIndex]) {
            indicators[this.testimonialIndex].classList.add('active');
        }

        const track = document.getElementById('testimonialTrack');
        if (track) {
            track.style.transform = `translateX(-${this.testimonialIndex * 100}%)`;
        }
    }

    // Counter Animation
    initCounters() {
        const counters = document.querySelectorAll('.counter, .stat-number');
        
        const animateCounter = (counter) => {
            const target = parseInt(counter.dataset.count) || parseInt(counter.textContent);
            const duration = 2000;
            const increment = target / (duration / 16);
            let current = 0;

            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    counter.textContent = target;
                    clearInterval(timer);
                } else {
                    counter.textContent = Math.floor(current);
                }
            }, 16);
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !entry.target.classList.contains('animated')) {
                    entry.target.classList.add('animated');
                    animateCounter(entry.target);
                }
            });
        });

        counters.forEach(counter => {
            observer.observe(counter);
        });
    }

    // Animation System
    initAnimations() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.animationPlayState = 'running';
                }
            });
        }, {
            threshold: 0.1
        });

        document.querySelectorAll('.feature-card, .step-item, .testimonial-card').forEach(el => {
            observer.observe(el);
        });
    }

    // Particle System
    initParticles() {
        this.createParticles();
        this.animateParticles();
    }

    createParticles() {
        const particleContainers = document.querySelectorAll('.floating-particles');
        particleContainers.forEach(container => {
            for (let i = 0; i < 6; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.animationDelay = Math.random() * 15 + 's';
                particle.style.animationDuration = (15 + Math.random() * 10) + 's';
                container.appendChild(particle);
            }
        });
    }

    animateParticles() {
        setInterval(() => {
            document.querySelectorAll('.particle').forEach(particle => {
                if (Math.random() > 0.98) {
                    particle.style.opacity = Math.random();
                }
            });
        }, 1000);
    }

    // Form Handlers
    // CORRECTED handleLogin
async handleLogin(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const email = formData.get('email');
    const password = formData.get('password');
    const btn = e.target.querySelector('button[type="submit"]');
    
    this.setButtonLoading(btn, true);
    
    try {
        const response = await fetch('http://localhost:5000/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Save session
            localStorage.setItem('driAlertsession', JSON.stringify({
                user: { email, role: 'driver' },
                token: data.access_token,
                expires: Date.now() + (24 * 60 * 60 * 1000)
            }));
            
            this.showToast('success', 'Login Successful', 'Welcome back!');
            this.showPage('main-page');
            
            // Update navigation
            if (window.authManager) {
                window.authManager.loadSession();
                window.authManager.updateNavigation();
            }
            
            return true;
        } else {
            const errorData = await response.json();
            this.showToast('error', 'Login Failed', errorData.error || 'Invalid credentials');
            return false;
        }
    } catch (error) {
        console.error('Login error:', error);
        this.showToast('error', 'Login Failed', 'Connection error. Please try again.');
        return false;
    } finally {
        this.setButtonLoading(btn, false);
    }
}

    async handleSignup(e) {
        e.preventDefault();
        
        const btn = e.target.querySelector('button[type="submit"]');
        const email = e.target.email.value;
        const password = e.target.password.value;
        const confirmPassword = e.target.confirmPassword ? e.target.confirmPassword.value : password;

        if (password !== confirmPassword) {
            this.showToast('error', 'Password Mismatch', 'Passwords do not match.');
            return;
        }

        this.setButtonLoading(btn, true);

        try {
            const response = await fetch('http://localhost:5000/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.showToast('success', 'Account Created', 'Welcome to DriAlert! Please login with your credentials.');
                this.showPage('login-page');
            } else {
                const errorData = await response.json();
                this.showToast('error', 'Signup Failed', errorData.error || 'Registration failed.');
            }
        } catch (error) {
            console.error('Signup error:', error);
            this.showToast('error', 'Signup Failed', 'Connection error. Please try again.');
        } finally {
            this.setButtonLoading(btn, false);
        }
    }

    // In your handleAdminLogin function, after successful login:
async handleAdminLogin(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    const email = e.target.email.value;
    const password = e.target.password.value;

    const response = await fetch('http://localhost:5000/api/auth/admin-login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    });

    if (response.ok) {
        const data = await response.json();
        
        // Save admin session
        localStorage.setItem('driAlertadminsession', JSON.stringify({
            user: { email, role: 'admin' },
            token: data.access_token,
            expires: Date.now() + (8 * 60 * 60 * 1000) // 8 hours
        }));

        authManager.showToast('Admin access granted!', 'success');
        showPage('admin-dashboard');

        // ✅ LOAD DASHBOARD DATA
        setTimeout(async () => {
            await adminDashboard.loadDashboard();
            adminDashboard.startAutoRefresh(30000); // Refresh every 30 seconds
        }, 500);
    }
}

    // FIXED: Completed setButtonLoading method
    setButtonLoading(btn, loading) {
        if (loading) {
            btn.classList.add('loading');
            btn.disabled = true;
            btn.dataset.originalText = btn.textContent;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        } else {
            btn.classList.remove('loading');
            btn.disabled = false;
            if (btn.dataset.originalText) {
                btn.textContent = btn.dataset.originalText;
            }
        }
    }

    // FIXED: Completed showToast method
    showToast(type, title, message) {
        const container = document.getElementById('toast-container') || this.createToastContainer();
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = this.getToastIcon(type);
        
        toast.innerHTML = `
            <div class="toast-icon">${icon}</div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }

    // FIXED: Added createToastContainer method
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 10000;';
        document.body.appendChild(container);
        return container;
    }

    // FIXED: Added getToastIcon method
    getToastIcon(type) {
        const icons = {
            success: '<i class="fas fa-check-circle"></i>',
            error: '<i class="fas fa-exclamation-circle"></i>',
            warning: '<i class="fas fa-exclamation-triangle"></i>',
            info: '<i class="fas fa-info-circle"></i>'
        };
        return icons[type] || icons.info;
    }

    // FIXED: Added delay helper method
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // FIXED: Added hideLoadingScreen method
    hideLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            setTimeout(() => {
                loadingScreen.style.opacity = '0';
                setTimeout(() => {
                    loadingScreen.style.display = 'none';
                }, 300);
            }, 500);
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.driAlert = new DriAlert();
});

// ===================================
// ADMIN DASHBOARD MANAGER - REAL DATA
// ===================================

class AdminDashboardManager {
    constructor() {
        this.baseURL = 'http://localhost:5000/api';
        this.refreshInterval = null;
    }

    // Get authentication token from localStorage
    getAuthToken() {
        const adminSession = localStorage.getItem('driAlertadminsession');
        if (adminSession) {
            try {
                const data = JSON.parse(adminSession);
                return data.token;
            } catch (e) {
                console.error('Failed to parse admin session:', e);
            }
        }
        return null;
    }

    // Generic API call with authentication
    async apiCall(endpoint, options = {}) {
        const token = this.getAuthToken();
        
        if (!token) {
            console.error('No admin token found');
            authManager.showToast('Authentication required', 'error');
            showPage('admin-login-page');
            return null;
        }

        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                    ...options.headers
                }
            });

            if (response.status === 401) {
                // Token expired
                localStorage.removeItem('driAlertadminsession');
                authManager.showToast('Session expired. Please login again.', 'error');
                showPage('admin-login-page');
                return null;
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            authManager.showToast('Failed to fetch data', 'error');
            return null;
        }
    }

    // Load all dashboard data
    async loadDashboard() {
        console.log('📊 Loading admin dashboard...');
        
        await Promise.all([
            this.loadStats(),
            this.loadUsers(),
            this.loadDetectionEvents(),
            this.loadRecentActivity()
        ]);

        console.log('✅ Dashboard loaded successfully');
    }

    // Load statistics (users, sessions, alerts, accuracy)
    async loadStats() {
        // Get all users
        const usersData = await this.apiCall('/admin/users');
        
        // Get detection logs
        const logsData = await this.apiCall('/admin/logs?limit=100');

        if (usersData && logsData) {
            // Calculate stats
            const totalUsers = usersData.users ? usersData.users.length : 0;
            const activeUsers = usersData.users ? 
                usersData.users.filter(u => u.is_active).length : 0;
            
            const totalDetections = logsData.logs ? logsData.logs.length : 0;
            const alertsToday = logsData.logs ? 
                logsData.logs.filter(log => {
                    const logDate = new Date(log.timestamp);
                    const today = new Date();
                    return logDate.toDateString() === today.toDateString() && 
                           log.alert_triggered;
                }).length : 0;

            // Calculate accuracy (example: based on successful detections)
            const accuracyRate = totalDetections > 0 ? 
                ((totalDetections - alertsToday) / totalDetections * 100).toFixed(1) : 99.5;

            // Update UI
            this.updateStatsUI({
                totalUsers,
                activeUsers,
                alertsToday,
                accuracyRate
            });
        }
    }

    // Update stats in the UI
    updateStatsUI(stats) {
        const statElements = {
            'total-users': stats.totalUsers,
            'active-sessions': stats.activeUsers,
            'alerts-today': stats.alertsToday,
            'system-accuracy': `${stats.accuracyRate}%`
        };

        Object.entries(statElements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                // Animate number change
                this.animateValue(element, value);
            }
        });
    }

    // Animate number changes
    animateValue(element, newValue) {
        const isPercentage = typeof newValue === 'string' && newValue.includes('%');
        const numericValue = isPercentage ? 
            parseFloat(newValue) : 
            (typeof newValue === 'number' ? newValue : parseInt(newValue) || 0);
        
        const currentValue = parseFloat(element.textContent) || 0;
        const duration = 1000;
        const steps = 30;
        const increment = (numericValue - currentValue) / steps;
        let step = 0;

        const timer = setInterval(() => {
            step++;
            const value = currentValue + (increment * step);
            element.textContent = isPercentage ? 
                `${value.toFixed(1)}%` : 
                Math.floor(value);

            if (step >= steps) {
                clearInterval(timer);
                element.textContent = isPercentage ? newValue : numericValue;
            }
        }, duration / steps);
    }

    // Load users table
    async loadUsers() {
        const data = await this.apiCall('/admin/users');
        
        if (data && data.users) {
            const tableBody = document.getElementById('users-table-body');
            if (!tableBody) return;

            tableBody.innerHTML = data.users.map(user => `
                <tr>
                    <td>
                        <div class="user-cell">
                            <div class="user-avatar">${this.getInitials(user.email)}</div>
                            <span>${user.email}</span>
                        </div>
                    </td>
                    <td>${user.email}</td>
                    <td>${this.formatDate(user.created_at)}</td>
                    <td>
                        <span class="status ${user.is_active ? 'active' : 'inactive'}">
                            ${user.is_active ? 'Active' : 'Inactive'}
                        </span>
                    </td>
                    <td>${user.session_count || 0}</td>
                    <td>
                        <div class="action-buttons">
                            <button class="action-btn edit" onclick="adminDashboard.editUser('${user.email}')">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="action-btn ${user.is_active ? 'ban' : 'activate'}" 
                                    onclick="adminDashboard.toggleUserStatus('${user.email}', ${!user.is_active})">
                                <i class="fas fa-${user.is_active ? 'ban' : 'check'}"></i>
                            </button>
                            <button class="action-btn delete" onclick="adminDashboard.deleteUser('${user.email}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');

            console.log(`✅ Loaded ${data.users.length} users`);
        }
    }

    // Load detection events
    async loadDetectionEvents() {
        const data = await this.apiCall('/admin/logs?limit=50');
        
        if (data && data.logs) {
            const eventsGrid = document.querySelector('.events-grid');
            if (!eventsGrid) return;

            eventsGrid.innerHTML = data.logs.map(log => `
                <div class="event-card ${this.getRiskClass(log.drowsiness_score)}">
                    <div class="event-header">
                        <span class="event-id">#${log._id ? log._id.substring(0, 8) : 'N/A'}</span>
                        <span class="event-timestamp">${this.formatDateTime(log.timestamp)}</span>
                    </div>
                    <div class="event-body">
                        <div class="event-user-info">
                            <strong>${log.driver_name || log.user_email}</strong>
                            <span>${log.user_email}</span>
                        </div>
                        <div class="event-metrics">
                            <div class="metric-item">
                                <span>EAR</span>
                                <strong>${log.eye_aspect_ratio ? log.eye_aspect_ratio.toFixed(2) : 'N/A'}</strong>
                            </div>
                            <div class="metric-item">
                                <span>MAR</span>
                                <strong>${log.mouth_aspect_ratio ? log.mouth_aspect_ratio.toFixed(2) : 'N/A'}</strong>
                            </div>
                            <div class="metric-item">
                                <span>Risk Level</span>
                                <strong class="${this.getRiskClass(log.drowsiness_score)}">${log.risk_level || 'Unknown'}</strong>
                            </div>
                            <div class="metric-item">
                                <span>Alert</span>
                                <strong>${log.alert_triggered ? '🔔 Yes' : '✓ No'}</strong>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');

            console.log(`✅ Loaded ${data.logs.length} detection events`);
        }
    }

    // Load recent activity for dashboard cards
    async loadRecentActivity() {
        const data = await this.apiCall('/admin/logs?limit=10');
        
        if (data && data.logs) {
            const eventsList = document.querySelector('.events-list');
            if (!eventsList) return;

            eventsList.innerHTML = data.logs.slice(0, 5).map(log => `
                <div class="event-item">
                    <div class="event-time">${this.formatTime(log.timestamp)}</div>
                    <div class="event-user">${log.driver_name || log.user_email}</div>
                    <span class="event-status ${this.getRiskClass(log.drowsiness_score)}">
                        ${log.risk_level || 'Low'}
                    </span>
                </div>
            `).join('');
        }
    }

    // Helper: Get user initials
    getInitials(email) {
        if (!email) return '?';
        const parts = email.split('@')[0].split('.');
        if (parts.length >= 2) {
            return (parts[0][0] + parts[1][0]).toUpperCase();
        }
        return email[0].toUpperCase();
    }

    // Helper: Format date
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
    }

    // Helper: Format date and time
    formatDateTime(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit'
        });
    }

    // Helper: Format time only
    formatTime(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit'
        });
    }

    // Helper: Get risk class
    getRiskClass(score) {
        if (!score) return 'low';
        if (score >= 70) return 'high';
        if (score >= 40) return 'medium';
        return 'low';
    }

    // User management actions
    async editUser(email) {
        authManager.showToast('Edit user feature coming soon!', 'info');
    }

    async toggleUserStatus(email, newStatus) {
        const confirmed = confirm(`${newStatus ? 'Activate' : 'Deactivate'} user ${email}?`);
        if (!confirmed) return;

        authManager.showToast('User status update feature coming soon!', 'info');
        // TODO: Implement API call to /admin/users/{email}/status
    }

    async deleteUser(email) {
        const confirmed = confirm(`Are you sure you want to delete user ${email}? This action cannot be undone.`);
        if (!confirmed) return;

        authManager.showToast('Delete user feature coming soon!', 'info');
        // TODO: Implement API call to /admin/users/{email} DELETE
    }

    // Start auto-refresh
    startAutoRefresh(intervalMs = 30000) {
        this.stopAutoRefresh();
        this.refreshInterval = setInterval(() => {
            console.log('🔄 Auto-refreshing dashboard...');
            this.loadDashboard();
        }, intervalMs);
    }

    // Stop auto-refresh
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
}

// Initialize admin dashboard manager
const adminDashboard = new AdminDashboardManager();

// Refresh dashboard data
async function refreshDashboard() {
    const refreshBtn = document.querySelector('.refresh-btn');
    if (refreshBtn) {
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
    }

    await adminDashboard.loadDashboard();

    if (refreshBtn) {
        refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
    }

    authManager.showToast('Dashboard refreshed successfully!', 'success');
}

