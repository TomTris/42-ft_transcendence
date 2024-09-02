let socket1 = null;
let canvas;
let ctx ;
let scriptCounter = 1;
let defaultOption = {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    }
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
    if (socket1) {
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

async function new_access_token() {
    const refreshResponse = await fetch('/accounts/refresh/', {
        method: 'POST',
        credentials: 'include'
    });
    if (refreshResponse.ok) {
        return 1;
    }
    return 0
}

async function loop_detect()
{
	await fetch('/loop_detect/', {
		method: 'GET'
	})
	.then (response => response.text())
	.then (html => {
		return html;
	})
}

// when call this function, nbr must be 0

// Mindset:
// register, login, password-reset => user old way - check 'XMLHttpRequest' or not, then render based on request
// login, register: Authorized  
// else: XMLHttpRequest -> ok, if not -> home/login
// 

// just send their request to server to check authorization:
// if GET, 
// POST -> who cares

// inside server, each function permision and redirect if needed.

// login => permission -> login / home
// other resources => permission -> correct / login
// register, password change -> don't care permission

async function myFetch(url, option, loop_detect)
{
    if (loop_detect >= 5) {
        return loop_detect();
    }

    await fetch(url, option)
    .then(response => {
        if (response.status >= 200 && response.status < 300) {
            return response.text();
        }
        if (response.status == 401) {
            if (new_access_token() == 1) {
                return myFetch(url, option, loop_detect + 1);
            }
            return myFetch('/login401/', loop_detect + 1);
        }
    })
    .catch(error => {
        console.error('Error loading content:', error);
        myFetch(myFetch('/login401/', loop_detect + 1));
    });
}

async function loadContent(url, option, pushToHistory = false) {
    removeScripts();
    await myFetch(url, option, 0)
    .then(html => {
        var appDiv = document.getElementById('app');
        if (option.method == 'GET'){
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
    console.log("1a1a");
    var option = JSON.parse(JSON.stringify(defaultOption));
    option.method = originalMethod;
    loadContent(window.location.pathname, option, true);
});
