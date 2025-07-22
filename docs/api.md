# Cibozer API Documentation

This document provides comprehensive documentation for the Cibozer API endpoints.

## Base URL
```
https://cibozer.com/api
```

## Authentication

Most endpoints require user authentication. Use the `/auth/login` endpoint to obtain a session.

## Endpoints

### Core Functionality

#### `GET /`

Home page - displays meal planning interface

**Response:**

```
HTML page with meal planning form
```

#### `POST /generate_meal_plan`

Generate personalized meal plan based on user preferences

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| dietary_restrictions | list | Yes | - | - |
| budget | number | Yes | - | - |
| meals_per_day | number | No | 3 | - |
| days | number | No | 7 | - |

**Response:**

```
JSON object with meal plan and recipes
```

**Example Request:**

```json
{
  "dietary_restrictions": ["vegetarian"],
  "budget": 50,
  "meals_per_day": 3,
  "days": 7
}
```

#### `POST /generate_video`

Generate cooking video for a specific recipe

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| recipe_name | string | Yes | - | - |
| ingredients | list | Yes | - | - |
| instructions | list | Yes | - | - |

**Response:**

```
JSON object with video URL and metadata
```

#### `POST /save_meal_plan`

Save meal plan to user account

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| meal_plan | object | Yes | - | - |
| name | string | Yes | - | - |

**Response:**

```
JSON object with save status
```

#### `POST /export_grocery_list`

Export grocery list as PDF

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| meal_plan | object | Yes | - | - |
| format | string | No | pdf | - |

**Response:**

```
PDF file download
```

### Authentication

#### `GET, POST /auth/login`

User authentication endpoint

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| username | string | Yes | - | - |
| password | string | Yes | - | - |

**Response:**

```
Redirect to dashboard on success
```

#### `GET, POST /auth/register`

User registration endpoint

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| username | string | Yes | - | - |
| email | string | Yes | - | - |
| password | string | Yes | - | - |

**Response:**

```
Redirect to login on success
```

### Payments

#### `POST /payments/checkout`

Process premium subscription payment

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| plan_id | string | Yes | - | - |
| payment_method | string | Yes | - | - |

**Response:**

```
JSON object with payment status
```

### System

#### `GET /api/health`

Health check endpoint for monitoring

**Response:**

```
JSON object with system status
```

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient credits/permissions |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Internal Server Error |

## Rate Limiting

API requests are rate limited based on user tier:

- **Free Users**: 10 requests per hour
- **Premium Users**: 100 requests per hour

## Credits System

Some endpoints consume user credits:

- **Meal Plan Generation**: 1 credit
- **Video Generation**: 5 credits
- **PDF Export**: 1 credit
