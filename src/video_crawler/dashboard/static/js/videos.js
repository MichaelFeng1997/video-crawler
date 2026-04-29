document.addEventListener('DOMContentLoaded', () => {
    let currentOffset = 0;

    const grid = document.getElementById('videoGrid');
    const pagination = document.getElementById('pagination');
    const resultInfo = document.getElementById('resultInfo');
    const btnSearch = document.getElementById('btnSearch');
    const filterCategory = document.getElementById('filterCategory');
    const filterKeyword = document.getElementById('filterKeyword');
    const filterLimit = document.getElementById('filterLimit');

    btnSearch.addEventListener('click', () => { currentOffset = 0; loadVideos(); });
    filterCategory.addEventListener('change', () => { currentOffset = 0; loadVideos(); });
    filterLimit.addEventListener('change', () => { currentOffset = 0; loadVideos(); });
    filterKeyword.addEventListener('keydown', e => {
        if (e.key === 'Enter') { currentOffset = 0; loadVideos(); }
    });

    async function loadVideos() {
        const limit = parseInt(filterLimit.value);
        const params = new URLSearchParams({ limit, offset: currentOffset });
        const category = filterCategory.value;
        const keyword = filterKeyword.value.trim();
        if (category) params.set('category', category);
        if (keyword) params.set('keyword', keyword);

        grid.innerHTML = '<div class="col-12 loading-state"><div class="spinner-border text-primary"></div><p class="mt-2">加载中...</p></div>';

        try {
            const resp = await fetch('/api/videos?' + params);
            const data = await resp.json();
            renderGrid(data.items);
            renderPagination(data.total, limit);
            resultInfo.textContent = `共 ${data.total} 个视频`;
        } catch (e) {
            grid.innerHTML = '<div class="col-12 empty-state"><i class="bi bi-exclamation-circle"></i><p>加载失败，请重试</p></div>';
        }
    }

    function renderGrid(items) {
        if (!items || items.length === 0) {
            grid.innerHTML = '<div class="col-12 empty-state"><i class="bi bi-camera-video-off"></i><p>没有找到视频</p></div>';
            return;
        }
        grid.innerHTML = items.map(v => `
            <div class="col-sm-6 col-md-4 col-xl-3">
                <a href="/videos/${v.platform}/${v.video_id}" class="text-decoration-none">
                    <div class="card video-card h-100">
                        <img src="${v.cover_url || ''}" class="card-img-top" alt=""
                             onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22320%22 height=%22180%22><rect fill=%22%23dee2e6%22 width=%22100%25%22 height=%22100%25%22/><text x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 fill=%22%23adb5bd%22 font-size=%2214%22>No Image</text></svg>'">
                        <div class="card-body py-2 px-3">
                            <div class="text-truncate fw-medium text-dark" style="font-size:0.9rem">${escapeHtml(v.title)}</div>
                            <small class="text-muted">
                                <i class="bi bi-person me-1"></i>${escapeHtml(v.author_name || '')}
                            </small>
                        </div>
                        <div class="card-footer bg-transparent border-0 py-2 px-3">
                            <small class="text-muted">
                                <i class="bi bi-play-circle me-1"></i>${formatNumber(v.view_count || 0)}
                                <span class="ms-2"><i class="bi bi-hand-thumbs-up me-1"></i>${formatNumber(v.like_count || 0)}</span>
                            </small>
                        </div>
                    </div>
                </a>
            </div>
        `).join('');
    }

    function renderPagination(total, limit) {
        const pages = Math.ceil(total / limit);
        const current = Math.floor(currentOffset / limit);
        if (pages <= 1) { pagination.innerHTML = ''; return; }

        let html = '';
        html += `<li class="page-item ${current === 0 ? 'disabled' : ''}">
                    <a class="page-link" href="#" data-offset="${(current - 1) * limit}">上一页</a></li>`;

        const start = Math.max(0, current - 2);
        const end = Math.min(pages, start + 5);
        for (let i = start; i < end; i++) {
            html += `<li class="page-item ${i === current ? 'active' : ''}">
                        <a class="page-link" href="#" data-offset="${i * limit}">${i + 1}</a></li>`;
        }

        html += `<li class="page-item ${current >= pages - 1 ? 'disabled' : ''}">
                    <a class="page-link" href="#" data-offset="${(current + 1) * limit}">下一页</a></li>`;
        pagination.innerHTML = html;
    }

    pagination.addEventListener('click', e => {
        e.preventDefault();
        const link = e.target.closest('[data-offset]');
        if (!link || link.closest('.disabled')) return;
        currentOffset = parseInt(link.dataset.offset);
        loadVideos();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    loadVideos();
});
