/* CashTrace AI - shared navigation, authentication and page-back controls */
(function () {
  const links = [
    ['Overview','/'], ['Cases','/case_intelligence.html'], ['Forecasts','/prediction.html'],
    ['Hotspots','/hotspot.html'], ['Alerts','/alerts.html'], ['Report Incident','/report.html'],
    ['My Cases','/citizen_dashboard.html'], ['About','/about.html'], ['Safety','/safety.html']
  ];
  function currentPath(){ return (location.pathname || '/').replace(/\\/g,'/'); }
  function isActive(href){ const p=currentPath(); return href==='/' ? (p==='/'||p==='/index.html') : p.endsWith(href); }
  function makeHeader(){
    if(document.querySelector('.ct-top')) return;
    const header=document.createElement('header'); header.className='ct-top';
    header.innerHTML='<a class="ct-brand" href="/"><span class="ct-mark">CT</span><span class="brand-copy">CashTrace AI<small>AI-Powered Financial Intelligence</small></span></a><nav class="ct-nav"></nav><div class="ct-actions"><button class="ct-iconbtn" onclick="toggleCashTraceTheme()">◐ <span data-theme-label>Dark mode</span></button></div>';
    document.body.insertBefore(header,document.body.firstChild);
  }
  function buildNav(){ const nav=document.querySelector('.ct-nav'); if(!nav)return; nav.innerHTML=links.map(([label,href])=>`<a href="${href}"${isActive(href)?' class="active"':''}>${label}</a>`).join(''); }
  async function buildAuth(){
    const host=document.querySelector('.ct-actions'); if(!host)return;
    let theme=host.querySelector('.ct-iconbtn'); host.innerHTML=''; if(theme)host.appendChild(theme);
    const actions=document.createElement('span'); actions.className='ct-auth-actions';
    actions.innerHTML='<a class="ct-btn auth-login" href="/login.html">Complainant Login</a><a class="ct-btn auth-logout" href="#" style="display:none">Logout</a>';
    host.appendChild(actions);
    try{const r=await fetch('/api/auth/status',{credentials:'same-origin',cache:'no-store'});const data=await r.json();if(data?.authenticated){const login=actions.querySelector('.auth-login'),logout=actions.querySelector('.auth-logout');login.style.display='none';logout.style.display='inline-flex';logout.addEventListener('click',async e=>{e.preventDefault();logout.textContent='Logging out…';try{await fetch('/api/logout',{method:'POST',credentials:'same-origin'});}finally{location.href='/';}});}}catch(_e){}
  }
  function addBack(){
    if(document.body.classList.contains('no-page-back') || document.querySelector('.page-back')) return;
    const main=document.querySelector('.ct-main'); if(!main)return;
    const b=document.createElement('button'); b.className='ct-btn page-back'; b.type='button'; b.textContent='← Back';
    b.onclick=()=>{ if(history.length>1)history.back(); else location.href='/'; };
    main.insertBefore(b,main.firstChild);
  }
  function removeProjectUI(){document.querySelectorAll('a,button,.nav-item,.side-link,.menu-item').forEach(el=>{if((el.textContent||'').trim().toLowerCase()==='project')el.remove();});document.querySelectorAll('h1,h2,h3,h4,.eyebrow,.section-title').forEach(el=>{if((el.textContent||'').trim().toLowerCase()==='project'){const parent=el.closest('section,.panel,.card,.menu-section');if(parent)parent.remove();else el.remove();}});}
  document.addEventListener('DOMContentLoaded',()=>{makeHeader();buildNav();buildAuth();addBack();removeProjectUI();});
})();
