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

document.addEventListener('click', (event) => {
  const trigger = event.target.closest('[data-inline-video]');
  if (!trigger) return;
  const video = document.createElement('video');
  video.controls = true;
  video.autoplay = true;
  video.playsInline = true;
  video.preload = 'metadata';
  video.src = trigger.dataset.videoSrc;
  if (trigger.dataset.poster) video.poster = trigger.dataset.poster;
  video.className = 'inline-card-video';
  trigger.replaceWith(video);
  video.play().catch(() => {});
});
