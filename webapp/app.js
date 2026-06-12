const tg = window.Telegram?.WebApp;
let sessionScore = 0;
let questionNum = 0;
const Q_MAX = 10;
let currentGame = null;

// ── Init ──────────────────────────────────────────────────────────────────────
(function init() {
  if (tg) {
    tg.ready(); tg.expand();
    try { tg.setHeaderColor('#090915'); } catch(e){}
    try { tg.setBackgroundColor('#090915'); } catch(e){}
  }
  const name = tg?.initDataUnsafe?.user?.first_name || 'Игрок';
  const el = document.getElementById('user-name');
  if (el) el.textContent = name;
  showScreen('main');
})();

// ── Screens ───────────────────────────────────────────────────────────────────
function showScreen(name) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById('screen-' + name).classList.add('active');
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.screen === name);
  });
}

// ── Toast ─────────────────────────────────────────────────────────────────────
let _toastTimer;
function showToast(msg) {
  let t = document.querySelector('.toast');
  if (!t) { t = document.createElement('div'); t.className = 'toast'; document.body.appendChild(t); }
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => t.classList.remove('show'), 2200);
}

// ── Player silhouette SVG ─────────────────────────────────────────────────────
function playerSVG() {
  return `<svg viewBox="0 0 100 120" class="player-svg" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <filter id="gl" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="5" result="b"/>
        <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
    </defs>
    <ellipse cx="50" cy="27" rx="19" ry="22" fill="#180e2e" stroke="#c8a030" stroke-width="1.5" filter="url(#gl)"/>
    <path d="M12 120 Q18 70 50 63 Q82 70 88 120Z" fill="#180e2e" stroke="#c8a030" stroke-width="1.5" filter="url(#gl)"/>
    <ellipse cx="50" cy="65" rx="46" ry="56" fill="none" stroke="rgba(200,160,48,.15)" stroke-width="10"/>
  </svg>`;
}

// ── Launch game ───────────────────────────────────────────────────────────────
function showGame(type) {
  currentGame = type;
  questionNum = questionNum < Q_MAX ? questionNum + 1 : 1;
  const GAMES = { legends: LegendsGame, national: NationalGame, trophy: TrophyGame };
  const state = GAMES[type].start();
  renderGameScreen(type, state);
  showScreen('game');
}

function renderGameScreen(type, state) {
  const TITLES = { legends: 'ЛЕГЕНДЫ ЧМ', national: 'УГАДАЙ СБОРНУЮ', trophy: 'ПУТЬ К ТРОФЕЮ' };
  const pct = (questionNum / Q_MAX) * 100;

  document.getElementById('screen-game').innerHTML = `
    <div class="game-topbar">
      <button class="btn-back" onclick="showScreen('main')">←</button>
      <div class="topbar-center">
        <div class="game-title">${TITLES[type]}</div>
        <div class="progress-row">
          <span class="progress-text">${questionNum}/${Q_MAX}</span>
          <div class="progress-bar"><div class="progress-fill" style="width:${pct}%"></div></div>
        </div>
      </div>
      <div class="score-chip" id="score-chip">+${sessionScore}</div>
    </div>

    <div class="game-scroll">
      <div class="player-zone">${playerSVG()}</div>
      <div class="clues-zone" id="clues-zone">${state.bodyHTML}</div>
      <div class="answer-zone">
        <input id="answer-input" class="answer-input" type="text"
          placeholder="${state.placeholder}"
          autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false"/>
      </div>
    </div>

    <div class="bottom-actions">
      <button id="btn-hint" class="btn-hint" onclick="useHint()" ${state.canHint ? '' : 'disabled'}>
        💡 Подсказка <span class="hint-badge" id="hint-badge">${state.hintsLeft}</span>
      </button>
      <button class="btn-skip" onclick="skipQuestion()">&gt;&gt; Пропустить</button>
    </div>
  `;

  const inp = document.getElementById('answer-input');
  inp.addEventListener('keydown', e => { if (e.key === 'Enter') submitAnswer(); });
  setTimeout(() => inp.focus(), 250);
}

