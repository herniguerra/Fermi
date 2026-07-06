import { execFile } from 'child_process';
import path from 'path';

/**
 * Spawns a Python script and captures its JSON stdout output.
 * Handles Windows encoding issues and timeouts gracefully.
 */
export function runPython(scriptPath, args = []) {
  return new Promise((resolve, reject) => {
    // Use pyenv Python binary directly (Node's execFile doesn't resolve .bat shims)
    const pythonCmd = process.platform === 'win32'
      ? 'C:\\Users\\hernan.g\\.pyenv\\pyenv-win\\versions\\3.11.9\\python.exe'
      : 'python3';

    const opts = {
      timeout: 30_000,
      maxBuffer: 10 * 1024 * 1024, // 10MB
      encoding: 'utf8',
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
      windowsHide: true,
    };

    execFile(pythonCmd, [scriptPath, ...args], opts, (error, stdout, stderr) => {
      if (error) {
        const msg = error.killed
          ? `Python script timed out after 30s: ${path.basename(scriptPath)}`
          : `Python error (${path.basename(scriptPath)}): ${error.message}`;
        console.error(`[python-runner] ${msg}`);
        if (stderr) console.error(`[python-runner] stderr: ${stderr}`);
        return reject(new Error(msg));
      }

      try {
        const data = JSON.parse(stdout.trim());
        resolve(data);
      } catch (parseErr) {
        console.error(`[python-runner] Failed to parse JSON from ${path.basename(scriptPath)}`);
        console.error(`[python-runner] stdout was: ${stdout.substring(0, 500)}`);
        reject(new Error(`Invalid JSON output from ${path.basename(scriptPath)}`));
      }
    });
  });
}
