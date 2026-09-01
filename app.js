/* КООПТЕХ — поведение нового дизайна.
   Ничего не удаляет из разметки: только добавляет тоггл темы, мобильное меню,
   нижнюю таб-панель, лист фильтров и SVG-иконки вместо эмодзи. */
(function () {
  var I = {
    sun: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.6v2.6M12 18.8v2.6M2.6 12h2.6M18.8 12h2.6M5.6 5.6l1.8 1.8M16.6 16.6l1.8 1.8M18.4 5.6l-1.8 1.8M7.4 16.6l-1.8 1.8"/></svg>',
    moon: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M20.4 14.8A8.8 8.8 0 019.2 3.6 8.8 8.8 0 1020.4 14.8z"/></svg>',
    plus: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M12 5.5v13M5.5 12h13"/></svg>',
    burger: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
    chevron: '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9.5l6 6 6-6"/></svg>',
    filter: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 7.5h14M8 12h8M10.6 16.5h2.8"/></svg>',
    search: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"><circle cx="10.8" cy="10.8" r="6.4"/><path d="M15.6 15.6l4 4"/></svg>',
    /* Пути для ссылок аккаунта в мобильном меню — рисуются через ico() */
    gearPath: 'M12 15.1a3.1 3.1 0 100-6.2 3.1 3.1 0 000 6.2M19.3 12c0-.4 0-.8-.1-1.2l1.9-1.5-1.9-3.3-2.3 1c-.6-.5-1.2-.9-1.9-1.1L14.6 3.4h-3.8l-.4 2.5c-.7.2-1.3.6-1.9 1.1l-2.3-1-1.9 3.3L6.2 10.8a7 7 0 000 2.4l-1.9 1.5 1.9 3.3 2.3-1c.6.5 1.2.9 1.9 1.1l.4 2.5h3.8l.4-2.5c.7-.2 1.3-.6 1.9-1.1l2.3 1 1.9-3.3-1.9-1.5c.1-.4.1-.8.1-1.2z',
    exitPath: 'M14.4 7.4V5.6a1.6 1.6 0 00-1.6-1.6H5.6A1.6 1.6 0 004 5.6v12.8a1.6 1.6 0 001.6 1.6h7.2a1.6 1.6 0 001.6-1.6v-1.8M9.6 12h10.8M17.4 8.8l3.2 3.2-3.2 3.2'
  };
  function ico(d, w) {
    return '<svg width="' + (w || 17) + '" height="' + (w || 17) + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><path d="' + d + '"/></svg>';
  }

  /* Иконки разделов меню — по атрибуту data-icon у ссылки (в tools/shell.html),
     а не по её тексту: переименование подписи не должно ломать иконку. */
  var NAV_ICONS = {
    'my-page': 'M12 8.4a3.2 3.2 0 100-6.4 3.2 3.2 0 000 6.4M5.4 20c0-3.5 3-5.3 6.6-5.3s6.6 1.8 6.6 5.3',
    'messages': 'M20.5 12.4c0 3.8-3.8 6.9-8.5 6.9-1 0-2-.14-2.9-.4L4.6 20.4l1.2-3.3c-1.2-1.2-2.3-2.8-2.3-4.7 0-3.8 3.8-6.9 8.5-6.9s8.5 3.1 8.5 6.9z',
    'people': 'M8.4 10.4a2.8 2.8 0 100-5.6 2.8 2.8 0 000 5.6M16 11a2.4 2.4 0 100-4.8A2.4 2.4 0 0016 11M2.8 19.4c0-3.1 2.5-4.7 5.6-4.7s5.6 1.6 5.6 4.7M15.4 14.9c3 .2 5.2 1.7 5.2 4.5',
    'skills': 'M12 3.6l2.5 5.1 5.6.8-4 4 .9 5.6-5-2.7-5 2.7.9-5.6-4-4 5.6-.8z',
    'vacancies': 'M3.2 9.6a2.2 2.2 0 012.2-2.2h13.2a2.2 2.2 0 012.2 2.2v7.8a2.2 2.2 0 01-2.2 2.2H5.4a2.2 2.2 0 01-2.2-2.2zM9 7.4V5.6a2 2 0 012-2h2a2 2 0 012 2v1.8M3.2 12.6h17.6',
    'resources': 'M4 4h6.6v6.6H4zM13.4 4H20v6.6h-6.6zM4 13.4h6.6V20H4zM13.4 13.4H20V20h-6.6',
    'projects': 'M12 3.4l8.4 4.6-8.4 4.6L3.6 8zM3.6 12.6L12 17.2l8.4-4.6',
    'organizations': 'M3.6 5.6a1.6 1.6 0 011.6-1.6h6.6a1.6 1.6 0 011.6 1.6V20H3.6zM13.4 9.2h7V20h-7M6.6 8h3.6M6.6 12h3.6M6.6 16h3.6',
    'communities': 'M12 3.4a8.6 8.6 0 100 17.2 8.6 8.6 0 000-17.2M3.6 12h16.8M12 3.4c2.4 2.3 3.6 5.1 3.6 8.6s-1.2 6.3-3.6 8.6c-2.4-2.3-3.6-5.1-3.6-8.6s1.2-6.3 3.6-8.6',
    'wallet': 'M3.2 8.4a2.4 2.4 0 012.4-2.4h12.8a2.4 2.4 0 012.4 2.4v8.2a2.4 2.4 0 01-2.4 2.4H5.6a2.4 2.4 0 01-2.4-2.4zM3.2 10.2h17.6M16.4 14.6h1.8',
    /* Сделки — рукопожатие: сделка закрывается двусторонними отзывами */
    'deals': 'M4 12.4l3.4-3.4 4.6 1.6 4.6-1.6L20 12.4M4 12.4l4 5 4-2 4 2 4-5M8 9v-2h8v2'
  };

  /* Эмодзи → SVG для плиток и иконок содержимого */
  var EMOJI_ICONS = {
    '\uD83D\uDCCD': 'M12 21s6.4-6 6.4-10.4a6.4 6.4 0 10-12.8 0C5.6 15 12 21 12 21zM12 12.7a2.2 2.2 0 100-4.4 2.2 2.2 0 000 4.4',
    '\uD83D\uDD14': 'M18 15.4V10a6 6 0 10-12 0v5.4L4.6 18h14.8M10 20.4a2 2 0 004 0',
    '\uD83D\uDC65': 'M8.4 10.4a2.8 2.8 0 100-5.6 2.8 2.8 0 000 5.6M16 11a2.4 2.4 0 100-4.8A2.4 2.4 0 0016 11M2.8 19.4c0-3.1 2.5-4.7 5.6-4.7s5.6 1.6 5.6 4.7M15.4 14.9c3 .2 5.2 1.7 5.2 4.5',
    '\uD83D\uDE80': 'M12 3.4c3.4 2.6 5 6 5 10.2l-2.6 2.4h-4.8L7 13.6c0-4.2 1.6-7.6 5-10.2M9.6 16v3.4M14.4 16v3.4M12 8.6h.01',
    '\uD83D\uDCF7': 'M3.4 8.4a1.6 1.6 0 011.6-1.6h2l1.4-2h7.2l1.4 2h2a1.6 1.6 0 011.6 1.6v8.4a1.6 1.6 0 01-1.6 1.6H5a1.6 1.6 0 01-1.6-1.6zM12 15.4a3.2 3.2 0 100-6.4 3.2 3.2 0 000 6.4',
    '\uD83D\uDD04': 'M4.4 12a7.6 7.6 0 0112.8-5.4M19.6 12a7.6 7.6 0 01-12.8 5.4M17.6 3.6v3.4h-3.4M6.4 20.4V17H9.8',
    '\uD83D\uDD01': 'M4.4 12a7.6 7.6 0 0112.8-5.4M19.6 12a7.6 7.6 0 01-12.8 5.4M17.6 3.6v3.4h-3.4M6.4 20.4V17H9.8',
    '\uD83C\uDF81': 'M3.6 9.4h16.8v10.2H3.6zM3.6 9.4h16.8M12 9.4v10.2M8.4 9.4a2.4 2.4 0 010-4.8c2 0 3.6 4.8 3.6 4.8M15.6 9.4a2.4 2.4 0 000-4.8c-2 0-3.6 4.8-3.6 4.8',
    '\uD83C\uDF31': 'M12 20.4v-7.6M12 12.8C12 8.8 9 6 5.4 6c0 4 3 6.8 6.6 6.8M12 12.8c0-4 3-6.8 6.6-6.8 0 4-3 6.8-6.6 6.8',
    '\uD83D\uDCBB': 'M3.6 6.4a1.6 1.6 0 011.6-1.6h13.6a1.6 1.6 0 011.6 1.6v9.2H3.6zM2 17.6h20',
    '\uD83D\uDEE0': 'M14.6 6.4a3.6 3.6 0 004.9 4.9l-9 9-4.9-4.9 9-9z',
    '\uD83C\uDFA8': 'M12 3.6a8.4 8.4 0 100 16.8c1.4 0 2-1 2-1.8s-.6-1.6-2-1.6h-1.4a2 2 0 010-4h5.4a4.4 4.4 0 004.4-4.4c0-3-3.6-5-8.4-5M7.6 9.4h.01M9.8 6.6h.01M14.4 6.6h.01',
    '\uD83E\uDD1D': 'M4 12.4l3.4-3.4 4.6 1.6 4.6-1.6L20 12.4M4 12.4l4 5 4-2 4 2 4-5M8 9v-2h8v2',
    '\uD83D\uDE97': 'M4 15.6h16M5.6 15.6l1.4-5.2h10l1.4 5.2M6.6 18.6a1.4 1.4 0 100-2.8 1.4 1.4 0 000 2.8M17.4 18.6a1.4 1.4 0 100-2.8 1.4 1.4 0 000 2.8',
    '\uD83C\uDFE0': 'M4 11.4L12 4.6l8 6.8v8.2H4zM9.6 19.6v-5.4h4.8v5.4',
    '\uD83C\uDFE1': 'M4 11.4L12 4.6l8 6.8v8.2H4zM9.6 19.6v-5.4h4.8v5.4',
    '\uD83C\uDFD8': 'M4 20.4V9.4L10 5.4v15M10 9.4l6 3v8M16 12.4h4v8M6.6 13h1.4M6.6 16.4h1.4',
    '\uD83C\uDFE2': 'M5.4 20.4V4.4h9v16M14.4 9.4h4.2v11M8 8h3.4M8 11.6h3.4M8 15.2h3.4',
    '\uD83C\uDFDB': 'M3.6 9.4L12 4l8.4 5.4M5.6 9.4v9M9.6 9.4v9M14.4 9.4v9M18.4 9.4v9M3.6 20.6h16.8',
    '\uD83C\uDFE5': 'M12 5.4v13.2M5.4 12h13.2',
    '\uD83C\uDF93': 'M3.6 9.4L12 5.4l8.4 4-8.4 4zM7 12.6v4c0 1.4 2.2 2.4 5 2.4s5-1 5-2.4v-4',
    '\uD83C\uDF3E': 'M12 20.4V9M12 9c0-3-2-5.4-5-5.4 0 3 2 5.4 5 5.4M12 9c0-3 2-5.4 5-5.4 0 3-2 5.4-5 5.4M6.6 20.4h10.8',
    '\uD83E\uDDF0': 'M3.6 9.4h16.8v10.2H3.6zM9 9.4V7a1.6 1.6 0 011.6-1.6h2.8A1.6 1.6 0 0115 7v2.4M3.6 13.6h16.8',
    '\uD83C\uDFC3': 'M13.6 5.4a1.6 1.6 0 100-3.2 1.6 1.6 0 000 3.2M8 20.4l2.4-4.4-1.4-4 3.4-2.4 3 2.4 3 .8M10.4 12l-3.8.8',
    '\uD83D\uDC9E': 'M12 20.2l-1.4-1.3C5.4 14.2 2.6 11.7 2.6 8.6A4.6 4.6 0 017.2 4c1.7 0 3.3.8 4.3 2.1L12 6.6l.5-.5A5.4 5.4 0 0116.8 4a4.6 4.6 0 014.6 4.6c0 3.1-2.8 5.6-8 10.3z',
    '\uD83C\uDFD7': 'M5.4 20.6V4.4l12 5.6M5.4 9.4l8 4M5.4 14.4l8 4M18.6 20.6V9.4',
    '\uD83E\uDDF5': 'M12 3.6v16.8M8.4 6.4a3.6 3.6 0 007.2 0M8.4 12a3.6 3.6 0 007.2 0M8.4 17.6a3.6 3.6 0 007.2 0',
    '\uD83C\uDF1F': 'M12 3.6l2.5 5.1 5.6.8-4 4 .9 5.6-5-2.7-5 2.7.9-5.6-4-4 5.6-.8z',
    '\uD83D\uDC11': 'M6 15.4a4 4 0 018 0M4.6 11.4a2 2 0 013.2-1.6M19.4 11.4a2 2 0 00-3.2-1.6M8 19.6v-2M16 19.6v-2M12 8.4a3.4 3.4 0 100-4.8 3.4 3.4 0 000 4.8',
    '\uD83D\uDC55': 'M8.6 4.4L12 7l3.4-2.6 4.2 2.2-1.6 4.4-1.6-.6v9.2H7.6v-9.2l-1.6.6L4.4 6.6z',
    '\uD83E\uDD55': 'M6 18.6c4-1.4 8.4-5.8 10.4-10.4M16.4 8.2l2.6-2.6M12.4 6.2l1.6-2.6M9 9.6L7 7.4',
    '\uD83D\uDC3E': 'M8.4 8.6a1.8 1.8 0 100-3.6 1.8 1.8 0 000 3.6M15.6 8.6a1.8 1.8 0 100-3.6 1.8 1.8 0 000 3.6M6 13.6a1.6 1.6 0 100-3.2 1.6 1.6 0 000 3.2M18 13.6a1.6 1.6 0 100-3.2 1.6 1.6 0 000 3.2M12 19.6c-2.6 0-4.4-1.6-4.4-3.4S9.4 12 12 12s4.4 2.4 4.4 4.2-1.8 3.4-4.4 3.4',
    '\uD83D\uDCA1': 'M9.4 18.6h5.2M10 21h4M12 3.4a5.6 5.6 0 013.4 10.1v2.1H8.6v-2.1A5.6 5.6 0 0112 3.4',
    '\u2699': 'M12 15a3 3 0 100-6 3 3 0 000 6M19.4 14.6a7.6 7.6 0 00.1-5.2l-2.1-.5-1-1.7.6-2A7.6 7.6 0 0012 3.5l-1.3 1.7-2 .2-1.5-1.4a7.6 7.6 0 00-2.6 4.5l1.4 1.5v2l-1.4 1.5a7.6 7.6 0 002.6 4.5l1.5-1.4 2 .2L12 20.5a7.6 7.6 0 005-2.3l-.6-2 1-1.7z',
    '\u2691': 'M6.6 20.4V4.4l11 3.6-11 3.6',
    '\u2696': 'M12 3.4v17.2M6 7h12M6 7l-2.6 6h5.2zM18 7l-2.6 6h5.2zM8 20.6h8',
    '\uD83D\uDCB0': 'M12 3.2l7.6 8.8-7.6 8.8-7.6-8.8zM12 8.4v7.2M9 12h6',
    '\uD83D\uDCC8': 'M4 19V9M9.4 19V5M14.8 19v-7M20.2 19v-4',
    '\uD83D\uDCCA': 'M4 19V9M9.4 19V5M14.8 19v-7M20.2 19v-4',
    '\uD83E\uDDEE': 'M4.4 4.4h15.2v15.2H4.4zM4.4 9.4h15.2M4.4 14.4h15.2M9.4 4.4v15.2M14.4 4.4v15.2',
    '\uD83D\uDC77': 'M6 12a6 6 0 0112 0M4.4 12h15.2M12 4.4v3.2M8.6 16.4a3.4 3.4 0 006.8 0',
    '\uD83D\uDCE6': 'M4 8.4L12 4.4l8 4v7.2L12 19.6l-8-4zM4 8.4l8 4 8-4M12 12.4v7.2',
    '\uD83D\uDD27': 'M14.6 6.4a3.6 3.6 0 004.9 4.9l-9 9-4.9-4.9 9-9z',
    '\uD83D\uDCC5': 'M4 7.4a1.6 1.6 0 011.6-1.6h12.8A1.6 1.6 0 0120 7.4v11.2H4zM4 11h16M8.6 4v3.4M15.4 4v3.4',
    '\uD83D\uDCAC': 'M20.5 12.4c0 3.8-3.8 6.9-8.5 6.9-1 0-2-.14-2.9-.4L4.6 20.4l1.2-3.3c-1.2-1.2-2.3-2.8-2.3-4.7 0-3.8 3.8-6.9 8.5-6.9s8.5 3.1 8.5 6.9z',
    '\uD83D\uDCDA': 'M4.4 5.4h5.4v13.2H4.4zM11.4 5.4h8.2v13.2h-8.2M14 9h3.4M14 12.6h3.4',
    '\uD83D\uDDC2': 'M3.6 7.4a1.6 1.6 0 011.6-1.6h4l1.8 2.2h7.4a1.6 1.6 0 011.6 1.6v8.4a1.6 1.6 0 01-1.6 1.6H5.2a1.6 1.6 0 01-1.6-1.6z',
    '\u267B': 'M8.4 5.4l2-2.6 2.4 3.4M15.6 8.6l3.2 1.2-1.6 3.8M9 18.6l-3.4-.4.6-4M6.4 9.4L4 13l3.6 2M17.6 15.6l-2 3.2-3.6-1.4',
    '\u2B50': 'M12 3.6l2.5 5.1 5.6.8-4 4 .9 5.6-5-2.7-5 2.7.9-5.6-4-4 5.6-.8z',
    '\uD83D\uDD25': 'M12 20.6c3.2 0 5.4-2.2 5.4-5 0-3.6-3.4-5.2-3.4-9.2-2.6 1.4-4 3.6-4 6 0-1.4-.6-2.4-1.6-3.2-1 1.6-1.8 3.6-1.8 6.4 0 2.8 2.2 5 5.4 5z'
  };

  /* 1. Тема. Саму тему ставит theme-init.js в <head> — до первой отрисовки,
     иначе страница мигает светлым. Здесь только кнопка-переключатель. */

  function buildToggle() {
    var b = document.createElement('button');
    b.className = 'theme-toggle';
    b.type = 'button';
    b.setAttribute('aria-label', 'Тёмная тема');
    b.setAttribute('aria-pressed', document.documentElement.getAttribute('data-theme') === 'dark' ? 'true' : 'false');
    b.innerHTML = '<span class="tt-sun">' + I.sun + '</span><span class="tt-moon">' + I.moon + '</span><span class="tt-knob"></span>';
    b.addEventListener('click', function () {
      var dark = document.documentElement.getAttribute('data-theme') === 'dark';
      /* Явный выбор пользователя записываем — с этого момента страница
         перестаёт следовать за системной темой (см. theme-init.js). */
      document.documentElement.setAttribute('data-theme', dark ? 'light' : 'dark');
      b.setAttribute('aria-pressed', dark ? 'false' : 'true');
      try { localStorage.setItem('cooptech_theme', dark ? 'light' : 'dark'); } catch (e) {}
    });
    return b;
  }

  /* ── Доступность ───────────────────────────────────────────
     Кнопки-иконки (☰/▦, скрепка, эмодзи, стрелки календаря) подписаны только
     атрибутом title — скринридер его не всегда озвучивает; переносим в
     aria-label. Переключатели вида получают aria-pressed. Модальные окна —
     role="dialog", закрытие по Esc, фокус внутрь и возврат обратно. */
  function a11y() {
    /* 1. Имя для кнопки без текста: берём из title */
    var btns = document.querySelectorAll('button[title], a[title]');
    for (var i = 0; i < btns.length; i++) {
      var b = btns[i];
      if (b.getAttribute('aria-label')) continue;
      if (b.textContent.trim()) continue;          /* текст есть — имя уже есть */
      b.setAttribute('aria-label', b.getAttribute('title'));
    }

    /* 2. Переключатель «списком / плиткой» — это состояние, а не действие */
    var toggles = document.querySelectorAll('.view-toggle');
    for (var t = 0; t < toggles.length; t++) {
      toggles[t].setAttribute('role', 'group');
      toggles[t].setAttribute('aria-label', 'Вид каталога');
      var tb = toggles[t].querySelectorAll('button');
      for (var j = 0; j < tb.length; j++) {
        tb[j].setAttribute('aria-pressed', tb[j].classList.contains('active') ? 'true' : 'false');
      }
      toggles[t].addEventListener('click', function (e) {
        var host = e.currentTarget;
        setTimeout(function () {
          var list = host.querySelectorAll('button');
          for (var k = 0; k < list.length; k++) {
            list[k].setAttribute('aria-pressed', list[k].classList.contains('active') ? 'true' : 'false');
          }
        }, 0);
      });
    }

    /* 3. Модальные окна */
    var overlays = document.querySelectorAll('.modal-overlay');
    for (var o = 0; o < overlays.length; o++) setupModal(overlays[o], o);

    /* 4. Формы. Бэкенда нет, поэтому отправку перехватываем: браузер сначала
       сам проверит required/type (покажет свою подсказку у поля), а дальше
       либо уводим на страницу из data-demo-form, либо просто ничего не делаем —
       у форм размещения объявлений свой пошаговый сценарий на кнопках. */
    var forms = document.querySelectorAll('form[data-demo-form]');
    for (var f = 0; f < forms.length; f++) {
      forms[f].addEventListener('submit', function (e) {
        e.preventDefault();
        var target = e.currentTarget.getAttribute('data-demo-form');
        if (target) location.href = target;
      });
    }
  }

  function setupModal(overlay, idx) {
    var box = overlay.querySelector('.modal');
    if (!box) return;
    /* Роль не перезаписываем: диалог подтверждения объявляет себя alertdialog,
       а a11y() проходит по всем окнам ещё раз и затирал её обратно. */
    if (!box.getAttribute('role')) box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    var head = box.querySelector('h1, h2, h3, .modal-head');
    if (head) {
      if (!head.id) head.id = 'modal-title-' + idx;
      box.setAttribute('aria-labelledby', head.id);
    }
    var closeBtn = box.querySelector('.modal-close');
    var opener = null;

    function focusables() {
      return box.querySelectorAll('a[href], button:not([disabled]), input:not([type="hidden"]), select, textarea, [tabindex]:not([tabindex="-1"])');
    }
    function onKey(e) {
      if (e.key === 'Escape' || e.keyCode === 27) {
        if (closeBtn) closeBtn.click();
        return;
      }
      if (e.key !== 'Tab' && e.keyCode !== 9) return;
      var f = focusables();
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
    /* Окна на страницах показываются снятием атрибута hidden — следим за ним */
    var obs = new MutationObserver(function () {
      if (!overlay.hasAttribute('hidden')) {
        opener = document.activeElement;
        document.addEventListener('keydown', onKey);
        var safe = box.querySelector('[data-focus-first]');
        if (safe) safe.focus();
        else { var f = focusables(); if (f.length) f[0].focus(); }
      } else {
        document.removeEventListener('keydown', onKey);
        if (opener && opener.focus) opener.focus();
        opener = null;
      }
    });
    obs.observe(overlay, { attributes: true, attributeFilter: ['hidden'] });
  }


  /* ============================================================
     Избранное — одно хранилище на все каталоги
     ------------------------------------------------------------
     Разметка: список карточек помечен data-fav-section="vacancies",
     карточка — data-fav-id="<слаг>", кнопка-сердечко внутри карточки —
     .fav-btn. На детальной странице кнопка несёт data-fav="секция:слаг"
     (и data-fav-text, если у неё меняется подпись).
     Сердечко живёт внутри карточки-ссылки, поэтому это span с role="button":
     вложенная <button> внутри <a> — невалидная разметка (тот же приём, что
     у кнопок «Написать» в каталоге людей).
     ============================================================ */
  var FAV_KEY = 'coop_favorites';
  var favSubs = [];

  function favRead() {
    try { return JSON.parse(localStorage.getItem(FAV_KEY)) || {}; } catch (e) { return {}; }
  }
  function favHas(section, id) {
    return (favRead()[section] || []).indexOf(id) !== -1;
  }
  function favCount(section) {
    return (favRead()[section] || []).length;
  }
  function favToggle(section, id) {
    var map = favRead();
    var list = map[section] || [];
    var i = list.indexOf(id);
    if (i === -1) list.push(id); else list.splice(i, 1);
    map[section] = list;
    try { localStorage.setItem(FAV_KEY, JSON.stringify(map)); } catch (e) {}
    favRefresh();
    for (var k = 0; k < favSubs.length; k++) favSubs[k]();
    return i === -1;
  }
  /* Вкладка «Избранное» — это тот же каталог с ?tab=favorites */
  function favMode() {
    return (location.search || '').indexOf('tab=favorites') !== -1;
  }
  function favTarget(el) {
    var direct = el.getAttribute('data-fav');
    if (direct) {
      var p = direct.split(':');
      return { section: p[0], id: p.slice(1).join(':') };
    }
    var card = el.closest('[data-fav-id]');
    var box = el.closest('[data-fav-section]');
    if (!card || !box) return null;
    return { section: box.getAttribute('data-fav-section'), id: card.getAttribute('data-fav-id') };
  }
  function favPaint(el) {
    var t = favTarget(el);
    if (!t) return;
    var on = favHas(t.section, t.id);
    var label = on ? 'В избранном' : 'Добавить в избранное';
    el.classList.toggle('active', on);
    el.setAttribute('aria-pressed', on ? 'true' : 'false');
    el.setAttribute('title', label);
    if (el.hasAttribute('data-fav-text')) el.textContent = label;
    else el.setAttribute('aria-label', label);
  }
  function favRefresh() {
    var btns = document.querySelectorAll('.fav-btn, [data-fav]');
    for (var i = 0; i < btns.length; i++) favPaint(btns[i]);
    var tabs = document.querySelectorAll('[data-fav-tab]');
    for (var j = 0; j < tabs.length; j++) {
      var badge = tabs[j].querySelector('.fav-tab-count');
      if (badge) badge.textContent = favCount(tabs[j].getAttribute('data-fav-tab'));
    }
  }
  function favorites() {
    document.addEventListener('click', function (e) {
      var btn = e.target.closest ? e.target.closest('.fav-btn, [data-fav]') : null;
      if (!btn) return;
      e.preventDefault();
      e.stopPropagation();
      var t = favTarget(btn);
      if (t) favToggle(t.section, t.id);
    });
    /* Сердечко в карточке — не настоящая кнопка, клавиатуру обрабатываем сами */
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      var btn = e.target.closest ? e.target.closest('.fav-btn') : null;
      if (!btn) return;
      e.preventDefault();
      btn.click();
    });

    if (favMode()) {
      document.body.classList.add('fav-mode');
      var tab = document.querySelector('[data-fav-tab]');
      if (tab && tab.parentNode) {
        var siblings = tab.parentNode.querySelectorAll('a');
        for (var i = 0; i < siblings.length; i++) siblings[i].classList.remove('active');
        tab.classList.add('active');
      }
      var empty = document.querySelector('[data-fav-empty]');
      if (empty) empty.textContent = empty.getAttribute('data-fav-empty');
      /* Заголовок списка: «Все вакансии» → «Избранное» (счётчик рядом остаётся) */
      var title = document.querySelector('.cat-section-title > span');
      if (title && title.firstChild && title.firstChild.nodeType === 3) {
        title.firstChild.nodeValue = 'Избранное ';
      }
    }
    favRefresh();
  }

  window.CoopFav = {
    has: favHas,
    toggle: favToggle,
    count: favCount,
    mode: favMode,
    refresh: favRefresh,
    onChange: function (fn) { favSubs.push(fn); }
  };


  /* ── Каталог расширений ────────────────────────────────────
     Единый список модулей платформы: из него рисуется каталог
     (extensions.html) и вкладки подключённых модулей на странице
     организации. Что подключено — в localStorage, как в Odoo Apps:
     модуль ставится один раз и дальше живёт вкладкой в интерфейсе. */
  var MODULES = [
    { id: 'stock',    name: 'Склад',                  cat: 'Учёт',        page: 'ext-warehouse.html',             org: true,
      desc: 'Остатки, партии и резервы. Показывает, сколько ресурса свободно, а сколько уже обещано по сделкам.' },
    { id: 'docs',     name: 'Документы и ЭДО',        cat: 'Учёт',        page: '',                        org: true,
      desc: 'Договоры, счета и акты из сделок, подписание обеими сторонами, хранение с номерами и датами.' },
    { id: 'approve',  name: 'Согласования',           cat: 'Процессы',    page: '',                        org: true,
      desc: 'Маршруты решений: приём в пайщики, выделение техники, выплаты. Видно, кто высказался и кто следующий.' },
    { id: 'reports',  name: 'Отчёты',                 cat: 'Учёт',        page: 'ext-analytics.html',      org: true,
      desc: 'Обороты по ресурсам, участникам и проектам за период, выгрузка в таблицу.' },
    { id: 'booking',  name: 'Бронирование ресурсов',  cat: 'Процессы',    page: '',                        org: true,
      desc: 'Календарь общей техники и помещений: трактор, цех, переговорная — без пересечений и споров.' },
    { id: 'buying',   name: 'Совместные закупки',     cat: 'Сбыт',        page: 'ext-group-buying.html',   org: true,
      desc: 'Общая закупка нескольких участников: чем больше объём, тем ниже цена за единицу.' },
    { id: 'programs', name: 'Целевые программы ПК',   cat: 'Сбыт',        page: 'ext-programs.html',       org: false,
      desc: 'Программы потребкооперации: участие, отчётность, распределение по участникам.' },
    { id: 'token',    name: 'Токеномика',             cat: 'Финансы',     page: 'tokenomics.html',         org: true,
      desc: 'Взаимные обязательства, уступка требований, реестр НМА и выход на ЦФА через оператора. Ничего не эмитирует: ведёт учёт, а не выпускает свою единицу.' },
    { id: 'assets',   name: 'Цифровые активы',        cat: 'Финансы',     page: 'digital-assets.html',     org: false,
      desc: 'Учёт ЦФА и токенов платформы в кошельке организации.' },
    { id: 'intang',   name: 'Нематериальные активы',  cat: 'Финансы',     page: 'intangible-assets.html',  org: false,
      desc: 'Реестр прав, лицензий и разработок по ФСБУ 14/2022.' },
    { id: 'events',   name: 'События',                cat: 'Сообщество',  page: 'ext-events.html',         org: false,
      desc: 'Встречи, ярмарки, собрания: анонсы, запись участников, напоминания.' },
    { id: 'edu',      name: 'Образование',            cat: 'Сообщество',  page: 'ext-education.html',      org: false,
      desc: 'Курсы и обучение участников, зачёт пройденного в навыки профиля.' },
    { id: 'auction',  name: 'Аукционы',               cat: 'Сбыт',        page: 'ext-auctions.html',       org: false,
      desc: 'Продажа ресурсов на повышение и на понижение, когда цена неочевидна.' },
    { id: 'library',  name: 'Библиотеки',             cat: 'Сообщество',  page: 'ext-libraries.html',      org: false,
      desc: 'Библиотеки инструментов и вещей общего пользования с очередью и залогом.' },
    { id: 'drive',    name: 'Диск',                   cat: 'Сообщество',  page: 'ext-drive.html',          org: false,
      desc: 'Общие файлы организации и проектов с версиями.' },
    { id: 'health',   name: 'Здоровье',               cat: 'Сообщество',  page: 'ext-health.html',         org: false,
      desc: 'Медосмотры, страхование и взаимопомощь участников.' },
    { id: 'exchange', name: 'Обмен с 1С',             cat: 'Интеграции',  page: '',                        org: true,
      desc: 'Двусторонний обмен с 1С:Предприятием: номенклатура, контрагенты, документы. Бухгалтерия остаётся в 1С.' },
    { id: 'api',      name: 'API и вебхуки',          cat: 'Интеграции',  page: '',                        org: false,
      desc: 'Открытый REST API и уведомления во внешние системы кооператива.' },
    { id: 'kb',       name: 'База знаний',            cat: 'Сообщество',  page: '',                        org: true,
      desc: 'Устав, регламенты и инструкции организации с версиями и поиском.' },
    { id: 'rights',   name: 'Права и роли',           cat: 'Процессы',    page: '',                        org: true,
      desc: 'Кто что видит и может менять: пайщик, правление, ревизионная комиссия, наёмный сотрудник. Плюс передача полномочий на время отсутствия.' },
    { id: 'audit',    name: 'Журнал аудита',          cat: 'Учёт',        page: '',                        org: true,
      desc: 'Кто что изменил и когда: правки документов, суммы, роли. Нужен ревизионной комиссии, чтобы проверять, а не верить на слово.' },
    { id: 'portal',   name: 'Портал для контрагентов',cat: 'Процессы',    page: '',                        org: true,
      desc: 'Внешний участник видит только свою сделку и документы по ней — без регистрации и без доступа к остальной платформе.' }
  ];
  var DEFAULT_ON = ['stock', 'docs'];
  window.CoopModules = {
    all: MODULES,
    connected: function () {
      try {
        var v = JSON.parse(localStorage.getItem('cooptech_modules') || 'null');
        return v && v.length !== undefined ? v : DEFAULT_ON.slice();
      } catch (e) { return DEFAULT_ON.slice(); }
    },
    isOn: function (id) { return this.connected().indexOf(id) >= 0; },
    toggle: function (id) {
      var list = this.connected(), i = list.indexOf(id);
      if (i >= 0) list.splice(i, 1); else list.push(id);
      try { localStorage.setItem('cooptech_modules', JSON.stringify(list)); } catch (e) {}
      return list.indexOf(id) >= 0;
    }
  };


  /* ── Документ в блокчейне ──────────────────────────────────
     Кнопка с отпечатком (data-chain) открывает карточку записи: что именно
     лежит в реестре, в каком блоке и кто подписал. В блокчейн пишется не сам
     документ, а его хэш — иначе реквизиты и коммерческие условия утекли бы в
     публичный реестр. Здесь же можно выбрать файл и сверить его отпечаток с
     записью: хэш считается прямо в браузере (SHA-256), файл никуда не уходит. */
  function initChain() {
    var triggers = document.querySelectorAll('[data-chain]');
    if (!triggers.length) return;

    var overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.id = 'chain-modal';
    overlay.hidden = true;
    overlay.innerHTML =
      '<div class="modal wide">'
      + '<div class="modal-head"><h2 id="chain-title">Запись в блокчейне</h2>'
      + '<button class="modal-close" id="chain-close" type="button" aria-label="Закрыть">✕</button></div>'
      + '<dl class="chain-grid" id="chain-grid"></dl>'
      + '<div class="card" style="padding:14px 16px;background:var(--paper)">'
      + '<b style="font-size:12.5px">Сверить файл с записью</b>'
      + '<p style="color:var(--slate);font-size:12px;margin:6px 0 10px">Выберите файл документа — браузер посчитает его отпечаток и сравнит с тем, что записан в реестре. Файл при этом никуда не отправляется.</p>'
      + '<input type="file" id="chain-file" aria-label="Файл для сверки">'
      + '<div class="chain-verdict" id="chain-verdict" hidden></div>'
      + '</div>'
      + '<div class="modal-actions">'
      + '<button class="button secondary" type="button" id="chain-cancel">Закрыть</button>'
      + '<a class="button" id="chain-explorer" href="#" rel="noopener">Открыть в обозревателе</a>'
      + '</div></div>';
    document.body.appendChild(overlay);
    setupModal(overlay, 'chain');

    var grid = document.getElementById('chain-grid');
    var verdict = document.getElementById('chain-verdict');
    var current = null;

    function row(k, v) { return '<dt>' + k + '</dt><dd>' + v + '</dd>'; }

    function open(btn) {
      current = btn.getAttribute('data-chain');
      document.getElementById('chain-title').textContent =
        'В блокчейне: ' + (btn.getAttribute('data-doc') || 'документ');
      grid.innerHTML =
        row('Документ', btn.getAttribute('data-doc') || '—')
        + row('Отпечаток документа', '<span class="chain-hash">' + current + '</span>')
        + row('Сеть', btn.getAttribute('data-net') || 'ДАО КООПЕХ Chain')
        + row('Блок', btn.getAttribute('data-block') || '—')
        + row('Записано', btn.getAttribute('data-time') || '—')
        + row('Подтверждений', btn.getAttribute('data-conf') || '—')
        + row('Подписали', btn.getAttribute('data-signers') || '—')
        + row('Что лежит в реестре',
              'Только отпечаток файла и время записи. Сам документ хранится на платформе: '
              + 'реквизиты, суммы и условия в публичный реестр не попадают.');
      verdict.hidden = true;
      verdict.textContent = '';
      var f = document.getElementById('chain-file');
      if (f) f.value = '';
      document.getElementById('chain-explorer').setAttribute('href',
        'https://explorer.example.com/tx/' + current.replace(/….*$/, ''));
      overlay.hidden = false;
    }
    function close() { overlay.hidden = true; }

    document.addEventListener('click', function (e) {
      var btn = e.target.closest('[data-chain]');
      if (btn) { e.preventDefault(); open(btn); return; }
    });
    document.getElementById('chain-close').addEventListener('click', close);
    document.getElementById('chain-cancel').addEventListener('click', close);
    overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });

    document.getElementById('chain-file').addEventListener('change', function (e) {
      var file = e.target.files && e.target.files[0];
      if (!file) return;
      verdict.hidden = false;
      verdict.className = 'chain-verdict';
      verdict.textContent = 'Считаем отпечаток…';
      if (!window.crypto || !crypto.subtle) {
        verdict.textContent = 'Браузер не умеет считать SHA-256 — сверку можно сделать только на стороне платформы.';
        return;
      }
      file.arrayBuffer().then(function (buf) {
        return crypto.subtle.digest('SHA-256', buf);
      }).then(function (digest) {
        var hex = '0x' + Array.prototype.map.call(new Uint8Array(digest), function (b) {
          return ('00' + b.toString(16)).slice(-2);
        }).join('');
        var short = hex.slice(0, 10) + '…' + hex.slice(-4);
        var same = current && (hex === current || short === current);
        verdict.className = 'chain-verdict ' + (same ? 'ok' : 'no');
        verdict.textContent = same
          ? 'Отпечаток совпал: это тот самый файл, что записан в реестре.'
          : 'Отпечаток не совпал — это другой файл или другая его версия. Посчитано: ' + short;
      }).catch(function () {
        verdict.className = 'chain-verdict no';
        verdict.textContent = 'Не удалось прочитать файл.';
      });
    });
  }


  /* ── От чьего имени я действую (идея 29) ───────────────────
     Человек бывает и физлицом, и учредителем ООО, и пайщиком кооператива.
     Раньше платформа этого не различала: любое действие выглядело как
     действие человека. Теперь контекст выбирается в шапке и виден всегда. */
  var CONTEXTS = [
    { id: 'self', name: 'Дашкевич Данил Игоревич', img: 'images/avatars/13.jpg' },
    { id: 'coop', name: 'Кооператив «Шукты»',      initial: 'Ш' },
    { id: 'ooo',  name: 'ООО «Мириталь»',          initial: 'М' },
    { id: 'fond', name: 'Фонд «Территория 2020»',  initial: 'Т' }
  ];
  function initContext() {
    var right = document.querySelector('.topbar-right');
    if (!right) return;
    var cur = 'self';
    try { cur = localStorage.getItem('cooptech_ctx') || 'self'; } catch (e) {}
    function ctx(id) {
      for (var i = 0; i < CONTEXTS.length; i++) if (CONTEXTS[i].id === id) return CONTEXTS[i];
      return CONTEXTS[0];
    }
    var wrap = document.createElement('div');
    wrap.className = 'ctx-wrap';
    var btn = document.createElement('button');
    btn.className = 'ctx-switch';
    btn.type = 'button';
    btn.setAttribute('aria-haspopup', 'true');
    btn.setAttribute('aria-expanded', 'false');
    var menu = document.createElement('div');
    menu.className = 'ctx-menu';
    menu.hidden = true;
    menu.setAttribute('role', 'menu');
    menu.setAttribute('aria-label', 'От чьего имени действовать');

    /* Иконка аккаунта — она же указатель контекста: у физлица фото,
       у организации инициал. Кем человек действует, видно без подписи. */
    function label() {
      var c = ctx(cur);
      btn.innerHTML = c.img
        ? '<img class="ctx-avatar" src="' + c.img + '" alt="">'
        : '<span class="ctx-avatar ctx-initial">' + c.initial + '</span>';
      btn.setAttribute('title', c.name);
      btn.setAttribute('aria-label', 'Аккаунт: ' + c.name);
    }
    function draw() {
      menu.innerHTML = CONTEXTS.map(function (c) {
        return '<button type="button" role="menuitem" data-ctx="' + c.id + '"'
          + (c.id === cur ? ' aria-current="true"' : '') + '>'
          + (c.img ? '<img class="ctx-avatar" src="' + c.img + '" alt="">'
                   : '<span class="ctx-avatar ctx-initial">' + c.initial + '</span>')
          + '<span>' + c.name + '</span></button>';
      }).join('');
    }
    function close() { menu.hidden = true; btn.setAttribute('aria-expanded', 'false'); }

    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      menu.hidden = !menu.hidden;
      btn.setAttribute('aria-expanded', menu.hidden ? 'false' : 'true');
    });
    menu.addEventListener('click', function (e) {
      var b = e.target.closest('[data-ctx]');
      if (!b) return;
      cur = b.getAttribute('data-ctx');
      try { localStorage.setItem('cooptech_ctx', cur); } catch (err) {}
      label(); draw(); close();
    });
    document.addEventListener('click', function (e) {
      if (!wrap.contains(e.target)) close();
    });
    document.addEventListener('keydown', function (e) {
      if ((e.key === 'Escape' || e.keyCode === 27) && !menu.hidden) { close(); btn.focus(); }
    });

    label(); draw();
    wrap.appendChild(btn);
    wrap.appendChild(menu);
    /* Место иконки — в конце шапки, рядом с выходом: там её и ищут */
    var exit = right.querySelector('a[href="index.html"], a[href="login.html"]');
    if (exit) right.insertBefore(wrap, exit); else right.appendChild(wrap);
  }


  /* ── Постраничный просмотр каталогов ───────────────────────
     В каталогах по сотне объектов, показывать их одной лентой — значит
     заставить человека крутить экран минуту. Показываем по 20 и даём
     перелистывание.

     Как это уживается с фильтрами: фильтры на страницах прячут карточки
     через свойство hidden, поэтому страница считается только по тем, что
     фильтр оставил. Сам листатель прячет лишнее классом pager-off — так две
     механики не спорят друг с другом и не зацикливаются. */
  var PAGE_SIZE = 20;
  /* #deal-list сюда не входит: у реестра сделок свой листатель, встроенный
     в его фильтры, — второй поверх него только мешал бы. */
  var GRIDS = ['#people-grid', '#resumes-list', '#vacancies-list', '#projects-grid',
               '#orgs-grid', '#resources-grid', '#groups-grid',
               '#cfa-list', '#nma-list'];

  function setupPager(box) {
    if (box.__pager) return;
    box.__pager = true;
    var page = 1;

    var nav = document.createElement('nav');
    nav.className = 'pager';
    nav.setAttribute('aria-label', 'Страницы каталога');
    box.parentNode.insertBefore(nav, box.nextSibling);

    function items() {
      return Array.prototype.filter.call(box.children, function (el) {
        return el.nodeType === 1 && !el.classList.contains('pager-off') ? true : el.nodeType === 1;
      });
    }
    /* «Живые» — те, что не спрятаны фильтром страницы */
    function live() {
      return Array.prototype.filter.call(box.children, function (el) {
        if (el.nodeType !== 1) return false;
        if (el.hasAttribute('hidden')) return false;
        if (el.style && el.style.display === 'none') return false;
        return true;
      });
    }

    function render() {
      var list = live();
      var pages = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
      if (page > pages) page = pages;
      var from = (page - 1) * PAGE_SIZE;
      var to = from + PAGE_SIZE;
      list.forEach(function (el, i) {
        el.classList.toggle('pager-off', i < from || i >= to);
      });

      if (list.length <= PAGE_SIZE) { nav.innerHTML = ''; return; }

      var html = '<span class="pager-info">Показано ' + (from + 1) + '–'
        + Math.min(to, list.length) + ' из ' + list.length + '</span>'
        + '<button type="button" class="pager-btn" data-go="prev"'
        + (page === 1 ? ' disabled' : '') + '>Назад</button>';

      var nums = [];
      for (var p = 1; p <= pages; p++) {
        if (p === 1 || p === pages || Math.abs(p - page) <= 1) nums.push(p);
        else if (nums[nums.length - 1] !== '…') nums.push('…');
      }
      nums.forEach(function (p) {
        html += p === '…'
          ? '<span class="pager-gap">…</span>'
          : '<button type="button" class="pager-btn pager-num' + (p === page ? ' active' : '')
            + '" data-go="' + p + '"' + (p === page ? ' aria-current="page"' : '') + '>' + p + '</button>';
      });
      html += '<button type="button" class="pager-btn" data-go="next"'
        + (page === pages ? ' disabled' : '') + '>Вперёд</button>';
      nav.innerHTML = html;
    }

    nav.addEventListener('click', function (e) {
      var b = e.target.closest('[data-go]');
      if (!b) return;
      var go = b.getAttribute('data-go');
      var pages = Math.max(1, Math.ceil(live().length / PAGE_SIZE));
      if (go === 'prev') page = Math.max(1, page - 1);
      else if (go === 'next') page = Math.min(pages, page + 1);
      else page = parseInt(go, 10);
      render();
      var top = box.getBoundingClientRect().top + window.scrollY - 90;
      window.scrollTo({ top: top, behavior: 'smooth' });
    });

    /* Фильтр отработал — пересобираем страницы и возвращаемся на первую */
    var timer = null;
    new MutationObserver(function (recs) {
      var byFilter = recs.some(function (r) {
        return r.type === 'childList'
          || (r.type === 'attributes' && r.attributeName !== 'class');
      });
      if (!byFilter) return;
      clearTimeout(timer);
      timer = setTimeout(function () { page = 1; render(); }, 30);
    }).observe(box, { childList: true, subtree: true, attributes: true,
                      attributeFilter: ['hidden', 'style'] });

    render();
  }

  function initPager() {
    GRIDS.forEach(function (sel) {
      var box = document.querySelector(sel);
      if (box) setupPager(box);
    });
  }


  /* ── Сколько карточек показывать в полке каталога ──────────
     Плитка «Смотреть все» стоит последней в той же сетке. Если карточек
     ровно столько, что плитка не помещается в строку, она съезжает вниз
     одна — полка выглядит оборванной. Сколько плиток влезает в строку,
     зависит от ширины экрана, поэтому число не зашито в разметку: строка
     измеряется по факту, и полка обрезается так, чтобы «Смотреть все»
     закрывала последнюю строку. Четыре карточки не показываем никогда —
     это тот самый случай, с которого началась правка. */
  function fitShelves() {
    document.querySelectorAll('.shelf-row').forEach(function (shelf) {
      var grid = shelf.querySelector('.ptile-grid, .vacancy-list');
      if (!grid) return;
      var kids = Array.prototype.filter.call(grid.children, function (el) { return el.nodeType === 1; });
      kids.forEach(function (el) { el.classList.remove('shelf-off'); });

      var tile = null, cards = [];
      kids.forEach(function (el) {
        if (/view-all/.test(el.className)) tile = el; else cards.push(el);
      });
      if (cards.length < 2) return;

      /* ёмкость строки — по позициям плиток после сброса */
      var tops = {};
      kids.forEach(function (el) {
        var t = Math.round(el.getBoundingClientRect().top);
        tops[t] = (tops[t] || 0) + 1;
      });
      var perRow = tops[Object.keys(tops)[0]] || 4;
      if (perRow < 2) return;

      var target = perRow - (tile ? 1 : 0);          /* одна полная строка */
      while (target + perRow <= cards.length) target += perRow;
      /* Больше семи карточек в полке — уже не витрина, а стена: обрезаем
         на целую строку назад, пока не уложимся в семь. */
      while (target > 7) target -= perRow;
      if (target === 4) target = 3;                 /* четвёрку не показываем */
      if (target > cards.length) target = (cards.length === 4) ? 3 : cards.length;
      if (target < 1) target = Math.min(cards.length, 3);

      cards.forEach(function (el, i) { el.classList.toggle('shelf-off', i >= target); });
    });
  }

  function initShelfFit() {
    var host = document.querySelector('[id$="-home"], .main');
    if (!host) return;
    var timer = null;
    var schedule = function () { clearTimeout(timer); timer = setTimeout(fitShelves, 60); };
    new MutationObserver(schedule).observe(host, { childList: true, subtree: true });
    window.addEventListener('resize', schedule);
    schedule();
  }


  /* ============================================================
     Состояния экрана: озвучивание, подтверждение действия, тост.
     Разметку компонентов см. в styles.css и theme.css.
     ============================================================ */

  /* Живые области создаются пустыми и заранее: если вставить область вместе
     с текстом, часть программ чтения с экрана ничего не прочитает. */
  function initLive() {
    if (document.getElementById('live-polite')) return;
    ['polite', 'alert'].forEach(function (kind) {
      var el = document.createElement('div');
      el.id = 'live-' + kind;
      el.className = 'live-region';
      el.setAttribute('role', kind === 'alert' ? 'alert' : 'status');
      el.setAttribute('aria-live', kind === 'alert' ? 'assertive' : 'polite');
      el.setAttribute('aria-atomic', 'true');
      document.body.appendChild(el);
    });
  }

  /* Говорит вслух для тех, кто не видит экрана. Только о завершённых
     изменениях: не на каждый символ в поиске и не на наведение мыши. */
  function say(text, urgent) {
    var el = document.getElementById(urgent ? 'live-alert' : 'live-polite');
    if (!el) return;
    el.textContent = '';
    setTimeout(function () { el.textContent = text; }, 50);
  }

  /* Тост — для действий, ради которых не стоит спрашивать заранее:
     избранное, подписка, снятие с публикации. Отмена вместо вопроса. */
  var toastTimer = null;
  function toast(text, undo) {
    var el = document.querySelector('.toast.shared-toast');
    if (!el) {
      el = document.createElement('div');
      el.className = 'toast shared-toast';
      document.body.appendChild(el);
    }
    el.innerHTML = '';
    el.appendChild(document.createTextNode(text));
    if (undo) {
      var btn = document.createElement('button');
      btn.className = 'toast-undo';
      btn.type = 'button';
      btn.textContent = 'Отменить';
      btn.addEventListener('click', function () {
        el.classList.remove('show');
        undo();
        say('Действие отменено');
      });
      el.appendChild(btn);
    }
    el.classList.add('show');
    say(text);
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { el.classList.remove('show'); }, undo ? 7000 : 4000);
  }

  /* Один диалог подтверждения на весь прототип. Страницы объявляют намерение
     атрибутами, разметку не пишут:

       data-confirm      — заголовок вопроса (наличие атрибута включает диалог)
       data-confirm-text — пояснение: что произойдёт и можно ли откатить
       data-confirm-ok   — подпись кнопки согласия
       data-confirm-word — необратимое: требует ввести это слово
       data-confirm-done — текст тоста после подтверждения

     Подтверждаем то, что меняет обязательства: приёмку, отзыв подтверждения,
     отмену сделки, спор, отклик, заявление в пайщики, выход из кооператива,
     взаимозачёт. Для обратимого — тост с отменой, а не вопрос. */
  function initConfirm() {
    var triggers = document.querySelectorAll('[data-confirm]');
    if (!triggers.length) return;

    var overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.id = 'confirm-modal';
    overlay.hidden = true;
    overlay.innerHTML =
      '<div class="modal">' +
        '<div class="modal-head"><h2 id="confirm-title"></h2>' +
        '<button class="modal-close" type="button" aria-label="Закрыть">✕</button></div>' +
        '<p class="modal-hint" id="confirm-text"></p>' +
        '<div class="field" id="confirm-word-field" hidden>' +
          '<label class="label" for="confirm-word"></label>' +
          '<input class="input" id="confirm-word" type="text" autocomplete="off">' +
        '</div>' +
        '<div class="modal-actions">' +
          '<button class="button secondary" type="button" data-focus-first id="confirm-cancel">Отмена</button>' +
          '<button class="button" type="button" id="confirm-ok">Подтвердить</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(overlay);

    var title = overlay.querySelector('#confirm-title');
    var text = overlay.querySelector('#confirm-text');
    var wordField = overlay.querySelector('#confirm-word-field');
    var wordLabel = wordField.querySelector('label');
    var wordInput = overlay.querySelector('#confirm-word');
    var okBtn = overlay.querySelector('#confirm-ok');
    var current = null;

    function close() {
      overlay.hidden = true;
      current = null;
    }
    overlay.querySelector('.modal-close').addEventListener('click', close);
    overlay.querySelector('#confirm-cancel').addEventListener('click', close);
    overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });

    wordInput.addEventListener('input', function () {
      var need = current && current.getAttribute('data-confirm-word');
      okBtn.disabled = !!need && wordInput.value.trim().toLowerCase() !== need.toLowerCase();
    });

    okBtn.addEventListener('click', function () {
      var trigger = current;
      close();
      if (!trigger) return;
      var done = trigger.getAttribute('data-confirm-done');
      if (done) toast(done);
      /* Страница может перехватить событие и сделать своё; если никто не
         перехватил, а кнопка была ссылкой — переходим по ней. */
      var ev = new CustomEvent('coop:confirmed', { bubbles: true, cancelable: true });
      var proceed = trigger.dispatchEvent(ev);
      if (proceed && trigger.tagName === 'A' && trigger.getAttribute('href')) {
        location.href = trigger.getAttribute('href');
      }
    });

    for (var i = 0; i < triggers.length; i++) {
      triggers[i].addEventListener('click', function (e) {
        e.preventDefault();
        current = e.currentTarget;
        title.textContent = current.getAttribute('data-confirm') || 'Подтвердите действие';
        text.textContent = current.getAttribute('data-confirm-text') || '';
        text.hidden = !text.textContent;
        okBtn.textContent = current.getAttribute('data-confirm-ok') || 'Подтвердить';
        okBtn.className = 'button' + (current.classList.contains('danger') ? ' danger' : '');
        var word = current.getAttribute('data-confirm-word');
        wordField.hidden = !word;
        wordInput.value = '';
        okBtn.disabled = !!word;
        if (word) wordLabel.innerHTML = 'Введите «' + word + '», чтобы подтвердить';
        overlay.hidden = false;
      });
    }
    setupModal(overlay, 'confirm');
    /* Роль ставится после setupModal: тот назначает обычный dialog, а вопрос
       о необратимом действии — это alertdialog, его читают настойчивее. */
    overlay.querySelector('.modal').setAttribute('role', 'alertdialog');
    overlay.querySelector('.modal').setAttribute('aria-describedby', 'confirm-text');
  }

  window.Coop = window.Coop || {};
  window.Coop.say = say;
  window.Coop.toast = toast;

  /* Ошибка поля: раньше это был просто <div>, который программа чтения с
     экрана не озвучивала и не связывала с полем — человек слышал название
     поля и не слышал причину отказа. Здесь связь проставляется один раз для
     всех форм сразу, а `aria-invalid` едет следом за классом .invalid,
     который страницы уже переключают своими скриптами. */
  function initFieldErrors() {
    var errors = document.querySelectorAll('.field-error');
    var seq = 0;
    for (var i = 0; i < errors.length; i++) {
      var err = errors[i];
      if (!err.id) err.id = 'field-error-' + (++seq);
      err.setAttribute('role', 'alert');
      var field = err.closest ? err.closest('.field') : null;
      if (!field) field = err.parentElement;
      if (!field) continue;
      var controls = field.querySelectorAll('input, select, textarea');
      for (var c = 0; c < controls.length; c++) {
        var had = controls[c].getAttribute('aria-describedby');
        if (!had || had.indexOf(err.id) === -1) {
          controls[c].setAttribute('aria-describedby', had ? had + ' ' + err.id : err.id);
        }
      }
      watchInvalid(field);
    }
  }

  function watchInvalid(field) {
    var apply = function () {
      var bad = field.classList.contains('invalid');
      var controls = field.querySelectorAll('input, select, textarea');
      for (var c = 0; c < controls.length; c++) {
        controls[c].setAttribute('aria-invalid', bad ? 'true' : 'false');
      }
    };
    apply();
    new MutationObserver(apply).observe(field, { attributes: true, attributeFilter: ['class'] });
  }

  function init() {
    initLive();
    initConfirm();
    initFieldErrors();
    var right = document.querySelector('.topbar-right');
    if (right) right.insertBefore(buildToggle(), right.firstChild);

    /* 2. Иконки в меню + кнопка «Добавить» + «+» у расширений */
    var sidebar = document.querySelector('.sidebar');
    if (sidebar) {
      var links = sidebar.querySelectorAll('nav a[data-icon]');
      for (var i = 0; i < links.length; i++) {
        var key = links[i].getAttribute('data-icon');
        if (NAV_ICONS[key]) {
          var s = document.createElement('span');
          s.className = 'nav-ico';
          s.innerHTML = ico(NAV_ICONS[key]);
          links[i].insertBefore(s, links[i].firstChild);
        }
      }
      var add = document.createElement('button');
      add.className = 'sb-add';
      add.type = 'button';
      add.innerHTML = I.plus + 'Добавить';
      add.addEventListener('click', function () { location.href = 'add-resource.html'; });
      sidebar.insertBefore(add, sidebar.firstChild);

      var extTitle = sidebar.querySelector('.ext-title');
      if (extTitle && !extTitle.querySelector('.ext-add')) {
        var ea = document.createElement('button');
        ea.className = 'ext-add';
        ea.type = 'button';
        ea.title = 'Подключить расширение';
        ea.innerHTML = I.plus;
        ea.setAttribute('aria-label', 'Каталог расширений');
        ea.addEventListener('click', function (e) { e.preventDefault(); location.href = 'extensions.html'; });
        extTitle.appendChild(ea);
      }
    }

    /* 3. Бургер и затемнение для мобильного меню */
    var left = document.querySelector('.topbar-left');
    if (left && sidebar) {
      var burger = document.createElement('button');
      burger.className = 'burger';
      burger.type = 'button';
      burger.setAttribute('aria-label', 'Меню');
      burger.setAttribute('aria-expanded', 'false');
      if (sidebar.id) burger.setAttribute('aria-controls', sidebar.id);
      burger.innerHTML = I.burger;
      burger.addEventListener('click', function () {
        var open = document.documentElement.classList.toggle('sidebar-open');
        burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
      left.insertBefore(burger, left.firstChild);

      var scrim = document.createElement('div');
      scrim.className = 'sidebar-scrim';
      scrim.setAttribute('aria-hidden', 'true');
      scrim.addEventListener('click', function () {
        document.documentElement.classList.remove('sidebar-open');
        burger.setAttribute('aria-expanded', 'false');
      });
      document.body.appendChild(scrim);
    }

    /* 3.1 Поиск и аккаунт на мобильном.
       Под 900px строка поиска и ссылки «настройки»/«выйти» в шапке скрыты, и
       замены им не было: с телефона нельзя было ни искать, ни выйти из аккаунта.
       Поиск раскрывается отдельной строкой под шапкой по кнопке-лупе,
       ссылки аккаунта дублируются в выдвижное меню. */
    var search = right ? right.querySelector('.topbar-search') : null;
    if (search) {
      var sbtn = document.createElement('button');
      sbtn.className = 'search-btn';
      sbtn.type = 'button';
      sbtn.setAttribute('aria-label', 'Поиск по платформе');
      sbtn.setAttribute('aria-expanded', 'false');
      if (!search.id) search.id = 'topbar-search';
      sbtn.setAttribute('aria-controls', search.id);
      sbtn.innerHTML = I.search;
      function setSearch(open) {
        document.documentElement.classList.toggle('search-open', open);
        sbtn.setAttribute('aria-expanded', open ? 'true' : 'false');
        if (open) search.focus();
      }
      sbtn.addEventListener('click', function () {
        setSearch(!document.documentElement.classList.contains('search-open'));
      });
      search.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' || e.keyCode === 27) { setSearch(false); sbtn.focus(); }
      });
      right.insertBefore(sbtn, right.firstChild);
    }

    if (sidebar && right) {
      /* Колокольчик не дублируем: он и на мобильном остаётся в шапке */
      var accLinks = right.querySelectorAll('a:not(.topbar-bell)');
      if (accLinks.length) {
        var acc = document.createElement('div');
        acc.className = 'sidebar-account';
        var accTitle = document.createElement('div');
        accTitle.className = 'ext-title';
        accTitle.textContent = 'Аккаунт';
        acc.appendChild(accTitle);
        var accNav = document.createElement('nav');
        for (var k = 0; k < accLinks.length; k++) {
          var copy = accLinks[k].cloneNode(true);
          var href = copy.getAttribute('href') || '';
          /* В шапке эти ссылки — только иконки; в выдвижном меню нужна подпись.
             Берём её из aria-label и выкидываем скопированную из шапки svg. */
          copy.textContent = copy.getAttribute('aria-label') || copy.textContent;
          copy.removeAttribute('aria-label');
          copy.removeAttribute('title');
          copy.removeAttribute('class');
          var ic = document.createElement('span');
          ic.className = 'nav-ico';
          /* Иконку выбираем по адресу ссылки, а не по её тексту: переименование
             подписи не должно молча ломать иконку. */
          ic.innerHTML = ico(href.indexOf('settings') >= 0 ? I.gearPath : I.exitPath);
          copy.insertBefore(ic, copy.firstChild);
          accNav.appendChild(copy);
        }
        acc.appendChild(accNav);
        sidebar.appendChild(acc);
      }
    }

    /* 4. Лист фильтров на мобильном */
    var panel = document.querySelector('.filter-panel');
    if (panel) {
      if (!panel.id) panel.id = 'filter-panel';
      var fscrim = document.createElement('div');
      fscrim.className = 'filter-scrim';
      fscrim.setAttribute('aria-hidden', 'true');
      fscrim.addEventListener('click', function () {
        document.documentElement.classList.remove('filters-open');
        fb.setAttribute('aria-expanded', 'false');
      });
      document.body.appendChild(fscrim);

      var host = document.querySelector('.search-row') || document.querySelector('.main');
      var fb = document.createElement('button');
      fb.className = 'filter-sheet-btn';
      fb.type = 'button';
      fb.setAttribute('aria-expanded', 'false');
      fb.setAttribute('aria-controls', panel.id);
      fb.innerHTML = I.filter + 'Фильтр';
      fb.addEventListener('click', function () {
        document.documentElement.classList.add('filters-open');
        fb.setAttribute('aria-expanded', 'true');
      });
      if (host === panel.parentNode) host.insertBefore(fb, panel);
      else if (host) host.appendChild(fb);

      var apply = document.createElement('button');
      apply.className = 'button';
      apply.type = 'button';
      apply.style.cssText = 'width:100%;margin-top:16px';
      apply.textContent = 'Показать результаты';
      apply.addEventListener('click', function () {
        document.documentElement.classList.remove('filters-open');
        fb.setAttribute('aria-expanded', 'false');
      });
      panel.appendChild(apply);
    }

    /* 5. Нижняя таб-панель */
    var TABS = [
      ['my-page.html', 'Моя страница', NAV_ICONS['my-page']],
      ['messages.html', 'Сообщения', NAV_ICONS['messages']],
      ['resources.html', 'Ресурсы', NAV_ICONS['resources']],
      ['projects.html', 'Проекты', NAV_ICONS['projects']],
      ['wallet.html', 'Кошелёк', NAV_ICONS['wallet']]
    ];
    var page = location.pathname.split('/').pop() || 'index.html';
    if (document.querySelector('.layout')) {
      var bar = document.createElement('nav');
      bar.className = 'mobile-tabbar';
      bar.setAttribute('aria-label', 'Быстрые разделы');
      var html = '';
      for (var k = 0; k < TABS.length; k++) {
        html += '<a href="' + TABS[k][0] + '"' + (page === TABS[k][0] ? ' class="active"' : '') + '>'
          + ico(TABS[k][2], 21) + '<span>' + TABS[k][1] + '</span></a>';
      }
      bar.innerHTML = html;
      document.body.appendChild(bar);
    }

    /* 5.2 Избранное — сердечки на карточках и вкладка «Избранное» */
    favorites();

    /* 5.1 Доступность: имена для кнопок-иконок, состояние переключателей,
       семантика и поведение модальных окон. Делается здесь, в общем слое,
       чтобы не размазывать одни и те же атрибуты по 59 страницам. */
    a11y();
    initChain();
    initContext();
    initPager();
    initShelfFit();

    /* 6. Эмодзи → SVG */
    var BLOCK_SEL = '.cat-icon, .out-icon, .f-icon, .thumb, .cat-icon.line-icon';
    var blocks = document.querySelectorAll(BLOCK_SEL);
    for (var n = 0; n < blocks.length; n++) {
      var t = blocks[n].textContent.trim();
      if (t && EMOJI_ICONS[t]) {
        blocks[n].innerHTML = ico(EMOJI_ICONS[t], 34);
        blocks[n].style.cssText += ';color:var(--teal-dark);display:flex;align-items:center;justify-content:center';
      }
    }

    /* Инлайновые подписи: эмодзи меняем на SVG перед текстом */
    var INLINE_SEL = '.loc-bar, .type-badge, .promo-badge, .saved-search-badge, .chip, .badge,'
      + ' .quick-chip, .cat-label, .out-label, .saved-search-item-label, .cat-status,'
      + ' .vacancy-tags .chip, .gb-category, .feature-card .f-title, .usecase-kicker';
    var inline = document.querySelectorAll(INLINE_SEL);
    var EMOJI_RE = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}]\u{FE0F}?/gu;
    for (var m = 0; m < inline.length; m++) {
      var el = inline[m];
      if (el.querySelector('svg')) continue;
      var raw = el.innerHTML;
      if (!EMOJI_RE.test(raw)) continue;
      EMOJI_RE.lastIndex = 0;
      var out = raw.replace(EMOJI_RE, function (ch) {
        var key = ch.replace('\uFE0F', '');
        if (EMOJI_ICONS[key]) return '<span class="ico">' + ico(EMOJI_ICONS[key], 13) + '</span>';
        return '';
      });
      el.innerHTML = out;
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
