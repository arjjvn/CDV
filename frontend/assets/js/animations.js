// ======================================================================
// CDVH | ANIMATIONS.JS — PURE CLIENT-SIDE UI ANIMATIONS ONLY
// All data, authentication, chat, and matching are handled by Python backend
// ======================================================================

(function () {
    'use strict';

    // ------------------------------------------------------------------
    // 1. NAVBAR SCROLL SHADOW
    // ------------------------------------------------------------------
    function initNavbarScroll() {
        const header = document.querySelector('header');
        if (!header) return;

        function updateHeader() {
            if (window.scrollY > 20) {
                header.classList.add('shadow-md');
            } else {
                header.classList.remove('shadow-md');
            }
        }

        window.addEventListener('scroll', updateHeader, { passive: true });
        updateHeader();
    }

    // ------------------------------------------------------------------
    // 2. SCROLL REVEAL (INTERSECTION OBSERVER)
    // ------------------------------------------------------------------
    function initScrollReveal() {
        const reveals = document.querySelectorAll('.reveal, .reveal-scale, .reveal-left, .reveal-right');
        if (reveals.length === 0) return;

        if (!('IntersectionObserver' in window)) {
            reveals.forEach(el => el.classList.add('active'));
            return;
        }

        const observer = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                    obs.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        reveals.forEach(el => observer.observe(el));
    }

    // ------------------------------------------------------------------
    // 3. BUTTON RIPPLE EFFECT
    // ------------------------------------------------------------------
    function initButtonRipples() {
        document.addEventListener('click', function (e) {
            const btn = e.target.closest('.btn-ripple, .btn-hover');
            if (!btn) return;

            const rect = btn.getBoundingClientRect();
            const ripple = document.createElement('span');
            const diameter = Math.max(rect.width, rect.height);
            const radius = diameter / 2;

            ripple.style.width = ripple.style.height = `${diameter}px`;
            ripple.style.left = `${e.clientX - rect.left - radius}px`;
            ripple.style.top = `${e.clientY - rect.top - radius}px`;
            ripple.className = 'ripple';

            btn.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        });
    }

    // ------------------------------------------------------------------
    // 4. MOBILE MENU ANIMATION
    // ------------------------------------------------------------------
    function initMobileMenuAnimation() {
        const hamburger = document.getElementById("hamburger");
        const mobileMenu = document.getElementById("mobile-menu");
        if (!hamburger || !mobileMenu) return;

        hamburger.addEventListener("click", function () {
            mobileMenu.classList.toggle("open");
        });

        mobileMenu.querySelectorAll("a").forEach(function (link) {
            link.addEventListener("click", function () {
                mobileMenu.classList.remove("open");
            });
        });
    }

    // ------------------------------------------------------------------
    // 5. HERO PARTICLES ANIMATION (CANVAS)
    // ------------------------------------------------------------------
    function initHeroParticles() {
        const canvas = document.getElementById("particles");
        if (!canvas) return;

        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        let width = 0;
        let height = 0;
        let particles = [];
        const particleCount = 28;

        function resize() {
            if (!canvas.parentElement) return;
            width = canvas.width = canvas.parentElement.offsetWidth || window.innerWidth;
            height = canvas.height = canvas.parentElement.offsetHeight || 600;
        }

        function createParticles() {
            particles = [];
            for (let i = 0; i < particleCount; i++) {
                particles.push({
                    x: Math.random() * (width || window.innerWidth),
                    y: Math.random() * (height || 600),
                    radius: Math.random() * 2 + 1,
                    vx: (Math.random() - 0.5) * 0.4,
                    vy: (Math.random() - 0.5) * 0.4,
                    alpha: Math.random() * 0.5 + 0.2
                });
            }
        }

        function animate() {
            ctx.clearRect(0, 0, width, height);

            for (let i = 0; i < particles.length; i++) {
                const p = particles[i];
                p.x += p.vx;
                p.y += p.vy;

                if (p.x < 0) p.x = width;
                if (p.x > width) p.x = 0;
                if (p.y < 0) p.y = height;
                if (p.y > height) p.y = 0;

                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(255, 255, 255, ${p.alpha})`;
                ctx.fill();
            }

            requestAnimationFrame(animate);
        }

        window.addEventListener("resize", resize);
        resize();
        createParticles();
        animate();
    }

    // ------------------------------------------------------------------
    // 6. CHATBOT WINDOW TOGGLE
    // ------------------------------------------------------------------
    function initChatbotToggle() {
        const toggleBtn = document.getElementById("chatToggleButton");
        const closeBtn = document.getElementById("chatCloseButton");
        const chatWin = document.getElementById("chatWindow");
        if (toggleBtn && chatWin) {
            toggleBtn.addEventListener("click", function () {
                chatWin.classList.toggle("hidden");
                chatWin.classList.toggle("flex");
            });
        }
        if (closeBtn && chatWin) {
            closeBtn.addEventListener("click", function () {
                chatWin.classList.add("hidden");
                chatWin.classList.remove("flex");
            });
        }
    }

    // ------------------------------------------------------------------
    // 7. MODAL UI HANDLERS (EXPOSED GLOBALLY)
    // ------------------------------------------------------------------
    window.openNewTaskModal = function () {
        const modal = document.getElementById('newTaskModal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    };

    window.closeNewTaskModal = function () {
        const modal = document.getElementById('newTaskModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    };

    window.openCoordinatorEditSkillModal = function (volId, volName, s1, s2, s3, exp) {
        const modal = document.getElementById('coordinatorSkillModal');
        const form = document.getElementById('coordinatorSkillForm');
        const nameEl = document.getElementById('coordSkillVolName');
        const s1El = document.getElementById('coordSkill1');
        const s2El = document.getElementById('coordSkill2');
        const s3El = document.getElementById('coordSkill3');
        const expEl = document.getElementById('coordSkillExp');
        if (modal && form) {
            form.action = `/coordinator/volunteers/${volId}/skills`;
            if (nameEl) nameEl.textContent = volName;
            if (s1El) s1El.value = s1 || '';
            if (s2El) s2El.value = s2 || '';
            if (s3El) s3El.value = s3 || '';
            if (expEl) expEl.value = exp || 0;
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    };

    window.closeCoordinatorEditSkillModal = function () {
        const modal = document.getElementById('coordinatorSkillModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    };

    window.openVolunteerSkillModal = function () {
        const modal = document.getElementById("volunteerSkillModal");
        if (modal) {
            modal.classList.remove("hidden");
            modal.classList.add("flex");
            document.body.classList.add("overflow-hidden");
        }
    };

    window.closeVolunteerSkillModal = function () {
        const modal = document.getElementById("volunteerSkillModal");
        if (modal) {
            modal.classList.add("hidden");
            modal.classList.remove("flex");
            document.body.classList.remove("overflow-hidden");
        }
    };

    // Close modals on Escape key
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") {
            window.closeNewTaskModal();
            window.closeCoordinatorEditSkillModal();
            window.closeVolunteerSkillModal();
        }
    });

    // ------------------------------------------------------------------
    // INITIALIZATION
    // ------------------------------------------------------------------
    function initAllAnimations() {
        initNavbarScroll();
        initScrollReveal();
        initButtonRipples();
        initMobileMenuAnimation();
        initHeroParticles();
        initChatbotToggle();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAllAnimations);
    } else {
        initAllAnimations();
    }
})();
