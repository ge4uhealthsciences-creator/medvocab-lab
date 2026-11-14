/**
 * GE4u Hub – real-time sync (Google Apps Script, free).
 * Copies status/today.csv (branch "status", written by social-post/post.py every ~10 min)
 * into the LiveStatus tab every minute, so the Hub no longer waits for IMPORTDATA's ~1 h cache.
 *
 * Install once: open the GE4u Orders sheet → Extensions → Apps Script → paste this file →
 * choose function "setup" → Run → allow access. Done; it then runs by itself every minute.
 */
const GE4U_CSV = 'https://raw.githubusercontent.com/ge4uhealthsciences-creator/medvocab-lab/status/status/today.csv';
const GE4U_API = 'https://api.github.com/repos/ge4uhealthsciences-creator/medvocab-lab/contents/status/today.csv?ref=status';

function syncLive() {
  let r = UrlFetchApp.fetch(GE4U_CSV + '?t=' + Date.now(), {muteHttpExceptions: true});
  if (r.getResponseCode() !== 200) {
    r = UrlFetchApp.fetch(GE4U_API, {headers: {Accept: 'application/vnd.github.raw'}, muteHttpExceptions: true});
    if (r.getResponseCode() !== 200) return;  // keep the last good table
  }
  const rows = Utilities.parseCsv(r.getContentText()).slice(0, 400)
    .map((x) => { const y = x.slice(0, 9); while (y.length < 9) y.push(''); return y; });
  if (rows.length < 1 || rows[0][0] !== 'date') return;  // not the status table
  const sh = SpreadsheetApp.getActive().getSheetByName('LiveStatus');
  sh.getRange('A1:I400').clearContent();
  sh.getRange(1, 1, rows.length, 9).setNumberFormat('@').setValues(rows);
}

function setup() {
  ScriptApp.getProjectTriggers().forEach((t) => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('syncLive').timeBased().everyMinutes(1).create();
  syncLive();
}
