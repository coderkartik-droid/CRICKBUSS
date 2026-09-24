/**
 * CRICKBUSS - Premium Frontend Engine
 * Handles CSRF cookies, AJAX interactions (bookmarks, likes), toast alerts,
 * search autocomplete with debounce, recent searches, password strength evaluation,
 * sticky navbar behavior, smooth animations, and premium interactions.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Premium Sticky Navbar Behavior
    const navbar = document.getElementById('mainNavbar');
    if (navbar) {
        let lastScroll = 0;
        
        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset;
            
            // Add/remove scrolled class for visual effects
            if (currentScroll > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
            
            // Hide/show navbar on scroll direction
            if (currentScroll > lastScroll && currentScroll > 100) {
                navbar.style.transform = 'translateY(-100%)';
            } else {
                navbar.style.transform = 'translateY(0)';
            }
            
            lastScroll = currentScroll;
        });
    }

    // 2. Premium Scroll Animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe elements with animation classes
    document.querySelectorAll('.team-card, .player-card, .content-card, .live-match-card').forEach(el => {
        el.classList.add('fade-in');
        observer.observe(el);
    });

    // 3. Initialize Bootstrap Tooltips & Popovers
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(el => new bootstrap.Tooltip(el));

    // 2. CSRF Token Helper
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // 3. Dynamic Toast Notification Helper
    window.showToast = function(message, type = 'success') {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toastId = 'toast-' + Date.now();
        const iconClass = type === 'success' ? 'fa-circle-check text-success' : 'fa-circle-exclamation text-danger';

        const toastHtml = `
            <div id="${toastId}" class="toast custom-toast align-items-center border-0 mb-2" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body d-flex align-items-center gap-2 py-2 px-3 small">
                        <i class="fa-solid ${iconClass} fs-6"></i>
                        <span class="fw-semibold">${message}</span>
                    </div>
                    <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;

        container.insertAdjacentHTML('beforeend', toastHtml);
        const toastEl = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastEl, { delay: 4500 });
        toast.show();

        toastEl.addEventListener('hidden.bs.toast', () => {
            toastEl.remove();
        });
    };

    // 4. AJAX Save / Bookmark Match
    document.querySelectorAll('.btn-save-match').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const matchId = btn.getAttribute('data-match-id');
            if (!matchId) return;

            try {
                const response = await fetch(`/dashboard/save-match/${matchId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken,
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json'
                    }
                });

                if (response.status === 403 || response.redirected) {
                    window.location.href = '/accounts/login/';
                    return;
                }

                const data = await response.json();
                if (data.is_saved) {
                    btn.classList.add('active');
                    btn.innerHTML = '<i class="fa-solid fa-bookmark text-warning"></i> <span>Saved</span>';
                } else {
                    btn.classList.remove('active');
                    btn.innerHTML = '<i class="fa-regular fa-bookmark"></i> <span>Save Match</span>';
                }
                showToast(data.message, 'success');
            } catch (err) {
                console.error('Save match error:', err);
            }
        });

        // Video detail actions use normal forms as a fallback, but stay in-page
        // when JavaScript is available.
        document.querySelectorAll('.ajax-video-toggle').forEach(form => {
            form.addEventListener('submit', async (event) => {
                event.preventDefault();
                const button = form.querySelector('button');
                const icon = button && button.querySelector('i');
                const type = form.dataset.toggleType;
                try {
                    const response = await fetch(form.action, {
                        method: 'POST',
                        body: new FormData(form),
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                            'Accept': 'application/json'
                        }
                    });
                    if (response.status === 403 || response.redirected) {
                        window.location.href = '/accounts/login/';
                        return;
                    }
                    const data = await response.json();
                    if (type === 'like') {
                        if (icon) icon.className = `${data.liked ? 'fa-solid' : 'fa-regular'} fa-heart me-1${data.liked ? ' text-danger' : ''}`;
                        const count = button && button.querySelector('span');
                        if (count) count.textContent = data.total_likes;
                        showToast(data.liked ? 'You liked this video' : 'Like removed', 'success');
                    } else {
                        if (icon) icon.className = `${data.bookmarked ? 'fa-solid' : 'fa-regular'} fa-bookmark`;
                        showToast(data.message, 'success');
                    }
                } catch (error) {
                    console.error('Video action failed:', error);
                }
            });
        });
    });

    // 5. AJAX Like News Article
    const likeBtn = document.getElementById('likeArticleBtn');
    if (likeBtn) {
        likeBtn.addEventListener('click', async () => {
            const slug = likeBtn.getAttribute('data-slug');
            try {
                const res = await fetch(`/news/${slug}/like/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken,
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json'
                    }
                });
                if (res.status === 403) {
                    window.location.href = '/accounts/login/';
                    return;
                }
                const data = await res.json();
                const icon = likeBtn.querySelector('i');
                const countSpan = document.getElementById('likesCountDisplay');

                if (data.liked) {
                    icon.className = 'fa-solid fa-heart text-danger';
                    showToast('You liked this story', 'success');
                } else {
                    icon.className = 'fa-regular fa-heart';
                }
                if (countSpan) countSpan.textContent = data.total_likes;
            } catch (err) {
                console.error(err);
            }
        });
    }

    // 6. AJAX Bookmark News Article
    const bookmarkNewsBtn = document.getElementById('bookmarkNewsBtn');
    if (bookmarkNewsBtn) {
        bookmarkNewsBtn.addEventListener('click', async () => {
            const slug = bookmarkNewsBtn.getAttribute('data-slug');
            try {
                const res = await fetch(`/news/${slug}/bookmark/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken,
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json'
                    }
                });
                if (res.status === 403) {
                    window.location.href = '/accounts/login/';
                    return;
                }
                const data = await res.json();
                const icon = bookmarkNewsBtn.querySelector('i');
                if (data.bookmarked) {
                    icon.className = 'fa-solid fa-bookmark text-warning';
                } else {
                    icon.className = 'fa-regular fa-bookmark';
                }
                showToast(data.message, 'success');
            } catch (err) {
                console.error(err);
            }
        });
    }

    // 7. Search Autocomplete & Recent Searches Engine
    const searchInput = document.getElementById('navSearchInput');
    const searchDropdown = document.getElementById('navSearchDropdown');
    const searchSuggestionsList = document.getElementById('searchSuggestionsList');
    const recentSearchesWrap = document.getElementById('recentSearchesWrap');
    const recentSearchesList = document.getElementById('recentSearchesList');
    const clearRecentBtn = document.getElementById('clearRecentSearchesBtn');
    const searchForm = document.getElementById('navSearchForm');

    const RECENT_KEY = 'crickscore_recent_searches';

    function getRecentSearches() {
        try {
            return JSON.parse(localStorage.getItem(RECENT_KEY)) || [];
        } catch {
            return [];
        }
    }

    function addRecentSearch(term) {
        if (!term) return;
        let list = getRecentSearches().filter(item => item.toLowerCase() !== term.toLowerCase());
        list.unshift(term);
        if (list.length > 5) list = list.slice(0, 5);
        localStorage.setItem(RECENT_KEY, JSON.stringify(list));
    }

    function renderRecentSearches() {
        if (!recentSearchesWrap || !recentSearchesList) return;
        const list = getRecentSearches();
        if (list.length === 0) {
            recentSearchesWrap.style.display = 'none';
            return;
        }
        recentSearchesList.innerHTML = list.map(item => `
            <a href="/search/?q=${encodeURIComponent(item)}" class="badge bg-secondary bg-opacity-25 text-light text-decoration-none px-2 py-1 small">
                <i class="fa-solid fa-clock-rotate-left me-1" style="font-size:0.65rem;"></i>${item}
            </a>
        `).join('');
        recentSearchesWrap.style.display = 'block';
    }

    if (clearRecentBtn) {
        clearRecentBtn.addEventListener('click', () => {
            localStorage.removeItem(RECENT_KEY);
            renderRecentSearches();
        });
    }

    if (searchForm) {
        searchForm.addEventListener('submit', () => {
            if (searchInput && searchInput.value.trim()) {
                addRecentSearch(searchInput.value.trim());
            }
        });
    }

    if (searchInput && searchDropdown) {
        let debounceTimer = null;

        searchInput.addEventListener('focus', () => {
            renderRecentSearches();
            searchDropdown.style.display = 'block';
        });

        document.addEventListener('click', (e) => {
            const container = document.getElementById('navSearchContainer');
            if (container && !container.contains(e.target)) {
                searchDropdown.style.display = 'none';
            }
        });

        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            const query = searchInput.value.trim();

            if (query.length < 2) {
                if (searchSuggestionsList) {
                    searchSuggestionsList.innerHTML = '';
                    searchSuggestionsList.style.display = 'none';
                }
                return;
            }

            debounceTimer = setTimeout(async () => {
                try {
                    const res = await fetch(`/search/suggest/?q=${encodeURIComponent(query)}`);
                    if (!res.ok) return;
                    const data = await res.json();

                    if (!searchSuggestionsList) return;

                    if (data.suggestions && data.suggestions.length > 0) {
                        searchSuggestionsList.innerHTML = data.suggestions.map(item => {
                            const badgeColor = item.type === 'Team' ? 'bg-primary' : (item.type === 'Player' ? 'bg-success' : 'bg-warning text-dark');
                            return `
                                <a href="${item.url}" class="search-suggestion-item">
                                    <i class="${item.icon} text-muted"></i>
                                    <div class="flex-grow-1 text-truncate">
                                        <div class="fw-semibold text-truncate">${item.title}</div>
                                        <div class="text-muted small text-truncate" style="font-size:0.75rem;">${item.subtitle}</div>
                                    </div>
                                    <span class="badge ${badgeColor} search-badge-tag">${item.type}</span>
                                </a>
                            `;
                        }).join('');
                        searchSuggestionsList.style.display = 'block';
                    } else {
                        searchSuggestionsList.innerHTML = `
                            <div class="p-2 text-center text-muted small">
                                No direct match for "${query}". Press Enter to search all.
                            </div>
                        `;
                        searchSuggestionsList.style.display = 'block';
                    }
                } catch (err) {
                    console.error('Search suggest error:', err);
                }
            }, 250);
        });
    }

    // 8. Reusable password field component and strength indicator
    function setupPasswordField(input) {
        if (!input.matches('input[type="password"][name*="password"]')) return;

        let field = input.closest('.password-field');
        if (!field || !field.contains(input)) {
            field = document.createElement('span');
            field.className = 'password-field';
            input.parentNode.insertBefore(field, input);
            field.appendChild(input);
        }

        if (!field.querySelector('.password-toggle')) {
            const toggle = document.createElement('button');
            toggle.type = 'button';
            toggle.className = 'password-toggle';
            toggle.setAttribute('aria-label', 'Show password');
            toggle.innerHTML = '<i class="fa-regular fa-eye" aria-hidden="true"></i>';
            field.appendChild(toggle);
        }

        if (input.name === 'password' || input.name === 'new_password1' || input.name === 'password1') {
            if (field.nextElementSibling?.classList.contains('password-strength-bar')) return;
            const barContainer = document.createElement('div');
            barContainer.className = 'password-strength-bar';
            const fill = document.createElement('div');
            fill.className = 'password-strength-fill';
            barContainer.appendChild(fill);
            field.parentNode.insertBefore(barContainer, field.nextSibling);

            input.addEventListener('input', () => {
                const val = input.value;
                let score = 0;
                if (val.length >= 8) score++;
                if (/[A-Z]/.test(val)) score++;
                if (/[0-9]/.test(val)) score++;
                if (/[^A-Za-z0-9]/.test(val)) score++;

                const width = (score / 4) * 100;
                fill.style.width = width + '%';

                if (score <= 1) {
                    fill.style.backgroundColor = '#D8A7B1';
                    fill.classList.remove('medium', 'strong');
                    fill.classList.add('weak');
                } else if (score === 2) {
                    fill.style.backgroundColor = '#F7E7CE';
                    fill.classList.remove('weak', 'strong');
                    fill.classList.add('medium');
                } else if (score === 3) {
                    fill.style.backgroundColor = '#0B1F3A';
                    fill.classList.remove('weak', 'medium');
                    fill.classList.add('strong');
                } else {
                    fill.style.backgroundColor = '#F8F6F0';
                    fill.classList.remove('weak', 'medium');
                    fill.classList.add('strong');
                }
            });
        }
    }

    function setupPasswordFields(root = document) {
        root.querySelectorAll('input[type="password"][name*="password"]').forEach(setupPasswordField);
    }

    setupPasswordFields();

    // Delegation keeps toggles working for dynamically rendered forms and modals.
    document.addEventListener('click', (event) => {
        const toggle = event.target.closest('.password-toggle');
        if (!toggle) return;

        const input = toggle.closest('.password-field')?.querySelector('input');
        if (!input) return;

        const visible = input.type === 'text';
        input.type = visible ? 'password' : 'text';
        toggle.setAttribute('aria-label', visible ? 'Show password' : 'Hide password');
        
        const icon = toggle.querySelector('i');
        if (icon) {
            icon.className = visible ? 'fa-regular fa-eye' : 'fa-regular fa-eye-slash';
        }
    });

    new MutationObserver(mutations => {
        mutations.forEach(mutation => {
            mutation.addedNodes.forEach(node => {
                if (node.nodeType === Node.ELEMENT_NODE) {
                    if (node.matches('input[type="password"][name*="password"]')) setupPasswordField(node);
                    setupPasswordFields(node);
                }
            });
        });
    }).observe(document.body, { childList: true, subtree: true });

    // 9. Premium Card Hover Effects Enhancement
    document.querySelectorAll('.content-card, .team-card, .player-card, .live-match-card').forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-4px)';
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0)';
        });
    });

    // 10. Smooth Scroll for Anchor Links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // 11. Premium Button Ripple Effect
    document.querySelectorAll('.btn-emerald, .btn-gold').forEach(button => {
        button.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const ripple = document.createElement('span');
            ripple.style.cssText = `
                position: absolute;
                background: rgba(248, 246, 240, 0.3);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple 0.6s linear;
                left: ${x}px;
                top: ${y}px;
                width: 100px;
                height: 100px;
                margin-left: -50px;
                margin-top: -50px;
            `;
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });

    // Add ripple animation keyframes dynamically
    const style = document.createElement('style');
    style.textContent = `
        @keyframes ripple {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);

    // 13. Media Carousel Horizontal Scrolling Enhancement
    const carousels = document.querySelectorAll('.media-carousel-track');
    
    carousels.forEach(track => {
        let isDown = false;
        let startX;
        let scrollLeft;
        let isDragging = false;

        // Mouse wheel scrolling
        track.addEventListener('wheel', (e) => {
            if (e.deltaY !== 0) {
                e.preventDefault();
                track.scrollLeft += e.deltaY;
            }
        });

        // Touch swipe support
        track.addEventListener('touchstart', (e) => {
            isDown = true;
            startX = e.touches[0].pageX - track.offsetLeft;
            scrollLeft = track.scrollLeft;
        });

        track.addEventListener('touchmove', (e) => {
            if (!isDown) return;
            e.preventDefault();
            const x = e.touches[0].pageX - track.offsetLeft;
            const walk = (x - startX) * 2;
            track.scrollLeft = scrollLeft - walk;
        });

        track.addEventListener('touchend', () => {
            isDown = false;
        });

        // Mouse drag support for desktop
        track.addEventListener('mousedown', (e) => {
            isDown = true;
            isDragging = false;
            startX = e.pageX - track.offsetLeft;
            scrollLeft = track.scrollLeft;
        });

        track.addEventListener('mouseleave', () => {
            isDown = false;
        });

        track.addEventListener('mouseup', () => {
            isDown = false;
        });

        track.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            e.preventDefault();
            const x = e.pageX - track.offsetLeft;
            const walk = (x - startX) * 2;
            track.scrollLeft = scrollLeft - walk;
            isDragging = true;
        });

        // Prevent link clicks when dragging
        track.addEventListener('click', (e) => {
            if (isDragging) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    });

    // 12. Premium Loading States for Forms
    const mainContent = document.querySelector('main');
    if (mainContent) {
        mainContent.classList.add('page-transition');
    }

    // Apply the same tactile ripple to every primary interactive control.
    document.querySelectorAll('.btn').forEach(button => {
        button.addEventListener('click', function (event) {
            if (this.disabled) return;
            const rect = this.getBoundingClientRect();
            const ripple = document.createElement('span');
            ripple.className = 'ui-ripple';
            ripple.style.left = `${event.clientX - rect.left}px`;
            ripple.style.top = `${event.clientY - rect.top}px`;
            this.appendChild(ripple);
            window.setTimeout(() => ripple.remove(), 620);
        });
    });

    document.querySelectorAll('form').forEach(form => {
        // Skip logout form - it should submit normally without interference
        if (form.classList.contains('logout-form')) {
            return;
        }
        
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> Processing...';

                if (!this.classList.contains('management-form')) {
                    setTimeout(() => {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalText;
                    }, 5000);
                }
            }
        });
    });

    // 13. Mobile Menu Behavior
    const navbarCollapse = document.getElementById('mainNavbarNav');
    const navbarToggler = document.querySelector('.navbar-toggler');
    
    if (navbarCollapse && navbarToggler) {
        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            const isClickInside = navbarCollapse.contains(e.target) || navbarToggler.contains(e.target);
            const isMenuOpen = navbarCollapse.classList.contains('show');
            
            if (!isClickInside && isMenuOpen) {
                const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
                if (bsCollapse) {
                    bsCollapse.hide();
                }
            }
        });
        
        // Close mobile menu when clicking a navigation link
        const navLinks = navbarCollapse.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
                if (bsCollapse) {
                    bsCollapse.hide();
                }
            });
        });
        
        // Prevent body scroll when mobile menu is open
        navbarCollapse.addEventListener('show.bs.collapse', () => {
            document.body.classList.add('navbar-open');
        });
        
        navbarCollapse.addEventListener('hidden.bs.collapse', () => {
            document.body.classList.remove('navbar-open');
        });
    }

    document.querySelectorAll('[data-server-toast]').forEach((el) => {
        const text = (el.getAttribute('data-server-toast') || '').trim();
        if (!text || typeof window.showToast !== 'function') return;
        const tags = el.getAttribute('data-toast-type') || 'success';
        window.showToast(text, tags.includes('error') ? 'error' : 'success');
    });
});

/* ============================================================
   Mobile navbar behavior: outside-click close, link-click close,
   body scroll lock while the panel is open.
   ============================================================ */
