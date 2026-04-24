// Aprende sobre Alzheimer - Portal Script
document.addEventListener('DOMContentLoaded', function() {
    // RSS Feed Fetcher
    const rssContainer = document.getElementById('rss-container');
    // Using a public RSS to JSON converter to bypass CORS
    const RSS_URL = 'https://medicine.yale.edu/adrc/news-events/?rss=1';
    const API_URL = `https://api.rss2json.com/v1/api.json?rss_url=${encodeURIComponent(RSS_URL)}`;

    async function fetchRSS() {
        try {
            const response = await fetch(API_URL);
            const data = await response.json();

            if (data.status === 'ok') {
                rssContainer.innerHTML = ''; // Clear loading message

                data.items.slice(0, 5).forEach(item => {
                    const article = document.createElement('div');
                    article.className = 'rss-item';

                    const pubDate = new Date(item.pubDate).toLocaleDateString('es-ES', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                    });

                    article.innerHTML = `
                        <h4><a href="${item.link}" target="_blank" rel="noopener noreferrer">${item.title}</a></h4>
                        <p class="date">${pubDate}</p>
                        <p>${item.description.substring(0, 150)}...</p>
                    `;
                    rssContainer.appendChild(article);
                });
            } else {
                rssContainer.innerHTML = '<p>No se pudieron cargar las noticias en este momento. Por favor, inténtelo más tarde.</p>';
            }
        } catch (error) {
            console.error('Error fetching RSS:', error);
            rssContainer.innerHTML = '<p>Error al conectar con el servidor de noticias.</p>';
        }
    }

    fetchRSS();

    // Track interactions (privacy-friendly)
    console.log('Portal "Aprende sobre Alzheimer" cargado correctamente.');
});
