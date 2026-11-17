/* Restores prototype attributes/elements on Elementor atomic markup (keyed by element id) */
(function(){
  var M=window.CRAIG_ATTRS||{};
  document.querySelectorAll('[data-id]').forEach(function(el){
    var m=M[el.getAttribute('data-id')]; if(!m||el.__craig) return; el.__craig=1;
    if(m.r){var t=document.createElement('template');t.innerHTML=m.r.trim();var n=t.content.firstElementChild;if(n){el.replaceWith(n);}return;}
    var a=m.a||{};
    for(var k in a){ if(k==='style'){el.style.cssText+=';'+a[k];} else el.setAttribute(k,a[k]); }
    if('hidden' in a) el.classList.remove('x-hidden');
  });
  ['sub-page','gl-page','bn-page','rf-page'].forEach(function(c){ if(document.querySelector('main.'+c)) document.documentElement.classList.add(c); });
  // aria-current for navigation
  var p=location.pathname.replace(/\/+$/,'/')||'/';
  document.querySelectorAll('.nav-link[href], .foot-col a[href]').forEach(function(a){
    var h=a.getAttribute('href'); if(h&&h.charAt(0)==='/'&&h.indexOf('#')<0&&h===p) a.setAttribute('aria-current','page');
  });
  // details/summary behaviour for converted FAQ items
  document.querySelectorAll('.tg-details').forEach(function(d){
    var s=d.querySelector(':scope > .tg-summary'); if(!s) return;
    s.setAttribute('role','button'); s.setAttribute('tabindex','0'); s.setAttribute('aria-expanded', d.hasAttribute('open')?'true':'false');
    var tog=function(){ var o=!d.hasAttribute('open'); if(o) d.setAttribute('open',''); else d.removeAttribute('open'); s.setAttribute('aria-expanded',String(o)); d.dispatchEvent(new Event('toggle')); };
    s.addEventListener('click',tog);
    s.addEventListener('keydown',function(e){ if(e.key==='Enter'||e.key===' '){e.preventDefault();tog();} });
  });
  // CCM19: footer link opens the consent settings (floating icon is hidden via CSS)
  document.querySelectorAll('.ccm-open').forEach(function(a){ a.addEventListener('click',function(e){ e.preventDefault(); if(window.CCM&&typeof CCM.openWidget==='function') CCM.openWidget(); }); });
  // Google-Bewertungen (Trustindex): Widget wird aus einer versteckten WP-Seite geladen, da Elementor V4 keine Shortcodes rendert
  var ti=document.querySelector('.x-ti');
  if(ti){ fetch('/wp-json/wp/v2/pages/956?_fields=content').then(function(r){return r.json()}).then(function(d){
    ti.innerHTML=d.content.rendered;
    ti.querySelectorAll('script').forEach(function(o){ var n=document.createElement('script'); for(var i=0;i<o.attributes.length;i++) n.setAttribute(o.attributes[i].name,o.attributes[i].value); n.text=o.textContent; o.replaceWith(n); });
  }).catch(function(){}); }
  // buttons outside forms never submit
  document.querySelectorAll('button.x-btn:not([type])').forEach(function(b){ b.type='button'; });
})();
