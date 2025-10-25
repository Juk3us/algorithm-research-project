// Global state
let currentThreadId = null;
let isLoggedIn = false;
let currentUsername = null;

// DOM elements
const loginModal = document.getElementById('login-modal');
const loginBtn = document.getElementById('login-btn');
const cancelLoginBtn = document.getElementById('cancel-login');
const submitLoginBtn = document.getElementById('submit-login');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const userInfo = document.getElementById('user-info');

// Menu navigation
document.querySelectorAll('.menu-item').forEach(item => {
    item.addEventListener('click', () => {
        const page = item.dataset.page;
        showPage(page);

        document.querySelectorAll('.menu-item').forEach(m => m.classList.remove('active'));
        item.classList.add('active');
    });
});

function showPage(pageName) {
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById(`${pageName}-page`).classList.add('active');

    // Load data for specific pages
    if (pageName === 'messages' && isLoggedIn) {
        loadMessages();
    } else if (pageName === 'training') {
        loadTrainingData();
    } else if (pageName === 'settings') {
        loadSettings();
    } else if (pageName === 'statistics') {
        loadStatistics();
    } else if (pageName === 'dashboard') {
        loadDashboard();
    }
}

// Login functionality
loginBtn.addEventListener('click', () => {
    loginModal.classList.add('active');
});

cancelLoginBtn.addEventListener('click', () => {
    loginModal.classList.remove('active');
});

submitLoginBtn.addEventListener('click', async () => {
    const username = usernameInput.value.trim();
    const password = passwordInput.value.trim();

    if (!username || !password) {
        alert('لطفاً یوزرنیم و پسورد را وارد کنید');
        return;
    }

    submitLoginBtn.disabled = true;
    submitLoginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> در حال ورود...';

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();

        if (data.success) {
            isLoggedIn = true;
            currentUsername = username;
            loginModal.classList.remove('active');
            updateUserInfo();
            loadDashboard();
            alert('ورود موفقیت‌آمیز بود!');
        } else {
            alert(`خطا: ${data.error}`);
        }
    } catch (error) {
        alert(`خطا در ورود: ${error.message}`);
    } finally {
        submitLoginBtn.disabled = false;
        submitLoginBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> ورود';
    }
});

function updateUserInfo() {
    if (isLoggedIn) {
        userInfo.innerHTML = `
            <div style="text-align: center; margin-bottom: 12px;">
                <i class="fas fa-user-circle" style="font-size: 48px;"></i>
                <div style="margin-top: 8px; font-weight: 500;">@${currentUsername}</div>
            </div>
            <button class="btn btn-secondary" onclick="logout()" style="width: 100%;">
                <i class="fas fa-sign-out-alt"></i>
                خروج
            </button>
        `;
    } else {
        userInfo.innerHTML = `
            <button class="btn btn-primary" id="login-btn" style="width: 100%;">
                <i class="fas fa-sign-in-alt"></i>
                ورود به اینستاگرام
            </button>
        `;
    }
}

async function logout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
        isLoggedIn = false;
        currentUsername = null;
        currentThreadId = null;
        updateUserInfo();
        showPage('dashboard');
        alert('خروج موفقیت‌آمیز بود');
    } catch (error) {
        alert(`خطا در خروج: ${error.message}`);
    }
}

// Dashboard
async function loadDashboard() {
    try {
        const response = await fetch('/api/statistics');
        const data = await response.json();

        if (data.success) {
            const stats = data.statistics;
            document.getElementById('total-conversations').textContent = stats.total_conversations || 0;
            document.getElementById('total-messages').textContent = stats.total_messages || 0;
            document.getElementById('today-conversations').textContent = stats.today_conversations || 0;
        }

        const settingsResponse = await fetch('/api/settings');
        const settingsData = await settingsResponse.json();

        if (settingsData.success) {
            const autoReply = settingsData.settings.auto_reply_enabled === 'true';
            document.getElementById('auto-reply-status').textContent = autoReply ? 'فعال' : 'غیرفعال';
        }
    } catch (error) {
        console.error('خطا در بارگذاری داشبورد:', error);
    }
}

// Messages
document.getElementById('refresh-messages')?.addEventListener('click', loadMessages);

