const API_BASE = '/api/v1';
let state = {
    token: localStorage.getItem('access_token'),
    user: null,
    currentView: 'login',
    authMode: 'login',
    activeChat: null,
    socket: null
};

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    if (state.token) {
        initApp();
    } else {
        switchView('login');
    }
});

async function initApp() {
    try {
        await fetchProfile();
        updateNavUser();

        document.getElementById('nav-login').style.display = 'none';
        document.getElementById('nav-logout').style.display = 'block';
        document.getElementById('nav-profile').style.display = 'block';

        switchView('social-search'); // Default after login
    } catch (e) {
        logout();
    }
}

// --- Navigation & UI ---
function switchView(viewId) {
    // Determine active section for nav
    const viewName = `view-${viewId}`;
    document.querySelectorAll('.view').forEach(el => el.classList.add('hidden'));
    document.getElementById(viewName).classList.remove('hidden');

    // Update Sidebar Active state
    document.querySelectorAll('.nav-links li').forEach(li => li.classList.remove('active'));
    // Find the li that triggered this (naive matching)
    // ... skipping strictly for simplicity

    state.currentView = viewId;

    if (viewId === 'chat') refreshChatList();
    if (viewId === 'social-friends') loadFriends();
    if (viewId === 'social-requests') loadRequests();
    if (viewId === 'profile') loadProfile();
}

function setAuthMode(mode) {
    state.authMode = mode;
    document.querySelectorAll('.tabs button').forEach(b => b.classList.remove('active'));
    document.getElementById(`tab-${mode}`).classList.add('active');

    // Show/Hide fields
    const fields = {
        login: ['grp-username', 'grp-password'],
        register: ['grp-email', 'grp-password', 'grp-username', 'grp-fullname', 'grp-birthdate', 'grp-role'],
        verify: ['grp-email', 'grp-code']
    };

    document.querySelectorAll('.form-group').forEach(f => f.classList.add('hidden'));
    fields[mode].forEach(id => document.getElementById(id).classList.remove('hidden'));

    document.getElementById('auth-submit-btn').innerText = mode.toUpperCase();
}

// --- API Helper ---
async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = { 'Content-Type': 'application/json' };
    if (state.token) headers['Authorization'] = `Bearer ${state.token}`;

    logConsole(`REQ: ${method} ${endpoint}`, 'req');

    try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method,
            headers,
            body: body ? JSON.stringify(body) : null
        });

        const data = await res.json();

        if (res.ok) {
            logConsole(`RES: ${res.status} OK`, 'success');
            return data;
        } else {
            console.error(data);
            logConsole(`ERR: ${res.status} - ${JSON.stringify(data)}`, 'error');
            throw data;
        }
    } catch (e) {
        logConsole(`FAIL: ${e.message || JSON.stringify(e)}`, 'error');
        throw e;
    }
}

function logConsole(msg, type) {
    const consoleDiv = document.getElementById('api-console');
    const div = document.createElement('div');
    div.className = `log-entry log-${type}`;
    div.innerText = `[${new Date().toLocaleTimeString()}] ${msg}`;
    consoleDiv.prepend(div);
}

function clearConsole() {
    document.getElementById('api-console').innerHTML = '';
}

// --- Auth Functions ---
async function handleAuthSubmit(e) {
    e.preventDefault();
    const mode = state.authMode;
    const body = {};

    if (mode === 'login') {
        // Actually login endpoint uses username/password usually, but let's check input
        // Since we are using email for input ID, but serializers usually take 'username' or 'email'.
        // LoginSerializer takes 'username' (which can be email) and 'password'.
        body.username = document.getElementById('username').value;
        body.password = document.getElementById('password').value;

        try {
            const data = await apiCall('/auth/login/', 'POST', body);
            state.token = data.tokens.access;
            localStorage.setItem('access_token', state.token);
            initApp();
        } catch (e) { }

    } else if (mode === 'register') {
        body.email = document.getElementById('email').value;
        body.password = document.getElementById('password').value;
        body.username = document.getElementById('username').value;
        body.full_name = document.getElementById('full_name').value;
        body.birth_date = document.getElementById('birth_date').value;
        body.role = document.getElementById('role').value;

        try {
            await apiCall('/auth/register/', 'POST', body);
            alert('OTP Sent! Please switch to Verify mode.');
            setAuthMode('verify');
        } catch (e) { }

    } else if (mode === 'verify') {
        body.email = document.getElementById('email').value;
        body.code = document.getElementById('code').value;

        try {
            const data = await apiCall('/auth/verify-otp/', 'POST', body);
            alert('Verified! You can now Login.');
            setAuthMode('login');
        } catch (e) { }
    }
}