// ── Submit ────────────────────────────────────────────────────────────────────
function submitAnswer() {
  const GAMES = { legends: LegendsGame, national: NationalGame, trophy: TrophyGame };
  const inp = document.getElementById('answer-input');
  const val = inp.value.trim();
  if (!val) return;

  const result = GAMES[currentGame].handleAnswer(val);
  if (!result) return;

  if (result.correct) {
    sessionScore += result.score;
    document.getElementById('score-chip').textContent = '+' + sessionScore;
    showResult(true, result);
  } else if (result.outOfHints) {
    showResult(false, result);
  } else {
    inp.classList.add('flash-wrong');
    inp.addEventListener('animationend', () => inp.classList.remove('flash-wrong'), { once: true });
    showToast('❌ Неверно! Открылась подсказка');
    inp.value = '';
    updateGameBody(result.newRender);
    setTimeout(() => inp.focus(), 100);
  }
}

function updateGameBody(state) {
  document.getElementById('clues-zone').innerHTML = state.bodyHTML;
  const hb = document.getElementById('hint-badge');
  const btn = document.getElementById('btn-hint');
  if (hb) hb.textContent = state.hintsLeft;
  if (btn) btn.disabled = !state.canHint;
}

// ── Hint ──────────────────────────────────────────────────────────────────────
function useHint() {
  const GAMES = { legends: LegendsGame, national: NationalGame, trophy: TrophyGame };
  const state = GAMES[currentGame].handleHint();
  updateGameBody(state);
}

// ── Skip ──────────────────────────────────────────────────────────────────────
function skipQuestion() {
  const GAMES = { legends: LegendsGame, national: NationalGame, trophy: TrophyGame };
  const game = GAMES[currentGame];
  // Force out-of-hints by draining hints
  let result;
  do { result = game.handleAnswer('__skip__'); } while (result && !result.correct && !result.outOfHints && result.newRender);
  if (!result || result.correct) {
    showGame(currentGame);
  } else {
    showResult(false, result);
  }
}

// ── Result screen ─────────────────────────────────────────────────────────────
function showResult(won, data) {
  const score = data.score || 0;
  let subText = '';
  if (currentGame === 'legends') {
    subText = `${data.flag || ''} ${data.country || ''}, ЧМ ${data.year || ''}<br><small style="opacity:.6">${data.hint3 || ''}</small>`;
  } else if (currentGame === 'national') {
    subText = `${data.flag || ''} Сборная ${data.name}`;
  } else {
    subText = `${data.flag || ''} ${data.name}, ЧМ ${data.year || ''}`;
  }

  const saveBtn = sessionScore > 0
    ? `<button class="btn-save" onclick="saveScore()">✅ Отправить +${sessionScore} очков в бот</button>`
    : '';

  document.getElementById('screen-result').innerHTML = `
    <div class="result-emoji">${won ? '🏆' : '😔'}</div>
    <div class="result-title ${won ? 'win' : 'lose'}">${won ? 'Правильно!' : 'Не угадал...'}</div>
    <div class="result-name">${data.name}</div>
    <div class="result-sub">${subText}</div>
    <div class="score-box">
      <div class="lbl">${won ? 'Заработано' : 'Очков за вопрос'}</div>
      <div class="pts">${score > 0 ? '+' + score : '0'}</div>
      <div class="tot">За сессию: +${sessionScore} очков</div>
    </div>
    <div class="result-btns">
      <button class="btn-primary" onclick="showGame('${currentGame}')">⚽ Следующий вопрос</button>
      <button class="btn-secondary" onclick="showScreen('main')">🏠 Выбрать игру</button>
      ${saveBtn}
    </div>
  `;
  showScreen('result');
}

// ── Send to bot ───────────────────────────────────────────────────────────────
function saveScore() {
  if (sessionScore <= 0) return;
  const payload = JSON.stringify({ game: currentGame, score: sessionScore, won: true });
  if (tg && tg.sendData) {
    tg.sendData(payload);
  } else {
    showToast('Тест: ' + payload);
  }
}
