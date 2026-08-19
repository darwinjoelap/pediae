/* =====================================================
   Ginea — JS principal
   ===================================================== */

// Registrar Service Worker con scope del tenant
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    const path = window.location.pathname;
    const match = path.match(/^(\/t\/[^/]+)/);
    const scope = match ? match[1] + '/' : '/';

    navigator.serviceWorker.register('/sw.js', { scope: scope })
      .then(reg => console.log('SW registrado con scope:', reg.scope))
      .catch(err => console.warn('SW error:', err));
  });
}

// Auto-cerrar alertas después de 4 segundos
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.alert-dismissible.auto-close').forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert.close();
    }, 4000);
  });
});