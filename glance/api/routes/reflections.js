import { Router } from 'express';
import fs from 'fs/promises';
import path from 'path';
import { marked } from 'marked';

const router = Router();
const REFLECTIONS_DIR = path.join('D:', 'dev', 'Fermi', 'memory', 'reflections');
const REFLECTIONS_FILE = path.join(REFLECTIONS_DIR, 'reflections.md');

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
  strong { color: #d8d0f0; }
  em { font-style: italic; opacity: 0.9; }
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
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
`;

// JSON endpoints
router.get('/api/reflections', async (req, res) => {
  try {
    const [raw, stat] = await Promise.all([
      fs.readFile(REFLECTIONS_FILE, 'utf-8'),
      fs.stat(REFLECTIONS_FILE),
    ]);
    const html = await marked(raw);
    res.json({ raw, html, size: stat.size, modified: stat.mtime.toISOString() });
  } catch (err) {
    if (err.code === 'ENOENT') return res.status(404).json({ error: 'reflections.md not found' });
    res.status(500).json({ error: `Failed to read reflections: ${err.message}` });
  }
});

router.get('/api/reflections/archive', async (req, res) => {
  try {
    const entries = await scanForDatedFiles(REFLECTIONS_DIR);
    res.json(entries);
  } catch (err) {
    res.status(500).json({ error: `Failed to list archives: ${err.message}` });
  }
});

// Full HTML page endpoint (for iframe)
router.get('/api/page/reflections', async (req, res) => {
  try {
    const [raw, stat] = await Promise.all([
      fs.readFile(REFLECTIONS_FILE, 'utf-8'),
      fs.stat(REFLECTIONS_FILE),
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
    res.type('html').send(`<!DOCTYPE html><html><head>${PAGE_STYLES}</head><body><p style="color:#f59e0b;">⚠ Could not load reflections</p></body></html>`);
  }
});

async function scanForDatedFiles(dir, basePath = '') {
  const results = [];
  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    for (const entry of entries) {
      const rel = path.join(basePath, entry.name);
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        results.push(...await scanForDatedFiles(full, rel));
      } else if (entry.name.endsWith('.md') && entry.name !== 'reflections.md') {
        const dateMatch = rel.match(/(\d{4}-\d{2}-\d{2})/);
        if (dateMatch) results.push({ date: dateMatch[1], path: rel.replace(/\\/g, '/') });
      }
    }
  } catch (err) {
    if (err.code !== 'ENOENT') console.error(`[reflections] Error: ${err.message}`);
  }
  return results.sort((a, b) => b.date.localeCompare(a.date));
}

export default router;
