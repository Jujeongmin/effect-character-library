#!/usr/bin/env node
// Local dev server for this repo — plain static file server, plus PUT support
// so tools/part_editor.html can save skeleton.json edits straight to disk.
// Not meant for deployment (GitHub Pages serves the repo statically as-is).
//
// Usage:
//   node tools/dev_server.js [port]
//   -> http://localhost:8934/characters/index.html
//   -> http://localhost:8934/tools/part_editor.html?char=<character id>
const http = require('http');
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const port = Number(process.argv[2]) || 8934;

const mime = {
  '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json',
  '.png': 'image/png', '.txt': 'text/plain', '.css': 'text/css',
  '.svg': 'image/svg+xml', '.woff2': 'font/woff2',
};

http.createServer((req, res) => {
  const p = decodeURIComponent(req.url.split('?')[0]);
  let filePath = path.join(root, p);

  if (req.method === 'PUT') {
    if (!filePath.startsWith(root)) { res.writeHead(403); res.end(); return; }
    const chunks = [];
    req.on('data', (c) => chunks.push(c));
    req.on('end', () => {
      fs.mkdirSync(path.dirname(filePath), { recursive: true });
      fs.writeFileSync(filePath, Buffer.concat(chunks));
      res.writeHead(200);
      res.end('ok ' + filePath);
    });
    return;
  }

  if (p === '/' || p.endsWith('/')) filePath = path.join(filePath, 'index.html');
  fs.readFile(filePath, (err, data) => {
    if (err) { res.writeHead(404); res.end('not found'); return; }
    res.writeHead(200, { 'Content-Type': mime[path.extname(filePath)] || 'application/octet-stream' });
    res.end(data);
  });
}).listen(port, () => console.log('dev server listening on http://localhost:' + port));
