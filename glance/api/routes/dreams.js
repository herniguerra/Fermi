import { Router } from 'express';
import fs from 'fs/promises';
import path from 'path';
import { marked } from 'marked';

const router = Router();
const DREAMS_DIR = path.join('D:', 'dev', 'Fermi', 'memory', 'dreams');

const PAGE_STYLES = `
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: transparent;
    color: #c8c8d0;
    font-size: 14px;
    line-height: 1.8;
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

async function findMarkdownFiles(dir, basePath = '') {
  const results = [];
  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    for (const entry of entries) {
      const rel = path.join(basePath, entry.name);
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        results.push(...await findMarkdownFiles(full, rel));
      } else if (entry.name.endsWith('.md')) {
        results.push({ relativePath: rel, fullPath: full });
      }
    }
  } catch (err) {
    console.error(`[dreams] Error scanning ${dir}: ${err.message}`);
  }
  return results;
}

function extractDate(relativePath) {
  const match = relativePath.match(/(\d{4}-\d{2}-\d{2})/);
  if (match) return match[1];
  const pathMatch = relativePath.match(/(\d{4})[/\\](\d{2})[/\\](\d{2})/);
  if (pathMatch) return `${pathMatch[1]}-${pathMatch[2]}-${pathMatch[3]}`;
  return path.basename(relativePath, '.md');
}

// JSON endpoints
router.get('/api/dreams', async (req, res) => {
  try {
    const files = await findMarkdownFiles(DREAMS_DIR);
    const dreams = files
      .map(f => ({ date: extractDate(f.relativePath), path: f.relativePath.replace(/\\/g, '/') }))
      .sort((a, b) => b.date.localeCompare(a.date));
    res.json(dreams);
  } catch (err) {
    res.status(500).json({ error: `Failed to list dreams: ${err.message}` });
  }
});

router.get('/api/dreams/latest', async (req, res) => {
  try {
    const files = await findMarkdownFiles(DREAMS_DIR);
    if (files.length === 0) return res.status(404).json({ error: 'No dream files found' });
    files.sort((a, b) => extractDate(b.relativePath).localeCompare(extractDate(a.relativePath)));
    const latest = files[0];
    const raw = await fs.readFile(latest.fullPath, 'utf-8');
    const html = await marked(raw);
    res.json({ date: extractDate(latest.relativePath), raw, html });
  } catch (err) {
    res.status(500).json({ error: `Failed to read latest dream: ${err.message}` });
  }
});

// Full HTML page endpoint (for iframe)
router.get('/api/page/dreams/latest', async (req, res) => {
  try {
    const files = await findMarkdownFiles(DREAMS_DIR);
    if (files.length === 0) {
      return res.type('html').send(`<!DOCTYPE html><html><head>${PAGE_STYLES}</head><body><p style="opacity:0.5;font-style:italic;">No dreams recorded yet</p></body></html>`);
    }
    files.sort((a, b) => extractDate(b.relativePath).localeCompare(extractDate(a.relativePath)));
    const latest = files[0];
    const raw = await fs.readFile(latest.fullPath, 'utf-8');
    const html = await marked(raw);
    const date = extractDate(latest.relativePath);

    res.type('html').send(`<!DOCTYPE html>
<html><head><meta charset="utf-8">${PAGE_STYLES}</head>
<body>
  <div class="meta">🌙 ${date}</div>
  ${html}
</body></html>`);
  } catch (err) {
    res.type('html').send(`<!DOCTYPE html><html><head>${PAGE_STYLES}</head><body><p style="color:#f59e0b;">⚠ Could not load dream</p></body></html>`);
  }
});

export default router;
