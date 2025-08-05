# 📚 Cibozer API Documentation

## Overview

The Cibozer API provides programmatic access to meal planning functionality. All API endpoints require authentication except for health checks.

## Base URL

```
https://api.cibozer.com/api/v1
```

## Authentication

All API requests require authentication using an API key passed in the header:

```
Authorization: Bearer YOUR_API_KEY
```

To generate an API key:
1. Log in to your Cibozer account
2. Navigate to Settings → API Keys
3. Click "Generate New Key"
4. Store the key securely (it won't be shown again)

## Rate Limiting

- **Free tier**: 100 requests per hour
- **Pro tier**: 1000 requests per hour  
- **Premium tier**: 10000 requests per hour

Rate limit headers are included in all responses:
- `X-RateLimit-Limit`: Your rate limit
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## Common Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing API key |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

## Error Response Format

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request was invalid",
    "details": {
      "field": "calories",
      "error": "Must be between 1200 and 5000"
    }
  },
  "request_id": "req_1234567890"
}
```

---

## Endpoints

### Health Check

Check API health and status.

**Endpoint:** `GET /api/health`

**Authentication:** Not required

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-12-01T12:00:00Z",
  "version": "1.0.0",
  "environment": "production"
}
```

---

### Generate Meal Plan

Generate a personalized meal plan based on dietary preferences and nutritional goals.

**Endpoint:** `POST /api/generate-meal-plan`

**Authentication:** Required

