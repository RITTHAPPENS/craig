(() => {
  // Header wird fest, sobald der Hero aus dem Bild ist
  const head = document.querySelector('[data-head]');
  const hero = document.querySelector('.hero');
  if (head && hero && 'IntersectionObserver' in window) {
    new IntersectionObserver(([en]) => head.classList.toggle('is-solid', !en.isIntersecting), { rootMargin: '-80px 0px 0px 0px' }).observe(hero);
  } else if (head) { head.classList.add('is-solid'); }

  // Abschnitte blenden beim Erreichen ein
  const items = document.querySelectorAll('.section .h2, .panels, .tvids, .vals, .owners-copy');
  items.forEach((el) => el.setAttribute('data-reveal', ''));
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); } }), { threshold: 0.15 });
    items.forEach((el) => io.observe(el));
  } else items.forEach((el) => el.classList.add('is-in'));

  // Formular (Prototyp): Pflichtfelder prüfen, Rückmeldung anzeigen
  const form = document.querySelector('[data-form]');
  if (form) {
    const status = form.querySelector('.form-status');
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      let first = null;
      form.querySelectorAll('[required]').forEach((f) => {
        const bad = f.type === 'checkbox' ? !f.checked : !f.value.trim() || (f.type === 'email' && !/^\S+@\S+\.\S+$/.test(f.value));
        f.setAttribute('aria-invalid', String(bad));
        if (bad && !first) first = f;
      });
      if (first) {
        status.textContent = 'Bitte füllen Sie die markierten Felder aus.';
        status.classList.add('is-error');
        first.focus();
        return;
      }
      status.classList.remove('is-error');
      status.textContent = 'Danke! Ihre Anfrage ist bei uns eingegangen. Wir melden uns persönlich.';
      form.reset();
    });
  }
})();