function logout() {
    state.token = null;
    state.user = null;
    localStorage.removeItem('access_token');
    location.reload();
}

async function fetchProfile() {
    const data = await apiCall('/auth/me/');
    state.user = data;
    return data;
}

function updateNavUser() {
    if (state.user) {
        document.getElementById('nav-user-info').style.display = 'flex';
        document.getElementById('nav-username').innerText = state.user.username;
        document.getElementById('nav-role').innerText = state.user.role;
        document.getElementById('nav-avatar').style.backgroundImage = `url(${state.user.profile_image || ''})`;
    }
}

// --- Social Functions ---
async function handleUserSearch() {
    const query = document.getElementById('user-search-input').value;
    if (query.length < 2) return;

    try {
        const users = await apiCall(`/auth/users/search/?query=${query}`);
        const container = document.getElementById('user-search-results');
        container.innerHTML = '';

        users.forEach(user => {
            container.innerHTML += `
                <div class="card">
                    <img src="${user.profile_image || 'https://via.placeholder.com/60'}" class="card-img">
                    <strong>${user.username}</strong>
                    <button class="btn-small" onclick="sendFriendRequest(${user.id})">Add Friend</button>
                    <button class="btn-small" onclick="startChat(${user.id}, '${user.username}')">Message</button>
                </div>
            `;
        });
    } catch (e) { }
}

async function sendFriendRequest(userId) {
    try {
        await apiCall('/auth/friends/requests/', 'POST', { to_user_id: userId });
        alert('Request Sent');
    } catch (e) { alert(e.error || 'Failed'); }
}

async function loadFriends() {
    const list = await apiCall('/auth/friends/');
    const container = document.getElementById('friends-list');
    container.innerHTML = '';
    list.forEach(user => {
        container.innerHTML += `
            <div class="card">
                <img src="${user.profile_image || 'https://via.placeholder.com/60'}" class="card-img">
                <strong>${user.username}</strong>
                <button class="btn-small" onclick="startChat(${user.id}, '${user.username}')">Message</button>
                <button class="btn-small" style="background:#cf6679" onclick="unfriend(${user.id})">Unfriend</button>
            </div>
        `;
    });
}

async function unfriend(id) {
    if (confirm('Are you sure?')) {
        await apiCall(`/auth/friends/${id}/`, 'DELETE');
        loadFriends();
    }
}

async function loadRequests() {
    const received = await apiCall('/auth/friends/requests/received/');
    const sent = await apiCall('/auth/friends/requests/sent/');

    const rDiv = document.getElementById('requests-received');
    rDiv.innerHTML = received.map(r => `
        <div class="list-item">
            <span>From: <b>${r.from_user.username}</b></span>
            <div>
                <button class="btn-small" onclick="respondRequest(${r.id}, 'accept')">Accept</button>
                <button class="btn-small" onclick="respondRequest(${r.id}, 'decline')">Decline</button>
            </div>
        </div>
    `).join('');

    const sDiv = document.getElementById('requests-sent');
    sDiv.innerHTML = sent.map(r => `
        <div class="list-item">
            <span>To: <b>${r.to_user.username}</b></span>
            <small>Pending</small>
        </div>
    `).join('');
}

async function respondRequest(id, action) {
    await apiCall(`/auth/friends/requests/${id}/${action}/`, 'PUT');
    loadRequests();
}

// --- Chat Functions ---
async function loadRooms() {
    const rooms = await apiCall('/chat/rooms/');
    const list = document.getElementById('room-list');
    list.innerHTML = '';

    rooms.forEach(room => {
        let name = room.name;
        if (!room.is_group) {
            // Find other participant
            const other = room.participants.find(p => p.username !== state.user.username);
            name = other ? other.username : 'Unknown';
        }

        const div = document.createElement('div');
        div.className = 'room-item';
        div.onclick = () => openChatRoom(room.id, name);
        div.innerHTML = `<h4>${name}</h4><p>${room.last_message ? room.last_message.text : 'No messages'}</p>`;
        list.appendChild(div);
    });
}

async function startChat(userId, username) {
    const room = await apiCall(`/chat/rooms/private/${userId}/`, 'POST');
    switchView('chat');
    openChatRoom(room.id, username);
}

