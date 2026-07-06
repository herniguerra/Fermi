import { Router } from 'express';
import fs from 'fs/promises';
import path from 'path';

const router = Router();
const MEMORY_DIR = path.join('D:', 'dev', 'Fermi', 'memory');
const DREAMS_DIR = path.join(MEMORY_DIR, 'dreams');

/**
 * Recursively find all .md files and return their paths.
 */
async function findMdFiles(dir) {
  const results = [];
  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        results.push(...await findMdFiles(full));
      } else if (entry.name.endsWith('.md')) {
        results.push(full);
      }
    }
  } catch {
    // directory may not exist
  }
  return results;
}

/**
 * Extract date from a path containing YYYY-MM-DD.
 */
function extractDate(filePath) {
  const match = filePath.match(/(\d{4}-\d{2}-\d{2})/);
  return match ? match[1] : null;
}

router.get('/api/fermi/status', async (req, res) => {
  try {
    const status = {};

    // 1. Last dream date
    try {
      const dreamFiles = await findMdFiles(DREAMS_DIR);
      const dates = dreamFiles.map(f => extractDate(f)).filter(Boolean);
      dates.sort((a, b) => b.localeCompare(a));
      status.last_dream = dates[0] || null;
    } catch {
      status.last_dream = null;
    }

    // 2. Last reflection modified date
    try {
      const reflStat = await fs.stat(path.join(MEMORY_DIR, 'reflections', 'reflections.md'));
      status.last_reflection = reflStat.mtime.toISOString();
    } catch {
      status.last_reflection = null;
    }

    // 3. Today briefing: does TODAY.md exist and was it modified today?
    try {
      const todayStat = await fs.stat(path.join(MEMORY_DIR, 'TODAY.md'));
      const todayStr = new Date().toISOString().slice(0, 10);
      const modStr = todayStat.mtime.toISOString().slice(0, 10);
      status.today_briefing = modStr === todayStr;
    } catch {
      status.today_briefing = false;
    }

    // 4. Memory size in bytes
    try {
      const memStat = await fs.stat(path.join(MEMORY_DIR, 'MEMORY.md'));
      status.memory_size = memStat.size;
    } catch {
      status.memory_size = 0;
    }

    // 5. Beliefs count — count lines starting with number+period or containing bold entries
    try {
      const beliefs = await fs.readFile(path.join(MEMORY_DIR, 'BELIEFS.md'), 'utf-8');
      const lines = beliefs.split('\n');
      let count = 0;
      let pastSeparator = false;
      for (const line of lines) {
        const trimmed = line.trim();
        // Start counting after the --- separator
        if (trimmed === '---') { pastSeparator = true; continue; }
        if (!pastSeparator) continue;
        // Count: ## headers, - ** bold entries, numbered items, or content paragraphs
        if (/^## /.test(trimmed) || /^- \*\*/.test(trimmed) || /^\d+\./.test(trimmed)) {
          count++;
        } else if (trimmed.length > 0 && !trimmed.startsWith('#') && !trimmed.startsWith('*')) {
          // Plain content paragraph (a belief statement)
          count++;
        }
      }
      status.beliefs_count = count;
    } catch {
      status.beliefs_count = 0;
    }

    res.json(status);
  } catch (err) {
    console.error(`[fermi-status] ${err.message}`);
    res.status(500).json({ error: `Failed to aggregate status: ${err.message}` });
  }
});

export default router;
