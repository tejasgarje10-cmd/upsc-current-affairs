<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>UPSC Current Affairs Digest</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --text: #f8fafc;
      --subtext: #94a3b8;
      --accent: #38bdf8;
      --border: #334155;
    }
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 2rem 1rem;
    }
    .header {
      max-width: 900px;
      margin: 0 auto 2rem;
      text-align: center;
    }
    .header h1 {
      font-size: 2rem;
      margin-bottom: 0.5rem;
    }
    .header p {
      color: var(--subtext);
    }
    .filters {
      display: flex;
      justify-content: center;
      gap: 10px;
      margin-bottom: 2rem;
      flex-wrap: wrap;
    }
    .btn {
      background: var(--card-bg);
      color: var(--text);
      border: 1px solid var(--border);
      padding: 8px 16px;
      border-radius: 6px;
      cursor: pointer;
      font-weight: 500;
      transition: all 0.2s ease;
    }
    .btn:hover, .btn.active {
      background: var(--accent);
      color: #000;
      border-color: var(--accent);
    }
    .grid {
      max-width: 900px;
      margin: 0 auto;
      display: grid;
      gap: 1.5rem;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.5rem;
    }
    .badge {
      display: inline-block;
      background: rgba(56, 189, 248, 0.15);
      color: var(--accent);
      padding: 4px 10px;
      border-radius: 4px;
      font-size: 0.85rem;
      font-weight: 600;
      margin-bottom: 0.75rem;
    }
    .card h2 {
      margin: 0 0 1rem;
      font-size: 1.25rem;
      line-height: 1.4;
    }
    .section-title {
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--subtext);
      margin-top: 1rem;
      font-weight: 700;
    }
    ul {
      margin: 0.5rem 0;
      padding-left: 1.2rem;
    }
    li {
      margin-bottom: 0.4rem;
    }
    p {
      margin: 0.4rem 0;
      line-height: 1.5;
    }
  </style>
</head>
<body>

  <div class="header">
    <h1>UPSC Syllabus-Aligned Current Affairs</h1>
    <p>Daily news categorized by General Studies papers with Prelims facts & Mains perspectives</p>
  </div>

  <div class="filters">
    <button class="btn active" onclick="filterNews('ALL', event)">All Papers</button>
    <button class="btn" onclick="filterNews('GS-1', event)">GS-1</button>
    <button class="btn" onclick="filterNews('GS-2', event)">GS-2</button>
    <button class="btn" onclick="filterNews('GS-3', event)">GS-3</button>
    <button class="btn" onclick="filterNews('GS-4', event)">GS-4</button>
  </div>

  <div id="news-grid" class="grid"></div>

  <script>
    let articlesData = [];

    async function loadNews() {
      const container = document.getElementById('news-grid');
      try {
        const res = await fetch('current_affairs.json');
        if (!res.ok) throw new Error("JSON payload not found");
        articlesData = await res.json();
        if(articlesData.length === 0) {
          container.innerHTML = '<p style="text-align:center;">No current affairs items found yet.</p>';
          return;
        }
        renderNews(articlesData);
      } catch (err) {
        container.innerHTML = '<p style="text-align:center; color:#94a3b8;">Loading latest updates or database initializing...</p>';
      }
    }

    function renderNews(articles) {
      const container = document.getElementById('news-grid');
      container.innerHTML = articles.map(art => `
        <div class="card">
          <span class="badge">${art.paper} • ${art.topic}</span>
          <h2>${art.title}</h2>
          
          <div class="section-title">📌 Prelims Pointers</div>
          <ul>
            ${(art.prelims_pointers || []).map(p => `<li>${p}</li>`).join('')}
          </ul>
          
          <div class="section-title">📝 Mains Perspective</div>
          <p><strong>Context:</strong> ${art.mains_perspective?.context || ''}</p>
          <p><strong>Key Arguments:</strong> ${art.mains_perspective?.key_arguments || ''}</p>
          <p><strong>Way Forward / Recommendations:</strong> ${art.mains_perspective?.way_forward || ''}</p>
        </div>
      `).join('');
    }

    function filterNews(paper, event) {
      document.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
      event.target.classList.add('active');
      
      if (paper === 'ALL') {
        renderNews(articlesData);
      } else {
        const filtered = articlesData.filter(a => a.paper === paper);
        renderNews(filtered);
      }
    }

    loadNews();
  </script>
</body>
</html>
