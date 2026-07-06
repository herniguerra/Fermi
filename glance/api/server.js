import express from 'express';
import cors from 'cors';

// Route imports
import projectsRouter from './routes/projects.js';
import emailRouter from './routes/email.js';
import calendarRouter from './routes/calendar.js';
import memoryRouter from './routes/memory.js';
import dreamsRouter from './routes/dreams.js';
import reflectionsRouter from './routes/reflections.js';
import fermiStatusRouter from './routes/fermi-status.js';
import wikiRouter from './routes/wiki.js';

const app = express();
const PORT = 8099;

// Middleware
app.use(cors());
app.use(express.json());

// Request logging
app.use((req, res, next) => {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${req.method} ${req.url}`);
  next();
});

// Mount routes
app.use(projectsRouter);
app.use(emailRouter);
app.use(calendarRouter);
app.use(memoryRouter);
app.use(dreamsRouter);
app.use(reflectionsRouter);
app.use(fermiStatusRouter);
app.use(wikiRouter);

// Health check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: `Not found: ${req.method} ${req.url}` });
});

// Global error handler
app.use((err, req, res, _next) => {
  console.error(`[ERROR] ${err.stack || err.message}`);
  res.status(500).json({ error: 'Internal server error' });
});

app.listen(PORT, () => {
  console.log(`\n🚀 Glance API sidecar running on http://localhost:${PORT}`);
  console.log(`   Routes:`);
  console.log(`     GET /api/health`);
  console.log(`     GET /api/projects`);
  console.log(`     GET /api/emails?days=N`);
  console.log(`     GET /api/calendar?future_days=N`);
  console.log(`     GET /api/memory/:file`);
  console.log(`     GET /api/dreams`);
  console.log(`     GET /api/dreams/latest`);
  console.log(`     GET /api/reflections`);
  console.log(`     GET /api/reflections/archive`);
  console.log(`     GET /api/fermi/status`);
  console.log(`     GET /api/wiki/list`);
  console.log(`     GET /api/wiki/page?path=relative/path.md`);
  console.log(``);
});
