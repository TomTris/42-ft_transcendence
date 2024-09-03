//wss/invitations/`
var invitationIcon
var invitationList
var inviteCountElement
var InviteSocket = null


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

var addFriendButton;
var acceptFriendButton;
var deleteFriendButton;
var cancelFriendButton;

let socket1 = null;
let canvas;
let ctx ;
let scriptCounter = 1;
let scriptCounterNavbar = 1;
var defaultOption = {
    method: 'GET',
    headers: {
        'X-Requested-With': 'XMLHttpRequest'
    },
    credentials: 'include'
};

let authorized_old = 2;
let authorized_new = 2;

document.addEventListener('click', function(event) {
    const anchor = event.target.closest('a[data-route]');
    if (anchor) {
        event.preventDefault();
        const path = anchor.getAttribute('data-route');
        loadContent(path, defaultOption, true);
    }
});

document.addEventListener('click', function(event) {
    const button = event.target.closest('button[data-route]');
    if (button) {
        event.preventDefault();
        const path = button.getAttribute('data-route');
        loadContent(path, defaultOption, true);
    }
});

function removeScripts() {
    if (socket1) {
        socket1.close();
        socket1 = null;
    }
    if (InviteSocket) {
        InviteSocket.close();
        InviteSocket = null;
    }

    for (let i = 1; i <= scriptCounter - 1; i++) {
        const scriptElement = document.getElementById(`script_inserted${i}`);
        if (scriptElement) {
            document.body.removeChild(scriptElement);
        }
    }
    scriptCounter = 1;
}

function removeScriptsNavbar() {
    for (let i = 1; i <= scriptCounterNavbar - 1; i++) {
        const scriptElement = document.getElementById(`navbar_script_inserted${i}`);
        if (scriptElement) {
            document.body.removeChild(scriptElement);
        }
    }
    scriptCounterNavbar = 1;
}

async function new_access_token() {
    console.log("new_access_token called");
    const refreshResponse = await fetch('/refresh/refresh/', {
        method: 'POST',
        credentials: 'include'
    });
    if (refreshResponse.ok) {
        console.log('new token ok');
        return 1;
    }
    console.log('token not ok');
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

async function myFetch(url, option, loop_detect)
{
    if (loop_detect >= 2) { 
        return loop_detect();
    }
    console.log("url =",url);
    try {
        var response = await fetch(url, option);
        if (response.status >= 200 && response.status < 300) {
            console.log("url =",url, "return < 300");
            return response;
        }
        if (response.status == 401) {
            if (await new_access_token() == 1) {
                console.log("new_access_token = 1");
                return await myFetch(url, option, loop_detect + 1);
            }
            console.log("new_access_token = 0")
            return await myFetch('/', option, loop_detect + 1);
        }
        if (response.status == 400) {
            var data = await response.json();
            alert(data.message);
            return await myFetch('/', option, loop_detect + 1);
        }
    }
    catch {
        console.error('Error loading content:', error);
        return await myFetch('/login/', option, loop_detect + 1);
    }
}

async function loadNavbar() {
    var response = await fetch('/is_authorized/', {
        method: 'POST',
        credentials: 'include'
    })
    if (response.status == 200)
        authorized_new = 1;
    else
        authorized_new = 0;
    console.log(response.status);
    console.log("authorized_new = ", authorized_new);
    console.log("authorized_old = ", authorized_old);
    if (authorized_new != authorized_old)
    {
        try {
            response = await fetch('/navbar_authorized/', {
                method: 'POST',
                credentials: 'include'
            })
            var html = await response.text();
            var navbarDiv = document.getElementById('navbar');
            removeScriptsNavbar();
            navbarDiv.innerHTML = html;
            var scripts = navbarDiv.querySelectorAll('script');
            for (let i = 0; i < scripts.length; i++) 
            {
                var newScript = document.createElement('script');
                newScript.textContent = scripts[i].textContent;
                newScript.id = `navbar_script_inserted${scriptCounterNavbar++}`;
                document.body.appendChild(newScript);
            }
            authorized_old = authorized_new;
        }
        catch {

        }
    }
}

async function loadContent(url, option, pushToHistory = false) {
    try {
        removeScripts();
        var response = await myFetch(url, option, 0)
        console.log(response)
        var html = await response.text();
        var appDiv = document.getElementById('app');
        loadNavbar();
        if (option.method == 'GET') {
            appDiv.innerHTML = html;
            var scripts = appDiv.querySelectorAll('script');
            for (let i = 0; i < scripts.length; i++) 
            {
                var newScript = document.createElement('script');
                newScript.textContent = scripts[i].textContent;
                newScript.id = `script_inserted${scriptCounter++}`;
                document.body.appendChild(newScript);
            }

            if (pushToHistory) {
                window.history.pushState({ url: url }, '', url);
            }
        }
    }
    catch (error) {
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
