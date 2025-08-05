/**
 * Comprehensive API Response Validator for Cibozer
 * Validates all API responses to ensure data integrity and security
 */

class ApiResponseValidator {
    constructor() {
        this.validationRules = new Map();
        this.setupDefaultRules();
    }
    
    setupDefaultRules() {
        // Default validation rules for common API responses
        this.validationRules.set('/api/generate-meal-plan', {
            required: ['success', 'meal_plan'],
            types: {
                success: 'boolean',
                meal_plan: 'object',
                credits_remaining: 'number'
            },
            structure: {
                meal_plan: {
                    required: ['days', 'meals'],
                    types: {
                        days: 'number',
                        meals: 'array'
                    }
                }
            }
        });
        
        this.validationRules.set('/api/save-meal-plan', {
            required: ['success', 'meal_plan_id'],
            types: {
                success: 'boolean',
                meal_plan_id: 'number',
                message: 'string'
            }
        });
        
        this.validationRules.set('/api/health', {
            required: ['status', 'timestamp'],
            types: {
                status: 'string',
                timestamp: 'string',
                version: 'string',
                response_time_ms: 'number'
            },
            values: {
                status: ['healthy', 'degraded', 'unhealthy']
            }
        });
        
        this.validationRules.set('/auth/login', {
            required: ['success'],
            types: {
                success: 'boolean',
                message: 'string',
                redirect_url: 'string'
            }
        });
    }
    
    /**
     * Validate API response data
     * @param {string} endpoint - API endpoint path
     * @param {Object} response - Response data to validate
     * @returns {Object} Validation result
     */
    validateResponse(endpoint, response) {
        const validation = {
            valid: true,
            errors: [],
            warnings: [],
            sanitized: null
        };
        
        try {
            // Check if response is valid JSON object
            if (typeof response !== 'object' || response === null) {
                validation.valid = false;
                validation.errors.push('Response is not a valid object');
                return validation;
            }
            
            // Get validation rules for endpoint
            const rules = this.getValidationRules(endpoint);
            
            if (!rules) {
                // No specific rules, do basic validation
                validation.sanitized = this.basicSanitization(response);
                validation.warnings.push('No specific validation rules found for endpoint');
                return validation;
            }
            
            // Validate required fields
            const missingFields = this.validateRequiredFields(response, rules.required || []);
            if (missingFields.length > 0) {
                validation.valid = false;
                validation.errors.push(`Missing required fields: ${missingFields.join(', ')}`);
            }
            
            // Validate field types
            const typeErrors = this.validateFieldTypes(response, rules.types || {});
            if (typeErrors.length > 0) {
                validation.valid = false;
                validation.errors.push(...typeErrors);
            }
            
            // Validate field values
            const valueErrors = this.validateFieldValues(response, rules.values || {});
            if (valueErrors.length > 0) {
                validation.valid = false;
                validation.errors.push(...valueErrors);
            }
            
            // Validate nested structures
            if (rules.structure) {
                const structureErrors = this.validateStructure(response, rules.structure);
                if (structureErrors.length > 0) {
                    validation.valid = false;
                    validation.errors.push(...structureErrors);
                }
            }
            
            // Sanitize response data
            validation.sanitized = this.sanitizeResponse(response, rules);
            
        } catch (error) {
            validation.valid = false;
            validation.errors.push(`Validation error: ${error.message}`);
        }
        
        return validation;
    }
    
    /**
     * Get validation rules for endpoint
     */
    getValidationRules(endpoint) {
        // Try exact match first
        if (this.validationRules.has(endpoint)) {
            return this.validationRules.get(endpoint);
        }
        
        // Try pattern matching
        for (const [pattern, rules] of this.validationRules.entries()) {
            if (pattern.includes('*') && this.matchesPattern(endpoint, pattern)) {
                return rules;
            }
        }
        
        return null;
    }
    
    /**
     * Validate required fields
     */
    validateRequiredFields(response, required) {
        const missing = [];
        for (const field of required) {
            if (!(field in response)) {
                missing.push(field);
            }
        }
        return missing;
    }
    
    /**
     * Validate field types
     */
    validateFieldTypes(response, types) {
        const errors = [];
        for (const [field, expectedType] of Object.entries(types)) {
            if (field in response) {
                const actualType = Array.isArray(response[field]) ? 'array' : typeof response[field];
                if (actualType !== expectedType) {
                    errors.push(`Field '${field}' should be ${expectedType}, got ${actualType}`);
                }
            }
        }
        return errors;
    }
    
    /**
     * Validate field values
     */
    validateFieldValues(response, values) {
        const errors = [];
        for (const [field, allowedValues] of Object.entries(values)) {
            if (field in response) {
                if (!allowedValues.includes(response[field])) {
                    errors.push(`Field '${field}' has invalid value '${response[field]}'. Allowed: ${allowedValues.join(', ')}`);
                }
            }
        }
        return errors;
    }
    
