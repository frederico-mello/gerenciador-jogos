/* Gerenciador de Jogos — app.js
 *
 * Único ponto de JavaScript da aplicação (CSP de produção `script-src 'self'`,
 * sem inline). Todas as interações usam listeners delegados acionados por
 * atributos declarativos `data-*` no HTML:
 *   - data-modal-open / data-modal-close  → <dialog> nativo
 *   - data-confirm                        → confirmação antes do submit
 *   - data-autosubmit                     → submit do form ao mudar de valor
 * Seções: modal, carousel, easymde, auto-submit, confirm.
 * Cada seção retorna cedo quando seu gancho não existe na página.
 */
(function () {
  'use strict';

  /* ------------------------------------------------------------------ *
   * Modal (data-modal-open / data-modal-close)
   * ------------------------------------------------------------------ */
  document.addEventListener('click', function (e) {
    var openBtn = e.target.closest ? e.target.closest('[data-modal-open]') : null;
    if (openBtn) {
      var dialog = document.getElementById(openBtn.getAttribute('data-modal-open'));
      if (dialog && typeof dialog.showModal === 'function') {
        e.preventDefault();
        dialog.showModal();
      }
      return;
    }

    var closeBtn = e.target.closest ? e.target.closest('[data-modal-close]') : null;
    if (closeBtn) {
      var host = closeBtn.closest('dialog');
      if (host && typeof host.close === 'function') {
        e.preventDefault();
        host.close();
      }
    }
  });

  /* ------------------------------------------------------------------ *
   * Carrossel do manual (#manual-carousel)
   * ------------------------------------------------------------------ */
  var carousel = document.getElementById('manual-carousel');
  if (carousel && !carousel.dataset.carouselBound) {
    carousel.dataset.carouselBound = '1';

    var slides = Array.prototype.slice.call(
      carousel.querySelectorAll('.carousel-slide')
    );

    if (slides.length > 1) {
      var prevBtn = document.getElementById('carousel-prev');
      var nextBtn = document.getElementById('carousel-next');
      var status = document.getElementById('carousel-status');
      var idx = 0;

      function render() {
        slides.forEach(function (el, i) {
          if (i === idx) {
            el.classList.add('active');
          } else {
            el.classList.remove('active');
          }
        });
        if (status) {
          status.textContent = 'Página ' + (idx + 1) + ' de ' + slides.length;
        }
        if (prevBtn) prevBtn.disabled = idx === 0;
        if (nextBtn) nextBtn.disabled = idx === slides.length - 1;
      }

      if (prevBtn) {
        prevBtn.addEventListener('click', function () {
          idx = Math.max(0, idx - 1);
          render();
        });
      }
      if (nextBtn) {
        nextBtn.addEventListener('click', function () {
          idx = Math.min(slides.length - 1, idx + 1);
          render();
        });
      }

      render();
    }
  }

  /* ------------------------------------------------------------------ *
   * EasyMDE (#descricao)
   * ------------------------------------------------------------------ */
  var descricao = document.getElementById('descricao');
  if (descricao && typeof window.EasyMDE !== 'undefined') {
    new window.EasyMDE({
      element: descricao,
      spellChecker: false,
      status: false,
      minHeight: '200px',
      toolbar: [
        'bold',
        'italic',
        'heading',
        '|',
        'unordered-list',
        'ordered-list',
        '|',
        'quote',
        'link',
        'image',
        '|',
        'preview',
        'side-by-side',
        'fullscreen',
        'guide'
      ]
    });
  }

  /* ------------------------------------------------------------------ *
   * Auto-submit (data-autosubmit) — substitui `onchange="this.form.submit()"`
   * ------------------------------------------------------------------ */
  document.addEventListener('change', function (e) {
    var el = e.target && e.target.closest ? e.target.closest('[data-autosubmit]') : null;
    if (!el) return;

    var form = el.closest('form');
    if (!form) return;

    if (typeof form.requestSubmit === 'function') {
      form.requestSubmit();
    } else {
      form.submit();
    }
  });

  /* ------------------------------------------------------------------ *
   * Confirm (data-confirm) — substitui `onsubmit="return confirm(...)"`
   * ------------------------------------------------------------------ */
  document.addEventListener(
    'submit',
    function (e) {
      var form = e.target;
      if (!form || form.nodeName !== 'FORM' || !form.hasAttribute('data-confirm')) {
        return;
      }
      var message = form.getAttribute('data-confirm') || 'Tem certeza?';
      if (!window.confirm(message)) {
        e.preventDefault();
      }
    },
    true
  );
})();
