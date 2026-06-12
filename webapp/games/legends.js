const LegendsGame = (() => {
  let current = null;
  let hintsShown = 1;
  let finished = false;
  const SCORES = { 1: 100, 2: 60, 3: 30 };
  const MAX_HINTS = 3;

  function pick() {
    return LEGENDS[Math.floor(Math.random() * LEGENDS.length)];
  }

  function checkAnswer(input, legend) {
    const s = input.toLowerCase().trim();
    if (!s || s.length < 2) return false;
    if (s === legend.name.toLowerCase()) return true;
    const parts = legend.name.toLowerCase().split(' ');
    if (parts.some(p => p.length >= 3 && p === s)) return true;
    if (legend.aliases.some(a => a === s)) return true;
    if (s.length >= 4 && legend.name.toLowerCase().includes(s)) return true;
    return false;
  }

  function buildHintHTML(legend, n) {
    const clues = [
      { icon: '📅', text: `Чемпион ЧМ ${legend.year} — ${legend.flag} ${legend.country}` },
      { icon: '⚽', text: `Забил ${legend.goals} ${plural(legend.goals)} на том турнире` },
      { icon: '💬', text: legend.hint3 },
    ];
    return clues.map((c, i) => {
      const revealed = i < n;
      return `<div class="clue-card ${revealed ? 'revealed' : 'locked'}">
        <span class="clue-icon">${revealed ? c.icon : '🔒'}</span>
        <span class="clue-text">${revealed ? c.text : 'Подсказка ' + (i + 1)}</span>
      </div>`;
    }).join('');
  }

  function plural(n) {
    if (n === 1) return 'гол';
    if (n >= 2 && n <= 4) return 'гола';
    return 'голов';
  }

  function getScore() { return SCORES[hintsShown] || 30; }
  function hintsLeft() { return MAX_HINTS - hintsShown; }

  function start() {
    current = pick();
    hintsShown = 1;
    finished = false;
    return render();
  }

  function render() {
    return {
      title: '🏆 Легенды ЧМ',
      scoreLabel: `${getScore()} очков`,
      bodyHTML: buildHintHTML(current, hintsShown),
      placeholder: 'Введи имя легенды...',
      canHint: hintsShown < MAX_HINTS,
      hintsLeft: hintsLeft(),
    };
  }

  function handleHint() {
    if (hintsShown < MAX_HINTS) hintsShown++;
    return render();
  }

  function handleAnswer(input) {
    if (finished) return null;
    const correct = checkAnswer(input, current);
    if (correct) {
      finished = true;
      return { correct: true, score: getScore(), name: current.name, hint3: current.hint3, year: current.year, flag: current.flag, country: current.country };
    }
    if (hintsShown < MAX_HINTS) {
      hintsShown++;
      return { correct: false, newRender: render() };
    }
    finished = true;
    return { correct: false, score: 0, name: current.name, hint3: current.hint3, year: current.year, flag: current.flag, country: current.country, outOfHints: true };
  }

  return { start, handleHint, handleAnswer };
})();
