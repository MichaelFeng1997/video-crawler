const CHART_COLORS = {
    view_count: '#818cf8',
    like_count: '#f87171',
    coin_count: '#fbbf24',
    favorite_count: '#22d3ee',
    reply_count: '#34d399',
    share_count: '#c084fc',
    danmaku_count: '#fb7185',
};

const METRIC_LABELS = {
    view_count: '播放量',
    like_count: '点赞',
    coin_count: '投币',
    favorite_count: '收藏',
    reply_count: '评论',
    share_count: '分享',
    danmaku_count: '弹幕',
};

function formatNumber(n) {
    if (n === null || n === undefined) return '0';
    if (n >= 100000000) return (n / 100000000).toFixed(1) + '亿';
    if (n >= 10000) return (n / 10000).toFixed(1) + '万';
    return n.toLocaleString('zh-CN');
}

function formatDateTime(isoStr) {
    if (!isoStr) return '-';
    const d = new Date(isoStr);
    return d.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
    });
}

function createStatsChart(canvasId, statsHistory) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !statsHistory || statsHistory.length === 0) return null;

    const labels = statsHistory.map(s => formatDateTime(s.crawled_at));

    const viewData = statsHistory.map(s => s.view_count || 0);
    const rightMetrics = ['like_count', 'coin_count', 'favorite_count', 'reply_count'];
    const rightDatasets = rightMetrics.map(key => ({
        label: METRIC_LABELS[key],
        data: statsHistory.map(s => s[key] || 0),
        borderColor: CHART_COLORS[key],
        backgroundColor: CHART_COLORS[key] + '15',
        borderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 7,
        pointBackgroundColor: CHART_COLORS[key],
        pointBorderColor: '#1e293b',
        pointBorderWidth: 2,
        tension: 0.4,
        yAxisID: 'y1',
    }));

    return new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: METRIC_LABELS.view_count,
                    data: viewData,
                    borderColor: CHART_COLORS.view_count,
                    backgroundColor: createGradient(canvas, CHART_COLORS.view_count),
                    borderWidth: 2.5,
                    pointRadius: 3,
                    pointHoverRadius: 7,
                    pointBackgroundColor: CHART_COLORS.view_count,
                    pointBorderColor: '#1e293b',
                    pointBorderWidth: 2,
                    tension: 0.4,
                    yAxisID: 'y',
                    fill: true,
                },
                ...rightDatasets,
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(99, 102, 241, 0.3)',
                    borderWidth: 1,
                    cornerRadius: 10,
                    padding: 12,
                    displayColors: true,
                    boxPadding: 4,
                    callbacks: {
                        label: ctx => ' ' + ctx.dataset.label + ': ' + formatNumber(ctx.parsed.y),
                    },
                },
                legend: {
                    position: 'top',
                    labels: {
                        color: '#94a3b8',
                        usePointStyle: true,
                        pointStyle: 'circle',
                        padding: 16,
                    },
                },
            },
            scales: {
                x: {
                    ticks: { color: '#64748b' },
                    grid: { color: 'rgba(148, 163, 184, 0.06)' },
                },
                y: {
                    type: 'linear',
                    position: 'left',
                    title: { display: true, text: '播放量', color: '#64748b' },
                    ticks: { color: '#64748b', callback: v => formatNumber(v) },
                    grid: { color: 'rgba(148, 163, 184, 0.06)' },
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    title: { display: true, text: '互动数据', color: '#64748b' },
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#64748b', callback: v => formatNumber(v) },
                },
            },
        },
    });
}

function createGradient(canvas, color) {
    const ctx = canvas.getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.parentElement?.clientHeight || 400);
    gradient.addColorStop(0, color + '30');
    gradient.addColorStop(1, color + '02');
    return gradient;
}
