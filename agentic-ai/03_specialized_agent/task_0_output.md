## Output ( Initialize yourself by reading the project memory file. Give me a brief summary of what you understood )

**Role:** I'm a Senior QA Engineer for this service. My only job is writing automated Jest tests. I must never modify, refactor, rename, or reformat anything in `/src`.

**Project context (`MEMORY.md`):**

- This is the Agentic E-Commerce microservice, in vanilla Node.js JavaScript, with no TypeScript.
- The main app stores prices in cents, but the legacy `cart_calculator.js` returns euros with two decimal places. That's known technical debt, so tests should pin down the current behavior and not assume cents.
- Absolute QA Rule: no changes to business logic in `/src` during test generation.
- Current priority: a robust unit test suite for the cart calculator before any migration.

**Testing standard (`TESTING_GUIDELINES.md`):**

- Test names follow `should_[EXPECTED_BEHAVIOR]_when_[CONDITION]`, for example `should_return_zero_when_cart_is_empty`.
- Each test body has three blocks separated by line breaks, marked with `// Arrange`, `// Act` (one call to the function under test), and `// Assert` (`expect()` checks).

**Before writing any test:** I still need to read the source file under test (`src/cart_calculator.js`) and state which constraints apply. I haven't read it yet since you only asked for initialization. Tell me when you want the tests written.
