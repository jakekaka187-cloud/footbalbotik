const TrophyGame = (() => {
  let current = null;
  let roundsShown = 1;
  let finished = false;

  const SCORE_MAP = { 1: 100, 2: 70, 3: 40, 4: 20 };

  function pick() {
    const idx = Math.floor(Math.random() * TROPHY_PATHS.length);
    return TROPHY_PATHS[idx];
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
    const shown = entry.path.slice(0, n);
    const total = entry.path.length;
    let html = `<div class="trophy-header">`;
    html += `<span class="trophy-year">🗓 ЧМ ${entry.year}</span>`;
    html += `</div>`;
    html += `<div class="path-list">`;
    shown.forEach(step => {
      html += `<div class="path-row">`;
      html += `<span class="path-result">${step.result}</span>`;
      html += `<div class="path-info">`;
      html += `<span class="path-round">${step.round}</span>`;
      html += `<span class="path-score">vs ${step.opponent} — <b>${step.score}</b></span>`;
      html += `</div>`;
      html += `</div>`;
    });
    const remaining = total - n;
    if (remaining > 0) {
      html += `<div class="path-remaining">🔒 Ещё ${remaining} ${remaining === 1 ? 'раунд' : 'раунда'} скрыто</div>`;
    }
    html += `</div>`;
    return html;
  }

  function getScore(n) {
    return SCORE_MAP[n] || 20;
  }

  function start() {
    current = pick();
    roundsShown = 1;
    finished = false;
    return render();
  }

  function render() {
    const total = current.path.length;
    const canMore = roundsShown < total;
    const score = getScore(roundsShown);
    return {
      title: '🛤️ Путь к трофею',
      scoreLabel: `${score} очков за правильный ответ`,
      bodyHTML: buildPathHTML(current, roundsShown),
      placeholder: 'Название сборной...',
      canHint: canMore,
      hintLabel: canMore ? `🔍 Следующий раунд (-${score - getScore(roundsShown + 1)} очков)` : '🔍 Все раунды открыты',
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
