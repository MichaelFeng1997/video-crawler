document.addEventListener('DOMContentLoaded', async () => {
    try {
        const resp = await fetch(`/api/videos/${VIDEO_PLATFORM}/${VIDEO_ID}`);
        if (!resp.ok) throw new Error('Failed to load video');
        const data = await resp.json();
        renderLatestStats(data.latest_stats);
        renderChart(data.stats_history);
        renderHistoryTable(data.stats_history);
    } catch (e) {
        document.getElementById('latestStats').innerHTML =
            '<div class="col-12 text-center text-danger py-3">加载失败</div>';
    }
});

function renderLatestStats(stats) {
    const container = document.getElementById('latestStats');
    if (!stats) {
        container.innerHTML = '<div class="col-12 text-center text-muted py-3">暂无统计数据</div>';
        return;
    }
    const items = [
        { icon: 'play-circle', label: '播放', value: stats.view_count, color: '#4e79a7' },
        { icon: 'hand-thumbs-up', label: '点赞', value: stats.like_count, color: '#e15759' },
        { icon: 'coin', label: '投币', value: stats.coin_count, color: '#f28e2b' },
        { icon: 'star', label: '收藏', value: stats.favorite_count, color: '#76b7b2' },
        { icon: 'chat-dots', label: '评论', value: stats.reply_count, color: '#59a14f' },
        { icon: 'send', label: '分享', value: stats.share_count, color: '#af7aa1' },
        { icon: 'body-text', label: '弹幕', value: stats.danmaku_count, color: '#ff9da7' },
    ];
    container.innerHTML = items.map(it => `
        <div class="col">
            <div class="detail-stat-card" style="border-top:3px solid ${it.color}">
                <div style="color:${it.color}"><i class="bi bi-${it.icon}" style="font-size:1.2rem"></i></div>
                <div class="fw-bold">${formatNumber(it.value || 0)}</div>
                <small class="text-muted">${it.label}</small>
            </div>
        </div>
    `).join('');
}

function renderChart(history) {
    const chartEl = document.getElementById('statsChart');
    const emptyEl = document.getElementById('chartEmpty');
    if (!history || history.length < 2) {
        chartEl.classList.add('d-none');
        emptyEl.classList.remove('d-none');
        return;
    }
    createStatsChart('statsChart', history);
}

function renderHistoryTable(history) {
    const body = document.getElementById('historyBody');
    if (!history || history.length === 0) {
        body.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-3">暂无数据</td></tr>';
        return;
    }
    body.innerHTML = history.slice().reverse().map(s => `
        <tr>
            <td class="text-nowrap">${formatDateTime(s.crawled_at)}</td>
            <td>${(s.view_count || 0).toLocaleString()}</td>
            <td>${(s.like_count || 0).toLocaleString()}</td>
            <td>${(s.coin_count || 0).toLocaleString()}</td>
            <td>${(s.favorite_count || 0).toLocaleString()}</td>
            <td>${(s.reply_count || 0).toLocaleString()}</td>
            <td>${(s.danmaku_count || 0).toLocaleString()}</td>
        </tr>
    `).join('');
}
