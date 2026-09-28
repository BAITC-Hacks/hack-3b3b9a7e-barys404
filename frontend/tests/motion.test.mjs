import assert from 'node:assert/strict'
import test from 'node:test'
import { load } from './helpers/load.mjs'

const { animateEntrance } = await load('src/shared/lib/useEntrance.ts')

test('native entrance is visible, cancels on cleanup and respects changed motion preference', () => {
  const original = globalThis.window
  let change,
    frames,
    options,
    cancellations = 0,
    detached = 0
  const preference = {
    matches: false,
    addEventListener: (_name, listener) => {
      change = listener
    },
    removeEventListener: () => {
      detached++
    },
  }
  globalThis.window = { matchMedia: () => preference }
  try {
    const cleanup = animateEntrance({
      animate: (keys, timing) => {
        frames = keys
        options = timing
        return {
          cancel: () => {
            cancellations++
          },
          addEventListener: () => {},
        }
      },
    })
    assert.equal(options.duration, 560)
    assert.equal(options.fill, 'backwards')
    assert.equal(options.iterations, undefined)
    assert.deepEqual(Object.keys(frames[0]).sort(), ['opacity', 'transform'])
    preference.matches = true
    change()
    assert.equal(cancellations, 1)
    cleanup()
    assert.equal(detached, 1)
    assert.equal(cancellations, 2)
  } finally {
    globalThis.window = original
  }
})

test('reduced motion or unsupported animation leaves content untouched', () => {
  const original = globalThis.window
  globalThis.window = { matchMedia: () => ({ matches: true }) }
  try {
    animateEntrance({ animate: () => assert.fail('must not animate') })()
    globalThis.window = { matchMedia: () => ({ matches: false }) }
    animateEntrance({})()
  } finally {
    globalThis.window = original
  }
})
