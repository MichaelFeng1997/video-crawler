document.addEventListener('DOMContentLoaded', () => {
    let currentOffset = 0;

    const grid = document.getElementById('videoGrid');
    const pagination = document.getElementById('pagination');
    const resultInfo = document.getElementById('resultInfo');
    const btnSearch = document.getElementById('btnSearch');
    const filterPlatform = document.getElementById('filterPlatform');
    const filterCategory = document.getElementById('filterCategory');
    const filterKeyword = document.getElementById('filterKeyword');
    const filterLimit = document.getElementById('filterLimit');

    btnSearch.addEventListener('click', () => { currentOffset = 0; loadVideos(); });
    filterPlatform.addEventListener('change', () => {
        updateCategories();
        currentOffset = 0;
        loadVideos();
    });
    filterCategory.addEventListener('change', () => { currentOffset = 0; loadVideos(); });
    filterLimit.addEventListener('change', () => { currentOffset = 0; loadVideos(); });
    filterKeyword.addEventListener('keydown', e => {
        if (e.key === 'Enter') { currentOffset = 0; loadVideos(); }
    });

    function updateCategories() {
        const platform = filterPlatform.value;
        if (!platform) {
            filterCategory.innerHTML = '<option value="">全部分区</option>';
            Object.entries(PLATFORM_CATEGORIES).forEach(([, cats]) => {
                Object.entries(cats).forEach(([key, label]) => {
                    if (!filterCategory.querySelector(`option[value="${key}"]`)) {
                        filterCategory.innerHTML += `<option value="${key}">${label}</option>`;
                    }
                });
            });
        } else {
            const cats = PLATFORM_CATEGORIES[platform] || {};
            filterCategory.innerHTML = '<option value="">全部分区</option>' +
                Object.entries(cats).map(([key, label]) =>
                    `<option value="${key}">${label}</option>`
                ).join('');
        }
    }

    async function loadVideos() {
        const limit = parseInt(filterLimit.value);
        const params = new URLSearchParams({ limit, offset: currentOffset });
        const platform = filterPlatform.value;
        const category = filterCategory.value;
        const keyword = filterKeyword.value.trim();
        if (platform) params.set('platform', platform);
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
            grid.innerHTML = '<div class="col-12 empty-state"><i class="bi bi-exclamation-circle"></i><p>加载失败���请重试</p></div>';
        }
    }

    function renderGrid(items) {
        if (!items || items.length === 0) {
            grid.innerHTML = '<div class="col-12 empty-state"><i class="bi bi-camera-video-off"></i><p>没有找到视频</p></div>';
            return;
        }
        grid.innerHTML = items.map((v, i) => {
            const platformBadge = v.platform === 'youtube'
                ? '<span class="badge" style="background:rgba(255,0,0,0.15);color:#f87171;font-size:0.7rem">YouTube</span>'
                : '<span class="badge" style="background:rgba(0,174,236,0.15);color:#22d3ee;font-size:0.7rem">B站</span>';
            return `
            <div class="col-sm-6 col-md-4 col-xl-3 animate-in" style="animation-delay:${i * 0.03}s">
                <a href="/videos/${v.platform}/${v.video_id}" class="text-decoration-none">
                    <div class="card video-card h-100">
                        <img src="${v.cover_url || ''}" class="card-img-top" alt=""
                             onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22320%22 height=%22180%22><rect fill=%22%231e293b%22 width=%22100%25%22 height=%22100%25%22/><text x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 fill=%22%2364748b%22 font-size=%2214%22>No Image</text></svg>'">
                        <div class="card-body py-2 px-3">
                            <div class="d-flex align-items-center gap-1 mb-1">
                                ${platformBadge}
                            </div>
                            <div class="text-truncate fw-medium" style="font-size:0.9rem">${escapeHtml(v.title)}</div>
                            <small class="text-muted">
                                <i class="bi bi-person me-1"></i>${escapeHtml(v.author_name || '')}
                            </small>
                        </div>
                        <div class="card-footer border-0 py-2 px-3">
                            <small class="text-muted">
                                <i class="bi bi-play-circle me-1"></i>${formatNumber(v.view_count || 0)}
                                <span class="ms-2"><i class="bi bi-hand-thumbs-up me-1"></i>${formatNumber(v.like_count || 0)}</span>
                            </small>
                        </div>
                    </div>
                </a>
            </div>
        `}).join('');
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
