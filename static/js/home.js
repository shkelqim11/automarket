(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // count-up numbers
  document.querySelectorAll('[data-count]').forEach(function (el) {
    var end = parseInt(el.dataset.count, 10) || 0;
    if (reduce || end < 2) return;
    var t0 = null;
    (function step(t) {
      if (t0 === null) t0 = t;
      var p = Math.min(1, (t - t0) / 1400);
      el.textContent = Math.round(end * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(step);
    })(performance.now());
  });
  if (reduce) return;

  // headline: word-by-word reveal
  var h1 = document.querySelector('.hero3 h1');
  if (h1) {
    var txt = h1.textContent.trim().replace(/\s+/g, ' ');
    h1.setAttribute('aria-label', txt);
    h1.classList.add('split');
    h1.textContent = '';
    txt.split(' ').forEach(function (w, i) {
      var s = document.createElement('span');
      s.className = 'w'; s.setAttribute('aria-hidden', 'true'); s.style.setProperty('--i', i); s.textContent = w;
      h1.appendChild(s); h1.appendChild(document.createTextNode(' '));
    });
  }

  // scroll reveal (only for elements below the fold, with stagger inside each group)
  if ('IntersectionObserver' in window) {
    var targets = document.querySelectorAll('.block-head, .block > .wrap > h2, .grid > *, .steps2 > div, .cta > *, .marquee, .statbar');
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target; io.unobserve(el);
        el.classList.add('in');
        el.addEventListener('transitionend', function done(ev) {
          if (ev.propertyName !== 'opacity') return;
          el.classList.remove('rv', 'in'); el.style.removeProperty('--d');
          el.removeEventListener('transitionend', done);
        });
      });
    }, { threshold: 0.12 });
    targets.forEach(function (el) {
      if (el.getBoundingClientRect().top < window.innerHeight * 0.92) return;
      var idx = Array.prototype.indexOf.call(el.parentNode.children, el);
      el.style.setProperty('--d', Math.min(idx, 5) * 80 + 'ms');
      el.classList.add('rv'); io.observe(el);
    });
  }

  // speedometer: tap / click / Enter to rev
  var gc = document.querySelector('.gauge-card');
  if (gc) {
    gc.setAttribute('tabindex', '0');
    var rev = function () { gc.classList.remove('revving'); void gc.offsetWidth; gc.classList.add('revving'); window.dispatchEvent(new Event('automarket:rev')); };
    gc.addEventListener('click', function (e) { if (!e.target.closest('a')) rev(); });
    gc.addEventListener('keydown', function (e) { if (e.key === 'Enter' && e.target === gc) rev(); });
  }

})();
