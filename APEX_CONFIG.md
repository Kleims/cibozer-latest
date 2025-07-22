# APEX_CONFIG.md - v3.0

## Health Calculation Formula
```
Test Health = (Backend_Pass_Rate × 0.6) + (Frontend_Pass_Rate × 0.4)
Security Health = 100 - (Critical × 20) - (High × 10) - (Medium × 2)
Performance Health = 100 × (Baseline_Time / Current_Time)
Overall Health = (Test × 0.5) + (Security × 0.3) + (Performance × 0.2)
```

## Mode Selection Rules
```python
if critical_vulnerabilities > 0:
    return "SECURITY"
elif health < 40 or critical_failures > 3:
    return "EMERGENCY"
elif iteration % 30 == 0:
    return "SECURITY"
elif iteration % 20 == 0:
    return "DOCUMENTATION"
elif iteration % 15 == 0 and performance_degraded:
    return "PERFORMANCE"
elif iteration % 10 == 0 and has_structural_issues:
    return "ARCHITECTURE"
elif health < 70:
    return "RECOVERY"
elif tech_debt > 80:
    return "DEBT_PAYMENT"
elif health > 85 and iteration % 5 == 0:
    return "FEATURE"
else:
    return "STANDARD"
```

## Mode Specifications

### EMERGENCY
**Goal**: Stop critical failures immediately
- Fix ONLY the most critical issue
- Add regression test
- Document root cause
- Max time: 2 hours

### RECOVERY  
**Goal**: Restore system to healthy state
- Fix top 2-3 test failures (80%)
- Improve critical path coverage (20%)
- No new features

### STANDARD
**Goal**: Balanced progress
- Fix 1-2 tests OR improve coverage (60%)
- Small improvements (30%)
  - IF you see obvious issues: simple refactors
  - IF not needed: add small feature/fix
- Address TODOs (10%)

### FEATURE
**Goal**: Add new capability
- Implement feature with tests (70%)
- Fix blockers only (20%)
- Update docs (10%)
- Requirement: >90% coverage on new code
- Note: Refactor ONLY if blocking feature

### ARCHITECTURE
**Goal**: Improve structure (when needed)
- Triggers:
  - Code duplication > 3 instances
  - Circular dependencies detected
  - Performance bottlenecks from poor structure
  - Major feature blocked by current design
- Actions:
  - Large-scale refactoring
  - Extract services/modules
  - Implement design patterns
  - Update dependency graph

### SECURITY
**Goal**: Zero vulnerabilities
- Run full audit
- Update all vulnerable deps
- Review auth code
- Add security tests
- Update SECURITY.log

### PERFORMANCE
**Goal**: Meet/exceed baselines
- Profile bottlenecks
- Optimize slowest parts
- Reduce bundle 10%
- Add benchmarks

### DOCUMENTATION
**Goal**: Knowledge capture
- Update API docs
- Architecture diagrams
- Setup guide
- Recent decisions (ADRs)

### DEBT_PAYMENT
**Goal**: Address accumulated issues
- Triggers:
  - Complexity score > threshold
  - TODO count > 20
  - Dead code detected
  - Team velocity declining
- Actions (pick based on need):
  - Refactor high-complexity functions
  - Remove unused code
  - Consolidate duplicates
  - Address oldest TODOs

### INTEGRATION
**Goal**: External reliability
- Add retry logic
- Circuit breakers
- Fallback mechanisms
- Integration tests

### COMPLIANCE
**Goal**: Meet requirements
- Privacy audit
- Accessibility check
- License review
- Audit trails

### RESILIENCE
**Goal**: System robustness
- Health endpoints
- Error boundaries
- Graceful degradation
- Chaos tests

## Success Criteria

### SUCCESS (all required)
- ✓ Critical tests pass
- ✓ No regression >2%
- ✓ No new vulnerabilities
- ✓ Performance within 10%
- ✓ Mode goals met

### PARTIAL
- Core goals met
- Minor regressions (<5%)
- Document issues

### FAILED  
- Critical tests fail
- Coverage drop >5%
- New vulnerabilities
- Performance >20% worse

## Weighted Coverage Formula
```
Weighted = (Backend_Coverage × 0.6) + (Frontend_Coverage × 0.4)
```

## Refactoring Guidelines by Mode

### Refactoring Philosophy:
- **Opportunistic**: Refactor when you see issues, not on schedule
- **Boy Scout Rule**: Leave code better than you found it
- **Pragmatic**: Only refactor if it provides clear value

### When to Refactor:
- **During STANDARD**: If touching code that needs cleanup
- **During DEBT_PAYMENT**: When metrics show it's needed
- **During ARCHITECTURE**: When structure blocks progress
- **During FEATURE**: Minimal - only if blocking
- **NEVER during**: Emergency, Security, Recovery modes

### Red Flags that Trigger Refactoring:
- Method > 50 lines
- Duplicated code (3+ copies)
- Complexity score > 10
- "TODO: refactor this" comments
- Performance bottlenecks from structure

## Commit Message Format
```
[MODE]: Iteration N - Brief description

Tests: Backend X/Y, Frontend A/B (Δ+Z)
Coverage: XX% → YY% (Δ+Z%), Weighted: WW%
[Additional metrics if relevant]
Result: [SUCCESS/PARTIAL/FAILED]
```

## Emergency Response
- EMERGENCY/SECURITY modes: Next iteration ASAP
- RECOVERY mode: Within 24 hours  
- Others: Regular schedule