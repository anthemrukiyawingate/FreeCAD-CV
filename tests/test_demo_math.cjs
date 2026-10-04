const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const pages = ['index.html', 'phase-1/index.html', 'phase-2/index.html', 'phase-3/index.html', 'capstone/index.html'];
const near = (actual, expected, tolerance = 1e-7) => assert.ok(Math.abs(actual - expected) < tolerance, `${actual} ≠ ${expected}`);
for (const page of pages) {
  test(`${page}: independent geometry and animation contracts`, () => {
    const html = fs.readFileSync(path.join(__dirname, '../docs', page), 'utf8');
    assert.equal((html.match(/<script>/g) || []).length, 1, 'one self-contained closure');
    assert.ok(!/<script[^>]+src=|<link[^>]+href=["']https?:/.test(html), 'no remote runtime');
    const context = { globalThis: {}, Math, Number, Object, RangeError };
    vm.runInNewContext(html.match(/<script>([\s\S]*?)<\/script>/)[1], context);
    const m = context.globalThis.CortexMath;
    assert.ok(m, 'testable pure math before browser initialization');
    for (let bits = 0; bits < 8; bits++) {
      const locks = { origin: Boolean(bits & 1), width: Boolean(bits & 2), height: Boolean(bits & 4) };
      assert.equal(m.rectangleDOF(locks), 4 - (locks.origin ? 2 : 0) - (locks.width ? 1 : 0) - (locks.height ? 1 : 0));
      const result = m.constrainRectangle({ x: 7, y: 9, width: 110, height: 60 }, locks, { x: 0, y: 0, width: 80, height: 50 });
      assert.equal(result.x, locks.origin ? 0 : 7);
      assert.equal(result.y, locks.origin ? 0 : 9);
      assert.equal(result.width, locks.width ? 80 : 110);
      assert.equal(result.height, locks.height ? 50 : 60);
    }
    assert.throws(() => m.constrainRectangle({ x: 0, y: 0, width: -1, height: 3 }, {}, {}), /positive/);
    // Half of a circle lies inside this rectangle: a closed-form oracle.
    near(m.circleRectangleIntersection({ x: 0, y: -10, width: 10, height: 20 }, { x: 0, y: 0, radius: 5 }), Math.PI * 25 / 2);
    near(m.circleRectangleIntersection({ x: -10, y: -10, width: 20, height: 20 }, { x: 0, y: 0, radius: 5 }), Math.PI * 25);
    near(m.circleRectangleIntersection({ x: 20, y: 20, width: 3, height: 4 }, { x: 0, y: 0, radius: 5 }), 0);
    near(m.circleRectangleIntersection({ x: -1, y: -2, width: 2, height: 4 }, { x: 0, y: 0, radius: 20 }), 8);
    near(m.circleRectangleIntersection({ x: 0, y: 0, width: 10, height: 10 }, { x: 0, y: 0, radius: 5 }), Math.PI * 25 / 4);
    near(m.circleRectangleIntersection({ x: 5, y: -5, width: 10, height: 10 }, { x: 0, y: 0, radius: 5 }), 0);
    // Translation must preserve overlap, including a rectangle spanning three quadrants.
    const shifted = m.circleRectangleIntersection({ x: 17, y: -29, width: 11, height: 13 }, { x: 23, y: -23, radius: 8 });
    const original = m.circleRectangleIntersection({ x: -6, y: -6, width: 11, height: 13 }, { x: 0, y: 0, radius: 8 });
    near(shifted, original);
    const sets = m.booleanAreas({ x: 0, y: -10, width: 10, height: 20 }, { x: 0, y: 0, radius: 5 });
    near(sets.union, 200 + Math.PI * 25 / 2);
    near(sets.difference, 200 - Math.PI * 25 / 2);
    near(sets.intersection, Math.PI * 25 / 2);
    assert.throws(() => m.booleanAreas({ x: 0, y: 0, width: 2, height: 3 }, { x: 0, y: 0, radius: NaN }), /finite/);
    // Independent cuboid dimensions, surface area, and cylindrical through-cut volume.
    const solid = m.plateProperties({ width: 100, depth: 60, thickness: 8, holeRadius: 5 });
    near(solid.volume, 48000 - Math.PI * 25 * 8);
    near(solid.footprint, 6000 - Math.PI * 25);
    assert.throws(() => m.plateProperties({ width: 10, depth: 8, thickness: 2, holeRadius: 5 }), /fit/);
    assert.throws(() => m.plateProperties({ width: Infinity, depth: 8, thickness: 2, holeRadius: 1 }), /finite/);
    const layout = m.layoutProperties({ projectorWidth: 120, cameraWidth: 40, gap: 20, margin: 12 });
    assert.equal(layout.plateWidth, 204);
    assert.equal(layout.cameraCenter - layout.projectorCenter, 100);
    near(m.lerpTime(0, 100, 1 / 60, 8), 100 * (1 - Math.exp(-8 / 60)));
    const once = m.lerpTime(0, 100, 1 / 30, 8);
    const twice = m.lerpTime(m.lerpTime(0, 100, 1 / 60, 8), 100, 1 / 60, 8);
    near(once, twice);
    near(m.lerpTime(0, 100, 1, 8, true), 100);
    assert.equal(m.resolutionScale(0.5, 40, 3), 0.5);
    assert.equal(m.resolutionScale(2, 8, 3), 2);
    assert.equal(m.resolutionScale(1.5, 8, 1), 1);
    assert.ok(m.resolutionScale(1.5, 40, 2) < 1.5);
    assert.ok(m.resolutionScale(0.5, 1000 / 60, 2) > 0.5, '60 Hz rendering must recover resolution after throttling');
    const frameStats = m.frameStatistics([10, 20, 30, 40]);
    assert.equal(frameStats.frameMs, 25);
    assert.equal(frameStats.fps, 40);
    assert.equal(frameStats.p95FrameMs, 40);
    assert.equal(m.frameStatistics([...Array(19).fill(10), 100]).p95FrameMs, 10);
    assert.throws(() => m.frameStatistics([]), /at least one/);
    assert.throws(() => m.frameStatistics([10, Infinity]), /finite/);
  });
}
