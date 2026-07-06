import { Router } from 'express';
import { runPython } from '../utils/python-runner.js';

const router = Router();

const SCRIPT_PATH = 'C:/Users/hernan.g/.gemini/config/plugins/fermi/skills/google-workspace/scripts/email_fetch.py';

// In-memory cache: { data, timestamp }
let cache = null;
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

router.get('/api/emails', async (req, res) => {
  const days = parseInt(req.query.days, 10) || 2;

  // Check cache (only valid for same or fewer days than cached)
  if (cache && (Date.now() - cache.timestamp < CACHE_TTL) && cache.days === days) {
    console.log(`[email] Serving from cache (${days} days)`);
    return res.json(cache.data);
  }

  try {
    const data = await runPython(SCRIPT_PATH, ['--days', String(days)]);
    cache = { data, timestamp: Date.now(), days };
    res.json(data);
  } catch (err) {
    console.error(`[email] ${err.message}`);
    res.status(500).json({ error: `Failed to fetch emails: ${err.message}` });
  }
});

export default router;
