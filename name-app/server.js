const { createServer } = require('node:http');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');

const PORT = process.env.PORT || 8090;
const html = readFileSync(join(__dirname, 'index.html'), 'utf8');

createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(html);
}).listen(PORT, () => {
  console.log(`Name app listening on http://localhost:${PORT}`);
});
