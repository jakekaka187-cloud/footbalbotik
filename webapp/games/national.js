const NationalGame = (() => {
  let current = null;
  let playersShown = 3;
  let finished = false;
  const SCORE_MAP = { 3: 100, 4: 80, 5: 60, 6: 50, 7: 40, 8: 30, 9: 20, 10: 15, 11: 10 };
  const MAX_PLAYERS = 11;

  function pick() {
    return NATIONAL_TEAMS[Math.floor(Math.random() * NATIONAL_TEAMS.length)];
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
    let html = shown.map((p, i) =>
      `<div class="clue-card revealed">
        <span class="clue-icon">${p.emoji}</span>
        <span class="clue-text">${p.club}<span class="pos-badge pos-${p.pos}">${p.pos}</span></span>
      </div>`
    ).join('');
    const rem = MAX_PLAYERS - n;
    if (rem > 0) {
      html += `<div class="clue-card locked">
        <span class="clue-icon">🔒</span>
        <span class="clue-text">+${rem} игроков скрыто</span>
      </div>`;
    }
    return html;
  }

  function getScore(n) { return SCORE_MAP[n] || 10; }
  function hintsLeft() { return MAX_PLAYERS - playersShown; }

  function start() {
    current = pick();
    playersShown = 3;
    finished = false;
    return render();
  }

  function render() {
    return {
      title: '🌍 Угадай сборную',
      scoreLabel: `${getScore(playersShown)} очков`,
      bodyHTML: buildPlayersHTML(current, playersShown),
      placeholder: 'Название страны...',
      canHint: playersShown < MAX_PLAYERS,
      hintsLeft: hintsLeft(),
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
