"""Response helper utilities for consistent API responses"""

from flask import jsonify, request
from typing import Any, Dict, Optional


def api_response(data: Any = None, message: str = None, success: bool = True, 
                status_code: int = 200, meta: Dict = None) -> tuple:
    """
    Create standardized API response
    
    Args:
        data: Response data
        message: Human-readable message
        success: Success status
        status_code: HTTP status code
        meta: Additional metadata
    
    Returns:
        Tuple of (response, status_code)
    """
    
    response = {
        'success': success,
        'data': data,
        'message': message
    }
    
    if meta:
        response['meta'] = meta
    
    # Add request context for debugging
    if request and hasattr(request, 'endpoint'):
        response['meta'] = response.get('meta', {})
        response['meta']['endpoint'] = request.endpoint
    
    return jsonify(response), status_code


def success_response(data: Any = None, message: str = "Operation successful", 
                    status_code: int = 200, meta: Dict = None) -> tuple:
    """Create successful API response"""
    return api_response(data, message, True, status_code, meta)


def error_response(message: str, error_code: str = None, 
                  status_code: int = 400, details: Dict = None) -> tuple:
    """Create error API response"""
    
    error_data = {'message': message}
    
    if error_code:
        error_data['code'] = error_code
    
    if details:
        error_data['details'] = details
    
    return api_response(error_data, None, False, status_code)


def validation_error_response(errors: Dict[str, list], 
                            message: str = "Validation failed") -> tuple:
    """Create validation error response with field-specific errors"""
    
    return error_response(
        message=message,
        error_code='VALIDATION_ERROR',
        status_code=400,
        details={'field_errors': errors}
    )


def not_found_response(resource: str = "Resource") -> tuple:
    """Create not found response"""
    return error_response(
        message=f"{resource} not found",
        error_code='NOT_FOUND',
        status_code=404
    )


def unauthorized_response(message: str = "Authentication required") -> tuple:
    """Create unauthorized response"""
    return error_response(
        message=message,
        error_code='UNAUTHORIZED',
        status_code=401
    )


def forbidden_response(message: str = "Access denied") -> tuple:
    """Create forbidden response"""
    return error_response(
        message=message,
        error_code='FORBIDDEN',
        status_code=403
    )


def paginated_response(items: list, page: int, per_page: int, 
                      total: int, message: str = None) -> tuple:
    """Create paginated response with metadata"""
    
    total_pages = (total + per_page - 1) // per_page
    
    meta = {
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }
    
    return success_response(
        data=items,
        message=message or f"Retrieved {len(items)} items",
        meta=meta
    )