**Request Body:**
```json
{
  "preferences": {
    "dietary_type": "balanced",
    "allergies": ["nuts", "shellfish"],
    "cuisine_preferences": ["mediterranean", "asian"],
    "meal_types": ["breakfast", "lunch", "dinner", "snack"]
  },
  "nutritional_goals": {
    "daily_calories": 2000,
    "protein_percentage": 30,
    "carbs_percentage": 40,
    "fat_percentage": 30
  },
  "plan_duration": 7,
  "exclude_ingredients": ["mushrooms", "olives"]
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| preferences | object | Yes | Dietary preferences |
| preferences.dietary_type | string | Yes | One of: balanced, vegetarian, vegan, keto, paleo |
| preferences.allergies | array | No | List of allergens to avoid |
| preferences.cuisine_preferences | array | No | Preferred cuisine types |
| preferences.meal_types | array | Yes | Types of meals to include |
| nutritional_goals | object | Yes | Nutritional targets |
| nutritional_goals.daily_calories | integer | Yes | Target daily calories (1200-5000) |
| nutritional_goals.protein_percentage | integer | Yes | Protein percentage (10-50) |
| nutritional_goals.carbs_percentage | integer | Yes | Carbs percentage (10-70) |
| nutritional_goals.fat_percentage | integer | Yes | Fat percentage (10-50) |
| plan_duration | integer | Yes | Days in plan (1-30) |
| exclude_ingredients | array | No | Ingredients to exclude |

**Success Response:**
```json
{
  "meal_plan_id": "mp_1234567890",
  "status": "completed",
  "created_at": "2023-12-01T12:00:00Z",
  "plan": {
    "duration_days": 7,
    "total_calories": 14000,
    "average_daily_calories": 2000,
    "days": [
      {
        "day": 1,
        "date": "2023-12-01",
        "total_calories": 1998,
        "meals": [
          {
            "type": "breakfast",
            "name": "Mediterranean Omelet",
            "calories": 450,
            "protein": 25,
            "carbs": 20,
            "fat": 30,
            "ingredients": [
              {
                "name": "eggs",
                "amount": 3,
                "unit": "large"
              },
              {
                "name": "feta cheese",
                "amount": 30,
                "unit": "grams"
              }
            ],
            "instructions": [
              "Heat olive oil in a non-stick pan",
              "Whisk eggs with salt and pepper",
              "Pour eggs into pan and cook until edges set"
            ],
            "prep_time": 10,
            "cook_time": 15
          }
        ]
      }
    ]
  },
  "shopping_list": {
    "grouped_by_category": {
      "proteins": [
        {
          "name": "eggs",
          "total_amount": 21,
          "unit": "large"
        }
      ],
      "dairy": [
        {
          "name": "feta cheese", 
          "total_amount": 210,
          "unit": "grams"
        }
      ]
    }
  }
}
```

---

### Get Meal Plan

Retrieve a previously generated meal plan.

**Endpoint:** `GET /api/meal-plans/{meal_plan_id}`

**Authentication:** Required

**Response:** Same format as Generate Meal Plan success response

---

### List Meal Plans

List all meal plans for the authenticated user.

**Endpoint:** `GET /api/meal-plans`

**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | integer | No | Page number (default: 1) |
| per_page | integer | No | Items per page (default: 20, max: 100) |
| sort | string | No | Sort by: created_at, -created_at (default: -created_at) |

**Response:**
```json
{
  "meal_plans": [
    {
      "meal_plan_id": "mp_1234567890",
      "created_at": "2023-12-01T12:00:00Z",
      "duration_days": 7,
      "dietary_type": "balanced",
      "total_calories": 14000
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "pages": 3
  }
}
```

---

### Delete Meal Plan

Delete a meal plan.

**Endpoint:** `DELETE /api/meal-plans/{meal_plan_id}`

**Authentication:** Required

**Response:**
```json
{
  "message": "Meal plan deleted successfully",
  "meal_plan_id": "mp_1234567890"
}
```

---

### Export Meal Plan

Export a meal plan in various formats.

**Endpoint:** `POST /api/meal-plans/{meal_plan_id}/export`

**Authentication:** Required

**Request Body:**
```json
{
  "format": "pdf",
  "options": {
    "include_shopping_list": true,
    "include_nutrition_details": true,
    "include_instructions": true
  }
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| format | string | Yes | Export format: pdf, csv, json |
| options | object | No | Export options |
| options.include_shopping_list | boolean | No | Include shopping list (default: true) |
| options.include_nutrition_details | boolean | No | Include nutrition info (default: true) |
| options.include_instructions | boolean | No | Include cooking instructions (default: true) |

**Response:**
```json
{
  "export_url": "https://api.cibozer.com/exports/exp_1234567890.pdf",
  "expires_at": "2023-12-01T13:00:00Z",
  "format": "pdf",
  "size_bytes": 245780
}
```

---

### Get User Profile

Get profile information for the authenticated user.

**Endpoint:** `GET /api/user/profile`

**Authentication:** Required

**Response:**
```json
{
  "user_id": "usr_1234567890",
  "email": "user@example.com",
  "name": "John Doe",
  "subscription": {
    "plan": "pro",
    "status": "active",
    "expires_at": "2024-01-01T00:00:00Z"
  },
  "preferences": {
    "dietary_type": "balanced",
    "allergies": ["nuts"],
    "default_calories": 2000
  },
  "usage": {
    "meal_plans_generated": 45,
    "meal_plans_remaining": 955,
    "reset_date": "2024-01-01T00:00:00Z"
  }
}
```

---

### Update User Preferences

Update dietary preferences for the authenticated user.

**Endpoint:** `PUT /api/user/preferences`

**Authentication:** Required

**Request Body:**
```json
{
  "dietary_type": "vegetarian",
  "allergies": ["nuts", "dairy"],
  "default_calories": 1800,
  "cuisine_preferences": ["italian", "mexican"]
}
```

**Response:**
```json
{
  "message": "Preferences updated successfully",
  "preferences": {
    "dietary_type": "vegetarian",
    "allergies": ["nuts", "dairy"],
    "default_calories": 1800,
    "cuisine_preferences": ["italian", "mexican"]
  }
}
```

---

## Webhooks

Cibozer can send webhooks to notify your application of important events.

### Webhook Events

| Event | Description |
|-------|-------------|
| meal_plan.created | A new meal plan was generated |
| meal_plan.deleted | A meal plan was deleted |
| subscription.updated | User's subscription changed |
| api_key.created | New API key was created |
| api_key.revoked | API key was revoked |

### Webhook Payload

```json
{
  "event": "meal_plan.created",
  "created_at": "2023-12-01T12:00:00Z",
  "data": {
    "meal_plan_id": "mp_1234567890",
    "user_id": "usr_1234567890",
    "duration_days": 7
  }
}
```

### Webhook Security

All webhooks include a signature header for verification:

```
X-Cibozer-Signature: sha256=abcdef1234567890...
```

Verify webhooks using your webhook secret:

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = 'sha256=' + hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

---

## Code Examples

### Python

```python
import requests

API_KEY = 'your_api_key'
BASE_URL = 'https://api.cibozer.com/api/v1'

headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

# Generate meal plan
data = {
    'preferences': {
        'dietary_type': 'balanced',
        'meal_types': ['breakfast', 'lunch', 'dinner']
    },
    'nutritional_goals': {
        'daily_calories': 2000,
        'protein_percentage': 30,
        'carbs_percentage': 40,
        'fat_percentage': 30
    },
    'plan_duration': 7
}

response = requests.post(
    f'{BASE_URL}/generate-meal-plan',
    json=data,
    headers=headers
)

meal_plan = response.json()
print(f"Generated meal plan: {meal_plan['meal_plan_id']}")
```

### JavaScript

```javascript
const API_KEY = 'your_api_key';
const BASE_URL = 'https://api.cibozer.com/api/v1';

async function generateMealPlan() {
    const response = await fetch(`${BASE_URL}/generate-meal-plan`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${API_KEY}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            preferences: {
                dietary_type: 'balanced',
                meal_types: ['breakfast', 'lunch', 'dinner']
            },
            nutritional_goals: {
                daily_calories: 2000,
                protein_percentage: 30,
                carbs_percentage: 40,
                fat_percentage: 30
            },
            plan_duration: 7
        })
    });

    const mealPlan = await response.json();
    console.log(`Generated meal plan: ${mealPlan.meal_plan_id}`);
}
```

### cURL

```bash
curl -X POST https://api.cibozer.com/api/v1/generate-meal-plan \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "preferences": {
      "dietary_type": "balanced",
      "meal_types": ["breakfast", "lunch", "dinner"]
    },
    "nutritional_goals": {
      "daily_calories": 2000,
      "protein_percentage": 30,
      "carbs_percentage": 40,
      "fat_percentage": 30
    },
    "plan_duration": 7
  }'
```

---

## SDKs

Official SDKs are available for:

- **Python**: `pip install cibozer-python`
- **JavaScript/Node**: `npm install @cibozer/sdk`
- **Ruby**: `gem install cibozer`
- **PHP**: `composer require cibozer/cibozer-php`

---

## Support

For API support:
- Email: api-support@cibozer.com
- Documentation: https://docs.cibozer.com/api
- Status Page: https://status.cibozer.com