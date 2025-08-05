# 🛡️ Cibozer Application Bulletproofing Prompt

Use this prompt to systematically bulletproof the Red Seal Question Bank Hub application. Copy and paste this entire prompt to ensure comprehensive coverage of all critical areas.

---

## PROMPT:

I need you to perform a comprehensive bulletproofing audit and fixes for the Red Seal Question Bank Hub (QBH) application. This is a production-ready educational platform for Canadian Red Seal trade certification. 

**Project Location:** C:\Empire\QBH

### 🎯 OBJECTIVE
Make this application absolutely bulletproof for production deployment with zero tolerance for errors, security vulnerabilities, or poor user experience. Fix everything you find immediately.

### 📋 SYSTEMATIC BULLETPROOFING CHECKLIST

Please complete ALL sections in order:

#### 1. 🔒 SECURITY HARDENING
- [ ] Audit all authentication flows for vulnerabilities
- [ ] Check for SQL injection vulnerabilities in all queries
- [ ] Validate all user inputs are properly sanitized
- [ ] Ensure all API endpoints have proper authentication
- [ ] Verify rate limiting is properly implemented
- [ ] Check for exposed sensitive data in logs
- [ ] Validate CORS configuration is restrictive
- [ ] Ensure all secrets are properly managed (not in code)
- [ ] Check for XSS vulnerabilities in frontend
- [ ] Validate CSRF protection
- [ ] Audit file upload security (if applicable)
- [ ] Check for dependency vulnerabilities (`npm audit fix`)
- [ ] Validate JWT implementation security
- [ ] Ensure proper password hashing (bcrypt rounds)
- [ ] Check for timing attacks in authentication

#### 2. 🐛 ERROR HANDLING & RESILIENCE
- [ ] Add try-catch blocks to all async operations
- [ ] Implement proper error boundaries in React
- [ ] Add fallback UI for all error states
- [ ] Ensure all promises have .catch handlers
- [ ] Validate all API responses before using data
- [ ] Add timeout handling for all external requests
- [ ] Implement retry logic for critical operations
- [ ] Add circuit breakers for external dependencies
- [ ] Ensure graceful degradation when services fail
- [ ] Add proper error logging without exposing sensitive data
- [ ] Validate all database operations have error handling
- [ ] Check for memory leaks in long-running operations
- [ ] Add health check endpoints
- [ ] Implement proper shutdown handlers

#### 3. 💾 DATABASE INTEGRITY & PERFORMANCE
- [ ] Add database indexes for all foreign keys
- [ ] Add indexes for commonly queried fields
- [ ] Implement database connection pooling
- [ ] Add transaction support for multi-step operations
- [ ] Validate all migrations are idempotent
- [ ] Add database backup strategy
- [ ] Implement query optimization for slow queries
- [ ] Add database constraints for data integrity
- [ ] Validate cascade deletes are properly configured
- [ ] Check for N+1 query problems
- [ ] Add database query logging and monitoring
- [ ] Implement proper database migration rollback
- [ ] Add data validation at database level
- [ ] Check for deadlock scenarios

#### 4. 🚀 PERFORMANCE OPTIMIZATION
- [ ] Implement Redis caching for frequently accessed data
- [ ] Add CDN configuration for static assets
- [ ] Optimize all images (compression, WebP format)
- [ ] Implement lazy loading for components
- [ ] Add pagination for all list endpoints
- [ ] Optimize bundle size (code splitting)
- [ ] Add service worker for offline capability
- [ ] Implement request debouncing where needed
- [ ] Add response compression (gzip)
- [ ] Optimize database queries (explain analyze)
- [ ] Add API response caching headers
- [ ] Implement request batching where applicable
- [ ] Minimize render cycles in React
- [ ] Add performance monitoring (Core Web Vitals)

#### 5. 🧪 TESTING COMPLETENESS
- [ ] Achieve 90%+ test coverage for backend
- [ ] Achieve 90%+ test coverage for frontend
- [ ] Add integration tests for all API endpoints
- [ ] Add E2E tests for critical user journeys
- [ ] Add load testing scripts
- [ ] Add security testing (OWASP)
- [ ] Add accessibility testing
- [ ] Add cross-browser testing setup
- [ ] Add mobile device testing
- [ ] Add performance testing benchmarks
- [ ] Validate all edge cases are tested
- [ ] Add chaos testing for resilience
- [ ] Add visual regression testing
- [ ] Add API contract testing

#### 6. 📱 USER EXPERIENCE PERFECTION
- [ ] Validate all forms have proper validation messages
- [ ] Add loading states for all async operations
- [ ] Add success confirmations for all actions
- [ ] Implement proper empty states
- [ ] Add helpful error messages (not technical)
- [ ] Add tooltips for complex features
- [ ] Implement undo functionality where applicable
- [ ] Add keyboard shortcuts for power users
- [ ] Validate all touch targets are 44px minimum
- [ ] Add proper focus management
- [ ] Implement autosave for long forms
- [ ] Add progress indicators for multi-step processes
- [ ] Validate all text is readable (contrast ratios)
- [ ] Add help documentation inline
- [ ] Implement smart defaults

