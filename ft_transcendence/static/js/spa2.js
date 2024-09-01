let socket1 = null;
let canvas;
let ctx ;
let scriptCounter = 1;
let defaultOption = {
    method: 'GET',
    headers: {
        'X-Requested-With': 'XMLHttpRequest'
    }}

document.addEventListener('click', function(event) {
    const anchor = event.target.closest('a[data-route]');
    if (anchor) {
        event.preventDefault();
        const path = anchor.getAttribute('data-route');
        console.log('Navigating to:', path);
        loadContent(path, defaultOption, true);
    }
});

document.addEventListener('click', function(event) {
    const button = event.target.closest('button[data-route]');
    if (button) {
        event.preventDefault();
        const path = button.getAttribute('data-route');
        console.log('Navigating to:', path);
        loadContent(path, defaultOption, true);
    }
});

function removeScripts() {
    if (socket1)
    {
        socket1.close();
        socket1 = null;
    }
    for (let i = 1; i <= scriptCounter - 1; i++) {
        const scriptElement = document.getElementById(`script_inserted${i}`);
        if (scriptElement) {
            document.body.removeChild(scriptElement);
        }
    }
}

async function loadContent(url, option, pushToHistory = false) {
    removeScripts();

    await fetch(url, option)
    .then(response => response.text())
    .then(html => {
        var appDiv = document.getElementById('app');
        if (option.method == 'GET') {
            appDiv.innerHTML = html;
            
            const scripts = appDiv.querySelectorAll('script');
            scripts.forEach(script => {
                const newScript = document.createElement('script');
                newScript.textContent = script.textContent;
                newScript.id = `script_inserted${scriptCounter++}`;
                document.body.appendChild(newScript);
            });
    
            if (pushToHistory) {
                window.history.pushState({ url: url }, '', url);
            }
        }
    })
    .catch(error => {
        console.error('Error loading content:', error);
    });
}

window.addEventListener('popstate', function(event) {
    if (event.state && event.state.url) {
        loadContent(event.state.url, defaultOption, false);
    } else {
        loadContent(window.location.pathname, defaultOption, false);
    }
});


document.addEventListener('DOMContentLoaded', function() {
    var option = JSON.parse(JSON.stringify(defaultOption));
    option.method = originalMethod;
    loadContent(window.location.pathname, option, true);
});
