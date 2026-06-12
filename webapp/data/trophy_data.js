const TROPHY_PATHS = [
  {
    id: 1, team: "Франция", flag: "🇫🇷", year: 1998,
    aliases: ["франция", "france"],
    path: [
      { round: "1/8 финала", result: "✅", opponent: "Парагвай", score: "1:0 (д.в.)" },
      { round: "1/4 финала", result: "✅", opponent: "Италия", score: "0:0 (пен 4:3)" },
      { round: "1/2 финала", result: "✅", opponent: "Хорватия", score: "2:1" },
      { round: "Финал 🏆",   result: "🥇", opponent: "Бразилия", score: "3:0" },
    ]
  },
  {
    id: 2, team: "Бразилия", flag: "🇧🇷", year: 2002,
    aliases: ["бразилия", "brazil", "brasil"],
    path: [
      { round: "1/8 финала", result: "✅", opponent: "Бельгия", score: "2:0" },
      { round: "1/4 финала", result: "✅", opponent: "Англия", score: "2:1" },
      { round: "1/2 финала", result: "✅", opponent: "Турция", score: "1:0" },
      { round: "Финал 🏆",   result: "🥇", opponent: "Германия", score: "2:0" },
    ]
  },
  {
    id: 3, team: "Италия", flag: "🇮🇹", year: 2006,
    aliases: ["италия", "italy", "адзурри"],
    path: [
      { round: "1/8 финала", result: "✅", opponent: "Австралия", score: "1:0" },
      { round: "1/4 финала", result: "✅", opponent: "Украина", score: "3:0" },
      { round: "1/2 финала", result: "✅", opponent: "Германия", score: "2:0 (д.в.)" },
      { round: "Финал 🏆",   result: "🥇", opponent: "Франция", score: "1:1 (пен 5:3)" },
    ]
  },
  {
    id: 4, team: "Испания", flag: "🇪🇸", year: 2010,
    aliases: ["испания", "spain", "ла роха"],
    path: [
      { round: "1/8 финала", result: "✅", opponent: "Португалия", score: "1:0" },
      { round: "1/4 финала", result: "✅", opponent: "Парагвай", score: "1:0" },
      { round: "1/2 финала", result: "✅", opponent: "Германия", score: "1:0" },
      { round: "Финал 🏆",   result: "🥇", opponent: "Нидерланды", score: "1:0 (д.в.)" },
    ]
  },
  {
    id: 5, team: "Германия", flag: "🇩🇪", year: 2014,
    aliases: ["германия", "germany", "бундестим"],
    path: [
      { round: "1/8 финала", result: "✅", opponent: "Алжир", score: "2:1 (д.в.)" },
      { round: "1/4 финала", result: "✅", opponent: "Франция", score: "1:0" },
      { round: "1/2 финала", result: "✅", opponent: "Бразилия", score: "7:1" },
      { round: "Финал 🏆",   result: "🥇", opponent: "Аргентина", score: "1:0 (д.в.)" },
    ]
  },
  {
    id: 6, team: "Франция", flag: "🇫🇷", year: 2018,
    aliases: ["франция", "france"],
    path: [
      { round: "1/8 финала", result: "✅", opponent: "Аргентина", score: "4:3" },
      { round: "1/4 финала", result: "✅", opponent: "Уругвай", score: "2:0" },
      { round: "1/2 финала", result: "✅", opponent: "Бельгия", score: "1:0" },
      { round: "Финал 🏆",   result: "🥇", opponent: "Хорватия", score: "4:2" },
    ]
  },
  {
    id: 7, team: "Аргентина", flag: "🇦🇷", year: 2022,
    aliases: ["аргентина", "argentina", "альбиселесте"],
    path: [
      { round: "1/8 финала", result: "✅", opponent: "Австралия", score: "2:1" },
      { round: "1/4 финала", result: "✅", opponent: "Нидерланды", score: "2:2 (пен 4:3)" },
      { round: "1/2 финала", result: "✅", opponent: "Хорватия", score: "3:0" },
      { round: "Финал 🏆",   result: "🥇", opponent: "Франция", score: "3:3 (пен 4:2)" },
    ]
  },
  {
    id: 8, team: "Бразилия", flag: "🇧🇷", year: 1994,
    aliases: ["бразилия", "brazil", "brasil"],
    path: [
      { round: "1/8 финала", result: "✅", opponent: "США", score: "1:0" },
      { round: "1/4 финала", result: "✅", opponent: "Нидерланды", score: "3:2" },
      { round: "1/2 финала", result: "✅", opponent: "Швеция", score: "1:0" },
      { round: "Финал 🏆",   result: "🥇", opponent: "Италия", score: "0:0 (пен 3:2)" },
    ]
  },
  {
    id: 9, team: "Германия", flag: "🇩🇪", year: 1990,
    aliases: ["германия", "germany", "зап германия", "зфг"],
    path: [
      { round: "1/8 финала", result: "✅", opponent: "Нидерланды", score: "2:1" },
      { round: "1/4 финала", result: "✅", opponent: "Чехословакия", score: "1:0" },
      { round: "1/2 финала", result: "✅", opponent: "Англия", score: "1:1 (пен 4:3)" },
      { round: "Финал 🏆",   result: "🥇", opponent: "Аргентина", score: "1:0" },
    ]
  },
  {
    id: 10, team: "Хорватия", flag: "🇭🇷", year: 2018,
    aliases: ["хорватия", "croatia", "ватрени"],
    path: [
      { round: "1/8 финала", result: "✅", opponent: "Дания", score: "1:1 (пен 3:2)" },
      { round: "1/4 финала", result: "✅", opponent: "Россия", score: "2:2 (пен 4:3)" },
      { round: "1/2 финала", result: "✅", opponent: "Англия", score: "2:1 (д.в.)" },
      { round: "Финал 🥈",   result: "🥈", opponent: "Франция", score: "2:4" },
    ]
  },
  {
    id: 11, team: "Нидерланды", flag: "🇳🇱", year: 2010,
    aliases: ["нидерланды", "netherlands", "голландия"],
    path: [
      { round: "1/8 финала", result: "✅", opponent: "Словакия", score: "2:1" },
      { round: "1/4 финала", result: "✅", opponent: "Бразилия", score: "2:1" },
      { round: "1/2 финала", result: "✅", opponent: "Уругвай", score: "3:2" },
      { round: "Финал 🥈",   result: "🥈", opponent: "Испания", score: "0:1 (д.в.)" },
    ]
  },
  {
    id: 12, team: "Португалия", flag: "🇵🇹", year: 2006,
    aliases: ["португалия", "portugal", "навигаторы"],
    path: [
      { round: "1/8 финала", result: "✅", opponent: "Нидерланды", score: "1:0" },
      { round: "1/4 финала", result: "✅", opponent: "Англия", score: "0:0 (пен 3:1)" },
      { round: "1/2 финала", result: "❌", opponent: "Франция", score: "0:1" },
      { round: "Матч за 3-е место 🥉", result: "🥉", opponent: "Хозяин — Германия", score: "2:3" },
    ]
  },
  {
    id: 13, team: "Уругвай", flag: "🇺🇾", year: 2010,
    aliases: ["уругвай", "uruguay", "небесные", "целесте"],
    path: [
      { round: "1/8 финала", result: "✅", opponent: "Южная Корея", score: "2:1" },
      { round: "1/4 финала", result: "✅", opponent: "Гана", score: "1:1 (пен 4:2)" },
      { round: "1/2 финала", result: "❌", opponent: "Нидерланды", score: "2:3" },
      { round: "Матч за 3-е место 🥉", result: "🥉", opponent: "Германия", score: "2:3" },
    ]
  },
  {
    id: 14, team: "Англия", flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", year: 1966,
    aliases: ["англия", "england", "три льва"],
    path: [
      { round: "1/4 финала", result: "✅", opponent: "Аргентина", score: "1:0" },
      { round: "1/2 финала", result: "✅", opponent: "Португалия", score: "2:1" },
      { round: "Финал 🏆",   result: "🥇", opponent: "Зап. Германия", score: "4:2 (д.в.)" },
    ]
  },
];
