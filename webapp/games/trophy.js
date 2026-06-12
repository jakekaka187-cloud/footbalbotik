const TrophyGame = (() => {
  let current = null;
  let roundsShown = 1;
  let finished = false;
  const SCORE_MAP = { 1: 100, 2: 70, 3: 40, 4: 20 };

  function pick() {
    return TROPHY_PATHS[Math.floor(Math.random() * TROPHY_PATHS.length)];
  }

  function checkAnswer(input, entry) {
    const s = input.toLowerCase().trim();
    if (!s || s.length < 2) return false;
    if (s === entry.team.toLowerCase()) return true;
    if (entry.aliases.some(a => a === s)) return true;
    if (s.length >= 4 && entry.team.toLowerCase().includes(s)) return true;
    return false;
  }

  function buildPathHTML(entry, n) {
    let html = `<div class="trophy-year-badge">🗓️ ЧМ ${entry.year}</div>`;
    html += entry.path.slice(0, n).map(step =>
      `<div class="clue-card revealed">
        <span class="clue-icon">${step.result}</span>
        <div class="clue-info">
          <div class="clue-round">${step.round}</div>
          <div class="clue-text">vs ${step.opponent} — <b>${step.score}</b></div>
        </div>
      </div>`
    ).join('');
    const rem = entry.path.length - n;
    if (rem > 0) {
      html += `<div class="clue-card locked">
        <span class="clue-icon">🔒</span>
        <span class="clue-text">${rem} ${rem === 1 ? 'раунд' : 'раунда'} ещё скрыто</span>
      </div>`;
    }
    return html;
  }

  function getScore(n) { return SCORE_MAP[n] || 20; }
  function hintsLeft() { return current.path.length - roundsShown; }

  function start() {
    current = pick();
    roundsShown = 1;
    finished = false;
    return render();
  }

  function render() {
    return {
      title: '🛤️ Путь к трофею',
      scoreLabel: `${getScore(roundsShown)} очков`,
      bodyHTML: buildPathHTML(current, roundsShown),
      placeholder: 'Название сборной...',
      canHint: roundsShown < current.path.length,
      hintsLeft: hintsLeft(),
    };
  }

  function handleHint() {
    if (roundsShown < current.path.length) roundsShown++;
    return render();
  }

  function handleAnswer(input) {
    if (finished) return null;
    const correct = checkAnswer(input, current);
    if (correct) {
      finished = true;
      return { correct: true, score: getScore(roundsShown), name: current.team, flag: current.flag, year: current.year };
    }
    if (roundsShown < current.path.length) {
      roundsShown++;
      return { correct: false, newRender: render() };
    }
    finished = true;
    return { correct: false, score: 0, name: current.team, flag: current.flag, year: current.year, outOfHints: true };
  }

  return { start, handleHint, handleAnswer };
})();
