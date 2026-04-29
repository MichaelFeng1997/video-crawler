document.addEventListener('DOMContentLoaded', () => {
    const categorySelect = document.getElementById('categorySelect');
    const rankingBody = document.getElementById('rankingBody');
    const snapshotInfo = document.getElementById('snapshotInfo');
    const entryCount = document.getElementById('entryCount');

    categorySelect.addEventListener('change', loadRankings);
    loadRankings();

    async function loadRankings() {
        const category = categorySelect.value;
        rankingBody.innerHTML = '<tr><td colspan="5" class="text-center py-5"><div class="spinner-border text-primary"></div></td></tr>';

        try {
            const resp = await fetch(`/api/rankings/bilibili?category=${category}`);
            const data = await resp.json();

            if (data.snapshot_time) {
                snapshotInfo.innerHTML = `<i class="bi bi-clock me-1"></i>数据时间: ${formatDateTime(data.snapshot_time)}`;
            } else {
                snapshotInfo.innerHTML = '<i class="bi bi-clock me-1"></i>暂无数据';
            }

            const entries = data.entries || [];
            entryCount.textContent = `${entries.length} 条`;

            if (entries.length === 0) {
                rankingBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-5">该分区暂无排行榜数据</td></tr>';
                return;
            }

            rankingBody.innerHTML = entries.map(e => {
                const v = e.video || {};
                const rankClass = e.rank <= 3 ? `rank-${e.rank}` : 'rank-other';
                return `
                    <tr onclick="window.location='/videos/${v.platform}/${v.video_id}'" style="cursor:pointer">
                        <td>
                            <span class="rank-badge ${rankClass}">${e.rank}</span>
                        </td>
                        <td>
                            <img src="${v.cover_url || ''}" class="video-thumbnail-sm" alt=""
                                 onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2280%22 height=%2245%22><rect fill=%22%23dee2e6%22 width=%22100%25%22 height=%22100%25%22/></svg>'">
                        </td>
                        <td>
                            <div class="text-truncate fw-medium" style="max-width:400px">${escapeHtml(v.title || '')}</div>
                            <small class="text-muted">${v.category || ''}</small>
                        </td>
                        <td class="text-muted">${escapeHtml(v.author_name || '')}</td>
                        <td class="text-end">
                            <span class="fw-bold">${formatNumber(e.score || 0)}</span>
                        </td>
                    </tr>
                `;
            }).join('');
        } catch (e) {
            rankingBody.innerHTML = '<tr><td colspan="5" class="text-center text-danger py-5">加载失败，请重试</td></tr>';
        }
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
});
