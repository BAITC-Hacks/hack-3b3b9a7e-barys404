import assert from 'node:assert/strict'
import test from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

import { load } from './helpers/load.mjs'

const { submittedSearchReducer } = await load('src/shared/lib/useSubmittedSearch.ts')
const { SearchForm } = await load('src/shared/ui/SearchForm.tsx')
const { ComparePage } = await load('src/pages/compare/ui/ComparePage.tsx')

test('typing and deleting do not apply a search before submission', () => {
  let state = { draft: 'old query', applied: 'old query' }
  for (const value of ['н', 'не', 'неврология', '']) {
    state = submittedSearchReducer(state, { type: 'edit', value })
    assert.equal(state.draft, value)
    assert.equal(state.applied, 'old query')
  }
})

test('submitting applies the complete trimmed query, including an empty query', () => {
  let state = submittedSearchReducer(
    { draft: '  University Medical Center  ', applied: '' },
    { type: 'submit' },
  )
  assert.deepEqual(state, {
    draft: 'University Medical Center',
    applied: 'University Medical Center',
  })
  state = submittedSearchReducer(state, { type: 'edit', value: '   ' })
  assert.deepEqual(submittedSearchReducer(state, { type: 'submit' }), { draft: '', applied: '' })
})

test('explicit clear resets both draft and applied search', () => {
  assert.deepEqual(submittedSearchReducer({ draft: 'new', applied: 'old' }, { type: 'clear' }), {
    draft: '',
    applied: '',
  })
})

test('the real search form edits without submitting and prevents full-page navigation', () => {
  const actions = []
  const form = SearchForm({
    value: 'query',
    label: 'Поиск',
    placeholder: 'Название',
    onChange: (value) => actions.push(['edit', value]),
    onSubmit: () => actions.push(['submit']),
    onClear: () => actions.push(['clear']),
  })
  assert.equal(form.type, 'form')
  const input = form.props.children.find((child) => child?.type === 'input')
  input.props.onChange({ target: { value: 'complete query' } })
  assert.deepEqual(actions, [['edit', 'complete query']])
  form.props.onSubmit({ preventDefault: () => actions.push(['preventDefault']) })
  assert.deepEqual(actions.slice(1), [['preventDefault'], ['submit']])
  const buttons = form.props.children.filter((child) => child?.type === 'button')
  assert.equal(buttons[0].props.type, 'button')
  assert.equal(buttons[1].props.type, 'submit')
  buttons[0].props.onClick()
  assert.deepEqual(actions.at(-1), ['clear'])
})

test('comparison keeps its search form mounted while data is loading', () => {
  const html = renderToStaticMarkup(
    createElement(ComparePage, {
      filters: { start: '2025-01-01', end: '2025-03-31', region: '', profile: '' },
      openHospital: () => {},
      focus: '',
    }),
  )
  assert.match(html, /role="search"/)
  assert.match(html, /aria-label="Найти организацию для сравнения"/)
  assert.match(html, /type="submit"[^>]*aria-label="Найти"/)
  assert.match(html, /Загружаем организации/)
})
