const gate = document.querySelector('[data-age-gate]');
if (document.cookie.split(';').some((item) => item.trim() === 'age_verified=true')) {
  gate?.remove();
} else {
  document.body.classList.add('age-locked');
}

document.querySelector('[data-age-accept]')?.addEventListener('click', () => {
  document.cookie = 'age_verified=true; Max-Age=31536000; Path=/; Secure; SameSite=Lax';
  document.body.classList.remove('age-locked');
  gate?.remove();
});
