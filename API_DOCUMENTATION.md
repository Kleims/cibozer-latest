# Cibozer API Documentation

## Overview

This document describes the Cibozer API endpoints with complete validation schemas and examples.

## Authentication

Most endpoints require authentication. Use the login endpoint to obtain a session.

### Login
```http
POST /auth/login
```

**Request Schema:**
```json
{
  "email": "string (email format, required)",
  "password": "string (required)",
  "remember": "boolean (optional, default: false)"
}
```

**Example:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "remember": true
}
```

### Registration
```http
POST /auth/register
```

**Request Schema:**
```json
{
  "email": "string (email format, required)",
  "password": "string (min 8 chars, required)",
  "full_name": "string (2-100 chars, required)",
  "agree_terms": "boolean (must be true, required)"
}
```

## Meal Planning API

### Generate Meal Plan
```http
POST /api/generate
```

**Authentication:** Required

**Request Schema:**
```json
{
  "diet": "string (required, one of: 'standard', 'keto', 'paleo', 'vegan', 'vegetarian', 'high_protein')",
  "calories": "integer (800-6000, required)",
  "days": "integer (1-14, optional, default: 7)",
  "restrictions": "array of strings (optional, default: [])",
  "meal_structure": "string (optional, default: 'standard')",
  "cuisines": "array of strings (optional, default: ['all'])",
  "cooking_methods": "array of strings (optional, default: ['all'])",
  "measurement_system": "string (optional, default: 'metric', one of: 'US', 'metric')",
  "allow_substitutions": "boolean (optional, default: true)"
}
```

**Valid Restrictions:**
- `nuts`, `dairy`, `gluten`, `shellfish`, `eggs`, `soy`, `sesame`, `fish`, `nightshades`, `legumes`

**Valid Meal Structures:**
- `standard`, `16_8_if`, `18_6_if`, `omad`, `3_plus_2`, `5_small`, `2_meals`

**Valid Cuisines:**
- `all`, `asian`, `latin_american`, `mediterranean`, `middle_eastern`, `african`, `european`, `american`, `mixed`

**Valid Cooking Methods:**
- `all`, `grilled`, `baked`, `steamed`, `stir_fried`, `slow_cooked`, `raw`, `pan_fried`, `roasted`, `boiled`, `sauteed`, `pressure_cooked`, `air_fried`, `simmered`

**Example Request:**
```json
{
  "diet": "keto",
  "calories": 2000,
  "days": 7,
  "restrictions": ["dairy", "nuts"],
  "meal_structure": "standard",
  "cuisines": ["mediterranean", "american"],
  "cooking_methods": ["grilled", "baked"],
  "measurement_system": "metric",
  "allow_substitutions": true
}
```

### Save Meal Plan
```http
POST /api/save-meal-plan
```

**Request Schema:**
```json
{
  "meal_plan": "object (required, the meal plan data)",
  "name": "string (optional, max 100 chars)",
  "description": "string (optional, max 500 chars)"
}
```

**Example:**
```json
{
  "meal_plan": {
    "days": 7,
    "calories": 2000,
    "meals": { /* meal data */ }
  },
  "name": "My Keto Plan",
  "description": "A 7-day ketogenic meal plan for weight loss"
}
```

## Export API

### Export Grocery List
```http
POST /api/export-grocery-list
```

**Request Schema:**
```json
{
  "meal_plan": "object (required, the meal plan data)",
  "format": "string (optional, default: 'pdf', one of: 'pdf', 'json')"
}
```

### Export PDF
```http
POST /api/export-pdf
```

**Request Schema:**
```json
{
  "meal_plan": "object (required, the meal plan data)",
  "format": "string (optional, default: 'detailed', one of: 'detailed', 'simple')",
  "include_recipes": "boolean (optional, default: true)"
}
```

## Video Generation API

### Generate Video
```http
POST /api/generate-video
```

**Request Schema:**
```json
{
  "meal_plan": "object (required, the meal plan data)",
  "platforms": "array of strings (optional, default: ['youtube_shorts'])",
  "voice": "string (optional, default: 'christopher', 1-50 chars)",
  "auto_upload": "boolean (optional, default: false)"
}
```

**Valid Platforms:**
- `youtube_shorts`, `tiktok`, `instagram_reels`, `youtube_regular`, `facebook_video`

**Example:**
```json
{
  "meal_plan": {
    "days": 7,
    "meals": { /* meal data */ }
  },
  "platforms": ["youtube_shorts", "tiktok"],
  "voice": "christopher",
  "auto_upload": false
}
```

### Test Voice
```http
POST /api/video/test-voice
```

**Request Schema:**
```json
{
  "text": "string (1-500 chars, required)",
  "voice_gender": "string (optional, default: 'female', one of: 'male', 'female')",
  "language": "string (optional, default: 'en-US', format: 'xx-XX')"
}
```

**Example:**
```json
{
  "text": "Hello! This is a test of the voice generation system.",
  "voice_gender": "female",
  "language": "en-US"
}
```

## Logging API

### Sync Frontend Logs
```http
POST /api/logs/sync
```

**Request Schema:**
```json
{
  "logs": "array of objects (required)",
  "session_id": "string (optional, max 100 chars)",
  "timestamp": "integer (optional, unix timestamp)"
}
```

**Example:**
```json
{
  "logs": [
    {
      "level": "info",
      "message": "User clicked generate meal plan",
      "timestamp": 1642684800
    }
  ],
  "session_id": "abc123",
  "timestamp": 1642684800
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error type",
  "details": "Detailed error message or validation errors"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (validation errors)
- `401` - Unauthorized
- `403` - Forbidden (insufficient credits)
- `404` - Not Found
- `429` - Rate Limited
- `500` - Internal Server Error
- `503` - Service Unavailable

## Rate Limiting

Most endpoints are rate-limited to prevent abuse:
- **Default**: 10 requests per minute per IP
- **Meal Generation**: Additional credit-based limiting

## Validation

All POST endpoints use comprehensive validation:
- **Required fields** are enforced
- **Data types** are validated
- **String lengths** are checked
- **Enum values** are validated
- **Email formats** are verified
- **Security** sanitization is applied

## Security

- All inputs are sanitized
- CSRF protection on forms
- Rate limiting enabled
- Security headers applied
- SQL injection prevention
- XSS protection

## Testing

Use the test endpoints to verify your integration:
- `GET /health` - Health check
- `POST /api/video/test-voice` - Test voice generation
- `GET /api/video/platforms` - Get available platforms