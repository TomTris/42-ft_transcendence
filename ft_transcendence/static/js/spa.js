// online tournaments
let statusDiv;
let playersDiv;
let actionsDiv;
let codeDiv;
let timerDiv;
let notificationPopup;
let popupTitle;
let popupMessage;


let countdownInterval;
let countdownTime;

// 
var addFriendButton;
var acceptFriendButton;
var deleteFriendButton;
var cancelFriendButton;

let socket1 = null;
let canvas;
let ctx ;
let scriptCounter = 1;
var defaultOption = {
    method: 'GET',
    headers: {
        'X-Requested-With': 'XMLHttpRequest'
    }
};

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
        console.log('ok');
        return 1;
    }
    console.log('not ok');
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
async function myFetch(url, option, loop_detect)
{
    if (loop_detect >= 2) { 
        return loop_detect();
    }
    try {
        var response = await fetch(url, option);
        if (response.status >= 200 && response.status < 300) {
            return response;
        }
        if (response.status == 401) {
            if (await new_access_token() == 1) {
                return await myFetch(url, option, loop_detect + 1);
            }
            return await myFetch('/accounts/login/', option, loop_detect + 1);
        }
    }
    catch {    
        console.error('Error loading content:', error);
        return await myFetch('/accounts/login/', option, loop_detect + 1);
    }
}


async function loadContent(url, option, pushToHistory = false) {
    console.log("first2");
    try {
        removeScripts();
        const response = await myFetch(url, option, 0)
        console.log(response)
        const html = await response.text();
        const appDiv = document.getElementById('app');
        if (option.method == 'GET') {
            appDiv.innerHTML = html;
            const scripts = appDiv.querySelectorAll('script');
            for (let i = 0; i < scripts.length; i++) 
            {
                const newScript = document.createElement('script');
                newScript.textContent = scripts[i].textContent;
                newScript.id = `script_inserted${scriptCounter++}`;
                document.body.appendChild(newScript);
            }

            if (pushToHistory) {
                window.history.pushState({ url: url }, '', url);
            }
        }
    }
    catch (error)
    {
        console.error('Error loading content:', error);
    }
}
    
window.addEventListener('popstate', async function(event) {
    if (event.state && event.state.url) {
        await loadContent(event.state.url, defaultOption, false);
    } else {
        await loadContent(window.location.pathname, defaultOption, false);
    }
});


document.addEventListener('DOMContentLoaded',  async function() {
    var option = JSON.parse(JSON.stringify(defaultOption));
    option.method = originalMethod;
    await loadContent(window.location.pathname, option, true);
});
