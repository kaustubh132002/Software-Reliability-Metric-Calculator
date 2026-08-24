/**
 * Main application script: Theme switching, mobile navigation, toast alerts, modal handlers.
 */

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initSidebarToggle();
  initFlashMessages();
});

/* ==========================================================================
   Theme Management (Light / Dark Mode)
   ========================================================================== */
function initTheme() {
  const savedTheme = localStorage.getItem('seqa_theme') || 'light';
  applyTheme(savedTheme);

  const themeToggleBtn = document.getElementById('themeToggleBtn');
  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      applyTheme(newTheme);
      localStorage.setItem('seqa_theme', newTheme);
      
      // Notify charts if initialized
      if (window.updateChartsTheme) {
        window.updateChartsTheme(newTheme);
      }
    });
  }
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const themeIcon = document.getElementById('themeIcon');
  const themeText = document.getElementById('themeText');
  
  if (themeIcon) {
    if (theme === 'dark') {
      themeIcon.className = 'fas fa-sun';
      if (themeText) themeText.textContent = 'Light Mode';
    } else {
      themeIcon.className = 'fas fa-moon';
      if (themeText) themeText.textContent = 'Dark Mode';
    }
  }
}

/* ==========================================================================
   Sidebar & Mobile Navigation
   ========================================================================== */
function initSidebarToggle() {
  const toggleBtn = document.getElementById('sidebarToggleBtn');
  const sidebar = document.querySelector('.sidebar');
  
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('mobile-open');
    });

    // Close sidebar on clicking outside in mobile mode
    document.addEventListener('click', (e) => {
      if (window.innerWidth <= 768 && 
          sidebar.classList.contains('mobile-open') && 
          !sidebar.contains(e.target) && 
          !toggleBtn.contains(e.target)) {
        sidebar.classList.remove('mobile-open');
      }
    });
  }
}

/* ==========================================================================
   Toast Notification System
   ========================================================================== */
function showToast(message, type = 'info', duration = 4000) {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const iconMap = {
    success: 'fa-check-circle',
    danger: 'fa-exclamation-circle',
    warning: 'fa-exclamation-triangle',
    info: 'fa-info-circle'
  };
  const icon = iconMap[type] || iconMap.info;

  toast.innerHTML = `
    <i class="fas ${icon} toast-icon"></i>
    <div class="toast-message">${message}</div>
    <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

function initFlashMessages() {
  const flashData = document.querySelectorAll('.flash-message-data');
  flashData.forEach(el => {
    const msg = el.getAttribute('data-message');
    const category = el.getAttribute('data-category') || 'info';
    showToast(msg, category);
    el.remove();
  });
}

/* ==========================================================================
   Modal Helpers
   ========================================================================== */
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
}

// Close modal when clicking backdrop
window.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-backdrop')) {
    e.target.classList.remove('active');
    document.body.style.overflow = '';
  }
});
