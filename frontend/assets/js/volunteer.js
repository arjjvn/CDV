// =============================================
// CDVH | Volunteer Dashboard Logic
// =============================================

// --- Task Acceptance ---
function acceptJobRole() {
    const btn = document.getElementById('acceptRoleBtn');
    const originalText = btn.innerHTML;

    // Loading State
    btn.innerHTML = `<svg class="animate-spin w-5 h-5 mx-auto" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>`;
    btn.disabled = true;

    setTimeout(() => {
        btn.innerHTML = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg> Deployment Accepted`;
        btn.classList.remove('bg-brand-navy', 'btn-hover');
        btn.classList.add('bg-green-600', 'cursor-default');
        btn.nextElementSibling.classList.add('opacity-40', 'pointer-events-none');
    }, 1200);
}

// --- Add New Skill Submission ---
document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('addSkillForm').addEventListener('submit', function (e) {
        e.preventDefault();
        const skillName = document.getElementById('newSkillName').value;
        const container = document.getElementById('skillTags');

        const newTag = document.createElement('span');
        newTag.className = "bg-brand-navy text-white px-3 py-1.5 rounded text-xs font-medium flex items-center gap-2 animate-fade-in";
        newTag.innerHTML = `${skillName} <button class="hover:text-red-400" onclick="this.parentElement.remove()">&times;</button>`;
        container.appendChild(newTag);
        this.reset();
    });
});

// =============================================
// RAG Chatbot Logic
// =============================================
let isChatOpen = false;
let isChatExpanded = false;
const chatWindow = document.getElementById('chatWindow');
const resizeBtn = document.getElementById('chatResizeBtn');

function toggleChat() {
    isChatOpen = !isChatOpen;
    if (isChatOpen) {
        chatWindow.classList.remove('hidden');
        chatWindow.classList.add('flex');
    } else {
        chatWindow.classList.add('hidden');
        chatWindow.classList.remove('flex');
        // Reset size when closing
        if (isChatExpanded) toggleChatSize();
    }
}

function toggleChatSize() {
    isChatExpanded = !isChatExpanded;
    if (isChatExpanded) {
        chatWindow.classList.add('chat-expanded');
        resizeBtn.innerHTML = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 14v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4M4 10V6m0 0h4m-4 0l5 5m11-5l-5 5m5-5v4m0-4h-4"></path></svg>`;
        resizeBtn.title = "Minimize";
    } else {
        chatWindow.classList.remove('chat-expanded');
        resizeBtn.innerHTML = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path></svg>`;
        resizeBtn.title = "Maximize";
    }
    const chatArea = document.getElementById('chatMessages');
    chatArea.scrollTop = chatArea.scrollHeight;
}

// Simulated RAG Vector Database
const ragDatabase = {
    "flood":    "In a flood scenario, move to higher ground immediately. Do not walk or drive through floodwaters. Ensure you have your ID badge visible at all times.",
    "fire":     "If there is a fire, evacuate immediately. Stay low to the ground to avoid inhaling smoke. Check in with your Sector Coordinator immediately via the hub.",
    "medical":  "Standard triage protocol applies. Tag critical patients in RED. If someone is bleeding, apply direct firm pressure. Contact ambulances via the central hub.",
    "protocol": "Standard operating protocol dictates logging your hours in the dashboard after completing a task. Contact your coordinator if you need to extend your shift."
};

document.getElementById('chatForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const input = document.getElementById('chatInput');
    const msg = input.value.trim();
    if (!msg) return;

    addChatMessage(msg, 'user');
    input.value = '';

    setTimeout(() => {
        let reply = "Searching vector database... Based on general guidelines, please stay calm and follow the standard protocols listed in your profile.";
        const lowerMsg = msg.toLowerCase();
        for (const [key, context] of Object.entries(ragDatabase)) {
            if (lowerMsg.includes(key)) {
                reply = `<strong class="text-brand-navy text-[10px] uppercase tracking-widest block mb-1">[Context Retrieved via FAISS]</strong>${context}`;
                break;
            }
        }
        addChatMessage(reply, 'bot');
    }, 800);
});

function addChatMessage(text, sender) {
    const chatArea = document.getElementById('chatMessages');
    const div = document.createElement('div');
    if (sender === 'user') {
        div.className = "bg-brand-navy text-white p-3 rounded-lg rounded-tr-none text-sm self-end max-w-[85%] shadow-sm animate-slide-up leading-relaxed";
    } else {
        div.className = "bg-white p-3 rounded-lg rounded-tl-none border border-gray-200 text-sm text-gray-700 self-start max-w-[85%] shadow-sm animate-slide-up leading-relaxed";
    }
    div.innerHTML = text;
    chatArea.appendChild(div);
    chatArea.scrollTop = chatArea.scrollHeight;
}