async function loadMessages() {
    if (!isLoggedIn) {
        document.getElementById('messages-list-content').innerHTML = '<p class="empty-state">لطفاً ابتدا وارد شوید</p>';
        return;
    }

    try {
        const response = await fetch('/api/messages');
        const data = await response.json();

        if (data.success) {
            displayMessages(data.messages);
        } else {
            alert(`خطا: ${data.error}`);
        }
    } catch (error) {
        alert(`خطا در دریافت پیام‌ها: ${error.message}`);
    }
}

function displayMessages(messages) {
    const container = document.getElementById('messages-list-content');

    if (messages.length === 0) {
        container.innerHTML = '<p class="empty-state">پیامی وجود ندارد</p>';
        return;
    }

    container.innerHTML = messages.map(msg => {
        const user = msg.users[0];
        const lastMsg = msg.last_message;

        return `
            <div class="message-item" onclick="loadConversation('${msg.thread_id}')">
                <div class="message-item-header">
                    <span class="message-item-user">${user.full_name || user.username}</span>
                    <span class="message-item-time">${lastMsg ? formatTime(lastMsg.timestamp) : ''}</span>
                </div>
                <div class="message-item-preview">${lastMsg ? lastMsg.text : 'بدون پیام'}</div>
            </div>
        `;
    }).join('');
}

async function loadConversation(threadId) {
    currentThreadId = threadId;

    try {
        const response = await fetch(`/api/conversation/${threadId}`);
        const data = await response.json();

        if (data.success) {
            displayConversation(data.conversation);
        } else {
            alert(`خطا: ${data.error}`);
        }
    } catch (error) {
        alert(`خطا در دریافت مکالمه: ${error.message}`);
    }
}

function displayConversation(conversation) {
    const container = document.getElementById('conversation-view');
    const user = conversation.users[0];

    const messagesHtml = conversation.messages.map(msg => {
        const className = msg.is_sent_by_me ? 'sent' : 'received';
        return `
            <div class="message-bubble ${className}">
                <div>${msg.text}</div>
                <div class="message-time">${formatTime(msg.timestamp)}</div>
            </div>
        `;
    }).join('');

    container.innerHTML = `
        <div class="conversation-header">
            <h3>${user.full_name || user.username}</h3>
        </div>
        <div class="conversation-messages">
            ${messagesHtml}
        </div>
        <div class="conversation-input">
            <input type="text" id="message-input" placeholder="پیام خود را بنویسید...">
            <button class="btn btn-primary" onclick="sendManualMessage()">
                <i class="fas fa-paper-plane"></i>
            </button>
            <button class="btn btn-primary" onclick="sendAutoReply()">
                <i class="fas fa-robot"></i>
                پاسخ هوشمند
            </button>
        </div>
    `;

    // Scroll to bottom
    const messagesContainer = container.querySelector('.conversation-messages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Highlight active message
    document.querySelectorAll('.message-item').forEach(item => item.classList.remove('active'));
}

async function sendManualMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();

    if (!message || !currentThreadId) return;

    try {
        const response = await fetch('/api/send-message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                thread_id: currentThreadId,
                message: message,
            }),
        });

        const data = await response.json();

        if (data.success) {
            input.value = '';
            loadConversation(currentThreadId);
        } else {
            alert(`خطا: ${data.error}`);
        }
    } catch (error) {
        alert(`خطا در ارسال پیام: ${error.message}`);
    }
}

