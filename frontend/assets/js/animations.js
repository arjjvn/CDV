// ======================================================================
// CDVH | ANIMATIONS.JS — PURE CLIENT-SIDE UI ANIMATIONS & INTERACTIONS
// All data, authentication, chat, and matching are handled by Python backend
// ======================================================================

(function () {
    'use strict';

    // ------------------------------------------------------------------
    // 1. NAVBAR SCROLL SHADOW & GLASS EFFECT
    // ------------------------------------------------------------------
    function initNavbarScroll() {
        const header = document.querySelector('header');
        if (!header) return;

        function updateHeader() {
            if (window.scrollY > 15) {
                header.classList.add('shadow-md');
                header.classList.add('nav-scrolled');
            } else {
                header.classList.remove('shadow-md');
                header.classList.remove('nav-scrolled');
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

        function markVisible(el) {
            el.classList.add('active');
            el.classList.add('visible');
        }

        if (!('IntersectionObserver' in window)) {
            reveals.forEach(markVisible);
            return;
        }

        const observer = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    obs.unobserve(entry.target);
                    // Defer to next frame so browser establishes initial state and triggers transition
                    requestAnimationFrame(() => {
                        markVisible(entry.target);
                    });
                }
            });
        }, {
            threshold: 0.05,
            rootMargin: '0px 0px -10px 0px'
        });

        reveals.forEach(el => observer.observe(el));

        // Safety fallback: ensure above-the-fold elements are revealed after initial entrance
        setTimeout(() => {
            reveals.forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.top < window.innerHeight && rect.bottom > 0) {
                    markVisible(el);
                }
            });
        }, 1200);

        // Expose helper to trigger scroll-reveal on dynamically filtered/added elements
        window.refreshScrollReveal = function () {
            document.querySelectorAll('.reveal:not(.visible), .reveal-scale:not(.visible), .reveal-left:not(.visible), .reveal-right:not(.visible)')
                .forEach(el => observer.observe(el));
        };
    }

    // ------------------------------------------------------------------
    // 2B. TYPEWRITER TEXT ANIMATION (#typed-text)
    // ------------------------------------------------------------------
    function initTypewriter() {
        const el = document.getElementById('typed-text');
        if (!el) return;

        const words = ['PROTECTING', 'SAVING', 'SUPPORTING', 'EMPOWERING', 'UNITING'];
        let wordIdx = 0;
        let charIdx = el.textContent ? el.textContent.trim().length : 0;
        let isDeleting = charIdx > 0;

        function tick() {
            const current = words[wordIdx];

            if (isDeleting) {
                el.textContent = current.substring(0, charIdx - 1);
                charIdx--;
            } else {
                el.textContent = current.substring(0, charIdx + 1);
                charIdx++;
            }

            let delay = isDeleting ? 55 : 110;

            if (!isDeleting && charIdx === current.length) {
                delay = 2000;
                isDeleting = true;
            } else if (isDeleting && charIdx === 0) {
                isDeleting = false;
                wordIdx = (wordIdx + 1) % words.length;
                delay = 350;
            }

            setTimeout(tick, delay);
        }

        setTimeout(tick, isDeleting ? 2200 : 400);
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
    // 6. CHATBOT WINDOW TOGGLE & INTERACTIVE MESSAGING
    // ------------------------------------------------------------------
    function formatMarkdownToHtml(text) {
        if (!text) return "";
        let raw = text.trim();

        // Clean up emoji bullet prefixes, smashed headers, and weird double hyphens
        raw = raw.replace(/([📱🚨✅📄⚠️🔗]+)\s*(\*\*[^*]+?\*\*)/g, "\n\n$2");
        raw = raw.replace(/([.!?])\s*([📱🚨✅📄⚠️🔗]+)\s*/g, "$1\n\n");
        raw = raw.replace(/([.!?])\s*(\*\*[^*]+?\*\*)/g, "$1\n\n$2");
        raw = raw.replace(/([📱🚨✅📄⚠️🔗]+)\s*-\s*/g, "\n- ");
        raw = raw.replace(/\s+-\s*-\s*/g, "\n- ");
        raw = raw.replace(/:\s*-\s*/g, ":\n- ");
        raw = raw.replace(/^[📱🚨✅📄⚠️🔗]\s*/gm, "");
        raw = raw.replace(/\s*[📱🚨✅📄⚠️🔗]\s*$/gm, "");
        raw = raw.replace(/\s*[📱🚨✅📄⚠️🔗]\s*/g, " ");
        raw = raw.replace(/^-\s*-\s*/gm, "- ");

        // Basic HTML escaping
        let html = raw
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // Bold formatting: **bold** or __bold__
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-brand-navy">$1</strong>');
        html = html.replace(/__(.*?)__/g, '<strong class="font-semibold text-brand-navy">$1</strong>');

        // Headers: ### Header
        html = html.replace(/^###\s+(.*$)/gm, '<h5 class="font-bold text-sm text-brand-navy mt-2 mb-1">$1</h5>');
        html = html.replace(/^##\s+(.*$)/gm, '<h4 class="font-bold text-base text-brand-navy mt-2.5 mb-1">$1</h4>');

        // Markdown Links: [label](url)
        html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-brand-blue font-semibold underline hover:text-blue-800">$1</a>');

        // Process lists and paragraphs
        const lines = html.split("\n");
        let inList = false;
        let out = [];

        for (let i = 0; i < lines.length; i++) {
            let line = lines[i].trim();
            if (line.startsWith("- ") || line.startsWith("* ")) {
                if (!inList) {
                    out.push('<ul class="list-disc ml-5 space-y-1 my-1.5">');
                    inList = true;
                }
                out.push(`<li>${line.substring(2)}</li>`);
            } else {
                if (inList) {
                    out.push('</ul>');
                    inList = false;
                }
                if (line.length > 0) {
                    out.push(`<p class="mb-2 leading-relaxed">${line}</p>`);
                }
            }
        }
        if (inList) {
            out.push('</ul>');
        }

        return out.join("");
    }

    function formatExistingBotMessages() {
        document.querySelectorAll(".bot-markdown").forEach(function (el) {
            if (!el.getAttribute("data-formatted")) {
                if (el.children.length === 0) {
                    const rawText = el.textContent || "";
                    if (rawText.includes("**") || rawText.includes("[") || rawText.includes("\n") || rawText.includes("- ")) {
                        el.innerHTML = formatMarkdownToHtml(rawText);
                    }
                }
                el.setAttribute("data-formatted", "true");
            }
        });
    }

    function initChatbotToggle() {
        const toggleBtn = document.getElementById("chatToggleButton");
        const closeBtn = document.getElementById("chatCloseButton");
        const chatWin = document.getElementById("chatWindow");
        const chatForm = document.getElementById("chatForm");
        const chatInput = document.getElementById("chatInput");
        const chatMessages = document.getElementById("chatMessages");

        if (!chatWin) return;

        function scrollToBottom() {
            if (chatMessages) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }

        function openChat() {
            chatWin.classList.remove("hidden");
            chatWin.classList.add("flex");
            setTimeout(scrollToBottom, 60);
            if (chatInput) chatInput.focus();
        }

        function closeChat() {
            chatWin.classList.add("hidden");
            chatWin.classList.remove("flex");
        }

        if (toggleBtn) {
            toggleBtn.onclick = function (e) {
                if (e) { e.preventDefault(); e.stopPropagation(); }
                if (chatWin.classList.contains("hidden")) {
                    openChat();
                } else {
                    closeChat();
                }
            };
        }

        if (closeBtn) {
            closeBtn.onclick = function (e) {
                if (e) { e.preventDefault(); e.stopPropagation(); }
                closeChat();
            };
        }

        // Format any server-rendered bot messages already present
        formatExistingBotMessages();

        // Scroll to bottom if opened initially by ?chat=open
        if (!chatWin.classList.contains("hidden")) {
            setTimeout(scrollToBottom, 120);
        }

        // Seamless Asynchronous Chat (no page reload) with fallback
        if (chatForm && chatInput && chatMessages) {
            chatForm.addEventListener("submit", async function (e) {
                const question = chatInput.value.trim();
                if (!question) return;

                if (window.fetch && window.FormData) {
                    e.preventDefault();

                    // 1. Add user bubble immediately
                    const userDiv = document.createElement("div");
                    userDiv.className = "bg-brand-navy text-white p-3 rounded-lg rounded-tr-none text-sm self-end max-w-[85%] shadow-sm animate-fade-in";
                    userDiv.textContent = question;
                    chatMessages.appendChild(userDiv);

                    chatInput.value = "";
                    const submitBtn = chatForm.querySelector('button[type="submit"]');
                    if (submitBtn) submitBtn.disabled = true;

                    // 2. Add typing indicator
                    const typingDiv = document.createElement("div");
                    typingDiv.id = "chatTypingIndicator";
                    typingDiv.className = "bg-white p-3 rounded-lg rounded-tl-none border border-gray-200 text-xs text-gray-500 self-start shadow-sm flex items-center gap-1.5 animate-pulse";
                    typingDiv.innerHTML = '<span class="font-medium text-brand-navy">Assistant thinking</span><span class="animate-bounce">.</span><span class="animate-bounce delay-100">.</span><span class="animate-bounce delay-200">.</span>';
                    chatMessages.appendChild(typingDiv);
                    scrollToBottom();

                    try {
                        const formData = new FormData(chatForm);
                        formData.set("question", question);

                        const response = await fetch("/chat", {
                            method: "POST",
                            headers: {
                                "Accept": "application/json"
                            },
                            body: formData
                        });

                        if (typingDiv && typingDiv.parentNode) {
                            typingDiv.remove();
                        }

                        if (response.ok) {
                            const data = await response.json();
                            const botAnswer = data.answer || "I could not retrieve disaster guidelines at this moment.";

                            const botDiv = document.createElement("div");
                            botDiv.className = "bg-white p-3 rounded-lg rounded-tl-none border border-gray-200 text-sm text-gray-800 self-start max-w-[85%] shadow-sm leading-relaxed whitespace-pre-wrap bot-markdown animate-fade-in";
                            botDiv.innerHTML = formatMarkdownToHtml(botAnswer);
                            chatMessages.appendChild(botDiv);
                            scrollToBottom();
                        } else {
                            const errDiv = document.createElement("div");
                            errDiv.className = "bg-red-50 text-red-600 p-3 rounded-lg text-xs self-start border border-red-200";
                            errDiv.textContent = "Could not fetch guidelines right now. Please call emergency hotline 112.";
                            chatMessages.appendChild(errDiv);
                            scrollToBottom();
                        }
                    } catch (err) {
                        if (typingDiv && typingDiv.parentNode) {
                            typingDiv.remove();
                        }
                        chatForm.submit();
                        return;
                    } finally {
                        if (submitBtn) submitBtn.disabled = false;
                        if (chatInput) chatInput.focus();
                    }
                }
            });
        }
    }

    // ------------------------------------------------------------------
    // 7. NUMERICAL COUNTERS ANIMATION (RAF EASING)
    // ------------------------------------------------------------------
    function initNumberCounters() {
        const counters = document.querySelectorAll('[data-counter]');
        if (counters.length === 0) return;

        function animateCounter(el) {
            const target = parseInt(el.getAttribute('data-counter'), 10);
            if (isNaN(target)) return;

            const duration = 1200; // ms
            const startTime = performance.now();
            const prefix = el.getAttribute('data-prefix') || '';
            const suffix = el.getAttribute('data-suffix') || '';

            function update(now) {
                const elapsed = now - startTime;
                const progress = Math.min(elapsed / duration, 1);
                // Ease out expo: 1 - 2^(-10 * progress)
                const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
                const currentVal = Math.floor(eased * target);

                el.textContent = `${prefix}${currentVal}${suffix}`;

                if (progress < 1) {
                    requestAnimationFrame(update);
                } else {
                    el.textContent = `${prefix}${target}${suffix}`;
                }
            }

            requestAnimationFrame(update);
        }

        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries, obs) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        animateCounter(entry.target);
                        obs.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.15 });

            counters.forEach(c => observer.observe(c));
        } else {
            counters.forEach(c => animateCounter(c));
        }
    }

    // ------------------------------------------------------------------
    // 8. 3D CARD TILT ON MOUSEMOVE
    // ------------------------------------------------------------------
    function initCardTiltEffects() {
        // Respect prefers-reduced-motion
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

        const tiltCards = document.querySelectorAll('.tilt-card');
        if (tiltCards.length === 0) return;

        tiltCards.forEach(card => {
            let isHovered = false;

            card.addEventListener('mouseenter', () => {
                isHovered = true;
                card.style.transition = 'transform 0.1s ease-out, box-shadow 0.25s ease';
            });

            card.addEventListener('mousemove', (e) => {
                if (!isHovered) return;
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;

                const centerX = rect.width / 2;
                const centerY = rect.height / 2;

                const rotateX = ((y - centerY) / centerY) * -4.5; // max 4.5 deg
                const rotateY = ((x - centerX) / centerX) * 4.5;

                card.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) translateY(-2px)`;
            });

            card.addEventListener('mouseleave', () => {
                isHovered = false;
                card.style.transition = 'transform 0.4s var(--ease-out-expo, cubic-bezier(0.16,1,0.3,1)), box-shadow 0.4s ease';
                card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)';
            });
        });
    }

    // ------------------------------------------------------------------
    // 9. PROGRESS BAR SCROLL TRIGGERED ANIMATIONS
    // ------------------------------------------------------------------
    function initProgressBars() {
        const progressFills = document.querySelectorAll('[data-progress-target]');
        if (progressFills.length === 0) return;

        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries, obs) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const targetWidth = entry.target.getAttribute('data-progress-target');
                        entry.target.style.width = targetWidth;
                        obs.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.1 });

            progressFills.forEach(p => observer.observe(p));
        } else {
            progressFills.forEach(p => {
                p.style.width = p.getAttribute('data-progress-target');
            });
        }
    }

    // ------------------------------------------------------------------
    // 10. STAGGER ENTRANCE DELAYS
    // ------------------------------------------------------------------
    function initStaggerDelays() {
        const groups = document.querySelectorAll('[data-stagger-group]');
        groups.forEach(group => {
            const items = group.querySelectorAll('.stagger-item');
            items.forEach((item, idx) => {
                item.style.setProperty('--stagger-i', idx);
            });
        });
    }

    // ------------------------------------------------------------------
    // 11. DASHBOARD CLIENT-SIDE FILTERS & LIVE SEARCH
    // ------------------------------------------------------------------
    function initDashboardFilters() {
        // --- A. Emergency Alerts Filter Tabs & Search ---
        const alertFilterTabs = document.querySelectorAll('#alertFilterTabs .filter-tab-btn');
        const alertSearchInput = document.getElementById('alertSearchInput');
        const alertItems = document.querySelectorAll('.alert-item');
        const alertEmptyFiltered = document.getElementById('alertEmptyFiltered');

        function filterAlerts() {
            let activeSeverity = 'all';
            alertFilterTabs.forEach(tab => {
                if (tab.classList.contains('active')) {
                    activeSeverity = tab.getAttribute('data-filter') || 'all';
                }
            });

            const query = (alertSearchInput ? alertSearchInput.value : '').trim().toLowerCase();
            let visibleCount = 0;

            alertItems.forEach(item => {
                const itemSeverity = (item.getAttribute('data-severity') || '').toLowerCase();
                const itemStatus = (item.getAttribute('data-status') || '').toLowerCase();
                const itemText = item.textContent.toLowerCase();

                let matchesFilter = false;
                if (activeSeverity === 'all') {
                    matchesFilter = true;
                } else if (activeSeverity === 'critical') {
                    matchesFilter = (itemSeverity === 'urgent' || itemSeverity === 'high');
                } else if (activeSeverity === 'medium') {
                    matchesFilter = (itemSeverity === 'medium');
                } else if (activeSeverity === 'resolved') {
                    matchesFilter = (itemStatus === 'resolved');
                } else if (activeSeverity === 'active') {
                    matchesFilter = (itemStatus === 'active');
                }

                const matchesQuery = !query || itemText.includes(query);

                if (matchesFilter && matchesQuery) {
                    item.style.display = '';
                    visibleCount++;
                } else {
                    item.style.display = 'none';
                }
            });

            if (alertEmptyFiltered) {
                if (visibleCount === 0 && alertItems.length > 0) {
                    alertEmptyFiltered.classList.remove('hidden');
                } else {
                    alertEmptyFiltered.classList.add('hidden');
                }
            }
        }

        if (alertFilterTabs.length > 0) {
            alertFilterTabs.forEach(tab => {
                tab.addEventListener('click', function () {
                    alertFilterTabs.forEach(t => t.classList.remove('active'));
                    this.classList.add('active');
                    filterAlerts();
                });
            });
        }

        if (alertSearchInput) {
            alertSearchInput.addEventListener('input', filterAlerts);
        }

        // --- B. Tasks Filter Tabs & Search ---
        const taskFilterTabs = document.querySelectorAll('#taskFilterTabs .filter-tab-btn');
        const taskSearchInput = document.getElementById('taskSearchInput');
        const taskItems = document.querySelectorAll('.task-item');
        const taskEmptyFiltered = document.getElementById('taskEmptyFiltered');

        function filterTasks() {
            let activeFilter = 'all';
            taskFilterTabs.forEach(tab => {
                if (tab.classList.contains('active')) {
                    activeFilter = tab.getAttribute('data-filter') || 'all';
                }
            });

            const query = (taskSearchInput ? taskSearchInput.value : '').trim().toLowerCase();
            let visibleCount = 0;

            taskItems.forEach(item => {
                const itemUrgency = (item.getAttribute('data-urgency') || '').toLowerCase();
                const itemStatus = (item.getAttribute('data-status') || '').toLowerCase();
                const isFull = item.getAttribute('data-is-full') === 'true';
                const itemText = item.textContent.toLowerCase();

                let matchesFilter = false;
                if (activeFilter === 'all') {
                    matchesFilter = true;
                } else if (activeFilter === 'urgent') {
                    matchesFilter = (itemUrgency === 'urgent');
                } else if (activeFilter === 'needs-volunteers') {
                    matchesFilter = !isFull && (itemStatus !== 'resolved');
                } else if (activeFilter === 'resolved') {
                    matchesFilter = (itemStatus === 'resolved');
                }

                const matchesQuery = !query || itemText.includes(query);

                if (matchesFilter && matchesQuery) {
                    item.style.display = '';
                    visibleCount++;
                } else {
                    item.style.display = 'none';
                }
            });

            if (taskEmptyFiltered) {
                if (visibleCount === 0 && taskItems.length > 0) {
                    taskEmptyFiltered.classList.remove('hidden');
                } else {
                    taskEmptyFiltered.classList.add('hidden');
                }
            }
        }

        if (taskFilterTabs.length > 0) {
            taskFilterTabs.forEach(tab => {
                tab.addEventListener('click', function () {
                    taskFilterTabs.forEach(t => t.classList.remove('active'));
                    this.classList.add('active');
                    filterTasks();
                });
            });
        }

        if (taskSearchInput) {
            taskSearchInput.addEventListener('input', filterTasks);
        }

        // --- C. Volunteer Pool Real-time Search & Filter ---
        const volSearchInput = document.getElementById('volSearchInput');
        const volCards = document.querySelectorAll('.volunteer-card');
        const volEmptyFiltered = document.getElementById('volEmptyFiltered');

        if (volSearchInput && volCards.length > 0) {
            volSearchInput.addEventListener('input', function () {
                const query = this.value.trim().toLowerCase();
                let visibleCount = 0;

                volCards.forEach(card => {
                    const text = card.textContent.toLowerCase();
                    if (!query || text.includes(query)) {
                        card.style.display = '';
                        visibleCount++;
                    } else {
                        card.style.display = 'none';
                    }
                });

                if (volEmptyFiltered) {
                    if (visibleCount === 0 && volCards.length > 0) {
                        volEmptyFiltered.classList.remove('hidden');
                    } else {
                        volEmptyFiltered.classList.add('hidden');
                    }
                }
            });
        }
    }

    // ------------------------------------------------------------------
    // 12. MODAL UI HANDLERS (EXPOSED GLOBALLY)
    // ------------------------------------------------------------------
    window.openNewTaskModal = function () {
        const modal = document.getElementById('newTaskModal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            document.body.classList.add('overflow-hidden');
            const titleInput = modal.querySelector('input[name="title"]');
            if (titleInput) setTimeout(() => titleInput.focus(), 100);
        }
    };

    window.closeNewTaskModal = function () {
        const modal = document.getElementById('newTaskModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            document.body.classList.remove('overflow-hidden');
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
            document.body.classList.add('overflow-hidden');
        }
    };

    window.closeCoordinatorEditSkillModal = function () {
        const modal = document.getElementById('coordinatorSkillModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            document.body.classList.remove('overflow-hidden');
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

    // Close modal on outside backdrop click
    document.addEventListener("click", function (e) {
        if (e.target && e.target.id === 'newTaskModal') {
            window.closeNewTaskModal();
        }
        if (e.target && e.target.id === 'coordinatorSkillModal') {
            window.closeCoordinatorEditSkillModal();
        }
        if (e.target && e.target.id === 'volunteerSkillModal') {
            window.closeVolunteerSkillModal();
        }
    });

    // ------------------------------------------------------------------
    // 13. DYNAMIC LOCATION SELECTORS (DISTRICT -> LOCALITY SYNC)
    // ------------------------------------------------------------------
    function initLocationSelectors() {
        const distSelect = document.getElementById('incidentDistrict');
        const placeSelect = document.getElementById('incidentPlace');

        if (distSelect && placeSelect) {
            distSelect.addEventListener('change', function () {
                const selectedDistrict = this.value.trim().toLowerCase();
                const optgroups = placeSelect.querySelectorAll('optgroup');

                let matched = false;
                optgroups.forEach(group => {
                    const groupLabel = (group.label || '').trim().toLowerCase();
                    if (!selectedDistrict || groupLabel === selectedDistrict) {
                        group.style.display = '';
                        matched = true;
                    } else {
                        group.style.display = 'none';
                    }
                });

                // Check if current place belongs to chosen district
                const currentOpt = placeSelect.selectedOptions ? placeSelect.selectedOptions[0] : null;
                if (currentOpt && currentOpt.parentElement && currentOpt.parentElement.tagName === 'OPTGROUP') {
                    const parentLabel = (currentOpt.parentElement.label || '').trim().toLowerCase();
                    if (selectedDistrict && parentLabel !== selectedDistrict) {
                        placeSelect.value = '';
                    }
                }
            });
        }
    }

    // ------------------------------------------------------------------
    // INITIALIZATION
    // ------------------------------------------------------------------
    function initAllAnimations() {
        initNavbarScroll();
        initScrollReveal();
        initTypewriter();
        initButtonRipples();
        initMobileMenuAnimation();
        initHeroParticles();
        initChatbotToggle();
        initNumberCounters();
        initCardTiltEffects();
        initProgressBars();
        initStaggerDelays();
        initDashboardFilters();
        initLocationSelectors();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAllAnimations);
    } else {
        initAllAnimations();
    }
})();
