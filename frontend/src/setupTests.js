import '@testing-library/jest-dom/vitest'

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
})

const originalGetComputedStyle = window.getComputedStyle.bind(window)
window.getComputedStyle = (element, pseudoElt) => {
  if (pseudoElt) {
    return {
      getPropertyValue: () => '',
    }
  }
  return originalGetComputedStyle(element)
}
