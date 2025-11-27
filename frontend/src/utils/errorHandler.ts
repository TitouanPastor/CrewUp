import { AxiosError } from 'axios';

/**
 * Backend error response format
 */
interface BackendErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Array<{
      field: string;
      message: string;
      type: string;
    }>;
  };
}

/**
 * Extract a user-friendly error message from an API error
 * Handles both structured backend errors and generic Axios errors
 */
export function extractErrorMessage(error: unknown): string {
  // Not an Axios error - return generic message
  if (!(error instanceof Error)) {
    return 'An unexpected error occurred';
  }

  const axiosError = error as AxiosError<BackendErrorResponse>;

  // No response from server (network error, timeout, etc.)
  if (!axiosError.response) {
    if (axiosError.code === 'ECONNABORTED') {
      return 'Request timeout - please try again';
    }
    if (axiosError.code === 'ERR_NETWORK') {
      return 'Network error - please check your connection';
    }
    return axiosError.message || 'Unable to connect to server';
  }

  const { status, data } = axiosError.response;

  // Structured backend error with details
  if (data?.error) {
    const { message, details } = data.error;

    // If there are validation details, format them nicely
    if (details && details.length > 0) {
      const fieldErrors = details
        .map((detail) => {
          // Remove "body." prefix from field names for cleaner display
          const fieldName = detail.field.replace(/^body\./, '');
          // Extract the actual error message, removing "Value error, " prefix if present
          const cleanMessage = detail.message.replace(/^Value error,\s*/, '');
          return `${fieldName}: ${cleanMessage}`;
        })
        .join('\n');

      return `${message}\n${fieldErrors}`;
    }

    // Return just the main error message
    return message;
  }

  // Handle common HTTP status codes
  switch (status) {
    case 400:
      return 'Invalid request - please check your input';
    case 401:
      return 'Authentication required - please log in';
    case 403:
      return 'Access forbidden - you do not have permission';
    case 404:
      return 'Resource not found';
    case 409:
      return 'Conflict - resource already exists';
    case 422:
      return 'Validation error - please check your input';
    case 500:
      return 'Server error - please try again later';
    case 503:
      return 'Service unavailable - please try again later';
    default:
      return `Error ${status}: ${axiosError.message}`;
  }
}

/**
 * Extract a short title for the error (without details)
 */
export function extractErrorTitle(error: unknown): string {
  const axiosError = error as AxiosError<BackendErrorResponse>;

  if (axiosError.response?.data?.error?.message) {
    return axiosError.response.data.error.message;
  }

  return 'Error';
}
