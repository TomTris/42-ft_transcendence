var addFriendButton;
var acceptFriendButton;
var deleteFriendButton;
var cancelFriendButton;
// let  socket1 = new WebSocket(`wss://${window.location.host}/wss/game/bot/`);;
let socket1 = null;
let canvas;
let ctx ;
let scriptCounter = 1;
document.addEventListener('click', function(event) {
    // console.log("1231");
    const anchor = event.target.closest('a[data-route]');
    // console.log("1232");
    if (anchor) {
        console.log("1233");
        event.preventDefault();
        const path = anchor.getAttribute('data-route');
        console.log('Navigating to:', path);  // Log the path for debugging
        loadContent(path, true); // Load content and push to history
    }
});
document.addEventListener('click', function(event) {
    // console.log(1111);
    const button = event.target.closest('button[data-route]');
    // console.log(1112);
    if (button) {
        console.log(1113);
        event.preventDefault(); // Prevent default button behavior
        const path = button.getAttribute('data-route');
        console.log('Navigating to:', path); // Log the path for debugging
        loadContent(path, true); // Load content and push to history
    }
});

function removeScripts() {
    for (let i = 1; i <= scriptCounter - 1; i++) {
        const scriptElement = document.getElementById(`script_inserted${i}`);
        if (scriptElement) {
            document.body.removeChild(scriptElement);
        }
    }
}

async function loadContent(url, pushToHistory = false) {
    if (socket1)
    {
        socket1.close();
        socket1 = null;
    }
    var element = document.getElementById("myElement");
    if (element)
        element.remove();
    removeScripts();
    await fetch(url, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.text())
    .then(html => {
        var appDiv = document.getElementById('app');
        appDiv.innerHTML = html;
        var tempDiv = document.createElement('div');
        tempDiv.id = "myElement";
        tempDiv.innerHTML = html;
        // document.body.appendChild(tempDiv);
        
        const scripts = tempDiv.querySelectorAll('script'); // Find all script tags
        scripts.forEach(script => {
            const newScript = document.createElement('script');
            newScript.textContent = script.textContent; // Copy script content
            newScript.id = `script_inserted${scriptCounter++}`;
            document.body.appendChild(newScript); // Append to the document
        });

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
