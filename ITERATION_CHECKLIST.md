# 🔄 APEX v4.1 - Iteration Checklist

## ☐ 1. Initialize
```bash
ITER=$(cat .iteration 2>/dev/null || echo "0")
echo "Starting Iteration: $((ITER+1))"
touch METRICS.md FAILED_ATTEMPTS.md SECURITY.log
```

## ☐ 2. Calculate Health

☐ Run: `pytest` (all tests)
☐ Run: `pip-audit` or `safety check`
☐ Run: `pytest --cov=. --cov-report=term-missing`
☐ Calculate scores (see APEX_CONFIG.md):
- Test Health: _____
- Security Health: _____
- Performance Health: _____
- Overall Health: _____

## ☐ 3. Check Triggers & Select Mode
Current iteration: $((ITER+1))

☐ Critical vulnerabilities? _____
☐ Performance degraded? _____
☐ Structural issues? _____
☐ Tech debt score: _____

**Selected Mode: [MODE]** (see APEX_CONFIG.md rules)

## ☐ 4. Create Branch
```bash
git checkout main && git pull
git checkout -b "iteration-$((ITER+1))-[MODE]"
```

## ☐ 5. BEFORE Metrics

☐ Tests: B:___/___ F:___/___
☐ Coverage: B:___% F:___% W:____%
☐ Security: C:___ H:___ M:___
☐ Performance: API:___ms Bundle:___KB
☐ Complexity: ___ TODOs: ___

## ☐ 6. Execute [MODE] Work
Check APEX_CONFIG.md for mode details.

☐ Primary objective complete
☐ Secondary objective (if applicable)
☐ Tests added/updated
☐ No regressions introduced

## ☐ 7. AFTER Metrics

☐ Tests: B:___/___ (Δ___) F:___/___ (Δ___)
☐ Coverage: B:__% (Δ___) F:__% (Δ___) W:__% (Δ___)
☐ Security: C:___ H:___ M:___ (Δ___)
☐ Performance: API:___ms (Δ___) Bundle:___KB (Δ___)
☐ Complexity: ___ (Δ___) TODOs: ___ (Δ___)

## ☐ 8. Evaluate Result
Check success criteria in APEX_CONFIG.md

☐ Critical tests pass? _____
☐ Coverage regression <2%? _____
☐ No new vulnerabilities? _____
☐ Performance within 10%? _____
☐ Mode goals achieved? _____

**Result: [SUCCESS/PARTIAL/FAILED]**

## ☐ 9. Commit
```bash
git add -A
git commit -m "[MODE]: Iteration N - [description]

Tests: B:X/Y F:A/B (Δ+N)  
Coverage: X%→Y% Weighted: Z%
Result: [RESULT]

🤖 APEX v4.1"
```

## ☐ 10. Update METRICS.md
```markdown
## Iteration #N - [DATE TIME]
Mode: [MODE] | Health: X/100 | Result: [RESULT]
Tests: B:X/Y F:A/B | Coverage: W:X%
Changes: [what was done]
```

## ☐ 11. Finalize
```bash
echo "$((ITER+1))" > .iteration

# If SUCCESS: merge
if [ "[RESULT]" == "SUCCESS" ]; then
    git checkout main
    git merge --no-ff "iteration-$((ITER+1))-[MODE]"
fi
```

## ☐ 12. Final Checks

☐ All boxes checked above
☐ METRICS.md has new entry
☐ .iteration incremented
☐ If FAILED: updated FAILED_ATTEMPTS.md
☐ If EMERGENCY/SECURITY: schedule immediate next iteration