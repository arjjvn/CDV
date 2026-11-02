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

// Emergency Report Handler
document.addEventListener('DOMContentLoaded', function () {
    const reportForm = document.getElementById('reportForm');
    if (reportForm) {
        reportForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const btn = this.querySelector('button[type="submit"]');
            const original = btn ? btn.innerHTML : '';
            if (btn) {
                btn.innerHTML = 'Submitting...';
                btn.disabled = true;
            }

            setTimeout(() => {
                const status = document.getElementById('reportStatus');
                if (status) {
                    status.classList.remove('hidden');
                    status.classList.add('flex');
                }
                reportForm.reset();
                if (btn) {
                    btn.innerHTML = original;
                    btn.disabled = false;
                }
            }, 800);
        });
    }
});
