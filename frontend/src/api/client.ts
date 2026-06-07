const API_BASE = 'http://localhost:3001';

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include', // Important: backend relies on httpOnly cookies
  });

  if (!response.ok) {
    let errorMessage = `HTTP error! Status: ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData.error === "Validation failed" && Array.isArray(errorData.details)) {
        errorMessage = `Validation failed:\n${errorData.details.map((d: string) => `• ${d}`).join('\n')}`;
      } else {
        errorMessage = errorData.error || errorData.message || errorMessage;
      }
    } catch {
      // ignore JSON parse failure
    }
    throw new Error(errorMessage);
  }

  // Handle successful status but empty body or non-JSON
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return response.json() as Promise<T>;
  }
  
  return {} as T;
}
