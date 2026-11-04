# Security review

## Prompt used

> @src/legacy_auth.js @test_security.js
>
> - SQL injection is possible because the query is built by concatenating email and password
> - Fix it with a parameterized query like SELECT \* FROM users WHERE email = ? AND password = ?, with email and password passed as the second argument to db.query
> - Update the mock db.query(sql, params) so the valid user is returned only when params match dev@entreprise.com and password123, and remove the "' OR '1'='1" check
> - Keep authenticateUser(email, password) and both return objects the same
> - Edit only src/legacy_auth.js
> - Run npm run test:security until both tests pass

## What was wrong

- `authenticateUser` built the SQL by sticking email and password into the string
- the mock treated an email containing `' OR '1'='1` as a successful admin login
- Test 1 passed, Test 2 failed

## What changed

- the query is now `SELECT * FROM users WHERE email = ? AND password = ?`
- email and password are passed as params `[email, password]`, not as raw SQL text
- the mock only returns the valid user when those params are `dev@entreprise.com` and `password123`
- removed the simulated SQL injection check

## Tests

- first run: Test 1 ok, Test 2 failed because the injection still logged in
- After copilot fixes the issue with the prompt above, `npm run test:security` now passes both tests
