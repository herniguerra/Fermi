import { Router } from 'express';
import fs from 'fs/promises';
import path from 'path';

const router = Router();
const PROJECTS_FILE = path.join('D:', 'dev', 'Projects', 'projects.json');

router.get('/api/projects', async (req, res) => {
  try {
    const raw = await fs.readFile(PROJECTS_FILE, 'utf-8');
    const data = JSON.parse(raw);
    res.json(data);
  } catch (err) {
    console.error(`[projects] Error reading projects.json: ${err.message}`);
    res.status(500).json({ error: `Failed to read projects: ${err.message}` });
  }
});

export default router;
