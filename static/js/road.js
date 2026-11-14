/* Night-highway hero animation (canvas, no libraries). Paused when off-screen, static when reduced motion. */
(function () {
  var hero = document.getElementById('hero'), cv = document.getElementById('road');
  if (!hero || !cv || !cv.getContext) return;
  var ctx = cv.getContext('2d');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var ZMIN = 0.14, ZMAX = 9, SPAN = ZMAX - ZMIN, ROAD = 2.2, LANES = [-1.65, -0.55, 0.55, 1.65];
  var W = 0, H = 0, cx = 0, hy = 0, F = 0, small = false;
  var cars = [], speed = 1, target = 1, boost = 0, zoff = 0;
  var running = false, visible = true, last = 0;

  function rnd(a, b) { return a + Math.random() * (b - a); }
  function newCar(anywhere) {
    var x = LANES[(Math.random() * 4) | 0];
    return { x: x, z: anywhere ? rnd(ZMIN, ZMAX) : rnd(ZMAX * 0.8, ZMAX), f: x < 0 ? 1.9 : 0.6,
             c: x < 0 ? '255,244,214' : '255,64,44', o: rnd(0.16, 0.26) };
  }
  function resize() {
    var dpr = Math.min(2, window.devicePixelRatio || 1), r = hero.getBoundingClientRect();
    W = r.width; H = r.height; small = W < 700;
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    cx = W * (small ? 0.5 : 0.6); hy = H * (small ? 0.6 : 0.52); F = Math.min(W, H * 1.6) * 0.55;
    var n = small ? 22 : 44; cars = []; for (var i = 0; i < n; i++) cars.push(newCar(true));
    draw();
  }
  function px(x, z) { return cx + x / z * F; }
  function py(y, z) { return hy + y / z * F; }
  function seg(x, y0, z0, y1, z1) { ctx.beginPath(); ctx.moveTo(px(x, z0), py(y0, z0)); ctx.lineTo(px(x, z1), py(y1, z1)); ctx.stroke(); }

  function ground(x, rgb, wWorld, len, gap, maxA) {
    ctx.lineCap = 'butt';
    for (var k = 0; k * gap < SPAN; k++) {
      var z0 = ZMIN + (((k * gap + zoff) % SPAN) + SPAN) % SPAN, z1 = z0 + len;
      if (z1 > ZMAX) continue;
      ctx.strokeStyle = 'rgba(' + rgb + ',' + (maxA * Math.min(1, (ZMAX - z0) / (ZMAX * 0.55)) * Math.min(1, (z0 - ZMIN) / 0.5)) + ')';
      ctx.lineWidth = Math.min(20, Math.max(0.6, wWorld / z0 * F));
      seg(x, 1, z0, 1, z1);
    }
  }

  function draw() {
    var g = ctx.createLinearGradient(0, 0, 0, hy);
    g.addColorStop(0, '#050505'); g.addColorStop(1, '#1d0f05');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, hy);
    ctx.fillStyle = '#0b0b0b'; ctx.fillRect(0, hy, W, H - hy);
    var rg = ctx.createRadialGradient(cx, hy, 0, cx, hy, W * 0.55);
    rg.addColorStop(0, 'rgba(255,106,0,.40)'); rg.addColorStop(1, 'rgba(255,106,0,0)');
    ctx.fillStyle = rg; ctx.fillRect(0, 0, W, H);

    var bx = ROAD * (H - hy), zb = F / (H - hy) * 0.9;
    var rd = ctx.createLinearGradient(0, hy, 0, H);
    rd.addColorStop(0, 'rgba(34,34,34,0)'); rd.addColorStop(1, 'rgba(28,28,28,1)');
    ctx.fillStyle = rd; ctx.beginPath(); ctx.moveTo(cx, hy); ctx.lineTo(cx - bx, H); ctx.lineTo(cx + bx, H); ctx.closePath(); ctx.fill();

    ctx.lineWidth = 2; ctx.strokeStyle = 'rgba(255,255,255,.22)';
    seg(-ROAD, 1, ZMAX, 1, zb); seg(ROAD, 1, ZMAX, 1, zb);
    ground(-1.1, '255,255,255', 0.035, 0.5, 1.2, 0.35);
    ground(1.1, '255,255,255', 0.035, 0.5, 1.2, 0.35);
    ground(0, '255,106,0', 0.05, 0.6, 1.2, 0.95);

    // street lamps on both sides
    for (var s = -1; s <= 1; s += 2) {
      for (var k = 0; k * 1.6 < SPAN; k++) {
        var z = ZMIN + (((k * 1.6 + zoff) % SPAN) + SPAN) % SPAN, a = Math.min(1, (ZMAX - z) / (ZMAX * 0.5)) * Math.min(1, (z - ZMIN) / 0.5), x = s * (ROAD + 0.5);
        ctx.strokeStyle = 'rgba(70,70,70,' + a + ')'; ctx.lineWidth = Math.min(14, Math.max(0.6, 0.05 / z * F));
        seg(x, 1, z, -1.6, z);
        ctx.fillStyle = 'rgba(255,170,80,' + a + ')';
        ctx.beginPath(); ctx.arc(px(x, z), py(-1.6, z), Math.min(26, Math.max(1, 0.1 / z * F)), 0, 6.283); ctx.fill();
      }
    }

    // car lights (streaks)
    ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
    var tail = 0.05 + 0.07 * speed;
    for (var i = 0; i < cars.length; i++) {
      var c = cars[i], a2 = Math.min(1, (ZMAX - c.z) / (ZMAX * 0.5)) * Math.min(1, (c.z - ZMIN) / 0.6), z2 = c.z + tail * c.f;
      for (var d = -1; d <= 1; d += 2) {
        var lx = c.x + d * c.o;
        if (c.z < 4) { ctx.strokeStyle = 'rgba(' + c.c + ',' + (a2 * 0.22) + ')'; ctx.lineWidth = Math.min(22, Math.max(2, 0.28 / c.z * F * 0.5)); seg(lx, 0.8, z2, 0.8, c.z); }
        ctx.strokeStyle = 'rgba(' + c.c + ',' + a2 + ')'; ctx.lineWidth = Math.min(9, Math.max(0.8, 0.09 / c.z * F * 0.5));
        seg(lx, 0.8, z2, 0.8, c.z);
      }
    }
    ctx.globalCompositeOperation = 'source-over';
  }

  function step(dt) {
    if (boost > 0) { boost -= dt; target = 5; } else target = 1;
    speed += (target - speed) * Math.min(1, dt * 5);
    var dz = 2.4 * speed * dt;
    zoff -= dz;
    for (var i = 0; i < cars.length; i++) { var c = cars[i]; c.z -= dz * c.f; if (c.z < ZMIN) cars[i] = newCar(false); }
  }
  function frame(t) {
    var dt = Math.min(0.05, (t - last) / 1000); last = t;
    step(dt); draw();
    if (running && visible && !document.hidden) requestAnimationFrame(frame); else running = false;
  }
  function start() { if (!running && !reduce) { running = true; last = performance.now(); requestAnimationFrame(frame); } }

  var rt, onResize = function () { clearTimeout(rt); rt = setTimeout(resize, 120); };
  if ('ResizeObserver' in window) new ResizeObserver(onResize).observe(hero); else window.addEventListener('resize', onResize);
  if ('IntersectionObserver' in window) new IntersectionObserver(function (e) { visible = e[0].isIntersecting; if (visible) start(); }).observe(hero);
  document.addEventListener('visibilitychange', function () { if (!document.hidden) start(); });
  window.addEventListener('automarket:rev', function () { boost = 1.4; });
  hero.addEventListener('pointerdown', function (e) { if (!e.target.closest('a,button,input')) boost = 1.4; });
  resize(); start();
})();
