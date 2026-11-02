// frontend/assets/js/volunteer.js
//
// Profile information is rendered by FastAPI + Jinja2.
// Do not clear the HTML fields or fetch /auth/me here.
// The JWT is stored in an HTTP-only cookie, not localStorage.

document.addEventListener("DOMContentLoaded", () => {
    initLogout();
});


// --------------------------------------------------
// LOGOUT
// --------------------------------------------------

function initLogout() {
    const logoutButton = document.getElementById("logoutButton");

    if (!logoutButton) {
        return;
    }

    logoutButton.addEventListener("click", async () => {
        logoutButton.disabled = true;
        logoutButton.textContent = "Signing out...";

        try {
            const response = await fetch("/auth/logout", {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Accept": "application/json"
                }
            });

            if (!response.ok) {
                throw new Error("Unable to log out.");
            }

            // Remove legacy data from the previous login system.
            localStorage.removeItem("cdvh_access_token");
            localStorage.removeItem("cdvh_user");
            localStorage.removeItem("cdvh_user_role");

            // The backend has deleted the authentication cookie.
            window.location.replace("/pages/login.html");

        } catch (error) {
            console.error("Logout failed:", error);

            logoutButton.disabled = false;
            logoutButton.textContent = "Sign out";

            alert(
                "Logout failed. Check your connection and try again."
            );
        }
    });
}