const gate = document.querySelector('[data-age-gate]');
const brand = document.querySelector('.brand');
if (brand && !brand.querySelector('.xpeach-robot')) {
  const robot = document.createElement('span'); robot.className='xpeach-robot state-idle'; robot.setAttribute('role','img'); robot.setAttribute('aria-label','XPeach robot');
  robot.innerHTML='<i class="robot-head"></i><i class="robot-body"></i><i class="robot-leg robot-leg-a"></i><i class="robot-leg robot-leg-b"></i><i class="robot-beam"></i><span class="robot-status" aria-live="polite"></span>'; brand.prepend(robot);
  const spriteProbe = new Image(); spriteProbe.onload = () => { if(spriteProbe.naturalWidth === 1344 && spriteProbe.naturalHeight === 96) robot.classList.add('has-sprite'); }; spriteProbe.src = '/assets/images/xpeach-robot-sprite.png';
  const seq=['walk','scan','found','collect','victory','idle'], msg={scan:'SEARCHING...',found:'VIDEO FOUND!',collect:'GET!',victory:'COLLECTION +1'}; let timer;
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const setState=(s)=>{if(!seq.includes(s)) return; if(motion.matches) s='idle'; seq.forEach(name=>robot.classList.remove(`state-${name}`)); robot.classList.add(`state-${s}`); robot.querySelector('.robot-status').textContent=msg[s]||''};
  const stop=()=>{clearTimeout(timer); setState('idle')};
  const schedule=()=>{clearTimeout(timer); if(motion.matches || document.hidden) return; timer=setTimeout(()=>{let i=0; const step=()=>{setState(seq[i++]); if(i<seq.length) timer=setTimeout(step,1000); else schedule()}; step()},10000+Math.random()*10000)};
  motion.addEventListener('change',()=>{stop(); schedule()});
  document.addEventListener('visibilitychange',()=>{stop(); schedule()});
  window.addEventListener('pagehide',stop);
  schedule(); window.XPeachRobot={setState:(s)=>{stop(); setState(s)},stop};
}
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
