// Determine API base URL based on environment
// On server (SSR), use full URL from environment variable
// On client, use relative path which will be proxied
const getApiBase = () => {
  // Check if we're in a server environment (SSR)
  if (typeof window === 'undefined') {
    // Server-side: use full API URL from environment variable
    // Astro uses import.meta.env for environment variables
    // Try multiple sources for API URL
    const apiUrl = import.meta.env.API_URL 
      || import.meta.env.PUBLIC_API_URL 
      || (typeof process !== 'undefined' && process.env?.API_URL)
    if (apiUrl) {
      // If API_URL already includes /api, use as-is, otherwise append it
      return apiUrl.includes('/api') ? apiUrl : `${apiUrl}/api`
    }
    // Default fallback
    return 'http://localhost:8000/api'
  }
  // Client-side: use relative path (will be proxied by Vite/Astro)
  return '/api'
}

const API_BASE = getApiBase()

export async function fetchBooks(
  page: number = 1,
  pageSize: number = 10,
  search?: string,
  stationId?: string,
  showId?: number
) {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  })
  
  if (search) {
    params.append('search', search)
  }
  if (showId) {
    params.append('brand', showId.toString())
  }
  if (stationId) {
    params.append('station_id', stationId)
  }
  
  const response = await fetch(`${API_BASE}/books/?${params.toString()}`)
  if (!response.ok) throw new Error('Failed to fetch books')
  const data = await response.json()
  // Handle both paginated and non-paginated responses
  if (data.results) {
    return data
  }
  return { count: data.length, results: data, next: null, previous: null }
}

export async function fetchBook(slug: string) {
  const response = await fetch(`${API_BASE}/books/${slug}/`);
  if (!response.ok) throw new Error('Failed to fetch book');
  return response.json();
}

export async function fetchShows() {
  const response = await fetch(`${API_BASE}/brands/`);
  if (!response.ok) throw new Error('Failed to fetch shows');
  const data = await response.json();
  // Handle both paginated and non-paginated responses
  if (data.results) {
    return data;
  }
  return Array.isArray(data) ? data : [];
}

export async function fetchShow(slug: string) {
  const response = await fetch(`${API_BASE}/brands/${slug}/`);
  if (!response.ok) throw new Error('Failed to fetch show');
  return response.json();
}

export async function fetchShowBooks(showSlug: string, page: number = 1, pageSize: number = 10) {
  const response = await fetch(`${API_BASE}/books/?brand_slug=${showSlug}&page=${page}&page_size=${pageSize}`);
  if (!response.ok) throw new Error('Failed to fetch show books');
  const data = await response.json();
  // Handle both paginated and non-paginated responses
  if (data.results) {
    return data;
  }
  return { count: data.length, results: data, next: null, previous: null };
}

export async function fetchStations() {
  const response = await fetch(`${API_BASE}/stations/`);
  if (!response.ok) throw new Error('Failed to fetch stations');
  const data = await response.json();
  // Handle both paginated and non-paginated responses
  if (data.results) {
    return data.results;
  }
  return Array.isArray(data) ? data : [];
}

export async function fetchStation(stationId: string) {
  const response = await fetch(`${API_BASE}/stations/?station_id=${stationId}`);
  if (!response.ok) throw new Error('Failed to fetch station');
  const data = await response.json();
  return data.results?.[0] || data;
}

export async function fetchStationShows(stationId: string) {
  const response = await fetch(`${API_BASE}/brands/?station_id=${stationId}`);
  if (!response.ok) throw new Error('Failed to fetch station shows');
  const data = await response.json();
  // Handle both paginated and non-paginated responses
  if (data.results) {
    return data.results;
  }
  return Array.isArray(data) ? data : [];
}

