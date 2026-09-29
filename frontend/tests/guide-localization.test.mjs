import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import ts from 'typescript'
import { load } from './helpers/load.mjs'

const ui = await load('tests/helpers/localization.ts')
const source = await readFile(
  new URL('../src/pages/methodology/ui/DataPage.tsx', import.meta.url),
  'utf8',
)
const file = ts.createSourceFile(
  'DataPage.tsx',
  source,
  ts.ScriptTarget.Latest,
  true,
  ts.ScriptKind.TSX,
)
const strings = new Set()
function visit(node) {
  if (ts.isStringLiteral(node) && /[А-Яа-яЁё]/u.test(node.text)) strings.add(node.text)
  ts.forEachChild(node, visit)
}
visit(file)

test('every guide instruction, role variant, FAQ and image label has both translations', () => {
  assert.ok(strings.size > 60, 'must inspect lesson data as well as direct translation calls')
  try {
    for (const language of ['kk', 'en']) {
      ui.setLanguage(language)
      for (const source of strings) {
        assert.ok(ui.messages[source]?.[language]?.trim(), `${language}: missing ${source}`)
        assert.equal(ui.t(source), ui.messages[source][language])
      }
      assert.equal(
        ui.t('Как начать работу'),
        language === 'kk' ? 'Жұмысты бастау' : 'Getting started',
      )
    }
    ui.setLanguage('ru')
    for (const source of strings) assert.equal(ui.t(source), source)
  } finally {
    ui.setLanguage('ru')
  }
})
