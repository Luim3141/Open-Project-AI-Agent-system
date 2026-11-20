const assert = require('node:assert/strict');
// Exact comparison contract saved on Jira; not a substitute for native race or delivery tests.
function accepts(key, currentStatus, type=10011) {
  const reviewStatuses = type === 10011 ? [10016,10012,10019] : type === 10010 ? [10016,10012] : [];
  return `${currentStatus}-${key.length}` === `${key.substring(9,14)}-32` && reviewStatuses.includes(currentStatus);
}
assert(accepts('qag3-a05-10012-20261012185216872',10012));
assert(!accepts('qag3-a05-10018-20261012185215830',10012));
assert(!accepts('qag3-a05-10018-20261012185215830',10018));
assert(!accepts('qag3-a05-10012-',10012));
assert(!accepts('qag3-a05-10012-20261012185216872',10016));
assert(!accepts('qag3-a05-10019-20261012185216872',10019,10010));
assert(/^[A-Za-z]+$/.test('qagReviewEventKey'));
console.log('PASS: frozen status, blank timestamp, delayed non-review event and Subtask release guards. Native delivery/concurrency NOT VERIFIED.');
