/**
 * Kids Monitoring System - Sleek UI Logic
 * Standardized for cleaner micro-interactions and performance.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Elegant Loader Handing
    const loader = document.getElementById('app-loader');
    if (loader) {
        window.onload = () => {
            loader.style.opacity = '0';
            setTimeout(() => {
                loader.style.display = 'none';
            }, 600);
        };
    }

    // Simulation of periodic alerts (simulated AI detection events)
    setTimeout(() => {
        createToast('Alert: Unknown person detected at South Fence.', 'error');
    }, 15000);
});

/**
 * Creates a sleek toast notification
 * @param {string} msg 
 * @param {string} mode - success, error, warning
 */
function createToast(msg, mode = 'success') {
    const box = document.getElementById('notifications');
    if (!box) return;

    const toast = document.createElement('div');
    toast.className = `toast ${mode}`;
    
    let icon = 'fa-circle-check';
    if (mode === 'error') icon = 'fa-circle-exclamation';
    if (mode === 'warning') icon = 'fa-triangle-exclamation';

    toast.innerHTML = `
        <i class="fa-solid ${icon}" style="color: ${mode === 'success' ? 'var(--accent-success)' : 'var(--accent-error)'};"></i>
        <span>${msg}</span>
    `;

    box.appendChild(toast);

    // Fade out and resolve
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 400);
    }, 5000);
}

// Global exposure
window.createToast = createToast;