#### 7. 📊 MONITORING & OBSERVABILITY
- [ ] Add application performance monitoring (APM)
- [ ] Implement structured logging with correlation IDs
- [ ] Add business metrics tracking
- [ ] Set up error tracking (Sentry or similar)
- [ ] Add uptime monitoring
- [ ] Implement audit logging for sensitive operations
- [ ] Add database query performance monitoring
- [ ] Set up alerting for critical issues
- [ ] Add user behavior analytics
- [ ] Implement A/B testing framework
- [ ] Add feature flag system
- [ ] Set up log aggregation
- [ ] Add custom dashboards for key metrics
- [ ] Implement SLI/SLO tracking

#### 8. 🚢 DEPLOYMENT READINESS
- [ ] Add production environment variables template
- [ ] Create comprehensive deployment documentation
- [ ] Add database migration scripts
- [ ] Implement blue-green deployment support
- [ ] Add rollback procedures
- [ ] Create backup and restore procedures
- [ ] Add SSL/TLS configuration
- [ ] Implement secrets management
- [ ] Add container health checks
- [ ] Create disaster recovery plan
- [ ] Add auto-scaling configuration
- [ ] Implement zero-downtime deployment
- [ ] Add deployment smoke tests
- [ ] Create runbooks for common issues

#### 9. 🔧 CODE QUALITY & MAINTAINABILITY
- [ ] Add JSDoc comments to all functions
- [ ] Implement consistent error codes
- [ ] Add API versioning strategy
- [ ] Create coding standards document
- [ ] Add pre-commit hooks for linting
- [ ] Implement consistent naming conventions
- [ ] Add architecture decision records (ADRs)
- [ ] Remove all console.log statements
- [ ] Add proper TypeScript types (no 'any')
- [ ] Implement dependency injection where needed
- [ ] Add code complexity limits
- [ ] Create component library documentation
- [ ] Add automated code review checks
- [ ] Implement feature toggles properly

#### 10. 🎯 BUSINESS CONTINUITY
- [ ] Add data export functionality
- [ ] Implement GDPR compliance features
- [ ] Add user data deletion capability
- [ ] Create admin dashboard for monitoring
- [ ] Add customer support tools
- [ ] Implement usage analytics
- [ ] Add billing failure handling
- [ ] Create user feedback system
- [ ] Add A/B testing infrastructure
- [ ] Implement email notification system
- [ ] Add subscription lifecycle handling
- [ ] Create content management system
- [ ] Add reporting and analytics
- [ ] Implement multi-tenancy if needed

### 🔍 SPECIFIC AREAS TO AUDIT

1. **Authentication System**
   - Registration flow with email verification
   - Login with proper session management
   - Password reset functionality
   - JWT token refresh mechanism
   - Role-based access control

2. **Payment Processing**
   - Stripe webhook handling
   - Subscription lifecycle management
   - Failed payment recovery
   - Invoice generation
   - Refund processing

3. **Question Bank System**
   - Question randomization algorithm
   - Progress tracking accuracy
   - Mock exam timing system
   - Answer validation logic
   - Statistics calculation

4. **Data Integrity**
   - User enrollment constraints
   - Question-answer relationships
   - Progress data consistency
   - Subscription state management
   - Trade filtering logic

5. **Mobile Experience**
   - Touch gesture handling
   - Offline functionality
   - Push notifications
   - App-like experience
   - Performance on slow networks

### 📝 OUTPUT REQUIREMENTS

For each issue found:
1. **Identify** the specific problem
2. **Explain** why it's a risk
3. **Fix** it immediately in the code
4. **Test** the fix works correctly
5. **Document** what was changed

### 🎬 EXECUTION INSTRUCTIONS

1. Start with security hardening (most critical)
2. Fix each issue as you find it
3. Run tests after each fix to ensure nothing breaks
4. Create a summary report of all fixes applied
5. Recommend any architectural changes needed

### 🚨 PRIORITY FOCUS AREAS

Based on the current MVP status (95% complete), prioritize:
1. **Security vulnerabilities** - Zero tolerance
2. **Data loss scenarios** - Prevent at all costs  
3. **Payment processing** - Must be 100% reliable
4. **User experience blockers** - Remove all friction
5. **Performance bottlenecks** - Sub-3 second page loads

### 💡 ADDITIONAL CONTEXT

- **Tech Stack**: Node.js, Express, React, TypeScript, SQLite, Stripe
- **Current State**: MVP with 8 high-demand trades ready
- **Target**: Production deployment for Canadian trade workers
- **Scale**: Expecting 10,000+ users in first year
- **Compliance**: Must meet Canadian privacy laws

---

**BEGIN BULLETPROOFING NOW** - Be thorough, be meticulous, and make this application unbreakable. Fix everything you find immediately and report what was done.