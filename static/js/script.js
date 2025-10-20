// static/js/script.js
document.addEventListener('DOMContentLoaded', () => {
  // Auto-hide flash messages after 4s
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach(f => setTimeout(()=> f.style.display='none', 4200));

  // Confirm delete forms (buttons use data-confirm attribute or class 'confirm-delete')
  document.querySelectorAll('.confirm-delete').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const ok = confirm('Are you sure? This action cannot be undone.');
      if(!ok) e.preventDefault();
    });
  });
});
