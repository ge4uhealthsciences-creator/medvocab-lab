// Export the doctor-mode cases of ge4u-hospital-3d.html to data/game/cases.json for the video renderer.
// Usage: node scripts/export_game_cases.js
const fs = require('fs');
const h = fs.readFileSync(__dirname + '/../ge4u-hospital-3d.html', 'utf8');
const s = h.split('<script>').slice(1).map(x => x.split('</script>')[0]).find(x => x.includes('const CASES='));
const a = s.indexOf('const CASES='), b = s.indexOf('const PROF=');
const CASES = new Function(s.slice(a, b) + ';return CASES')();
const out = CASES.filter(c => Array.isArray(c.d) && c.d.length === 3 && c.d.some(x => x[1]) && c.o && c.o[0]).map((c, i) => ({
  id: i, dept: c.dept, er: !!c.er, cc: c.cc, who: c.who, vit: c.vit || null, says: c.o[0],
  options: c.d.map(x => ({ en: x[0], ok: !!x[1], vi: x[2] || '', why: x[3] || '' })),
  src: c.src || null,
}));
fs.writeFileSync(__dirname + '/../data/game/cases.json', JSON.stringify(out, null, 1));
console.log(out.length, 'cases');
