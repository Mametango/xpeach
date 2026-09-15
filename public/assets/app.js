const gate = document.querySelector('[data-age-gate]');
const ageVerified = document.cookie.split(';').some((item) => item.trim() === 'age_verified=true');
const rememberAdult = () => {
  document.cookie = 'age_verified=true; Max-Age=31536000; Path=/; Domain=xpeach.tv; Secure; SameSite=Lax';
};

if (ageVerified) {
  // Upgrade older host-only cookies so the public media relay subdomain can
  // verify the same minimal age flag without storing personal information.
  rememberAdult();
  gate?.remove();
} else {
  document.body.classList.add('age-locked');
}

document.querySelector('[data-age-accept]')?.addEventListener('click', () => {
  rememberAdult();
  document.body.classList.remove('age-locked');
  gate?.remove();
});
