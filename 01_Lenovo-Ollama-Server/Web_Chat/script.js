const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const historyList = document.getElementById('history-list');
const sendBtn = document.getElementById('send-btn');

// Sohbetleri sunucudan çekeceğiz
let chats = [];
let currentChatId = null;
let abortController = null; // Bağlantıyı kesmek için kumanda

// --- AÇILIŞ ---
window.onload = async function() {
    await loadHistoryFromServer();
    
    if (chats.length > 0) {
        loadChat(chats[0].id);
    } else {
        startNewChat(false);
    }
    
    updateSystemStats();
};

if(userInput) {
    userInput.addEventListener("keypress", function(event) {
        // Eğer durdurma modundaysak Enter tuşu çalışmasın
        if (event.key === "Enter" && !sendBtn.classList.contains('stop-mode')) sendMessage();
    });
}
// Buton tıklaması dinamik olarak değişecek, event listener'a gerek kalmadı (HTML'de onclick var)

// --- BUTON DURUMUNU YÖNET ---
function toggleButtonState(state) {
    if (state === 'generating') {
        // Durdurma Moduna Geç
        sendBtn.innerHTML = '<i class="fa-solid fa-stop"></i>';
        sendBtn.classList.add('stop-mode');
        sendBtn.onclick = stopGeneration; // Tıklanınca durdursun
    } else {
        // Gönderme Moduna Geç
        sendBtn.innerHTML = '<i class="fa-solid fa-arrow-up"></i>';
        sendBtn.classList.remove('stop-mode');
        sendBtn.onclick = sendMessage; // Tıklanınca göndersin
    }
}

// --- DURDURMA İŞLEMİ ---
function stopGeneration() {
    if (abortController) {
        abortController.abort(); // Sunucuyla bağlantıyı kopar
        abortController = null;
    }
}

// --- SUNUCU İŞLEMLERİ ---
async function loadHistoryFromServer() {
    try {
        const res = await fetch('/api/history');
        if (res.ok) {
            chats = await res.json();
            renderHistoryList();
        }
    } catch (e) {
        console.error("Geçmiş yüklenemedi:", e);
    }
}

async function saveChatToServer(chatObj) {
    try {
        await fetch('/api/save_chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(chatObj)
        });
    } catch (e) {}
}

async function deleteChatFromServer(id) {
    try {
        await fetch('/api/delete_chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id })
        });
    } catch (e) {}
}

function startNewChat(saveImmediately = true) {
    const newId = Date.now();
    chatContainer.innerHTML = `
        <div class="message bot">
            <div class="avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="bubble">Sistem hazır. Ortak veritabanına bağlıyım.</div>
        </div>`;
    
    currentChatId = newId;

    if (saveImmediately) {
        const newChat = { id: newId, title: "Yeni Sohbet", messages: [] };
        chats.unshift(newChat);
        renderHistoryList();
        saveChatToServer(newChat);
    }
}

function deleteCurrentChat() {
    if (!currentChatId) return;
    if(confirm("Bu sohbeti KALICI OLARAK silmek istiyor musunuz?")) {
        deleteChatFromServer(currentChatId);
        chats = chats.filter(c => c.id !== currentChatId);
        if (chats.length > 0) loadChat(chats[0].id);
        else startNewChat(true);
        renderHistoryList();
    }
}

// --- MESAJ GÖNDERME (YENİLENMİŞ) ---
async function sendMessage() {
    const text = userInput.value;
    if (text.trim() === "") return;

    // UI Ekle
    addMessageToUI(text, 'user');
    userInput.value = '';
    userInput.disabled = true;

    // BUTONU DURDURMA MODUNA AL
    toggleButtonState('generating');

    updateLocalHistory(text, 'user');

    const botBubble = addMessageToUI("...", 'bot', true);
    let fullResponse = "";

    // İptal sinyalini oluştur
    abortController = new AbortController();
    const signal = abortController.signal;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text }),
            signal: signal // <--- İptal için gerekli sinyal
        });

        botBubble.innerHTML = ""; 
        botBubble.classList.remove('loading-dots');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            fullResponse += chunk;
            botBubble.innerHTML = marked.parse(fullResponse);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        botBubble.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });

        if (window.MathJax) MathJax.typeset();

        updateLocalHistory(fullResponse, 'bot');

    } catch (error) {
        if (error.name === 'AbortError') {
            botBubble.innerHTML += " <br><i>[İşlem durduruldu.]</i>";
            updateLocalHistory(fullResponse + " [Durduruldu]", 'bot');
        } else {
            botBubble.innerText += " [Bağlantı Hatası]";
        }
    } finally {
        // İŞLEM BİTTİ, BUTONU VE KUTUYU ESKİ HALİNE GETİR
        toggleButtonState('idle');
        userInput.disabled = false;
        userInput.focus();
        abortController = null;
    }
}

