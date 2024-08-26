// Intercept link clicks and load content via AJAX
document.addEventListener('click', function(event) {
    const anchor = event.target.closest('a[data-route]');
    if (anchor) {
        event.preventDefault();
        const path = anchor.getAttribute('data-route');
        console.log('Navigating to:', path);  // Log the path for debugging
        loadContent(path, true); // Load content and push to history
    }
});

// Load content based on the URL
function loadContent(url, pushToHistory = false) {
    fetch(url, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.text())
    .then(html => {
        document.getElementById('app').innerHTML = html;
        
        // Add the state to the history stack if pushToHistory is true
        if (pushToHistory) {
            window.history.pushState({ url: url }, '', url);
        }
    })
    .catch(error => {
        console.error('Error loading content:', error);
    });
}

// Handle browser back/forward navigation
window.addEventListener('popstate', function(event) {
    // Check if there's a state associated with this history entry
    if (event.state && event.state.url) {
        // Load content based on the URL stored in the state object
        loadContent(event.state.url, false); // Do not push to history on popstate
    } else {
        // Fallback to the current URL if no state is available
        loadContent(window.location.pathname, false); // Do not push to history on popstate
    }
});
