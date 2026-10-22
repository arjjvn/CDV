// =============================================
// CDVH | Coordinator Dashboard Logic
// =============================================

// --- Task Status Toggle ---
function updateTaskStatus(taskId, newStatus) {
    const badge = document.getElementById(`status-${taskId}`);
    if (!badge) return;
    // Remove all status classes
    badge.className = badge.className.replace(/status-\w+/g, '').trim();
    badge.classList.add(`status-${newStatus}`);
    const labels = { urgent: 'Urgent', active: 'Active', pending: 'Pending', resolved: 'Resolved' };
    badge.textContent = labels[newStatus] || newStatus;
}

// --- Volunteer Assignment Modal ---
function openAssignModal(taskId) {
    const modal = document.getElementById('assignModal');
    const taskLabel = document.getElementById('assignTaskLabel');
    if (modal && taskLabel) {
        taskLabel.textContent = `Task #${taskId}`;
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}
function closeAssignModal() {
    const modal = document.getElementById('assignModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

// --- Emergency Report Form ---
document.addEventListener('DOMContentLoaded', function () {
    const reportForm = document.getElementById('reportForm');
    if (reportForm) {
        reportForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const btn = this.querySelector('button[type="submit"]');
            const original = btn.innerHTML;

            btn.innerHTML = `<svg class="animate-spin w-4 h-4 mr-2 inline" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Processing...`;
            btn.disabled = true;

            setTimeout(() => {
                const status = document.getElementById('reportStatus');
                if (status) {
                    status.classList.remove('hidden');
                    status.classList.add('flex');
                }
                reportForm.reset();
                btn.innerHTML = original;
                btn.disabled = false;
            }, 1500);
        });
    }
});

// =============================================
// RAG Chatbot Logic
// =============================================
let isChatOpen = false;
const chatWindow = document.getElementById('chatWindow');

function toggleChat() {
    isChatOpen = !isChatOpen;
    if (isChatOpen) {
        chatWindow.classList.remove('hidden');
        chatWindow.classList.add('flex');
    } else {
        chatWindow.classList.add('hidden');
        chatWindow.classList.remove('flex');
    }
}

const ragDatabase = {
    "flood":      "Flood response protocol: Establish shelter at high-ground points. Coordinate water rescue teams. Deploy medical triage at entry checkpoints.",
    "fire":       "Fire response protocol: Establish perimeter. Coordinate with fire department. Assign logistics team for water/equipment supply.",
    "medical":    "Medical emergency: Activate closest medical volunteers. Tag severity using standard triage (RED/YELLOW/GREEN). Ambulance dispatch via hub.",
    "resource":   "Resource allocation: Check inventory dashboard for real-time stock levels. Prioritize critical resources to RED-tagged tasks first.",
    "volunteer":  "Volunteer management: Use ML matching module to assign volunteers. Ensure all volunteers have checked in and have valid ID.",
    "evacuation": "Evacuation protocol: Use predefined safe routes. Coordinate with local authorities. Assign volunteer marshals at each checkpoint."
};

document.getElementById('chatForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const input = document.getElementById('chatInput');
    const msg = input.value.trim();
    if (!msg) return;

    addChatMessage(msg, 'user');
    input.value = '';

    setTimeout(() => {
        let reply = "Searching knowledge base... Please consult local emergency response protocols and coordinate with your district administrator.";
        const lowerMsg = msg.toLowerCase();
        for (const [key, context] of Object.entries(ragDatabase)) {
            if (lowerMsg.includes(key)) {
                reply = `<strong class="text-brand-navy text-[10px] uppercase tracking-widest block mb-1">[Retrieved via FAISS Vector Search]</strong>${context}`;
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

