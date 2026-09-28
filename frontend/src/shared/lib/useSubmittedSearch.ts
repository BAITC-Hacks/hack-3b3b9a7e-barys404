import { useReducer } from 'react'

type SearchState = { draft: string; applied: string }
type SearchAction = { type: 'edit'; value: string } | { type: 'submit' } | { type: 'clear' }

export function submittedSearchReducer(state: SearchState, action: SearchAction): SearchState {
  switch (action.type) {
    case 'edit':
      return { ...state, draft: action.value }
    case 'submit': {
      const term = state.draft.trim()
      return { draft: term, applied: term }
    }
    case 'clear':
      return { draft: '', applied: '' }
  }
}

export function useSubmittedSearch() {
  const [state, dispatch] = useReducer(submittedSearchReducer, { draft: '', applied: '' })
  return {
    ...state,
    setDraft: (value: string) => dispatch({ type: 'edit', value }),
    submit: () => dispatch({ type: 'submit' }),
    clear: () => dispatch({ type: 'clear' }),
  }
}
