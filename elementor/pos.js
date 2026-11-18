;(function(){var p=location.pathname.replace(/\/+$/,'').split('/').pop(),m=(__POS__)[p]||{};
document.querySelectorAll('img').forEach(function(i){var f=(i.getAttribute('src')||'').split('?')[0].split('/').pop(),s=m[f]||m[f.replace(/-\d+(\.\w+)$/,'$1')];if(s)i.style.cssText+=';'+s;});})();
