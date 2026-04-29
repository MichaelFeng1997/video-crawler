document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('autoRefresh');
    if (!toggle) return;

    let timer = null;

    toggle.addEventListener('change', () => {
        if (toggle.checked) {
            timer = setInterval(refreshStats, 60000);
        } else {
            clearInterval(timer);
            timer = null;
        }
    });

    async function refreshStats() {
        try {
            const resp = await fetch('/api/health');
            if (!resp.ok) return;
            const data = await resp.json();
            const el = (id) => document.getElementById(id);
            if (el('stat-videos')) el('stat-videos').textContent = data.video_count ?? 0;
            if (el('stat-records')) el('stat-records').textContent = data.stat_count ?? 0;
            if (el('stat-rankings')) el('stat-rankings').textContent = data.ranking_snapshots ?? 0;
        } catch (e) {
            console.warn('Auto-refresh failed:', e);
        }
    }
});
