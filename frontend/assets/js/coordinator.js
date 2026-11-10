// =============================================
// CDVH | Coordinator Dashboard Operations
// =============================================

function openAssignModal(taskId, taskTitle) {
    const modal = document.getElementById('assignModal');
    const taskLabel = document.getElementById('assignTaskLabel');
    const taskIdInput = document.getElementById('assignTaskId');
    if (modal) {
        if (taskLabel) taskLabel.textContent = taskTitle || `Task #${taskId}`;
        if (taskIdInput) taskIdInput.value = taskId;
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

function openNewTaskModal() {
    const modal = document.getElementById('newTaskModal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

function closeNewTaskModal() {
    const modal = document.getElementById('newTaskModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

// ----------------------------------------------------------------------
// ML VOLUNTEER MATCHING FOR TASKS
// ----------------------------------------------------------------------

async function loadVolunteerMatches(taskId, topN = 5) {
    const btn = document.getElementById(`match-button-${taskId}`);
    const container = document.getElementById(`matches-${taskId}`);
    if (!container) return;

    const originalBtnText = btn ? btn.innerHTML : "Find ML Matches";

    if (btn) {
        btn.innerHTML = `<svg class="animate-spin w-3.5 h-3.5 mr-1 inline" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Matching...`;
        btn.disabled = true;
    }

    try {
        const response = await fetch(`/coordinator/tasks/${taskId}/matches?top_n=${topN}`);
        if (!response.ok) {
            throw new Error(`Match engine status: ${response.status}`);
        }

        const data = await response.json();
        const matches = data.matches || [];

        container.classList.remove('hidden');

        if (matches.length === 0) {
            container.innerHTML = `
                <div class="p-3 bg-amber-50 border border-amber-200 text-amber-800 rounded text-xs">
                    ℹ️ No eligible volunteers found matching the required skills and availability window.
                </div>
            `;
            return;
        }

        let html = `
            <div class="p-3 bg-gray-50 border border-gray-200 rounded space-y-2">
                <div class="flex items-center justify-between text-xs font-bold text-brand-navy border-b pb-1.5">
                    <span class="flex items-center gap-1">
                        <svg class="w-3.5 h-3.5 text-brand-red" fill="currentColor" viewBox="0 0 20 20"><path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z"/></svg>
                        Scikit-Learn ML Candidate Recommendations
                    </span>
                    <span class="text-green-700 bg-green-100 px-2 py-0.5 rounded text-[10px] uppercase">${matches.length} Recommended</span>
                </div>
                <div class="space-y-2 pt-1">
        `;

        matches.forEach(m => {
            html += `
                <div class="flex flex-col sm:flex-row sm:items-center justify-between bg-white p-2.5 rounded border border-gray-200 gap-2">
                    <div class="text-xs">
                        <span class="font-bold text-brand-navy block">${m.name}</span>
                        <span class="text-gray-500 text-[11px]">${m.city || 'Kerala'} · ${m.experience || 0} yrs exp · Skills: ${(m.matched_skills || []).join(', ') || m.skill || 'Relief'}</span>
                    </div>
                    <div class="flex items-center gap-2 self-end sm:self-auto">
                        <span class="bg-blue-100 text-brand-blue font-bold px-2 py-0.5 rounded text-[11px] whitespace-nowrap">
                            ${m.match_score}% Match
                        </span>
                        <form action="/coordinator/tasks/assign" method="post" class="inline m-0">
                            <input type="hidden" name="task_id" value="${taskId}">
                            <input type="hidden" name="volunteer_id" value="${m.id}">
                            <input type="hidden" name="match_score" value="${m.match_score}">
                            <button type="submit" class="btn-ripple bg-brand-navy hover:bg-[#152e59] text-white px-3 py-1.5 rounded font-bold text-[11px] uppercase tracking-wider transition">
                                Deploy
                            </button>
                        </form>
                    </div>
                </div>
            `;
        });

        html += `
                </div>
            </div>
        `;

        container.innerHTML = html;

    } catch (err) {
        console.error("Failed to load volunteer matches:", err);
        container.classList.remove('hidden');
        container.innerHTML = `
            <div class="p-2.5 bg-red-50 border border-red-200 text-red-700 rounded text-xs">
                ⚠️ ML matching engine temporarily unavailable: ${err.message}
            </div>
        `;
    } finally {
        if (btn) {
            btn.innerHTML = originalBtnText;
            btn.disabled = false;
        }
    }
}
