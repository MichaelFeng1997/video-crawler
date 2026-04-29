const CHART_COLORS = {
    view_count: '#4e79a7',
    like_count: '#e15759',
    coin_count: '#f28e2b',
    favorite_count: '#76b7b2',
    reply_count: '#59a14f',
    share_count: '#af7aa1',
    danmaku_count: '#ff9da7',
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
        backgroundColor: CHART_COLORS[key] + '20',
        borderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 6,
        tension: 0.3,
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
                    backgroundColor: CHART_COLORS.view_count + '20',
                    borderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    tension: 0.3,
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
                    backgroundColor: 'rgba(26, 26, 46, 0.9)',
                    titleColor: '#fff',
                    bodyColor: '#e8eaed',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 10,
                    callbacks: {
                        label: ctx => ctx.dataset.label + ': ' + formatNumber(ctx.parsed.y),
                    },
                },
                legend: { position: 'top' },
            },
            scales: {
                y: {
                    type: 'linear',
                    position: 'left',
                    title: { display: true, text: '播放量' },
                    ticks: {
                        callback: v => formatNumber(v),
                    },
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    title: { display: true, text: '互动数据' },
                    grid: { drawOnChartArea: false },
                    ticks: {
                        callback: v => formatNumber(v),
                    },
                },
            },
        },
    });
}
