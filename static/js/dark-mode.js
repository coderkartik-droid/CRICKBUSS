/**
 * CrickScore Live - Dark / Light Mode Toggle with LocalStorage persistence
 */

(() => {
    'use strict';

    const getStoredTheme = () => localStorage.getItem('theme');
    const setStoredTheme = theme => localStorage.setItem('theme', theme);

    const getPreferredTheme = () => {
        const storedTheme = getStoredTheme();
        if (storedTheme) {
            return storedTheme;
        }
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    };

    const setTheme = theme => {
        document.documentElement.setAttribute('data-bs-theme', theme);
        updateThemeIcon(theme);
    };

    const updateThemeIcon = theme => {
        ['themeToggleBtn', 'themeToggleBtnMobile'].forEach(id => {
            const btn = document.getElementById(id);
            if (!btn) return;
            const icon = btn.querySelector('i');
            if (!icon) return;

            if (theme === 'dark') {
                icon.className = 'fa-solid fa-sun text-warning';
                btn.setAttribute('title', 'Switch to Light Mode');
            } else {
                icon.className = 'fa-solid fa-moon text-light';
                btn.setAttribute('title', 'Switch to Dark Mode');
            }
        });
    };

    // Apply theme immediately to prevent flashing
    setTheme(getPreferredTheme());

    window.addEventListener('DOMContentLoaded', () => {
        updateThemeIcon(getPreferredTheme());

        ['themeToggleBtn', 'themeToggleBtnMobile'].forEach(id => {
            const btn = document.getElementById(id);
            if (btn) {
                btn.addEventListener('click', () => {
                    const currentTheme = document.documentElement.getAttribute('data-bs-theme');
                    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                    setStoredTheme(newTheme);
                    setTheme(newTheme);
                });
            }
        });
    });
})();
