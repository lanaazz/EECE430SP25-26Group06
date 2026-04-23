// volleyball.js — Volleyball Platform JS

// Auto-dismiss alerts after 4 seconds
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => alert.remove(), 4000);
    });
});
