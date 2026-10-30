(() => {
  document.documentElement.classList.add('js');
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');

  // Navigation: Mobilmenü und Mega-Menü "Leistungen"
  const btn = document.querySelector('[data-menu]');
  const nav = document.getElementById('nav');
  const trigger = document.querySelector('[data-mega-trigger]');
  const mega = document.querySelector('[data-mega]');
  const backdrop = document.querySelector('[data-backdrop]');
  const desktop = window.matchMedia('(min-width: 901px)');
  const fine = window.matchMedia('(hover: hover) and (pointer: fine)');

  const setMenu = (open) => {
    if (!btn) return;
    btn.setAttribute('aria-expanded', String(open));
    btn.querySelector('.sr').textContent = open ? 'Menü schließen' : 'Menü öffnen';
    nav.classList.toggle('is-open', open);
    document.documentElement.classList.toggle('menu-open', open);
    if (!open) setMega(false);
  };
  const setMega = (open) => {
    if (!trigger) return;
    trigger.setAttribute('aria-expanded', String(open));
    mega.classList.toggle('is-open', open);
    if (desktop.matches && backdrop) {
      if (open) { backdrop.hidden = false; requestAnimationFrame(() => backdrop.classList.add('is-on')); }
      else { backdrop.classList.remove('is-on'); setTimeout(() => { if (!mega.classList.contains('is-open')) backdrop.hidden = true; }, 220); }
    }
  };

  btn && btn.addEventListener('click', () => setMenu(btn.getAttribute('aria-expanded') !== 'true'));
  let hoverOpenedAt = 0;
  trigger && trigger.addEventListener('click', () => {
    if (Date.now() - hoverOpenedAt < 600) return;
    setMega(trigger.getAttribute('aria-expanded') !== 'true');
  });
  backdrop && backdrop.addEventListener('click', () => setMega(false));
  nav && nav.addEventListener('click', (e) => { if (e.target.closest('a')) { setMega(false); setMenu(false); } });
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (mega && mega.classList.contains('is-open')) { setMega(false); trigger.focus(); }
    else if (nav && nav.classList.contains('is-open')) { setMenu(false); btn.focus(); }
  });
  desktop.addEventListener('change', () => { setMega(false); setMenu(false); });

  // Desktop: Öffnen beim Überfahren mit kurzer Absichtsverzögerung
  if (trigger && mega) {
    const item = trigger.closest('.nav-item');
    let tOpen, tClose;
    item.addEventListener('pointerenter', (e) => {
      if (!desktop.matches || !fine.matches || e.pointerType !== 'mouse') return;
      clearTimeout(tClose); tOpen = setTimeout(() => { hoverOpenedAt = Date.now(); setMega(true); }, 90);
    });
    item.addEventListener('pointerleave', (e) => {
      if (!desktop.matches || e.pointerType !== 'mouse') return;
      clearTimeout(tOpen); tClose = setTimeout(() => setMega(false), 180);
    });
    // Fokus verlässt das Menü: schließen
    item.addEventListener('focusout', (e) => { if (desktop.matches && !item.contains(e.relatedTarget)) setMega(false); });

    // Vorschaubild wechselt mit der Leistung
    const imgs = mega.querySelectorAll('[data-preview-img]');
    const show = (key) => imgs.forEach((im) => im.classList.toggle('is-active', im.dataset.previewImg === key));
    mega.querySelectorAll('[data-preview]').forEach((a) => {
      a.addEventListener('pointerenter', () => show(a.dataset.preview));
      a.addEventListener('focus', () => show(a.dataset.preview));
    });
    mega.addEventListener('pointerleave', () => show('team'));
  }

  // Hero-Hintergrundvideo: passende Datei je Format, erst nach dem Poster laden, pausierbar
  const video = document.querySelector('.hero-video');
  const toggle = document.querySelector('[data-video-toggle]');
  if (video && toggle && !reduce.matches) {
    const tall = window.matchMedia('(max-aspect-ratio: 4/5)');
    const pick = () => tall.matches ? video.dataset.srcTall
      : (window.innerWidth * (window.devicePixelRatio || 1) > 2000 ? video.dataset.srcXl : video.dataset.srcWide);
    const saveData = navigator.connection && navigator.connection.saveData;
    const load = () => {
      const src = pick();
      if (video.getAttribute('src') === src) return;
      video.classList.remove('is-playing');
      video.src = src;
      video.play().catch(() => {});
    };
    const label = () => {
      toggle.textContent = video.paused ? 'Video abspielen' : 'Video anhalten';
      toggle.setAttribute('aria-pressed', String(video.paused));
    };
    video.addEventListener('playing', () => { video.classList.add('is-playing'); label(); });
    video.addEventListener('pause', label);
    toggle.addEventListener('click', () => { video.paused ? video.play() : video.pause(); });
    if (!saveData) {
      toggle.hidden = false;
      const start = () => ('requestIdleCallback' in window) ? requestIdleCallback(load, { timeout: 1200 }) : setTimeout(load, 300);
      document.readyState === 'complete' ? start() : window.addEventListener('load', start, { once: true });
      tall.addEventListener('change', load);
    }
    // außerhalb des Sichtfelds pausieren, spart Akku
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(([en]) => {
        if (!video.src) return;
        if (en.isIntersecting && toggle.dataset.user !== 'paused') video.play().catch(() => {}); else video.pause();
      }, { threshold: 0.1 }).observe(video);
      toggle.addEventListener('click', () => { toggle.dataset.user = video.paused ? 'paused' : ''; });
    }
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
