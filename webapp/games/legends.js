const LegendsGame = (() => {
  let current = null;
  let hintsShown = 1;
  let finished = false;
  const SCORES = { 1: 100, 2: 60, 3: 30 };
  const MAX_HINTS = 3;

  function pick() {
    const idx = Math.floor(Math.random() * LEGENDS.length);
    return LEGENDS[idx];
  }

  function checkAnswer(input, legend) {
    const s = input.toLowerCase().trim();
    if (!s || s.length < 2) return false;
    const nameParts = legend.name.toLowerCase().split(' ');
    if (s === legend.name.toLowerCase()) return true;
    if (nameParts.some(p => p.length >= 3 && p === s)) return true;
    if (legend.aliases.some(a => a === s)) return true;
    const full = legend.name.toLowerCase();
    if (s.length >= 4 && full.includes(s)) return true;
    return false;
  }

  function buildHintHTML(legend, n) {
    let html = `<div class="hint-block">`;
    html += `<div class="hint-row hint-visible">`;
    html += `<span class="hint-label">Подсказка 1</span>`;
    html += `<span class="hint-value">ЧМ ${legend.year} ${legend.flag} ${legend.country}</span>`;
    html += `</div>`;
    if (n >= 2) {
      html += `<div class="hint-row hint-visible">`;
      html += `<span class="hint-label">Подсказка 2</span>`;
      html += `<span class="hint-value">⚽ Голов на турнире: <b>${legend.goals}</b></span>`;
      html += `</div>`;
    } else {
      html += `<div class="hint-row hint-locked"><span class="hint-label">Подсказка 2</span><span class="hint-value">🔒 Откроется после неверного ответа</span></div>`;
    }
    if (n >= 3) {
      html += `<div class="hint-row hint-visible">`;
      html += `<span class="hint-label">Подсказка 3</span>`;
      html += `<span class="hint-value">💬 ${legend.hint3}</span>`;
      html += `</div>`;
    } else {
      html += `<div class="hint-row hint-locked"><span class="hint-label">Подсказка 3</span><span class="hint-value">🔒 Откроется после неверного ответа</span></div>`;
    }
    html += `</div>`;
    return html;
  }

  function start() {
    current = pick();
    hintsShown = 1;
    finished = false;
    return render();
  }

  function render() {
    const canHint = hintsShown < MAX_HINTS;
    const score = SCORES[hintsShown] || 30;
    return {
      title: '🏆 Легенды ЧМ',
      scoreLabel: `${score} очков за правильный ответ`,
      bodyHTML: buildHintHTML(current, hintsShown),
      placeholder: 'Введи имя легенды...',
      canHint,
      hintLabel: canHint ? `💡 Подсказка (-${score - (SCORES[hintsShown + 1] || 30)} очков)` : '💡 Подсказок больше нет',
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
      return { correct: true, score: SCORES[hintsShown] || 30, name: current.name, hint3: current.hint3, year: current.year, flag: current.flag, country: current.country };
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