async function sendAutoReply() {
    if (!currentThreadId) return;

    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> در حال تولید پاسخ...';

    try {
        // Get last message from conversation
        const conversationResponse = await fetch(`/api/conversation/${currentThreadId}`);
        const conversationData = await conversationResponse.json();

        if (!conversationData.success) {
            throw new Error('خطا در دریافت مکالمه');
        }

        const messages = conversationData.conversation.messages;
        const lastUserMessage = messages.reverse().find(m => !m.is_sent_by_me);

        if (!lastUserMessage) {
            alert('پیامی از کاربر یافت نشد');
            return;
        }

        const response = await fetch('/api/auto-reply', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                thread_id: currentThreadId,
                user_message: lastUserMessage.text,
            }),
        });

        const data = await response.json();

        if (data.success) {
            alert(`پاسخ ارسال شد!\nمرحله: ${data.conversation_stage}/5`);
            loadConversation(currentThreadId);
        } else {
            alert(`خطا: ${data.error}`);
        }
    } catch (error) {
        alert(`خطا: ${error.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-robot"></i> پاسخ هوشمند';
    }
}

// Training
const trainingTypeRadios = document.querySelectorAll('input[name="training-type"]');
trainingTypeRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
        if (e.target.value === 'text') {
            document.getElementById('text-training-group').classList.remove('hidden');
            document.getElementById('voice-training-group').classList.add('hidden');
        } else {
            document.getElementById('text-training-group').classList.add('hidden');
            document.getElementById('voice-training-group').classList.remove('hidden');
        }
    });
});

document.getElementById('save-training')?.addEventListener('click', async () => {
    const type = document.querySelector('input[name="training-type"]:checked').value;
    let content;

    if (type === 'text') {
        content = document.getElementById('training-text').value.trim();
        if (!content) {
            alert('لطفاً متن آموزشی را وارد کنید');
            return;
        }
    } else {
        alert('آپلود فایل صوتی هنوز پیاده‌سازی نشده است');
        return;
    }

    try {
        const response = await fetch('/api/train-agent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ type, content }),
        });

        const data = await response.json();

        if (data.success) {
            alert('اطلاعات آموزشی ذخیره شد!');
            document.getElementById('training-text').value = '';
            loadTrainingData();
        } else {
            alert(`خطا: ${data.error}`);
        }
    } catch (error) {
        alert(`خطا: ${error.message}`);
    }
});

async function loadTrainingData() {
    try {
        const response = await fetch('/api/statistics');
        const data = await response.json();

        // For now, we'll just show a placeholder
        // In a real implementation, you'd fetch training data specifically
        document.getElementById('training-items').innerHTML = `
            <p class="empty-state">اطلاعات آموزشی ذخیره شده در دیتابیس است</p>
        `;
    } catch (error) {
        console.error('خطا در بارگذاری اطلاعات آموزشی:', error);
    }
}

// Settings
document.getElementById('save-settings')?.addEventListener('click', async () => {
    const settings = {
        auto_reply_enabled: document.getElementById('auto-reply-toggle').checked.toString(),
        max_conversation_stages: document.getElementById('max-stages').value,
        response_delay_seconds: document.getElementById('response-delay').value,
    };

    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings),
        });

        const data = await response.json();

        if (data.success) {
            alert('تنظیمات ذخیره شد!');
        } else {
            alert(`خطا: ${data.error}`);
        }
    } catch (error) {
        alert(`خطا: ${error.message}`);
    }
});

async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        const data = await response.json();

        if (data.success) {
            const settings = data.settings;
            document.getElementById('auto-reply-toggle').checked = settings.auto_reply_enabled === 'true';
            document.getElementById('max-stages').value = settings.max_conversation_stages || 5;
            document.getElementById('response-delay').value = settings.response_delay_seconds || 3;
        }
    } catch (error) {
        console.error('خطا در بارگذاری تنظیمات:', error);
    }
}

// Statistics
async function loadStatistics() {
    try {
        const response = await fetch('/api/statistics');
        const data = await response.json();

        if (data.success) {
            const stats = data.statistics;
            const stages = stats.stage_distribution || {};

            const maxCount = Math.max(...Object.values(stages), 1);

            for (let i = 1; i <= 5; i++) {
                const count = stages[i] || 0;
                const percentage = (count / maxCount) * 100;

                const stageBars = document.querySelectorAll('.stage-bar');
                if (stageBars[i - 1]) {
                    stageBars[i - 1].querySelector('.bar-fill').style.width = `${percentage}%`;
                    stageBars[i - 1].querySelector('.count').textContent = count;
                }
            }
        }
    } catch (error) {
        console.error('خطا در بارگذاری آمار:', error);
    }
}

// Utilities
function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) return 'الان';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} دقیقه پیش`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} ساعت پیش`;

    return date.toLocaleDateString('fa-IR');
}

// Initialize
loadDashboard();
