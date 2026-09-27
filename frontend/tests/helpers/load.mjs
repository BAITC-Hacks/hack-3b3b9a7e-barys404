import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
import { build } from 'esbuild'

// Render the real component modules without a browser. These tests cover
// visible data and labels, not layout or browser interactions.
export async function load(entry) {
  const result = await build({
    absWorkingDir: fileURLToPath(new URL('../..', import.meta.url)),
    entryPoints: [entry],
    bundle: true,
    packages: 'external',
    platform: 'node',
    format: 'cjs',
    write: false,
    logLevel: 'silent',
  })
  const module = { exports: {} }
  new Function('require', 'module', 'exports', result.outputFiles[0].text)(
    createRequire(import.meta.url),
    module,
    module.exports,
  )
  return module.exports
}
