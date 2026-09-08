/* Закупки, написанные вручную. Отсюда их берёт tools/gen-group-buys.py,
   чтобы повторный запуск их не потерял. Правь здесь. */
window.GROUP_BUYS_MANUAL = [{
      id: 'cement',
      title: 'Цемент М500 навалом',
      image: 'images/photos/cement-bag.jpg',
      category: 'Для дома и дачи · стройматериалы',
      organizer: { name: 'Дашкевич Данил Игоревич', avatar: 'images/avatars/13.jpg', link: 'person.html' },
      supplier: 'ООО «Мириталь»',
      unit: 'тонна',
      collected: 27,
      goal: 40,
      participants: 14,
      stopDate: '25 августа 2026',
      pickupPoint: 'Цех кооператива, Тюмень',
      pickupLink: 'pickup-points.html',
      tiers: [
        { upTo: 10, price: 12000, label: 'до 10 т' },
        { upTo: 25, price: 10500, label: '10–25 т' },
        { upTo: Infinity, price: 9200, label: '25 т и больше' }
      ]
    },
    {
      id: 'kidswear',
      title: 'Детские зимние комбинезоны',
      image: 'images/photos/warehouse.jpg',
      category: 'Личные вещи · товары для детей',
      organizer: { name: 'Кузнецова Дарья Викторовна', avatar: 'images/avatars/16.jpg', link: 'person.html' },
      supplier: 'Фабрика «Kids Warm»',
      unit: 'шт.',
      collected: 42,
      goal: 60,
      participants: 31,
      stopDate: '22 августа 2026',
      pickupPoint: 'Точка выдачи — Центральный рынок, Тюмень',
      pickupLink: 'pickup-points.html',
      tiers: [
        { upTo: 30, price: 3200, label: 'до 30 шт.' },
        { upTo: 60, price: 2850, label: '30–60 шт.' },
        { upTo: Infinity, price: 2500, label: '60 шт. и больше' }
      ]
    },
    {
      id: 'seeds',
      title: 'Семена и рассада для теплиц',
      image: 'images/photos/carrot.jpg',
      category: 'Сельское хозяйство и еда',
      organizer: { name: 'Лебедева Ольга Игоревна', avatar: 'images/avatars/10.jpg', link: 'person.html' },
      supplier: 'Агрофирма «Седек»',
      unit: 'набор',
      collected: 18,
      goal: 50,
      participants: 12,
      stopDate: '1 сентября 2026',
      pickupPoint: 'Склад ООО «АгроСтрой», Пермь',
      pickupLink: 'pickup-points.html',
      tiers: [
        { upTo: 20, price: 890, label: 'до 20 наборов' },
        { upTo: 50, price: 690, label: '20–50 наборов' },
        { upTo: Infinity, price: 540, label: '50 наборов и больше' }
      ]
    }
];
