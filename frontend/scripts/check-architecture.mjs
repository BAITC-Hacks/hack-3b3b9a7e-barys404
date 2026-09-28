import fs from 'node:fs'
import path from 'node:path'
import ts from 'typescript'

const root = path.resolve('src')
const layers = ['app', 'pages', 'widgets', 'features', 'entities', 'shared']
const walk = (dir) =>
  fs
    .readdirSync(dir, { withFileTypes: true })
    .flatMap((entry) =>
      entry.isDirectory() ? walk(path.join(dir, entry.name)) : [path.join(dir, entry.name)],
    )
const location = (file) => {
  const [layer, slice] = path.relative(root, file).split(path.sep)
  return { layer, slice: ['app', 'shared'].includes(layer) ? null : slice }
}
const errors = []
for (const file of walk(root).filter((file) => /\.(ts|tsx)$/.test(file))) {
  const source = ts.createSourceFile(
    file,
    fs.readFileSync(file, 'utf8'),
    ts.ScriptTarget.Latest,
    true,
  )
  const from = location(file)
  const visit = (node) => {
    const specifier =
      (ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) && node.moduleSpecifier
    if (specifier && ts.isStringLiteral(specifier) && specifier.text.startsWith('.')) {
      const target = path.resolve(path.dirname(file), specifier.text)
      const to = location(target)
      const line = source.getLineAndCharacterOfPosition(node.getStart()).line + 1
      const fail = (reason) =>
        errors.push(`${path.relative(process.cwd(), file)}:${line}: ${reason}`)
      if (!layers.includes(to.layer)) fail(`Import outside FSD layers: ${specifier.text}`)
      else if (layers.indexOf(to.layer) < layers.indexOf(from.layer))
        fail(`Upward import ${from.layer} → ${to.layer}`)
      else if (from.layer === to.layer && from.slice && from.slice !== to.slice)
        fail(`Cross-slice import ${from.slice} → ${to.slice}`)
      else if (
        to.slice &&
        (from.layer !== to.layer || from.slice !== to.slice) &&
        !/[/\\]index(?:\.ts)?$/.test(target)
      )
        fail(`Use the public API of ${to.layer}/${to.slice}`)
    }
    ts.forEachChild(node, visit)
  }
  visit(source)
}
if (errors.length) {
  console.error(errors.join('\n'))
  process.exitCode = 1
} else console.log('FSD boundaries and public imports: OK')
