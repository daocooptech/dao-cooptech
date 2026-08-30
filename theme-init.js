/* Установка темы ДО первой отрисовки.
   Подключается синхронно в <head> — иначе страница успевает мигнуть светлым
   фоном, прежде чем app.js (он в конце <body>) применит тёмную тему.

   Порядок приоритетов:
   1) выбор пользователя, сохранённый в localStorage ('dark' / 'light');
   2) если выбора не было — системная настройка prefers-color-scheme;
   3) если и её нет — светлая тема.

   Пока пользователь не нажимал переключатель, страница следует за системой
   и переключается вместе с ней на лету. */
(function () {
  var saved = null;
  try { saved = localStorage.getItem('cooptech_theme'); } catch (e) {}

  function apply(mode) {
    if (mode === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
    else document.documentElement.setAttribute('data-theme', 'light');
  }

  var mq = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
  apply(saved || (mq && mq.matches ? 'dark' : 'light'));

  /* Системная тема сменилась — идём за ней, но только если своего выбора нет */
  if (mq) {
    var onChange = function (e) {
      var choice = null;
      try { choice = localStorage.getItem('cooptech_theme'); } catch (err) {}
      if (!choice) apply(e.matches ? 'dark' : 'light');
    };
    if (mq.addEventListener) mq.addEventListener('change', onChange);
    else if (mq.addListener) mq.addListener(onChange);
  }
})();
