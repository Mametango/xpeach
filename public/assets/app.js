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
