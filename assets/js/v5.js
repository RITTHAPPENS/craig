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
