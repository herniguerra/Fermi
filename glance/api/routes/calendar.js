import { Router } from 'express';
import { runPython } from '../utils/python-runner.js';

const router = Router();

const SCRIPT_PATH = 'C:/Users/hernan.g/.gemini/config/plugins/fermi/skills/google-workspace/scripts/calendar_fetch.py';

// In-memory cache: { data, timestamp }
let cache = null;
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

router.get('/api/calendar', async (req, res) => {
  const futureDays = parseInt(req.query.future_days, 10) || 7;

  if (cache && (Date.now() - cache.timestamp < CACHE_TTL) && cache.futureDays === futureDays) {
    console.log(`[calendar] Serving from cache (${futureDays} future days)`);
    return res.json(cache.data);
  }

  try {
    const data = await runPython(SCRIPT_PATH, ['--past-days', '0', '--future-days', String(futureDays)]);
    cache = { data, timestamp: Date.now(), futureDays };
    res.json(data);
  } catch (err) {
    console.error(`[calendar] ${err.message}`);
    res.status(500).json({ error: `Failed to fetch calendar: ${err.message}` });
  }
});

export default router;
