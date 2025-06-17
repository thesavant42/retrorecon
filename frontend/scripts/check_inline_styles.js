const fs = require('fs');
const glob = require('glob');
let failed = false;

for (const file of glob.sync('templates/**/*.html')) {
  if (file.includes('indexBack.html')) continue;
  const content = fs.readFileSync(file, 'utf8');
  const regex = /<[^>]+\sstyle=/i;
  if (regex.test(content)) {
    console.error(`Inline style found in ${file}`);
    failed = true;
  }
}
if (failed) {
  process.exit(1);
}
