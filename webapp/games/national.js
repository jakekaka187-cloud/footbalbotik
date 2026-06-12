const NationalGame = (() => {
  let current = null;
  let playersShown = 3;
  let finished = false;

  const SCORE_MAP = { 3: 100, 4: 80, 5: 60, 6: 50, 7: 40, 8: 30, 9: 20, 10: 15, 11: 10 };
  const MAX_PLAYERS = 11;

  function pick() {
    const idx = Math.floor(Math.random() * NATIONAL_TEAMS.length);
    return NATIONAL_TEAMS[idx];
  }

  function checkAnswer(input, team) {
    const s = input.toLowerCase().trim();
    if (!s || s.length < 2) return false;
    if (s === team.name.toLowerCase()) return true;
    if (team.aliases.some(a => a === s)) return true;
    if (s.length >= 4 && team.name.toLowerCase().includes(s)) return true;
    return false;
  }

  function buildPlayersHTML(team, n) {
    const shown = team.players.slice(0, n);
    let html = `<div class="players-list">`;
    shown.forEach((p, i) => {
      html += `<div class="player-row">`;
      html += `<span class="player-num">${i + 1}.</span>`;
      html += `<span class="player-club">${p.emoji} ${p.club}</span>`;
      html += `<span class="player-pos pos-${p.pos}">${p.pos}</span>`;
      html += `</div>`;
    });
    const remaining = MAX_PLAYERS - n;
    if (remaining > 0) {
      html += `<div class="players-remaining">+ ещё ${remaining} игроков</div>`;
    }
    html += `</div>`;
    return html;
  }

  function getScore(n) {
    return SCORE_MAP[n] || 10;
  }

  function start() {
    current = pick();
    playersShown = 3;
    finished = false;
    return render();
  }

  function render() {
    const canMore = playersShown < MAX_PLAYERS;
    const score = getScore(playersShown);
    return {
      title: '🌍 Угадай сборную',
      scoreLabel: `${score} очков за правильный ответ`,
      bodyHTML: buildPlayersHTML(current, playersShown),
      placeholder: 'Название страны...',
      canHint: canMore,
      hintLabel: canMore ? `👤 +1 игрок (-${score - getScore(playersShown + 1)} очков)` : '👤 Все игроки открыты',
    };
  }

  function handleHint() {
    if (playersShown < MAX_PLAYERS) playersShown++;
    return render();
  }

  function handleAnswer(input) {
    if (finished) return null;
    const correct = checkAnswer(input, current);
    if (correct) {
      finished = true;
      return { correct: true, score: getScore(playersShown), name: current.name, flag: current.flag };
    }
    if (playersShown < MAX_PLAYERS) {
      playersShown++;
      return { correct: false, newRender: render() };
    }
    finished = true;
    return { correct: false, score: 0, name: current.name, flag: current.flag, outOfHints: true };
  }

  return { start, handleHint, handleAnswer };
})();
