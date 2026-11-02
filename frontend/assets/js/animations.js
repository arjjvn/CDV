// CDVH | Minimal & Safe Animation Helper
(function () {
    'use strict';

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

    function initScrollReveal() {
        // Only observe elements that ALREADY have reveal classes explicitly in the HTML.
        // Never dynamically hide sections or cards.
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

    function initAll() {
        initNavbarScroll();
        initScrollReveal();
        initButtonRipples();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAll);
    } else {
        initAll();
    }
})();