// --- GEÇMİŞ YÖNETİMİ ---
function updateLocalHistory(text, sender) {
    let chatIndex = chats.findIndex(c => c.id === currentChatId);
    if (chatIndex === -1) {
        const newChat = { id: currentChatId, title: text.substring(0, 20) + "...", messages: [] };
        chats.unshift(newChat);
        chatIndex = 0;
    }
    let chat = chats[chatIndex];

    if (sender === 'user' && (chat.title === "Yeni Sohbet" || chat.messages.length === 0)) {
        let newTitle = text.substring(0, 25);
        if(text.length > 25) newTitle += "...";
        chat.title = newTitle;
    }

    if (sender === 'bot' && chat.messages.length > 0 && chat.messages[chat.messages.length - 1].sender === 'bot') {
        chat.messages[chat.messages.length - 1].text = text;
    } else {
        chat.messages.push({ text, sender });
    }

    chats.splice(chatIndex, 1);
    chats.unshift(chat);
    renderHistoryList();
    saveChatToServer(chat);
}

function loadChat(id) {
    currentChatId = id;
    const chat = chats.find(c => c.id === id);
    if (!chat) return;
    
    chatContainer.innerHTML = '';
    chat.messages.forEach(msg => {
        const bubble = addMessageToUI(msg.text, msg.sender, false);
        if(msg.sender === 'bot') {
            bubble.innerHTML = marked.parse(msg.text);
            bubble.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        }
    });
    renderHistoryList();
    if (window.MathJax) MathJax.typeset();
}

function renderHistoryList() {
    if (!historyList) return;
    historyList.innerHTML = '';
    chats.forEach(chat => {
        const isActive = chat.id === currentChatId ? 'active' : '';
        let safeTitle = chat.title.replace(/</g, "&lt;").replace(/>/g, "&gt;");
        historyList.insertAdjacentHTML('beforeend', 
            `<div class="history-item ${isActive}" onclick="loadChat(${chat.id})">
                <i class="fa-regular fa-message"></i> ${safeTitle}
            </div>`
        );
    });
}

function addMessageToUI(text, sender, isLoading = false) {
    const id = "msg-" + Date.now() + Math.floor(Math.random() * 1000);
    const icon = sender === 'user' ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';
    const loadingClass = isLoading ? 'loading-dots' : '';
    const html = `
        <div class="message ${sender}" id="${id}">
            <div class="avatar">${icon}</div>
            <div class="bubble ${loadingClass}"></div>
        </div>`;
    chatContainer.insertAdjacentHTML('beforeend', html);
    const bubble = document.querySelector(`#${id} .bubble`);
    if (sender === 'user') bubble.innerText = text;
    else bubble.innerText = text;
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return bubble;
}

// --- İSTATİSTİKLER ---
async function updateSystemStats() {
    try {
        const res = await fetch('/api/stats');
        if (!res.ok) return;
        const data = await res.json();
        const ramBar = document.getElementById('ram-bar');
        const ramText = document.getElementById('ram-text');
        if (ramBar) { ramBar.style.width = data.ram_percent + '%'; ramBar.style.backgroundColor = '#4f46e5'; }
        if (ramText) ramText.innerText = data.ram_text;
        const cpuBar = document.getElementById('cpu-bar');
        const cpuText = document.getElementById('cpu-text');
        if (cpuBar) cpuBar.style.width = data.cpu + '%';
        if (cpuText) cpuText.innerText = '%' + data.cpu + ' Kullanım';
        const tempCpu = document.getElementById('temp-cpu');
        const tempSys = document.getElementById('temp-sys');
        if (tempCpu) tempCpu.innerText = data.temp_cpu + '°C';
        if (tempSys) tempSys.innerText = data.temp_sys + '°C';
    } catch (e) {}
}
setInterval(updateSystemStats, 2000);