    /**
     * Validate nested structure
     */
    validateStructure(response, structure) {
        const errors = [];
        for (const [field, fieldRules] of Object.entries(structure)) {
            if (field in response && typeof response[field] === 'object') {
                const missingFields = this.validateRequiredFields(response[field], fieldRules.required || []);
                if (missingFields.length > 0) {
                    errors.push(`Missing required fields in '${field}': ${missingFields.join(', ')}`);
                }
                
                const typeErrors = this.validateFieldTypes(response[field], fieldRules.types || {});
                errors.push(...typeErrors.map(err => `In '${field}': ${err}`));
            }
        }
        return errors;
    }
    
    /**
     * Basic sanitization for responses without specific rules
     */
    basicSanitization(response) {
        const sanitized = {};
        
        for (const [key, value] of Object.entries(response)) {
            // Sanitize strings
            if (typeof value === 'string') {
                sanitized[key] = this.sanitizeString(value);
            }
            // Recursively sanitize objects
            else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                sanitized[key] = this.basicSanitization(value);
            }
            // Limit array size for security
            else if (Array.isArray(value)) {
                sanitized[key] = value.slice(0, 1000); // Limit to 1000 items
            }
            // Copy other types as-is
            else {
                sanitized[key] = value;
            }
        }
        
        return sanitized;
    }
    
    /**
     * Sanitize response data
     */
    sanitizeResponse(response, rules) {
        const sanitized = {};
        
        // Only include known fields
        const allowedFields = [
            ...(rules.required || []),
            ...Object.keys(rules.types || {}),
            ...Object.keys(rules.values || {})
        ];
        
        for (const field of allowedFields) {
            if (field in response) {
                const value = response[field];
                
                // Sanitize strings
                if (typeof value === 'string') {
                    sanitized[field] = this.sanitizeString(value);
                }
                // Sanitize arrays
                else if (Array.isArray(value)) {
                    sanitized[field] = value.slice(0, 1000).map(item => {
                        if (typeof item === 'string') {
                            return this.sanitizeString(item);
                        }
                        return item;
                    });
                }
                // Copy other types
                else {
                    sanitized[field] = value;
                }
            }
        }
        
        return sanitized;
    }
    
    /**
     * Sanitize string values
     */
    sanitizeString(str) {
        if (typeof str !== 'string') return str;
        
        // Limit string length
        const maxLength = 10000;
        let sanitized = str.length > maxLength ? str.substring(0, maxLength) : str;
        
        // Remove potentially dangerous characters (basic XSS prevention)
        sanitized = sanitized.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
        sanitized = sanitized.replace(/javascript:/gi, '');
        sanitized = sanitized.replace(/on\w+\s*=/gi, '');
        
        return sanitized;
    }
    
    /**
     * Check if endpoint matches pattern
     */
    matchesPattern(endpoint, pattern) {
        const regex = new RegExp(pattern.replace(/\*/g, '.*'));
        return regex.test(endpoint);
    }
    
    /**
     * Add custom validation rule
     */
    addValidationRule(endpoint, rules) {
        this.validationRules.set(endpoint, rules);
    }
    
    /**
     * Validate and handle API response
     */
    async validateAndHandle(endpoint, response) {
        const validation = this.validateResponse(endpoint, response);
        
        if (!validation.valid) {
            // Log validation errors
            if (window.ErrorHandling) {
                window.ErrorHandling.logError('API Response Validation Failed', {
                    endpoint,
                    errors: validation.errors,
                    response: response
                });
            }
            
            // Throw validation error
            const error = new Error(`API response validation failed: ${validation.errors.join(', ')}`);
            error.code = 'VALIDATION_ERROR';
            error.details = validation;
            throw error;
        }
        
        if (validation.warnings.length > 0) {
            // Log warnings
            if (window.ErrorHandling) {
                window.ErrorHandling.logError('API Response Validation Warnings', {
                    endpoint,
                    warnings: validation.warnings
                });
            }
        }
        
        return validation.sanitized || response;
    }
}

// Create global instance
const apiResponseValidator = new ApiResponseValidator();

// Export for use in other scripts
window.ApiResponseValidator = apiResponseValidator;

// Enhance the global API client to use validation
if (window.apiClient) {
    // Store original methods
    const originalGet = window.apiClient.get.bind(window.apiClient);
    const originalPost = window.apiClient.post.bind(window.apiClient);
    
    // Wrap methods with validation
    window.apiClient.get = async function(url, options = {}) {
        const response = await originalGet(url, options);
        return await apiResponseValidator.validateAndHandle(url, response.data || response);
    };
    
    window.apiClient.post = async function(url, data = null, options = {}) {
        const response = await originalPost(url, data, options);
        return await apiResponseValidator.validateAndHandle(url, response.data || response);
    };
}