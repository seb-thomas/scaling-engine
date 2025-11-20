# Frontend Testing

This project uses [Vitest](https://vitest.dev/) and [React Testing Library](https://testing-library.com/react) for testing.

## Running Tests

```bash
# Run tests in watch mode (default)
bun test

# Run tests once
bun run test:run

# Run tests with UI
bun run test:ui

# Run tests with coverage
bun run test:coverage
```

## Test Structure

Tests are located in `__tests__` directories next to the components they test:

```
src/
  components/
    BookCard.tsx
    __tests__/
      BookCard.test.tsx
```

## Writing Tests

Example test file:

```typescript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MyComponent } from '../MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
```

## Available Matchers

We use `@testing-library/jest-dom` matchers, which provide helpful assertions like:
- `toBeInTheDocument()`
- `toHaveAttribute()`
- `toBeDisabled()`
- `toHaveTextContent()`

See [jest-dom documentation](https://github.com/testing-library/jest-dom) for full list.

