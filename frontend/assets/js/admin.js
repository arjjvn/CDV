// =============================================
// CDVH | Admin Dashboard Operations
// =============================================

function confirmDelete(userId, userName) {
    if (confirm(`Are you sure you want to remove user "${userName}" (ID: ${userId})? This action cannot be undone.`)) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/users/${userId}/delete`;
        document.body.appendChild(form);
        form.submit();
    }
}