(() => {
  'use strict';
  document.addEventListener('DOMContentLoaded', () => {
    const collapseEl = document.getElementById('mainNavbarNav');
    if (!collapseEl) return;

    const isOpen = () => collapseEl.classList.contains('show');

    const syncBodyLock = () => {
      document.body.classList.toggle('navbar-open', isOpen());
    };

    collapseEl.addEventListener('shown.bs.collapse', syncBodyLock);
    collapseEl.addEventListener('hidden.bs.collapse', syncBodyLock);

    // Close the menu when a nav link / dropdown item inside it is clicked
    collapseEl.addEventListener('click', (e) => {
      const link = e.target.closest('a.nav-link-custom, .dropdown-item, a.btn');
      if (!link) return;
      // Allow the logout form / dropdown toggles to behave normally
      if (link.classList.contains('dropdown-toggle')) return;
      const instance = bootstrap.Collapse.getInstance(collapseEl);
      if (instance && isOpen()) instance.hide();
    });

    // Close when clicking/tapping outside the panel and outside the toggler
    document.addEventListener('click', (e) => {
      if (!isOpen()) return;
      if (collapseEl.contains(e.target)) return;
      if (e.target.closest('.navbar-toggler')) return;
      const instance = bootstrap.Collapse.getInstance(collapseEl);
      if (instance) instance.hide(); else bootstrap.Collapse.getOrCreateInstance(collapseEl).hide();
    }, true);
  });
})();
