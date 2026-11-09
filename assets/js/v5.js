(() => {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');

  // Leistungs-Slider: blättert ansichtsweise (Desktop drei Karten, mobil eine), keine Automatik
  const rail = document.querySelector('[data-rail]');
  const prev = document.querySelector('[data-rail-prev]');
  const next = document.querySelector('[data-rail-next]');
  const dotsBox = document.querySelector('[data-dots]');
  if (rail) {
    const cards = [...rail.children];
    const metrics = () => {
      const gap = parseFloat(getComputedStyle(rail).columnGap) || 0;
      const w = cards[0].getBoundingClientRect().width + gap;
      const per = Math.max(1, Math.round((rail.clientWidth + gap) / w));
      return { w, per, pages: Math.ceil(cards.length / per) };
    };
    let m = metrics();
    // Überschrift wechselt mit der Gruppe der ersten sichtbaren Karte
    const title = document.querySelector('[data-rail-title]');
    let shown = title ? title.textContent : '';
    let swapT = 0;
    const setTitle = (at) => {
      if (!title) return;
      const first = Math.min(cards.length - 1, at * m.per);
      const next = cards[first].dataset.group;
      if (!next || next === shown) return;
      shown = next;
      if (reduce.matches) { title.textContent = next; return; }
      clearTimeout(swapT);
      title.classList.add('is-swapping');
      swapT = setTimeout(() => { title.textContent = next; title.classList.remove('is-swapping'); }, 200);
    };
    const page = () => Math.min(m.pages - 1, Math.round(rail.scrollLeft / (m.w * m.per)));
    const buildDots = () => {
      if (!dotsBox) return;
      dotsBox.innerHTML = '';
      for (let i = 0; i < m.pages; i++) dotsBox.appendChild(document.createElement('span'));
    };
    const sync = () => {
      const max = rail.scrollWidth - rail.clientWidth - 2;
      if (prev) prev.disabled = rail.scrollLeft <= 2;
      if (next) next.disabled = rail.scrollLeft >= max;
      const at = rail.scrollLeft >= max ? m.pages - 1 : page();
      if (dotsBox) [...dotsBox.children].forEach((d, i) => d.classList.toggle('is-on', i === at));
      setTitle(at);
    };
    const go = (dir) => {
      const target = Math.max(0, Math.min(m.pages - 1, page() + dir));
      rail.scrollTo({ left: target * m.w * m.per, behavior: reduce.matches ? 'auto' : 'smooth' });
    };
    prev && prev.addEventListener('click', () => go(-1));
    next && next.addEventListener('click', () => go(1));
    rail.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight') { e.preventDefault(); go(1); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); go(-1); }
    });
    let raf = 0;
    rail.addEventListener('scroll', () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(sync); }, { passive: true });
    window.addEventListener('resize', () => { m = metrics(); buildDots(); sync(); });
    buildDots(); sync();
  }

  // Vorher/Nachher-Bühne: wischen oder Pfeile für das nächste Projekt, Regler am Griff ziehen
  const baTrack = document.querySelector('[data-ba-track]');
  if (baTrack) {
    const slides = [...baTrack.children];
    const prevB = document.querySelector('[data-ba-prev]');
    const nextB = document.querySelector('[data-ba-next]');
    const dotBox = document.querySelector('[data-ba-dots]');
    slides.forEach((_, i) => { const d = document.createElement('span'); d.addEventListener('click', () => goTo(i)); dotBox && dotBox.appendChild(d); });
    const cur = () => Math.round(baTrack.scrollLeft / baTrack.clientWidth);
    const goTo = (i) => baTrack.scrollTo({ left: Math.max(0, Math.min(slides.length - 1, i)) * baTrack.clientWidth, behavior: reduce.matches ? 'auto' : 'smooth' });
    const syncBa = () => {
      const i = cur();
      if (prevB) prevB.disabled = i <= 0;
      if (nextB) nextB.disabled = i >= slides.length - 1;
      dotBox && [...dotBox.children].forEach((d, k) => d.classList.toggle('is-on', k === i));
    };
    prevB && prevB.addEventListener('click', () => goTo(cur() - 1));
    nextB && nextB.addEventListener('click', () => goTo(cur() + 1));
    baTrack.addEventListener('keydown', (e) => {
      if (e.target.classList.contains('compare-range')) return;
      if (e.key === 'ArrowRight') { e.preventDefault(); goTo(cur() + 1); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); goTo(cur() - 1); }
    });
    let rafB = 0;
    baTrack.addEventListener('scroll', () => { cancelAnimationFrame(rafB); rafB = requestAnimationFrame(syncBa); }, { passive: true });
    window.addEventListener('resize', syncBa);
    syncBa();

    // Ziehen: mit der Maus überall im Bild, per Touch nur am Griff (sonst wird gewischt)
    slides.forEach((slide) => {
      const fig = slide.querySelector('[data-compare]');
      const range = fig.querySelector('.compare-range');
      const set = (x) => {
        const r = fig.getBoundingClientRect();
        range.value = Math.max(0, Math.min(100, ((x - r.left) / r.width) * 100));
        range.dispatchEvent(new Event('input', { bubbles: true }));
      };
      let drag = false;
      const start = (e) => { drag = true; fig.classList.add('is-dragging'); fig.setPointerCapture(e.pointerId); set(e.clientX); e.preventDefault(); };
      fig.addEventListener('pointerdown', (e) => {
        if (e.pointerType === 'mouse' || e.target.closest('[data-handle]')) start(e);
      });
      fig.addEventListener('pointermove', (e) => { if (drag) set(e.clientX); });
      const end = () => { drag = false; fig.classList.remove('is-dragging'); };
      fig.addEventListener('pointerup', end);
      fig.addEventListener('pointercancel', end);
    });
  }

  // Markierte Headlines: Balken wischt hinter den Text, sobald sie im Bild sind
  const marks = document.querySelectorAll('.mark');
  if (!('IntersectionObserver' in window) || reduce.matches) { marks.forEach((m) => m.classList.add('is-marked')); }
  else {
    const io = new IntersectionObserver((entries) => entries.forEach((en) => {
      if (en.isIntersecting) { en.target.classList.add('is-marked'); io.unobserve(en.target); }
    }), { threshold: 0.6 });
    marks.forEach((m) => io.observe(m));
  }
})();
