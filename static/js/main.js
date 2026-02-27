// Magzine - Main JavaScript

document.addEventListener('DOMContentLoaded', function () {
  // Auto-dismiss alerts
  const alerts = document.querySelectorAll('.alert.auto-dismiss');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });

  // Navbar active state
  const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
  navLinks.forEach(function (link) {
    if (link.href === window.location.href) {
      link.classList.add('active');
    }
  });

  // Search input debounce
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    let timeout;
    searchInput.addEventListener('input', function () {
      clearTimeout(timeout);
      timeout = setTimeout(function () {
        // Search is handled by form submission
      }, 300);
    });
  }

  // Confirm delete
  const deleteForms = document.querySelectorAll('.confirm-delete');
  deleteForms.forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (!confirm('Are you sure you want to delete this? This action cannot be undone.')) {
        e.preventDefault();
      }
    });
  });
});

// Get CSRF token from cookie
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

const CSRF_TOKEN = getCookie('csrftoken');
