(function(){
  var hd=document.querySelector('.site-header');
  if(hd){var sc=function(){hd.classList.toggle('scrolled',window.scrollY>8)};sc();window.addEventListener('scroll',sc,{passive:true})}
  var b=document.querySelector('.burger'),n=document.querySelector('.nav');
  if(b&&n){b.addEventListener('click',function(){var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o)})}
  // gallery
  document.querySelectorAll('.thumbs img').forEach(function(t){t.addEventListener('click',function(){
    var m=document.querySelector('.gallery .main img');m.src=t.dataset.full;
    document.querySelectorAll('.thumbs img').forEach(function(x){x.classList.remove('active')});t.classList.add('active')})});
  // upload preview + client-side validation
  var inp=document.getElementById('id_images'),box=document.getElementById('previews');
  if(inp&&box){inp.addEventListener('change',function(){
    box.innerHTML='';var max=(+inp.dataset.maxMb||5)*1048576,ok=['image/jpeg','image/png','image/webp'],err=document.getElementById('img-error');
    if(err)err.textContent='';
    Array.from(inp.files).forEach(function(f){
      if(ok.indexOf(f.type)<0||f.size>max){if(err)err.textContent=inp.dataset.msg;inp.value='';box.innerHTML='';return}
      var i=document.createElement('img');i.src=URL.createObjectURL(f);box.appendChild(i)})})}
  // listing preview
  var pb=document.getElementById('preview-btn');
  if(pb){pb.addEventListener('click',function(){
    var g=function(id){var e=document.getElementById(id);return e?e.value:''};
    var brand=document.getElementById('id_brand');var bn=brand&&brand.selectedIndex>0?brand.options[brand.selectedIndex].text:'';
    document.getElementById('pv-title').textContent=g('id_title')||(bn+' '+g('id_model'));
    document.getElementById('pv-price').textContent=g('id_price')?'€'+Number(g('id_price')).toLocaleString():'';
    document.getElementById('pv-meta').textContent=[g('id_year'),g('id_mileage')&&g('id_mileage')+' km',g('id_city')].filter(Boolean).join(' · ');
    document.getElementById('pv-desc').textContent=g('id_description');
    var pi=document.getElementById('pv-img'),f=inp&&inp.files[0];if(pi&&f)pi.src=URL.createObjectURL(f);
    document.getElementById('preview').hidden=false;document.getElementById('preview').scrollIntoView({behavior:'smooth'})})}
  // confirm
  document.querySelectorAll('form[data-confirm]').forEach(function(f){f.addEventListener('submit',function(e){if(!confirm(f.dataset.confirm))e.preventDefault()})});
})();

/* liquid glass: pointer light + optional ripple on desktop Chromium */
(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var chromium = !!window.chrome && /Chrome\//.test(navigator.userAgent);
  var desktop = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  var mem = navigator.deviceMemory || 8;
  if (chromium && desktop && mem >= 4 && !reduce && !window.matchMedia('(prefers-reduced-transparency: reduce)').matches) {
    document.documentElement.classList.add('refract');
  }
  if (reduce) return;
  var sel = '.site-header,.filters,.panel,.gauge-card,.fab', raf = 0, tgt = null, px = 0, py = 0;
  function apply() {
    raf = 0; if (!tgt) return;
    var r = tgt.getBoundingClientRect();
    tgt.style.setProperty('--lx', ((px - r.left) / r.width * 100).toFixed(1) + '%');
    tgt.style.setProperty('--ly', ((py - r.top) / r.height * 100).toFixed(1) + '%');
  }
  document.addEventListener('pointermove', function (e) {
    var t = e.target.closest && e.target.closest(sel);
    if (!t) return;
    tgt = t; px = e.clientX; py = e.clientY;
    if (!raf) raf = requestAnimationFrame(apply);
  }, { passive: true });
  document.addEventListener('pointerout', function (e) {
    var t = e.target.closest && e.target.closest(sel);
    if (t && !t.contains(e.relatedTarget)) { t.style.removeProperty('--lx'); t.style.removeProperty('--ly'); }
  }, { passive: true });
})();

/* share button (replaces an inline onclick so a strict Content-Security-Policy can be used) */
document.addEventListener('click', function (e) {
  var b = e.target.closest && e.target.closest('[data-share]');
  if (!b) return;
  if (navigator.share) { navigator.share({ title: document.title, url: location.href }).catch(function () {}); }
  else if (navigator.clipboard) { navigator.clipboard.writeText(location.href).then(function () { b.textContent = '✓'; }); }
});
