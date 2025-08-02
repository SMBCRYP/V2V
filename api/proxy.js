export default async function handler(request, response) {
  const { url: targetUrl } = request.query;

  if (!targetUrl) {
    return response.status(400).send('Error: "url" query parameter is missing.');
  }

  try {
    const fetchResponse = await fetch(targetUrl, {
      headers: { 'User-Agent': 'Vercel-Proxy/1.0' },
    });

    response.setHeader('Access-Control-Allow-Origin', '*');
    response.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    response.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    response.status(fetchResponse.status);
    
    // کد اصلاح شده در دو خط زیر است
    const body = await fetchResponse.text();
    return response.send(body);

  } catch (error) {
    console.error(error);
    return response.status(502).send(`Error fetching target: ${error.message}`);
  }
}
