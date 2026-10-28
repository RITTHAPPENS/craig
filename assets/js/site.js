(() => {
  document.documentElement.classList.add('js');
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');

  // Menü
  const btn = document.querySelector('[data-menu]');
  const nav = document.getElementById('nav');
  if (btn && nav) {
    const set = (open) => {
      btn.setAttribute('aria-expanded', String(open));
      btn.querySelector('.sr').textContent = open ? 'Menü schließen' : 'Menü öffnen';
      nav.classList.toggle('is-open', open);
    };
    btn.addEventListener('click', () => set(btn.getAttribute('aria-expanded') !== 'true'));
    nav.addEventListener('click', (e) => { if (e.target.closest('a')) set(false); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') set(false); });
  }

  // Hero-Video: respektiert reduzierte Bewegung, pausierbar
  const video = document.querySelector('.hero-video');
  const toggle = document.querySelector('[data-video-toggle]');
  if (video && toggle) {
    const label = () => {
      const paused = video.paused;
      toggle.textContent = paused ? 'Video abspielen' : 'Video anhalten';
      toggle.setAttribute('aria-pressed', String(paused));
    };
    if (reduce.matches) { video.removeAttribute('autoplay'); video.pause(); }
    toggle.addEventListener('click', () => { video.paused ? video.play() : video.pause(); });
    video.addEventListener('play', label);
    video.addEventListener('pause', label);
    label();
  }

  // Vorher/Nachher
  document.querySelectorAll('[data-compare]').forEach((fig) => {
    const range = fig.querySelector('.compare-range');
    const apply = () => fig.style.setProperty('--pos', range.value + '%');
    range.addEventListener('input', apply);
    range.addEventListener('pointerdown', () => fig.classList.add('is-dragging'));
    ['pointerup', 'pointercancel', 'blur'].forEach((ev) => range.addEventListener(ev, () => fig.classList.remove('is-dragging')));
    apply();
  });

  // Maßkette im Ablauf zeichnet sich beim Erreichen
  const steps = document.querySelector('[data-steps]');
  if (steps) {
    if (!('IntersectionObserver' in window) || reduce.matches) { steps.classList.add('is-in'); }
    else {
      const io = new IntersectionObserver((entries) => {
        entries.forEach((en) => { if (en.isIntersecting) { steps.classList.add('is-in'); io.disconnect(); } });
      }, { threshold: 0.35 });
      io.observe(steps);
    }
  }
})();
