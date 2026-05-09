document.addEventListener('DOMContentLoaded', () => {
  const storageKey = 'payroll_dark_mode';
  const themeToggle = document.getElementById('themeToggle');
  const darkModeToggle = document.getElementById('darkModeToggle');

  function setTheme(enabled) {
    document.body.classList.toggle('dark', enabled);
    localStorage.setItem(storageKey, enabled ? 'enabled' : 'disabled');
    if (darkModeToggle) darkModeToggle.checked = enabled;
  }

  setTheme(localStorage.getItem(storageKey) === 'enabled');

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      setTheme(!document.body.classList.contains('dark'));
    });
  }

  if (darkModeToggle) {
    darkModeToggle.addEventListener('change', () => {
      setTheme(darkModeToggle.checked);
    });
  }
});
