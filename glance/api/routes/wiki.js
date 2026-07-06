import { Router } from 'express';
import fs from 'fs/promises';
import path from 'path';

const router = Router();
const WIKI_ROOT = path.join('D:', 'dev', 'Fermi', 'wiki');

// Recursive file walker
async function walk(dir) {
  let files = [];
  try {
    const list = await fs.readdir(dir, { withFileTypes: true });
    for (const entry of list) {
      const res = path.resolve(dir, entry.name);
      if (entry.isDirectory()) {
        files = files.concat(await walk(res));
      } else {
        files.push(res);
      }
    }
  } catch (err) {
    console.error(`[wiki] Error walking directory ${dir}: ${err.message}`);
  }
  return files;
}

// Frontmatter and metadata parser
function parseFrontmatter(content) {
  const metadata = {};
  let body = content;

  if (content.startsWith('---')) {
    const parts = content.split('---');
    if (parts.length >= 3) {
      body = parts.slice(2).join('---').trim();
      const fmLines = parts[1].trim().split('\n');
      for (const line of fmLines) {
        if (line.includes(':')) {
          const index = line.indexOf(':');
          const k = line.substring(0, index).trim().toLowerCase();
          const v = line.substring(index + 1).trim().replace(/^['"]|['"]$/g, '');
          metadata[k] = v;
        }
      }
    }
  }

  return { metadata, body };
}

// GET /api/wiki/list
router.get('/api/wiki/list', async (req, res) => {
  try {
    // Check if wiki root exists
    try {
      await fs.access(WIKI_ROOT);
    } catch {
      return res.status(404).json({ error: 'Wiki root not found' });
    }

    const allFiles = await walk(WIKI_ROOT);
    const pages = [];

    for (const filePath of allFiles) {
      const fileName = path.basename(filePath);
      if (fileName.endsWith('.md') && !fileName.startsWith('_')) {
        const relPath = path.relative(WIKI_ROOT, filePath).replace(/\\/g, '/');
        let title = fileName.replace('.md', '');
        let category = 'other';

        try {
          const content = await fs.readFile(filePath, 'utf-8');
          const { metadata } = parseFrontmatter(content);
          if (metadata.title) {
            title = metadata.title;
          }
          if (metadata.category) {
            category = metadata.category;
          } else if (metadata.type) {
            category = metadata.type;
          }
        } catch (err) {
          console.error(`[wiki] Error reading/parsing file ${filePath}: ${err.message}`);
        }

        pages.append ? null : pages.push({
          path: relPath,
          title,
          category: category.toLowerCase()
        });
      }
    }

    res.json({ pages });
  } catch (err) {
    console.error(`[wiki] Error listing wiki: ${err.message}`);
    res.status(500).json({ error: `Failed to list wiki pages: ${err.message}` });
  }
});

// GET /api/wiki/page
router.get('/api/wiki/page', async (req, res) => {
  try {
    const pagePath = req.query.path;
    if (!pagePath) {
      return res.status(400).json({ error: 'Missing path parameter' });
    }

    const targetPath = path.resolve(WIKI_ROOT, pagePath);

    // Security check: ensure path is inside WIKI_ROOT and does not escape
    if (!targetPath.startsWith(WIKI_ROOT)) {
      return res.status(403).json({ error: 'Access denied: path escapes wiki root' });
    }

    try {
      await fs.access(targetPath);
    } catch {
      return res.status(404).json({ error: 'Page not found' });
    }

    const content = await fs.readFile(targetPath, 'utf-8');
    const { metadata, body } = parseFrontmatter(content);

    res.json({
      path: pagePath,
      metadata,
      content: body
    });
  } catch (err) {
    console.error(`[wiki] Error reading page ${req.query.path}: ${err.message}`);
    res.status(500).json({ error: `Failed to retrieve page: ${err.message}` });
  }
});

export default router;
