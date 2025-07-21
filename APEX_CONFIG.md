# APEX Configuration - Cibozer
*Last Updated: 2025-07-21*

## Health Calculation Formula

### Base Score
- Starting health: 100 points
- Floor: 0 (cannot go negative)
- Ceiling: 100 (perfect health)

### Failure Penalties
**Critical Module Failures** (auth/payment/database/video):
- Penalty: 10 points per failure
- These are high-priority and affect core functionality

**Normal Test Failures**:
- Small test suite (<50 tests): 5 points per failure
- Medium test suite (50-200 tests): 3 points per failure
- Large test suite (>200 tests): 2 points per failure

### Single-Component Project
Since this is a Flask monolith with integrated frontend:
- Tests run as single suite: `pytest`
- Health based on total test results
- Critical modules: auth.py, payments.py, models.py, video_generator.py

### Special Considerations
- Database connection failures: Immediate health = 0
- Build/dependency failures: Immediate health = 0
- No tests found: Health = 0
- Deprecation warnings: 1 point per warning (max 10)

## Mode Determination Rules

### Priority Order (check in sequence)
1. **RECOVERY MODE**
   - Condition: health < 60 OR last iteration FAILED/PARTIAL
   - Override: Always takes precedence
   - Focus: Fix most critical issue only

2. **ARCHITECTURE MODE**
   - Condition: iteration % 10 == 0 AND health > 80
   - Focus: Refactor patterns, reduce duplication
   - Requirement: Last 3 iterations must be successful

3. **FEATURE MODE**
   - Condition: iteration % 5 == 0 AND health > 85
   - Focus: Add new functionality (80% effort)
   - Requirement: No critical failures

4. **STANDARD MODE**
   - Condition: Default when no other mode applies
   - Focus: Fix 1-2 issues (80%) + improvement (20%)
   - Also used when: 60 ≤ health < 70 (stability focus)

## Success Criteria

### Result Determination
**SUCCESS**:
- All critical modules pass (100% pass rate)
- No test regressions (or documented reason)
- Coverage didn't drop > 2%
- pytest completes successfully
- Health improved or maintained > 90%

**PARTIAL**:
- 1-2 minor test failures
- Non-critical modules affected
- Health between 60-89%
- Some progress made but not all goals met

**FAILED**:
- Critical module failures
- pytest crashes or hangs
- Health < 60
- Regression in test count
- Unable to complete primary task

## Trend Analysis

### Health Trends
- Track last 3 iterations for trend
- Improving: 3 consecutive increases
- Declining: 3 consecutive decreases
- Stable: Variance < 5 points

### Mode History
- Don't repeat FEATURE/ARCHITECTURE if last attempt failed
- After RECOVERY, prefer STANDARD for stabilization
- Track success rate per mode type

## Calculation Examples

### Example 1: Normal Run
```
Total: 60 tests, 4 failures (1 in auth module)
Health: 100 - (1×10) - (3×3) = 81
```

### Example 2: Critical Failures
```
Total: 60 tests, 6 failures (2 in payments, 1 in auth)
Health: 100 - (3×10) - (3×3) = 61
```

## Coverage Calculation

### Accurate Coverage Tracking
- Run coverage: `pytest --cov=. --cov-report=term-missing`
- HTML report: `pytest --cov=. --cov-report=html`
- Coverage config in pytest.ini

### Coverage Health Indicators
- 80%+ : Excellent ✅
- 60-79%: Good 🟡
- 40-59%: Fair 🟠
- <40%  : Poor 🔴

## Flask-Specific Considerations

### Critical Test Categories
- Authentication flows (login, logout, registration)
- Payment processing (Stripe integration)
- Database operations (models, migrations)
- Video generation pipeline
- PDF generation
- API endpoints

### Common Issues to Watch
- SQLAlchemy session management
- CSRF token validation
- File upload security
- Async task handling
- Memory leaks in video processing

## Configuration History
- 2025-07-21: Initial configuration for Cibozer Flask project
- Based on APEX v2 universal template
- Adapted for Python/Flask architecture

## Notes
- Focus on integration tests due to monolithic architecture
- Video/PDF generation may require mocking for speed
- Database tests should use test database
- Consider test markers for slow tests