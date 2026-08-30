let somAtivo = false;
let audioCtx = null;
const metasJaAtingidas = new Set();

function startClock() {
    function tick() {
        const agora = new Date();
        const hh = String(agora.getHours()).padStart(2, '0');
        const mm = String(agora.getMinutes()).padStart(2, '0');
        const ss = String(agora.getSeconds()).padStart(2, '0');
        const el = document.getElementById('metas-relogio');
        if (el) el.textContent = `${hh}:${mm}:${ss}`;
    }
    tick();
    setInterval(tick, 1000);
}

function renderAnel(ringEl, percentual) {
    const pct = Math.max(0, Math.min(percentual, 100));
    ringEl.style.setProperty('--progress', pct);
    ringEl.classList.toggle('atingida', percentual >= 100);
    const pctEl = ringEl.querySelector('.ring-pct');
    if (pctEl) pctEl.textContent = percentual + '%';
}

function atualizarCard(blockId, bloco) {
    const card = document.querySelector(`[data-block="${blockId}"]`);
    if (!card) return;

    card.dataset.progress = Math.max(0, Math.min(bloco.percentual, 100));

    const numEl = card.querySelector('.metas-produzido-num');
    if (numEl) numEl.textContent = bloco.produzido;

    const ringEl = card.querySelector('.progress-ring');
    if (ringEl) renderAnel(ringEl, bloco.percentual);

    const footerEl = card.querySelector('.goal-footer');
    if (footerEl) {
        if (bloco.faltam <= 0) {
            footerEl.innerHTML = '<span class="metas-atingida">&#10003; META ATINGIDA</span>';
        } else {
            const label = card.dataset.footerLabel || 'A META';
            footerEl.innerHTML =
                `FALTAM <span class="metas-num-laranja">${bloco.faltam}</span> PARA ${label}`;
        }
    }
}

function atualizarPainel(dados) {
    atualizarCard('metas-card-diaria', dados.geral.diaria);
    atualizarCard('metas-card-semanal', dados.geral.semanal);
    atualizarCard('metas-card-mensal', dados.geral.mensal);

    dados.setores.forEach(s => {
        atualizarCard('metas-card-' + s.id, {
            produzido: s.produzido_hoje,
            faltam: s.faltam,
            percentual: s.percentual,
        });
    });

    checkMetas(dados);
}

function toggleSom(btn) {
    somAtivo = !somAtivo;
    btn.classList.toggle('ativo', somAtivo);
    btn.textContent = somAtivo ? '🔊 Som ativado' : '⏰ Ativar som';
    if (somAtivo && !audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
}

function tocarBeep() {
    if (!somAtivo || !audioCtx) return;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.value = 880;
    gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.5);
    osc.connect(gain).connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.5);
}

function checkMetas(dados) {
    const blocos = [
        ['metas-card-diaria', dados.geral.diaria],
        ['metas-card-semanal', dados.geral.semanal],
        ['metas-card-mensal', dados.geral.mensal],
        ...dados.setores.map(s => ['metas-card-' + s.id, { faltam: s.faltam }]),
    ];

    blocos.forEach(([id, bloco]) => {
        const atingida = bloco.faltam <= 0;
        if (atingida && !metasJaAtingidas.has(id)) {
            metasJaAtingidas.add(id);
            tocarBeep();
        } else if (!atingida && metasJaAtingidas.has(id)) {
            metasJaAtingidas.delete(id);
        }
    });
}

function startAutoRefresh() {
    setInterval(() => {
        fetch('/metas/dados')
            .then(r => r.json())
            .then(dados => atualizarPainel(dados))
            .catch(err => console.error('Falha ao atualizar metas:', err));
    }, 300000);
}

document.addEventListener('DOMContentLoaded', function () {
    if (window.DADOS_INICIAIS) {
        // Marca como já atingidas as metas que já nascem batidas, pra não
        // disparar beep no primeiro carregamento da página.
        atualizarPainel(window.DADOS_INICIAIS);
    }

    startClock();
    startAutoRefresh();

    const btnSom = document.getElementById('btn-ativar-som');
    if (btnSom) btnSom.addEventListener('click', () => toggleSom(btnSom));
});
