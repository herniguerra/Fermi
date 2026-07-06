import { Router } from 'express';
import fs from 'fs/promises';
import path from 'path';
import { marked } from 'marked';

const router = Router();
const MEMORY_DIR = path.join('D:', 'dev', 'Fermi', 'memory');

const FILE_MAP = {
  today: 'TODAY.md',
  memory: 'MEMORY.md',
  beliefs: 'BELIEFS.md',
  user: 'USER.md',
};

// Dark theme styles matching Glance's default dark mode
const PAGE_STYLES = `
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: transparent;
    color: #c8c8d0;
    font-size: 14px;
    line-height: 1.7;
    padding: 16px;
    -webkit-font-smoothing: antialiased;
  }
  h1 { font-size: 1.4rem; font-weight: 600; color: #e0e0e8; margin: 16px 0 8px 0; }
  h1:first-child { margin-top: 0; }
  h2 { font-size: 1.15rem; font-weight: 500; color: #d0d0d8; margin: 14px 0 6px 0; }
  h3 { font-size: 1rem; font-weight: 500; color: #c0c0c8; margin: 10px 0 4px 0; }
  p { margin: 6px 0; }
  ul, ol { padding-left: 20px; margin: 6px 0; }
  li { margin: 3px 0; }
  a { color: #8b7cf6; text-decoration: none; }
  a:hover { text-decoration: underline; }
  strong { color: #d8d0f0; }
  em { font-style: italic; opacity: 0.9; }
  code {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85em;
    background: rgba(255,255,255,0.06);
    padding: 1px 5px;
    border-radius: 4px;
  }
  blockquote {
    border-left: 3px solid #8b7cf6;
    padding-left: 12px;
    margin: 8px 0;
    opacity: 0.8;
    font-style: italic;
  }
  hr { border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 12px 0; }
  .meta {
    opacity: 0.4;
    font-size: 0.75rem;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }
</style>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
`;

// JSON endpoint (for custom-api widgets)
router.get('/api/memory/:file', async (req, res) => {
  const key = req.params.file.toLowerCase();
  const filename = FILE_MAP[key];

  if (!filename) {
    return res.status(400).json({
      error: `Invalid memory file: "${req.params.file}". Valid options: ${Object.keys(FILE_MAP).join(', ')}`,
    });
  }

  const filePath = path.join(MEMORY_DIR, filename);

  try {
    const [raw, stat] = await Promise.all([
      fs.readFile(filePath, 'utf-8'),
      fs.stat(filePath),
    ]);

    const html = await marked(raw);

    res.json({
      raw,
      html,
      size: stat.size,
      modified: stat.mtime.toISOString(),
    });
  } catch (err) {
    if (err.code === 'ENOENT') {
      return res.status(404).json({ error: `Memory file not found: ${filename}` });
    }
    console.error(`[memory] Error reading ${filename}: ${err.message}`);
    res.status(500).json({ error: `Failed to read ${filename}: ${err.message}` });
  }
});

// Full HTML page endpoint (for iframe widgets)
router.get('/api/page/memory/:file', async (req, res) => {
  const key = req.params.file.toLowerCase();
  const filename = FILE_MAP[key];

  if (!filename) {
    return res.type('html').send(`<!DOCTYPE html><html><head>${PAGE_STYLES}</head><body><p>Invalid file</p></body></html>`);
  }

  const filePath = path.join(MEMORY_DIR, filename);

  try {
    const [raw, stat] = await Promise.all([
      fs.readFile(filePath, 'utf-8'),
      fs.stat(filePath),
    ]);

    const html = await marked(raw);
    const sizeKb = (stat.size / 1024).toFixed(1);
    const modified = new Date(stat.mtime).toLocaleDateString('en-GB', {
      day: 'numeric', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });

    res.type('html').send(`<!DOCTYPE html>
<html><head><meta charset="utf-8">${PAGE_STYLES}</head>
<body>
  <div class="meta">${sizeKb} KB · Updated ${modified}</div>
  ${html}
</body></html>`);
  } catch (err) {
    res.type('html').send(`<!DOCTYPE html><html><head>${PAGE_STYLES}</head><body><p style="color:#f59e0b;">⚠ Could not load ${filename}</p></body></html>`);
  }
});

export default router;
