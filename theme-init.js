/* Установка темы ДО первой отрисовки.
   Подключается синхронно в <head> — иначе страница успевает мигнуть светлым
   фоном, прежде чем app.js (он в конце <body>) применит тёмную тему.

   Порядок приоритетов:
   1) выбор пользователя, сохранённый в localStorage ('dark' / 'light');
   2) если выбора не было — светлая тема по умолчанию (системная
      prefers-color-scheme не учитывается — см. решение владельца). */
(function () {
  var saved = null;
  try { saved = localStorage.getItem('cooptech_theme'); } catch (e) {}

  document.documentElement.setAttribute('data-theme', saved === 'dark' ? 'dark' : 'light');
})();