async function openChatRoom(roomId, name) {
    state.activeChat = roomId;
    document.getElementById('chat-participant-name').innerText = name;
    document.getElementById('message-input').disabled = false;
    document.getElementById('send-btn').disabled = false;

    // Load History
    const msgs = await apiCall(`/chat/messages/?room_id=${roomId}`);
    const container = document.getElementById('chat-messages');
    container.innerHTML = '';
    msgs.forEach(displayMessage);

    connectSocket(roomId);
}

function connectSocket(roomId) {
    if (state.socket) state.socket.close();

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}/ws/chat/${roomId}/?token=${state.token}`;

    state.socket = new WebSocket(url);

    state.socket.onmessage = (e) => {
        const data = JSON.parse(e.data);
        displayMessage(data);
    };
    state.socket.onopen = () => logConsole('WS Connected', 'success');
}

function displayMessage(msg) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    const isMe = msg.sender.username === state.user.username;
    div.className = `message ${isMe ? 'sent' : 'received'}`;
    div.innerText = msg.message || msg.text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function sendMessage() {
    const input = document.getElementById('message-input');
    const text = input.value.trim();
    if (text && state.socket) {
        state.socket.send(JSON.stringify({ message: text }));
        input.value = '';
    }
}
// --- Profile Functions ---
async function loadProfile() {
    const user = await fetchProfile(); // Gets from /me/

    // Populate fields
    document.getElementById('prof-fullname').value = user.full_name || '';
    document.getElementById('prof-phone').value = user.phone_number || '';
    document.getElementById('prof-settings').value = JSON.stringify(user.settings || {}, null, 2);
    document.getElementById('prof-birthdate').value = user.birth_date || '';
    document.getElementById('prof-role').value = user.role || 'ADULT';
    document.getElementById('prof-fav-roles').value = (user.favorite_roles || []).join(', ');

    // Image
    document.getElementById('profile-img-preview').src = user.profile_image || 'https://via.placeholder.com/100';
}

async function updateBasicProfile(e) {
    e.preventDefault();
    const body = {
        full_name: document.getElementById('prof-fullname').value,
        phone_number: document.getElementById('prof-phone').value
    };
    try {
        await apiCall('/auth/me/', 'PUT', body);
        alert('Profile Updated');
        initApp(); // Refresh global state
    } catch (e) { }
}

async function updateSettings() {
    try {
        const settings = JSON.parse(document.getElementById('prof-settings').value);
        await apiCall('/auth/me/settings/', 'PUT', { settings });
        alert('Settings Updated');
    } catch (e) { alert('Invalid JSON'); }
}

async function uploadProfileImage() {
    const file = document.getElementById('profile-image-input').files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('profile_image', file);

    logConsole(`REQ: PATCH /auth/me/profile-image/ [File]`, 'req');

    try {
        const res = await fetch(`${API_BASE}/auth/me/profile-image/`, {
            method: 'PATCH',
            headers: { 'Authorization': `Bearer ${state.token}` },
            body: formData
        });
        const data = await res.json();
        if (res.ok) {
            logConsole('RES: Image Uploaded', 'success');
            document.getElementById('profile-img-preview').src = data.profile_image;
            updateNavUser();
        } else {
            throw data;
        }
    } catch (e) { logConsole(JSON.stringify(e), 'error'); }
}

async function updateBirthDate() {
    const date = document.getElementById('prof-birthdate').value;
    try {
        await apiCall('/auth/me/birth-date/', 'PUT', { birth_date: date });
        alert('Birth Date Updated');
    } catch (e) { }
}

async function updateUserRole() {
    const role = document.getElementById('prof-role').value;
    try {
        await apiCall('/auth/me/user-type/', 'PUT', { role });
        alert('Role Updated');
        updateNavUser();
    } catch (e) { }
}

async function updateFavRoles() {
    const input = document.getElementById('prof-fav-roles').value;
    const roles = input.split(',').map(s => s.trim()).filter(s => s);
    try {
        await apiCall('/auth/me/favorite-roles/', 'PUT', { favorite_roles: roles });
        alert('Favorite Roles Updated');
    } catch (e) { }
}

async function deactivateAccount() {
    if (confirm('Are you sure you want to deactivate your account? This cannot be undone easily.')) {
        try {
            await apiCall('/auth/me/', 'DELETE');
            alert('Account Deactivated');
            logout();
        } catch (e) { }
    }
}
