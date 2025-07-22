# APEX_CONFIG v4.1

## Health Metrics
```python
# Component Health
Test_Health = (Backend_Pass% × 0.6) + (Frontend_Pass% × 0.4)
Test_Quality = (Assertions/LOC × 0.3) + (Mutations_Killed% × 0.3) + 
               (100-Flaky% × 0.2) + (Speed_Score × 0.2)
Security = 100 - (Critical × 20) - (High × 10) - (Medium × 2)
Performance = 100 × (Baseline_Time / Current_Time)
Logging = (Critical_Logged / Total_Critical) × 100
UX = (Nav_Clarity × 0.3) + (Content_Consistency × 0.3) + 
     (Journey_Success% × 0.2) + (Context_Preserved% × 0.2)

# Overall
Health = (Test × 0.25) + (Quality × 0.15) + (Security × 0.2) + 
         (Performance × 0.15) + (Logging × 0.1) + (UX × 0.15)
```

## Mode Selection
```python
if critical_vulns > 0: return "SECURITY"
elif health < 40 or critical_fails > 3: return "EMERGENCY"
elif test_quality < 50: return "TEST_QUALITY"
elif ux < 60: return "UX_COHERENCE"
elif logging < 60: return "LOGGING"
elif iteration % 30 == 0: return "SECURITY"
elif iteration % 25 == 0: return "LOGGING"
elif iteration % 20 == 0: return "DOCUMENTATION"
elif iteration % 18 == 0: return "UX_COHERENCE"
elif iteration % 15 == 0 and perf_degraded: return "PERFORMANCE"
elif iteration % 12 == 0 and quality < 70: return "TEST_QUALITY"
elif iteration % 10 == 0 and structural_issues: return "ARCHITECTURE"
elif health < 70: return "RECOVERY"
elif debt > 80: return "DEBT_PAYMENT"
elif health > 85 and iteration % 5 == 0: return "FEATURE"
else: return "STANDARD"
```

## Modes

### EMERGENCY
Fix critical issue only → Add regression test → Document → 2hr max

### RECOVERY
Fix top 3 test failures (80%) → Improve coverage (20%)

### STANDARD
- Tests/Coverage (35%)
- Review test quality (20%)
- Small improvements (20%)
- UX quick fixes (15%)
- Logging (5%)
- TODOs (5%)

### FEATURE
- Implementation + tests (50%)
- UX integration (20%)
- Blockers only (10%)
- Feature logging (10%)
- Docs (10%)
Requirements: 90% coverage, quality >75%, UX validated

### TEST_QUALITY
- Mutation testing (30%)
- Fix flaky tests (25%)
- Add assertions (20%)
- Parameterize tests (15%)
- Property tests (10%)

### UX_COHERENCE
- Navigation audit (30%)
- Content consistency (25%)
- Journey testing (25%)
- Context preservation (20%)

### ARCHITECTURE
Triggers: Duplication >3, circular deps, blockers
Actions: Refactor, extract, patterns, standardize

### SECURITY
Audit → Update deps → Auth review → Security tests → Logging

### PERFORMANCE
Profile → Optimize → Reduce bundle → Benchmarks → User metrics

### DOCUMENTATION
API docs → Diagrams → Test docs → UX patterns → ADRs

### DEBT_PAYMENT
Triggered by: Complexity, TODOs >20, dead code, velocity drop
Fix based on priority

### LOGGING
Security → Performance → Business → System → Compliance

## Standards

**Tests**: 3+ assertions, <100ms, no flaky, 80%+ mutation score
**Code**: <50 lines/method, <10 complexity, no duplication
**UX**: <5 clicks to goal, consistent terms, mobile-first

## Debt Tracking
```
Test_Debt = (No_Assertions × 5) + (Flaky × 10) + (Slow × 2) + 
            (Duplicate × 3) + (Commented × 20)
UX_Debt = (Dead_Ends × 10) + (Inconsistent × 3) + (Broken_Flows × 15) + 
          (No_Errors × 5) + (Unclear_CTAs × 2)
```

## Commit Format
```
[MODE]: Iteration N - Description

Tests: Backend X/Y, Frontend A/B (Δ+Z)
Coverage: XX%→YY% (Δ+Z%), Weighted: WW%, Effective: EE%
Quality: XX%→YY% (Δ+Z%)
UX: XX%→YY% (Δ+Z%)
Result: [SUCCESS/PARTIAL/FAILED]

🤖 APEX v4.1
```

## Success Criteria
SUCCESS: All critical pass + Quality >70% + UX >75% + No regression + Goals met
PARTIAL: Core goals met, minor issues documented
FAILED: Critical fail OR quality <50% OR major regression