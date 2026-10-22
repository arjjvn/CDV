// =============================================
// CDVH | Admin Dashboard Logic
// =============================================

// --- User Role Update ---
function updateUserRole(userId, newRole) {
    const badge = document.getElementById(`role-${userId}`);
    if (!badge) return;
    badge.className = badge.className.replace(/role-\w+/g, '').trim() + ` role-${newRole} px-2 py-0.5 rounded text-xs font-bold`;
    const labels = { admin: 'Admin', coordinator: 'Coordinator', volunteer: 'Volunteer' };
    badge.textContent = labels[newRole] || newRole;
}

// --- Confirm Delete User ---
function confirmDelete(userId, userName) {
    const modal = document.getElementById('deleteModal');
    const nameEl = document.getElementById('deleteUserName');
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    if (modal && nameEl && confirmBtn) {
        nameEl.textContent = userName;
        confirmBtn.onclick = () => {
            // In real app: call DELETE /api/users/{userId}
            const row = document.getElementById(`user-row-${userId}`);
            if (row) row.remove();
            closeDeleteModal();
            showToast(`User ${userName} has been removed.`, 'success');
        };
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}
function closeDeleteModal() {
    const modal = document.getElementById('deleteModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

// --- Toast Notification ---
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toastMessage');
    if (!toast || !toastMsg) return;
    toastMsg.textContent = message;
    toast.className = toast.className.replace(/bg-\w+-\d+/g, '');
    toast.classList.add(type === 'success' ? 'bg-green-600' : 'bg-brand-red');
    toast.classList.remove('translate-y-20', 'opacity-0');
    toast.classList.add('translate-y-0', 'opacity-100');
    setTimeout(() => {
        toast.classList.add('translate-y-20', 'opacity-0');
        toast.classList.remove('translate-y-0', 'opacity-100');
    }, 3000);
}

// --- System Settings Form ---
document.addEventListener('DOMContentLoaded', function () {
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const btn = this.querySelector('button[type="submit"]');
            const original = btn.innerHTML;
            btn.innerHTML = `<svg class="animate-spin w-4 h-4 mr-2 inline" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Saving...`;
            btn.disabled = true;
            setTimeout(() => {
                btn.innerHTML = original;
                btn.disabled = false;
                showToast('Settings saved successfully!', 'success');
            }, 1200);
        });
    }

    // --- Search / Filter Users ---
    const searchInput = document.getElementById('userSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            const query = this.value.toLowerCase();
            document.querySelectorAll('.user-row').forEach(row => {
                const name = row.dataset.name || '';
                row.style.display = name.toLowerCase().includes(query) ? '' : 'none';
            });
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
    "user":       "User management: Assign roles via the Users panel. Coordinators can manage tasks; volunteers can accept deployments. Admins have full system access.",
    "volunteer":  "Volunteer management: Volunteers are matched using the Scikit-learn ML module based on distance, skills, and availability score.",
    "ml":         "The ML Matching module uses Random Forest and KNN algorithms to score volunteers 0–100 per task. Scores above 80 are auto-suggested.",
    "disaster":   "During active disaster events, the system enters HIGH ALERT mode. All volunteers are pinged, and coordinators are notified via the system dashboard.",
    "system":     "System settings allow you to configure alert thresholds, enable/disable ML matching, manage API keys, and control the RAG knowledge base.",
    "security":   "The system uses JWT-based authentication with refresh tokens. All API endpoints are secured and role-gated via FastAPI middleware."
};

document.getElementById('chatForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const input = document.getElementById('chatInput');
    const msg = input.value.trim();
    if (!msg) return;
    addChatMessage(msg, 'user');
    input.value = '';
    setTimeout(() => {
        let reply = "Querying admin knowledge base... For advanced configuration, refer to the system documentation or contact the technical team.";
        const lowerMsg = msg.toLowerCase();
        for (const [key, context] of Object.entries(ragDatabase)) {
            if (lowerMsg.includes(key)) {
                reply = `<strong class="text-brand-navy text-[10px] uppercase tracking-widest block mb-1">[Admin Context via FAISS]</strong>${context}`;
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


// --- Aadhar Verification Modal ---
let currentVerifyUserId = null;

function openAadharModal(userId, userName) {
    currentVerifyUserId = userId;
    const modal = document.getElementById('aadharModal');
    const nameEl = document.getElementById('verifyUserName');
    const nameLabel = document.getElementById('verifyNameLabel');
    if (modal && nameEl && nameLabel) {
        nameEl.textContent = userName;
        nameLabel.textContent = userName;
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

function closeAadharModal() {
    const modal = document.getElementById('aadharModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        currentVerifyUserId = null;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const approveBtn = document.getElementById('approveKycBtn');
    const rejectBtn = document.getElementById('rejectKycBtn');
    
    if(approveBtn) {
        approveBtn.addEventListener('click', () => {
            if (currentVerifyUserId) {
                showToast('Aadhar KYC Approved successfully.', 'success');
                // Optional: Update row UI to Active
                const row = document.getElementById('user-row-' + currentVerifyUserId);
                if(row) {
                    const statusCell = row.querySelector('.status-pending');
                    if(statusCell) {
                        statusCell.classList.remove('status-pending');
                        statusCell.classList.add('status-active');
                        statusCell.parentElement.className = 'flex items-center gap-1.5 text-xs font-semibold text-green-600';
                        statusCell.parentElement.innerHTML = '<span class="w-2 h-2 rounded-full status-active inline-block"></span> Active';
                    }
                }
            }
            closeAadharModal();
        });
    }
    
    if(rejectBtn) {
        rejectBtn.addEventListener('click', () => {
            if (currentVerifyUserId) {
                showToast('Aadhar KYC Rejected.', 'error');
            }
            closeAadharModal();
        });
    }
});
