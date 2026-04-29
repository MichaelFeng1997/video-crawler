document.addEventListener('DOMContentLoaded', () => {
    animateCounters();

    const toggle = document.getElementById('autoRefresh');
    const liveDot = document.getElementById('liveDot');
    if (!toggle) return;

    let timer = null;

    toggle.addEventListener('change', () => {
        if (toggle.checked) {
            timer = setInterval(refreshStats, 60000);
            if (liveDot) liveDot.classList.remove('d-none');
        } else {
            clearInterval(timer);
            timer = null;
            if (liveDot) liveDot.classList.add('d-none');
        }
    });

    async function refreshStats() {
        try {
            const resp = await fetch('/api/health');
            if (!resp.ok) return;
            const data = await resp.json();
            animateValue('stat-videos', data.video_count ?? 0);
            animateValue('stat-records', data.stat_count ?? 0);
            animateValue('stat-rankings', data.ranking_snapshots ?? 0);
        } catch (e) {
            console.warn('Auto-refresh failed:', e);
        }
    }
});

function animateCounters() {
    document.querySelectorAll('.counter-animate[data-target]').forEach(el => {
        const target = parseInt(el.dataset.target) || 0;
        if (target === 0) return;
        animateValue(el.id, target, 800);
    });
}

function animateValue(elementId, target, duration = 500) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const start = parseInt(el.textContent) || 0;
    if (start === target) return;

    const startTime = performance.now();
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(start + (target - start) * eased);
        el.textContent = current.toLocaleString('zh-CN');
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}
