// Sharespace Technologies - Main JS
(function(){
  // Reveal-up effect on section headings
  const io = ('IntersectionObserver' in window) ? new IntersectionObserver((entries)=>{
    entries.forEach(e=>{
      if(e.isIntersecting){ e.target.classList.add('in-view'); io.unobserve(e.target); }
    })
  }, {threshold:0.2}) : null;
  document.querySelectorAll('.section-title').forEach(el=>{
    el.classList.add('reveal-up');
    if(io){ io.observe(el); } else { el.classList.add('in-view'); }
  });

  // Observe any .reveal-up targets (new sections, feature cards, etc.)
  if(io){
  document.querySelectorAll('.reveal-up').forEach(el=> io.observe(el));
    // Also toggle in-view on feature-title for underline animation
    document.querySelectorAll('.feature-title').forEach(el=> io.observe(el));
  }

  // Optional: smooth scroll for in-page anchors
  document.querySelectorAll('a[href^="#"]').forEach(a=>{
    a.addEventListener('click', e=>{
      const id = a.getAttribute('href');
      if(id.length>1){
        const el = document.querySelector(id);
        if(el){ e.preventDefault(); el.scrollIntoView({behavior:'smooth'}); }
      }
    })
  })

  // Contact form: simple client-side handler
  const form = document.getElementById('contactForm');
  if(form){
    form.addEventListener('submit', (e)=>{
      e.preventDefault();
      const alertEl = document.getElementById('formAlert');
      if(alertEl){
        alertEl.classList.remove('d-none');
      }
      form.reset();
    })
  }

  // Footer: set current year
  const y = document.getElementById('y');
  if(y){ y.textContent = new Date().getFullYear(); }

  // Build a reusable footer across all pages
  const footerMount = document.getElementById('app-footer');
  if(footerMount){
    const year = new Date().getFullYear();
    footerMount.innerHTML = `
      <footer class="site-footer">
        <div class="container">
          <div class="row g-4">
            <div class="col-12 col-md-6 col-lg-3 reveal-up">
              <h6 class="footer-title">Corporate Office</h6>
              <ul class="contact-list">
                <li><i class="bi bi-geo-alt"></i><span>#1-76, Rajannapalem, Atchutapuram, Anakapalli</span></li>
                <li><i class="bi bi-telephone"></i><a href="tel:85407616"> 85--407616</a></li>
                <li><i class="bi bi-envelope"></i><a href="mailto:info@sharespace.com"> info@sharespace.com</a></li>
              </ul>
            </div>
            <div class="col-12 col-md-6 col-lg-3 reveal-up">
              <h6 class="footer-title">Branch Office</h6>
              <ul class="contact-list">
                <li><i class="bi bi-geo-alt"></i><span>#65-6-705, Beside Gousia Masjid, New Gajuwaka Vegetable Market, Gajuwaka - 530026</span></li>
                <li><i class="bi bi-telephone"></i><a href="tel:85407616"> 85--407616</a></li>
                <li><i class="bi bi-envelope"></i><a href="mailto:support@sharespace.com"> support@sharespace.com</a></li>
              </ul>
            </div>
            <div class="col-12 col-md-6 col-lg-3 reveal-up">
              <h6 class="footer-title">Quick Links</h6>
              <ul class="list-unstyled small">
                <li><a href="index.html">Home</a></li>
                <li><a href="about.html">About</a></li>
                <li><a href="services.html">Services</a></li>
                <li><a href="products.html">Products</a></li>
                <li><a href="clients.html">Clients</a></li>
                <li><a href="contact.html">Contact</a></li>
                <li><a href="#">Privacy Policy</a></li>
                <li><a href="#">Terms of Service</a></li>
              </ul>
            </div>
            <div class="col-12 col-md-6 col-lg-3 reveal-up">
              <h6 class="footer-title">Follow Us</h6>
              <div class="social d-flex gap-2">
                <a href="#" aria-label="Facebook" title="Facebook"><i class="bi bi-facebook"></i></a>
                <a href="#" aria-label="Twitter" title="Twitter"><i class="bi bi-twitter-x"></i></a>
                <a href="#" aria-label="Instagram" title="Instagram"><i class="bi bi-instagram"></i></a>
                <a href="#" aria-label="LinkedIn" title="LinkedIn"><i class="bi bi-linkedin"></i></a>
              </div>
            </div>
          </div>
          <hr class="my-4" />
          <div class="d-flex flex-column flex-md-row justify-content-between small">
            <div>© <span id="y">${year}</span> Sharespace Technologies Pvt Ltd. All Rights Reserved.</div>
          </div>
        </div>
      </footer>
    `;

    // Observe newly added reveal-up elements
    if(io){ footerMount.querySelectorAll('.reveal-up').forEach(el=> io.observe(el)); }
  }

  // Product cards: View More / View Less toggle
  document.addEventListener('click', (e)=>{
    const btn = e.target.closest('[data-toggle="product-more"]');
    if(!btn) return;
    e.preventDefault();
    const card = btn.closest('.product-card');
    if(!card) return;
    const extra = card.querySelector('.product-extra');
    if(!extra) return;
    const isOpen = card.classList.toggle('is-open');
    // Smooth max-height animation: set to scrollHeight when opening
    if(isOpen){
      extra.style.maxHeight = extra.scrollHeight + 'px';
      extra.style.opacity = '1';
      btn.setAttribute('aria-expanded', 'true');
      if(btn.dataset.alt){ btn.dataset.tmp = btn.textContent; btn.textContent = btn.dataset.alt; }
    } else {
      extra.style.maxHeight = '0px';
      extra.style.opacity = '0';
      btn.setAttribute('aria-expanded', 'false');
      if(btn.dataset.tmp){ btn.textContent = btn.dataset.tmp; btn.dataset.tmp = ''; }
    }
  });
})();
