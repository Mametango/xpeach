const gate = document.querySelector('[data-age-gate]');
const ageVerified = document.cookie.split(';').some((item) => item.trim() === 'age_verified=true');
const rememberAdult = () => {
  document.cookie = 'age_verified=true; Max-Age=31536000; Path=/; Domain=xpeach.tv; Secure; SameSite=Lax';
};

const visitorCookieName = 'visitor_id';
let pageViewRecorded = false;
const readCookie = (name) => document.cookie.split(';').map((item) => item.trim()).find((item) => item.startsWith(`${name}=`))?.slice(name.length + 1);
const ensureVisitorId = () => {
  const current = readCookie(visitorCookieName);
  if (current) return current;
  const created = globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}`;
  document.cookie = `${visitorCookieName}=${encodeURIComponent(created)}; Max-Age=31536000; Path=/; Domain=xpeach.tv; Secure; SameSite=Lax`;
  return created;
};
const recordPageView = () => {
  if (pageViewRecorded || !location.hostname.endsWith('xpeach.tv')) return;
  pageViewRecorded = true;
  ensureVisitorId();
  fetch('https://admin.xpeach.tv/events/page-view', {
    method: 'POST',
    credentials: 'include',
    headers: {'Content-Type': 'text/plain;charset=UTF-8'},
    body: JSON.stringify({path: location.pathname}),
    keepalive: true,
  }).catch(() => {});
};

if (ageVerified) {
  // Upgrade older host-only cookies so the public media relay subdomain can
  // verify the same minimal age flag without storing personal information.
  rememberAdult();
  gate?.remove();
  recordPageView();
} else {
  document.body.classList.add('age-locked');
}

document.querySelector('[data-age-accept]')?.addEventListener('click', () => {
  rememberAdult();
  document.body.classList.remove('age-locked');
  gate?.remove();
  recordPageView();
});

const buildInlinePlaceholder = (container) => {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'inline-play-button';
  button.setAttribute('aria-label', container.dataset.videoLabel || '動画を再生');

  if (container.dataset.videoPoster) {
    const image = document.createElement('img');
    image.src = container.dataset.videoPoster;
    image.alt = '';
    image.loading = 'lazy';
    image.decoding = 'async';
    button.append(image);
  } else {
    const placeholder = document.createElement('span');
    placeholder.className = 'guide-placeholder';
    placeholder.textContent = 'X動画クリップ';
    button.append(placeholder);
  }

  const icon = document.createElement('span');
  icon.className = 'play-mark';
  icon.setAttribute('aria-hidden', 'true');
  icon.textContent = '▶';
  button.append(icon);
  return button;
};

const activateInlinePlayer = (container) => {
  document.querySelectorAll('[data-inline-player].is-active').forEach((other) => {
    if (other === container) return;
    other.querySelector('video')?.pause();
    other.classList.remove('is-active');
    other.replaceChildren(buildInlinePlaceholder(other));
  });

  const video = document.createElement('video');
  video.className = 'inline-card-video';
  video.controls = true;
  video.playsInline = true;
  video.setAttribute('playsinline', '');
  video.setAttribute('webkit-playsinline', '');
  video.preload = 'metadata';
  video.src = container.dataset.videoSrc;
  video.setAttribute('aria-label', container.dataset.videoLabel || '動画を再生');
  if (container.dataset.videoPoster) video.poster = container.dataset.videoPoster;

  container.classList.add('is-active');
  container.replaceChildren(video);
  video.load();
  video.play().catch((error) => {
    container.dataset.playbackError = error.name;
    // Native controls stay available if iOS needs a second explicit gesture.
  });
};

document.addEventListener('click', (event) => {
  const button = event.target.closest('[data-inline-player] .inline-play-button');
  if (!button) return;
  activateInlinePlayer(button.closest('[data-inline-player]'));
});
