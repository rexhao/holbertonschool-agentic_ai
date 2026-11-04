# Copilot Context

## Prompt used

> Analyze the existing architecture in `@src/repositories/user.repository.js` and `@src/services/user.service.js`.
>
> Create a new file `src/services/user-export.service.js` that defines a data export service following the same architecture:
>
> 1. Access data exactly as `user.service.js` does: require the repository with the same relative path and module style, and read data only through `userRepository.findByEmail(email)`.
> 2. Use the same service pattern.
> 3. Reproduce the exception handling of `user.service.js`.
> 4. The method returns a JSON-serializable object containing the email and the user fields.
> 5. Do not modify any other file.

## Files provided as context

- `src/repositories/user.repository.js`
- `src/services/user.service.js`

## Generated service

- Name: `user-export.service.js`
- Path: `src/services/user-export.service.js`

## Reused architecture

The export service follows the existing CommonJS service pattern: it requires the singleton repository using the same relative path, exposes an async class method, and exports a singleton instance. It looks up users only with `findByEmail(email)` and throws the same error when no user is found. On success, it returns a plain object containing the repository's user fields and the requested email.
