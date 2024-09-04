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

// user
var addFriendButton;
var acceptFriendButton;
var deleteFriendButton;
var cancelFriendButton;

let addInviteButton;
let acceptInviteButton;
let playInviteButton;
let cancelInviteButton;


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
    for (let i = 1; i <= scriptCounter - 1; i++) {
        const scriptElement = document.getElementById(`script_inserted${i}`);
        if (scriptElement) {
            document.body.removeChild(scriptElement);
        }
    }
    scriptCounter = 1;
}

function removeScriptsNavbar() {

    if (InviteSocket) {
        InviteSocket.close();
        InviteSocket = null;
        cleanup_navbar_authorized();
    }
    for (let i = 1; i <= scriptCounterNavbar - 1; i++) {
        const scriptElement = document.getElementById(`navbar_script_inserted${i}`);
        if (scriptElement) {
            document.body.removeChild(scriptElement);
        }
    }
    scriptCounterNavbar = 1;
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
    if (authorized_new != authorized_old)
    {
        var response = await fetch('/navbar_authorized/', {
            method: 'POST',
            credentials: 'include'
        })
        var html = await response.text();
        var navbarDiv = document.getElementById('navbar');
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
}

async function get_new_access_token()
{
    await fetch('/refresh/refresh/', {
        method: 'POST',
        credentials: 'include'
    });
}

async function loadContent2(url, option, pushToHistory)
{
    var response = await fetch(url, option)
    var html = await response.text();
    if (option.method == 'GET') {
        removeScripts();
        var appDiv = document.getElementById('app');
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

async function loadContent(url, option, pushToHistory = false) {
    try {
        
        await get_new_access_token();
        await loadContent2(url, option, pushToHistory);
        await get_new_access_token();
        await loadNavbar();
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
