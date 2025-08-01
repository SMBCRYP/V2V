export default {
  async fetch(request) {
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
      'Access-Control-Allow-Headers': '*',
    };
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }
    const url = new URL(request.url);
    const targetUrl = url.searchParams.get('url');
    if (!targetUrl) {
      return new Response('Error: "url" parameter is missing.', {
        status: 400,
        headers: corsHeaders,
      });
    }
    if (targetUrl.includes('rapid-scene-1da6.mbrgh87.workers.dev')) {
      return new Response('Error: Recursive proxy call detected.', {
        status: 400,
        headers: corsHeaders,
      });
    }
    try {
      const response = await fetch(targetUrl, {
        headers: { 'User-Agent': 'Cloudflare-Worker-Proxy' },
      });
      const headers = new Headers(response.headers);
      Object.entries(corsHeaders).forEach(([key, value]) => {
        headers.set(key, value);
      });
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers,
      });
    } catch (e) {
      return new Response(`Error fetching target: ${e.message}`, {
        status: 502,
        headers: corsHeaders,
      });
    }
  }
};
