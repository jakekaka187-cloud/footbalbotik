const tg = window.Telegram?.WebApp;
let sessionScore = 0;
let currentGame = null;

// ─── Init ───────────────────────────────────────────────────────────────────
(function init() {
  if (tg) {
    tg.ready();
    tg.expand();
    try { tg.setHeaderColor('#0a0118'); } catch(e){}
    try { tg.setBackgroundColor('#0a0118'); } catch(e){}
  }
  const user = tg?.initDataUnsafe?.user;
  const name = user?.first_name || 'Игрок';
  document.getElementById('user-name').textContent = `👋 ${name}`;
  showScreen('main');
})();

// ─── Screen management ──────────────────────────────────────────────────────
function showScreen(name) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(`screen-${name}`).classList.add('active');
}

// ─── Session score ──────────────────────────────────────────────────────────
function addScore(pts) {
  sessionScore += pts;
  document.querySelectorAll('.session-score-badge').forEach(el => {
    el.textContent = `+${sessionScore} за сессию`;
  });
}

// ─── Toast ───────────────────────────────────────────────────────────────────
let toastTimer = null;
function showToast(msg) {
  let toast = document.querySelector('.toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.className = 'toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add('show');
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2200);
}

// ─── Game launch ─────────────────────────────────────────────────────────────
function showGame(type) {
  currentGame = type;
  const GAMES = { legends: LegendsGame, national: NationalGame, trophy: TrophyGame };
  const game = GAMES[type];
  if (!game) return;

  const state = game.start();
  renderGameScreen(type, state, game);
  showScreen('game');
}

function renderGameScreen(type, state, game) {
  const container = document.getElementById('screen-game');
  container.innerHTML = `
    <div class="game-topbar">
      <button class="btn-back" onclick="showScreen('main')">←</button>
      <div class="game-topbar-title">
        <h2>${state.title}</h2>
        <div class="score-pot" id="score-pot">${state.scoreLabel}</div>
      </div>
      <div class="session-score-badge">${sessionScore > 0 ? '+' + sessionScore + ' за сессию' : '⚽ 0'}</div>
    </div>
    <div class="game-body" id="game-body">
      <div id="game-content">${state.bodyHTML}</div>
      <div class="input-area">
        <input id="answer-input" class="answer-input" type="text"
          placeholder="${state.placeholder}" autocomplete="off" autocorrect="off"
          autocapitalize="off" spellcheck="false" />
        <button class="btn-submit" onclick="submitAnswer()">→</button>
      </div>
      <button id="btn-hint" class="btn-hint" onclick="useHint()"
        ${state.canHint ? '' : 'disabled'}>${state.hintLabel}</button>
    </div>
  `;

  const input = document.getElementById('answer-input');
  input.addEventListener('keydown', e => { if (e.key === 'Enter') submitAnswer(); });
  setTimeout(() => input.focus(), 200);
}

function submitAnswer() {
  const GAMES = { legends: LegendsGame, national: NationalGame, trophy: TrophyGame };
  const game = GAMES[currentGame];
  const input = document.getElementById('answer-input');
  const val = input.value.trim();
  if (!val) return;

  const result = game.handleAnswer(val);
  if (!result) return;

  if (result.correct) {
    addScore(result.score);
    showResult(true, result);
  } else if (result.outOfHints) {
    showResult(false, result);
  } else {
    // Wrong answer but hints remain — already advanced
    input.classList.add('flash-wrong');
    input.addEventListener('animationend', () => input.classList.remove('flash-wrong'), { once: true });
    showToast('❌ Неверно! Открылась новая подсказка');
    input.value = '';

    const content = document.getElementById('game-content');
    const potEl = document.getElementById('score-pot');
    const hintBtn = document.getElementById('btn-hint');

    content.innerHTML = result.newRender.bodyHTML;
    potEl.textContent = result.newRender.scoreLabel;
    if (!result.newRender.canHint) {
      hintBtn.disabled = true;
      hintBtn.textContent = result.newRender.hintLabel;
    } else {
      hintBtn.textContent = result.newRender.hintLabel;
    }
    setTimeout(() => input.focus(), 100);
  }
}

function useHint() {
  const GAMES = { legends: LegendsGame, national: NationalGame, trophy: TrophyGame };
  const game = GAMES[currentGame];
  const state = game.handleHint();

  document.getElementById('game-content').innerHTML = state.bodyHTML;
  document.getElementById('score-pot').textContent = state.scoreLabel;
  const hintBtn = document.getElementById('btn-hint');
  hintBtn.textContent = state.hintLabel;
  if (!state.canHint) hintBtn.disabled = true;
}

// ─── Result screen ───────────────────────────────────────────────────────────
function showResult(won, data) {
  const container = document.getElementById('screen-result');
  const LABELS = { legends: '🏆 Легенды ЧМ', national: '🌍 Угадай сборную', trophy: '🛤️ Путь к трофею' };
  const gameLabel = LABELS[currentGame];
  const score = data.score || 0;

  let subText = '';
  if (currentGame === 'legends') {
    subText = `${data.flag || ''} ${data.country || ''}, ЧМ ${data.year || ''}<br><span style="font-size:13px;opacity:.7">${data.hint3 || ''}</span>`;
  } else if (currentGame === 'national') {
    subText = `${data.flag || ''} Это была сборная ${data.name}`;
  } else {
    subText = `${data.flag || ''} ${data.team || data.name}, ЧМ ${data.year || ''}`;
  }

  container.innerHTML = `
    <div class="result-icon">${won ? '🏆' : '😔'}</div>
    <div class="result-title ${won ? 'win' : 'lose'}">${won ? 'Правильно!' : 'Не угадал...'}</div>
    <div class="result-answer">${data.name}</div>
    <div class="result-sub">${subText}</div>
    <div class="result-score-box">
      <div class="pts-label">${won ? 'Заработано' : 'Очков'}</div>
      <div class="pts-value">${score > 0 ? '+' + score : '0'}</div>
      <div class="session-total">За сессию: +${sessionScore} очков</div>
    </div>
    <div class="result-actions">
      <button class="btn-primary" onclick="showGame('${currentGame}')">⚽ Ещё раз!</button>
      <button class="btn-secondary" onclick="showScreen('main')">🏠 Другая игра</button>
      ${sessionScore > 0 ? `<button class="btn-save" onclick="saveScore()">✅ Сохранить +${sessionScore} очков в бот</button>` : ''}
    </div>
  `;
  showScreen('result');
}

// ─── Send score to bot ────────────────────────────────────────────────────────
function saveScore() {
  if (sessionScore <= 0) return;
  const payload = JSON.stringify({ game: currentGame, score: sessionScore, won: true });
  if (tg && tg.sendData) {
    tg.sendData(payload);
  } else {
    showToast('📤 Тест-режим: ' + payload);
  }
}
