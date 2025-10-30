document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('routeForm');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoader = submitBtn.querySelector('.btn-loader');
    const resultsSection = document.getElementById('resultsSection');
    const routeResults = document.getElementById('routeResults');
    const errorMessage = document.getElementById('errorMessage');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

   
        hideError();
        resultsSection.style.display = 'none';
        setLoading(true);


        const formData = {
            interests: document.getElementById('interests').value.trim(),
            time_hours: parseFloat(document.getElementById('time').value),
            location: document.getElementById('location').value.trim()
        };

        try {
           
            const response = await fetch('/api/generate_route', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Ошибка при генерации маршрута');
            }

           
            if (data.успешно === false) {
                throw new Error(data.ошибка || 'Не удалось сгенерировать маршрут');
            }

    
            displayRoute(data);

        } catch (error) {
            console.error('Ошибка:', error);
            showError(error.message);
        } finally {
            setLoading(false);
        }
    });

    function setLoading(isLoading) {
        submitBtn.disabled = isLoading;
        btnText.style.display = isLoading ? 'none' : 'inline';
        btnLoader.style.display = isLoading ? 'inline-flex' : 'none';
    }

    function showError(message) {
        errorMessage.textContent = '❌ ' + message;
        errorMessage.style.display = 'block';
        errorMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function hideError() {
        errorMessage.style.display = 'none';
    }

    function displayRoute(data) {
        let html = '';


        if (data.общее_описание) {
            html += `
                <div class="route-overview">
                    <h3>🎯 Описание маршрута</h3>
                    <p>${escapeHtml(data.общее_описание)}</p>
                    <div class="route-stats">
                        <div class="stat-item">
                            <span>⏱️</span>
                            <span><strong>Общее время:</strong> ${data.общее_время_минут || 'не указано'} минут</span>
                        </div>
                        <div class="stat-item">
                            <span>📍</span>
                            <span><strong>Мест:</strong> ${data.маршрут?.length || 0}</span>
                        </div>
                    </div>
                </div>
            `;
        }


        if (data.категории_интересов && data.категории_интересов.length > 0) {
            html += `
                <div style="margin-bottom: 24px;">
                    <strong style="display: block; margin-bottom: 12px;">🏷️ Подобрано по категориям:</strong>
                    <div class="interest-tags">
                        ${data.категории_интересов.map(cat => 
                            `<span class="interest-tag">${escapeHtml(cat)}</span>`
                        ).join(' ')}
                    </div>
                </div>
            `;
        }

        if (data.маршрут && data.маршрут.length > 0) {
            html += '<h3 style="margin-top: 24px; margin-bottom: 16px;">🗺️ Маршрут</h3>';

            data.маршрут.forEach(place => {
                html += `
                    <div class="route-place">
                        <div class="place-header">
                            <div class="place-number">${place.порядок}</div>
                            <div class="place-info">
                                <h4>${escapeHtml(place.название)}</h4>
                                <div class="place-address">📍 ${escapeHtml(place.адрес)}</div>
                                ${place.время_посещения_минут ? 
                                    `<span class="place-time">⏱️ ${place.время_посещения_минут} минут</span>` 
                                    : ''}
                            </div>
                        </div>
                        
                        ${place.почему_выбрано ? `
                            <div class="place-reason">
                                <strong>🎯 Почему это место:</strong>
                                <p>${escapeHtml(place.почему_выбрано)}</p>
                            </div>
                        ` : ''}
                        
                        ${place.что_посмотреть ? `
                            <div class="place-todo">
                                <strong>👀 Что посмотреть:</strong>
                                <p>${escapeHtml(place.что_посмотреть)}</p>
                            </div>
                        ` : ''}
                    </div>
                `;
            });
        }

        if (data.советы && data.советы.length > 0) {
            html += `
                <div class="tips-section">
                    <h4>💡 Полезные советы</h4>
                    <ul>
                        ${data.советы.map(tip => 
                            `<li>${escapeHtml(tip)}</li>`
                        ).join('')}
                    </ul>
                </div>
            `;
        }

        routeResults.innerHTML = html;
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});