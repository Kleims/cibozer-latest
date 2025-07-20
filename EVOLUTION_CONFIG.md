# Evolution Engine Configuration

## Aspect Mapping
Map actual commit scopes to standard aspects for rotation tracking:

### Standard Aspects (for rotation):
1. **frontend** - UI, templates, static assets, user experience
2. **backend** - Core logic, API endpoints, business rules
3. **database** - Models, migrations, queries, data integrity
4. **testing** - Test suites, coverage, test infrastructure
5. **docs** - Documentation, README, API docs, comments
6. **security** - Authentication, authorization, validation, sanitization
7. **devops** - CI/CD, deployment, monitoring, infrastructure
8. **a11y** - Accessibility improvements
9. **logging** - Logging, monitoring, debugging tools
10. **refactor** - Code cleanup, optimization, technical debt

### Commit Format
```
type(aspect): description
```

Examples:
- `feat(backend): add meal plan sharing feature`
- `fix(security): add rate limiting to auth endpoints`
- `test(testing): add comprehensive test suite`
- `refactor(database): optimize query performance`

### Aspect Rotation Rules
1. Check last 3 commits for aspects used
2. Select different aspect for next iteration
3. Override if critical issues exist (failing tests → testing, security issues → security)
4. Document chosen aspect in commit and METRICS.md

### Current Rotation History
- Iteration 4: logging (centralized logging infrastructure)
- Iteration 5: testing (meal_optimizer test suite)
- Iteration 6: backend (sharing feature)
- Next suggested: frontend, database, or security