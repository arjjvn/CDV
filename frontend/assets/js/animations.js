// =============================================
// CDVH | Professional Global Animation & Effects Engine
// Consistent with index.html design language
// =============================================

(function () {
    'use strict';

    // --- 1. Dynamic Sticky Navbar on Scroll ---
    function initNavbarScroll() {
        const header = document.querySelector('header');
        if (!header) return;

        let lastScrollY = window.scrollY;
        let ticking = false;

        function updateHeader() {
            if (window.scrollY > 20) {
                header.classList.add('nav-scrolled');
            } else {
                header.classList.remove('nav-scrolled');
            }
            ticking = false;
        }

        window.addEventListener('scroll', () => {
            lastScrollY = window.scrollY;
            if (!ticking) {
                window.requestAnimationFrame(updateHeader);
                ticking = true;
            }
        }, { passive: true });

        // Initial check
        updateHeader();
    }

    // --- 2. Professional Scroll Reveal (Intersection Observer) ---
    function initScrollReveal() {
        if (!('IntersectionObserver' in window)) {
            // Fallback: activate all reveals immediately
            document.querySelectorAll('.reveal, .reveal-scale, .reveal-left, .reveal-right').forEach(el => {
                el.classList.add('active');
            });
            return;
        }

        const observerOptions = {
            threshold: 0.08,
            rootMargin: '0px 0px -40px 0px'
        };

        const revealObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        // A. Observe all explicitly marked reveal elements
        document.querySelectorAll('.reveal, .reveal-scale, .reveal-left, .reveal-right').forEach(el => {
            revealObserver.observe(el);
        });

        // B. Automatically observe major content sections
        document.querySelectorAll('section, main > div > .grid, main > .grid').forEach(sec => {
            if (!sec.closest('header') && !sec.closest('footer') && !sec.classList.contains('no-reveal')) {
                if (!sec.classList.contains('reveal')) {
                    sec.classList.add('reveal');
                }
                revealObserver.observe(sec);
            }
        });

        // C. Cascading wave effect for grid items/cards
        const gridItems = document.querySelectorAll('.grid > div, .grid > .group, .grid > article');
        gridItems.forEach((card, index) => {
            if (!card.closest('header') && !card.closest('footer') && !card.classList.contains('no-reveal')) {
                if (!card.classList.contains('reveal') && !card.classList.contains('reveal-scale')) {
                    card.classList.add('reveal');
                }
                // Stagger transition delay across columns (wave effect)
                const delay = (index % 4) * 0.12;
                card.style.transitionDelay = `${delay}s`;
                revealObserver.observe(card);
            }
        });
    }

    // --- 3. Number Counter Animation ---
    function initCounters() {
        const counterElements = [];

        // Find elements with explicit .counter or data-target
        document.querySelectorAll('.counter, [data-target]').forEach(el => counterElements.push(el));

        // Auto-detect stat numbers inside stats bars & heroes
        const statCandidates = document.querySelectorAll(
            '.text-3xl, .text-4xl, .text-5xl, .text-6xl'
        );

        statCandidates.forEach(el => {
            if (el.closest('header') || el.closest('footer') || el.classList.contains('no-counter')) return;
            const text = el.textContent.trim();
            // Match numbers like 94%, 1.5K+, 1,547, 12, 98%, 99.9%, 82
            if (/^([$#]?)\s*([\d,]+(?:\.\d+)?)\s*([KkMm%+]?[\w+]?)$/.test(text)) {
                if (!counterElements.includes(el)) {
                    el.classList.add('counter');
                    counterElements.push(el);
                }
            }
        });

        if (counterElements.length === 0) return;

        const counterObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateSingleCounter(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.15 });

        counterElements.forEach(el => {
            // Store original text
            if (!el.dataset.target) {
                const raw = el.textContent.trim();
                const match = raw.match(/^([$#]?)\s*([\d,]+(?:\.\d+)?)\s*(.*)$/);
                if (match) {
                    el.dataset.prefix = match[1] || '';
                    el.dataset.target = match[2].replace(/,/g, '');
                    el.dataset.suffix = match[3] || '';
                    el.dataset.hasComma = match[2].includes(',') ? 'true' : 'false';
                    el.dataset.decimals = match[2].includes('.') ? (match[2].split('.')[1].length) : '0';
                    el.textContent = (el.dataset.prefix || '') + '0' + (el.dataset.suffix || '');
                }
            }
            counterObserver.observe(el);
        });
    }

    function animateSingleCounter(el) {
        const target = parseFloat(el.dataset.target);
        if (isNaN(target)) return;

        const prefix = el.dataset.prefix || '';
        const suffix = el.dataset.suffix || '';
        const decimals = parseInt(el.dataset.decimals || '0', 10);
        const hasComma = el.dataset.hasComma === 'true';
        const duration = 1600; // ms
        const startTime = performance.now();

        function easeOutCubic(t) {
            return 1 - Math.pow(1 - t, 3);
        }

        function update(now) {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const current = target * easeOutCubic(progress);

            let formattedNumber = decimals > 0 ? current.toFixed(decimals) : Math.floor(current).toString();
            if (hasComma) {
                const parts = formattedNumber.split('.');
                parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
                formattedNumber = parts.join('.');
            }

            el.textContent = `${prefix}${formattedNumber}${suffix}`;

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                let finalNum = decimals > 0 ? target.toFixed(decimals) : target.toString();
                if (hasComma) {
                    const parts = finalNum.split('.');
                    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
                    finalNum = parts.join('.');
                }
                el.textContent = `${prefix}${finalNum}${suffix}`;
            }
        }

        requestAnimationFrame(update);
    }

    // --- 4. Button Click Ripple Effect ---
    function initButtonRipples() {
        document.addEventListener('click', function (e) {
            const btn = e.target.closest('.btn-hover, .btn-fill, button, a.btn');
            if (!btn) return;

            const rect = btn.getBoundingClientRect();
            const ripple = document.createElement('span');
            const diameter = Math.max(rect.width, rect.height);
            const radius = diameter / 2;

            ripple.style.width = ripple.style.height = `${diameter}px`;
            ripple.style.left = `${e.clientX - rect.left - radius}px`;
            ripple.style.top = `${e.clientY - rect.top - radius}px`;
            ripple.classList.add('ripple');

            // Detect if button is light or dark
            const isLightBg = window.getComputedStyle(btn).backgroundColor === 'rgb(255, 255, 255)' ||
                              btn.classList.contains('bg-white') ||
                              btn.classList.contains('bg-gray-50');
            if (isLightBg) {
                ripple.classList.add('ripple-dark');
            }

            const existingContainer = btn.querySelector('.ripple-container');
            if (existingContainer) {
                existingContainer.appendChild(ripple);
            } else {
                btn.style.position = btn.style.position || 'relative';
                btn.style.overflow = 'hidden';
                btn.appendChild(ripple);
            }

            setTimeout(() => {
                ripple.remove();
            }, 650);
        });
    }

    // --- 5. Interactive Card Elevation & Micro-Tilt ---
    function initCardInteractions() {
        const cards = document.querySelectorAll(
            '.bg-white.rounded, .stat-card, .task-card, .dashboard-card, [class*="shadow-card"]'
        );

        cards.forEach(card => {
            if (!card.closest('header') && !card.closest('footer') && !card.classList.contains('no-lift')) {
                card.classList.add('hover-lift');
            }
        });
    }

    // --- 6. Animated Progress Bars ---
    function initProgressBars() {
        const progressBars = document.querySelectorAll('.progress-bar, [data-progress]');
        if (progressBars.length === 0) return;

        const observer = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const bar = entry.target;
                    const targetWidth = bar.dataset.progress || bar.style.width || '100%';
                    bar.style.width = '0%';
                    bar.classList.add('progress-bar-animated');
                    
                    // Trigger expansion
                    setTimeout(() => {
                        bar.style.width = targetWidth;
                    }, 50);

                    obs.unobserve(bar);
                }
            });
        }, { threshold: 0.2 });

        progressBars.forEach(bar => observer.observe(bar));
    }

    // --- 7. Initialize Everything on DOM Ready ---
    function initAll() {
        initNavbarScroll();
        initScrollReveal();
        initCounters();
        initButtonRipples();
        initCardInteractions();
        initProgressBars();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAll);
    } else {
        initAll();
    }

    // Export helpers to window for optional programmatic triggers
    window.CDVH_ANIMATIONS = {
        refresh: initAll,
        animateCounter: animateSingleCounter
    };

})();

