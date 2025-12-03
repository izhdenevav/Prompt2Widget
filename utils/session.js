function generateUUID() {
    return crypto.randomUUID();
}

function getSessionId() {
    let sessionId = localStorage.getItem('chat_session_id');
    
    if (sessionId) {
        return sessionId;
    }

    const urlParams = new URLSearchParams(window.location.search);
    sessionId = urlParams.get('session');

    if (sessionId) {
        localStorage.setItem('chat_session_id', sessionId);
        return sessionId;
    }

    sessionId = generateUUID();
    localStorage.setItem('chat_session_id', sessionId);

    const newUrl = new URL(window.location);
    newUrl.searchParams.set('session', sessionId);
    window.history.pushState({}, '', newUrl);

    return sessionId;
}

export const SESSION_ID = getSessionId();
console.log('Твоя сессия:', SESSION_ID);