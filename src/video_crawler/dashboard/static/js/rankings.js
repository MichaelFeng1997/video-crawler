document.addEventListener('DOMContentLoaded', () => {
    const platformSelect = document.getElementById('platformSelect');
    const categorySelect = document.getElementById('categorySelect');
    const rankingBody = document.getElementById('rankingBody');
    const snapshotInfo = document.getElementById('snapshotInfo');
    const entryCount = document.getElementById('entryCount');
    const authorHeader = document.getElementById('authorHeader');

    platformSelect.addEventListener('change', () => {
        updateCategories();
        loadRankings();
    });
    categorySelect.addEventListener('change', loadRankings);

    function updateCategories() {
        const platform = platformSelect.value;
        const cats = PLATFORM_CATEGORIES[platform] || {};
        categorySelect.innerHTML = Object.entries(cats).map(([key, label]) =>
            `<option value="${key}" ${key === 'all' ? 'selected' : ''}>${label}</option>`
        ).join('');
        authorHeader.textContent = platform === 'youtube' ? '频道' : 'UP主';
    }

    loadRankings();

    async function loadRankings() {
        const platform = platformSelect.value;
        const category = categorySelect.value;
        rankingBody.innerHTML = '<tr><td colspan="5" class="loading-state"><div class="spinner-border text-primary"></div><p class="mt-2">加载中...</p></td></tr>';

        try {
            const resp = await fetch(`/api/rankings/${platform}?category=${category}`);
            const data = await resp.json();

            if (data.snapshot_time) {
                snapshotInfo.innerHTML = `<i class="bi bi-clock me-1"></i>数据时间: ${formatDateTime(data.snapshot_time)}`;
            } else {
                snapshotInfo.innerHTML = '<i class="bi bi-clock me-1"></i>暂无数据';
            }

            const entries = data.entries || [];
            entryCount.textContent = `${entries.length} 条`;

            if (entries.length === 0) {
                rankingBody.innerHTML = '<tr><td colspan="5" class="empty-state"><i class="bi bi-trophy"></i><p>该分区暂无排行榜数据</p></td></tr>';
                return;
            }

            const maxScore = Math.max(...entries.map(e => e.score || 0), 1);
            rankingBody.innerHTML = entries.map((e, i) => {
                const v = e.video || {};
                const rankClass = e.rank <= 3 ? `rank-${e.rank}` : 'rank-other';
                const pct = Math.round(((e.score || 0) / maxScore) * 100);
                return `
                    <tr class="animate-in" style="animation-delay:${i * 0.02}s" onclick="window.location='/videos/${v.platform}/${v.video_id}'" >
                        <td>
                            <span class="rank-badge ${rankClass}">${e.rank}</span>
                        </td>
                        <td>
                            <img src="${v.cover_url || ''}" class="video-thumbnail-sm" alt=""
                                 onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2280%22 height=%2245%22><rect fill=%22%231e293b%22 width=%22100%25%22 height=%22100%25%22/></svg>'">
                        </td>
                        <td>
                            <div class="text-truncate fw-medium" style="max-width:400px">${escapeHtml(v.title || '')}</div>
                            <small class="text-muted">${v.category || ''}</small>
                        </td>
                        <td class="text-muted">${escapeHtml(v.author_name || '')}</td>
                        <td class="text-end">
                            <div class="fw-bold mb-1">${formatNumber(e.score || 0)}</div>
                            <div class="score-bar"><div class="score-bar-fill" style="width:${pct}%"></div></div>
                        </td>
                    </tr>
                `;
            }).join('');
        } catch (e) {
            rankingBody.innerHTML = '<tr><td colspan="5" class="empty-state"><i class="bi bi-exclamation-circle"></i><p>加载失败，请重试</p></td></tr>';
        }
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
});
