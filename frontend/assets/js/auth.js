let currentMode = "login";
const API_URL = "/auth";

function getOptionalValue(id) {
    const element = document.getElementById(id);

    if (!element || !element.value.trim()) {
        return null;
    }

    return element.value.trim();
}

function showAuthToast(title, message) {
    const toast = document.getElementById("toast");

    if (!toast) {
        alert(`${title}\n${message}`);
        return;
    }

    const toastTitle = document.getElementById("toastTitle");
    const toastMessage = document.getElementById("toastMessage");

    if (toastTitle) {
        toastTitle.textContent = title;
    }

    if (toastMessage) {
        toastMessage.textContent = message;
    }

    toast.classList.remove("hidden");
    toast.classList.add("flex", "toast-enter");

    if (showAuthToast.timeoutId) {
        clearTimeout(showAuthToast.timeoutId);
    }

    showAuthToast.timeoutId = setTimeout(() => {
        toast.classList.add("hidden");
        toast.classList.remove("flex", "toast-enter");
    }, 5000);
}


// --------------------------------------------------
// SWITCH BETWEEN LOGIN AND REGISTRATION
// --------------------------------------------------

function switchMode(mode) {
    currentMode = mode === "register" ? "register" : "login";

    const tabLogin = document.getElementById("tabLogin");
    const tabRegister = document.getElementById("tabRegister");
    const title = document.getElementById("formTitle");
    const subtitle = document.getElementById("formSubtitle");
    const registerFields = document.getElementById("registerFields");
    const registerUtils = document.getElementById("RegisterUtils");
    const buttonLabel = document.querySelector("#submitBtn span");

    const adminRadio = document.getElementById("roleAdmin");
    const adminLabel = document.querySelector('label[for="roleAdmin"]');
    const volunteerRadio = document.getElementById("roleVolunteer");

    if (
        !tabLogin ||
        !tabRegister ||
        !title ||
        !subtitle ||
        !registerFields ||
        !registerUtils
    ) {
        return;
    }

    if (currentMode === "login") {
        tabLogin.className =
            "flex-1 pb-3 text-sm font-semibold border-b-2 border-brand-navy text-brand-navy transition";

        tabRegister.className =
            "flex-1 pb-3 text-sm font-medium border-b-2 border-transparent text-gray-400 hover:text-gray-600 transition";

        title.textContent = "Welcome back";

        subtitle.textContent =
            "Enter your credentials to access the CDVH dashboard.";

        if (buttonLabel) {
            buttonLabel.textContent = "Sign In";
        }

        registerFields.classList.add("hidden");
        registerUtils.classList.remove("hidden");

        if (adminRadio) {
            adminRadio.disabled = false;
        }

        if (adminLabel) {
            adminLabel.style.display = "";
        }

    } else {
        tabRegister.className =
            "flex-1 pb-3 text-sm font-semibold border-b-2 border-brand-navy text-brand-navy transition";

        tabLogin.className =
            "flex-1 pb-3 text-sm font-medium border-b-2 border-transparent text-gray-400 hover:text-gray-600 transition";

        title.textContent = "Create an Account";

        subtitle.textContent =
            "Join the CDVH community and support disaster response.";

        if (buttonLabel) {
            buttonLabel.textContent = "Register Profile";
        }

        registerFields.classList.remove("hidden");
        registerUtils.classList.add("hidden");

        // Public registration is not allowed for admin accounts.
        if (adminRadio) {
            adminRadio.disabled = true;

            if (adminRadio.checked && volunteerRadio) {
                volunteerRadio.checked = true;
            }
        }

        if (adminLabel) {
            adminLabel.style.display = "none";
        }
    }

    const selectedRole =
        document.querySelector('input[name="role"]:checked')?.value
        || "volunteer";

    updateRoleFields(selectedRole);
}


// --------------------------------------------------
// KERALA DISTRICTS AND PLACES
// --------------------------------------------------

const keralaPlacesByDistrict = {
    "Thiruvananthapuram": [
        "Thiruvananthapuram City",
        "Neyyattinkara",
        "Nedumangad",
        "Attingal",
        "Varkala",
        "Kazhakkoottam",
        "Vizhinjam",
        "Kovalam",
        "Kattakada",
        "Balaramapuram",
        "Poovar",
        "Parassala",
        "Venjaramoodu",
        "Kilimanoor",
        "Other / nearby locality"
    ],

    "Kollam": [
        "Kollam City",
        "Punalur",
        "Karunagappally",
        "Kottarakkara",
        "Paravur",
        "Anchal",
        "Kundara",
        "Chathannoor",
        "Sasthamkotta",
        "Oachira",
        "Pathanapuram",
        "Other / nearby locality"
    ],

    "Pathanamthitta": [
        "Pathanamthitta",
        "Thiruvalla",
        "Adoor",
        "Ranni",
        "Kozhencherry",
        "Pandalam",
        "Konni",
        "Mallappally",
        "Aranmula",
        "Perunad",
        "Sabarimala",
        "Other / nearby locality"
    ],

    "Alappuzha": [
        "Alappuzha",
        "Cherthala",
        "Kayamkulam",
        "Haripad",
        "Mavelikkara",
        "Chengannur",
        "Ambalappuzha",
        "Kuttanad",
        "Thanneermukkom",
        "Aroor",
        "Mannar",
        "Edathua",
        "Other / nearby locality"
    ],

    "Kottayam": [
        "Kottayam",
        "Changanassery",
        "Pala",
        "Vaikom",
        "Ettumanoor",
        "Kanjirappally",
        "Erattupetta",
        "Mundakayam",
        "Ponkunnam",
        "Kuravilangad",
        "Kumarakom",
        "Uzhavoor",
        "Other / nearby locality"
    ],

    "Idukki": [
        "Painavu",
        "Thodupuzha",
        "Munnar",
        "Adimali",
        "Kattappana",
        "Kumily",
        "Nedumkandam",
        "Peermade",
        "Vandiperiyar",
        "Marayoor",
        "Rajakkad",
        "Vazhathope",
        "Devikulam",
        "Other / nearby locality"
    ],

    "Ernakulam": [
        "Kochi",
        "Kakkanad",
        "Aluva",
        "Angamaly",
        "Perumbavoor",
        "Muvattupuzha",
        "Kothamangalam",
        "North Paravur",
        "Thrippunithura",
        "Kalamassery",
        "Edappally",
        "Fort Kochi",
        "Mattancherry",
        "Vypin",
        "Eloor",
        "Piravom",
        "Other / nearby locality"
    ],

    "Thrissur": [
        "Thrissur",
        "Chalakudy",
        "Kodungallur",
        "Irinjalakuda",
        "Guruvayur",
        "Kunnamkulam",
        "Wadakkanchery",
        "Chavakkad",
        "Chelakkara",
        "Anthikad",
        "Ollur",
        "Mala",
        "Other / nearby locality"
    ],

    "Palakkad": [
        "Palakkad",
        "Ottapalam",
        "Shoranur",
        "Chittur",
        "Mannarkkad",
        "Pattambi",
        "Alathur",
        "Cherpulassery",
        "Nenmara",
        "Kollengode",
        "Kozhinjampara",
        "Vadakkencherry",
        "Other / nearby locality"
    ],

    "Malappuram": [
        "Malappuram",
        "Manjeri",
        "Tirur",
        "Ponnani",
        "Perinthalmanna",
        "Kottakkal",
        "Nilambur",
        "Kondotty",
        "Parappanangadi",
        "Tanur",
        "Tirurangadi",
        "Areekode",
        "Wandoor",
        "Edappal",
        "Other / nearby locality"
    ],

    "Kozhikode": [
        "Kozhikode",
        "Vadakara",
        "Koyilandy",
        "Feroke",
        "Ramanattukara",
        "Kunnamangalam",
        "Mukkam",
        "Thamarassery",
        "Balussery",
        "Perambra",
        "Beypore",
        "Elathur",
        "Koduvally",
        "Other / nearby locality"
    ],

    "Wayanad": [
        "Kalpetta",
        "Sulthan Bathery",
        "Mananthavady",
        "Vythiri",
        "Meppadi",
        "Pulpally",
        "Panamaram",
        "Ambalavayal",
        "Thirunelly",
        "Pozhuthana",
        "Muttil",
        "Padinjarathara",
        "Other / nearby locality"
    ],

    "Kannur": [
        "Kannur",
        "Thalassery",
        "Payyannur",
        "Taliparamba",
        "Mattannur",
        "Iritty",
        "Koothuparamba",
        "Sreekandapuram",
        "Panoor",
        "Azhikode",
        "Dharmadam",
        "Other / nearby locality"
    ],

    "Kasaragod": [
        "Kasaragod",
        "Kanhangad",
        "Nileshwaram",
        "Uppala",
        "Manjeshwar",
        "Cheruvathur",
        "Trikaripur",
        "Bekal",
        "Periya",
        "Udma",
        "Mulleria",
        "Badiadka",
        "Other / nearby locality"
    ]
};


// --------------------------------------------------
// DISTRICT AND PLACE DROPDOWN
// --------------------------------------------------

function setupDistrictDropdown() {
    const districtSelect = document.getElementById("regDistrict");
    const placeSelect = document.getElementById("regPlace");

    if (!districtSelect || !placeSelect) {
        return;
    }

    function populatePlaces(district) {
        placeSelect.replaceChildren();

        if (!district) {
            placeSelect.add(
                new Option("Select a district first", "")
            );

            placeSelect.disabled = true;
            placeSelect.classList.add("bg-gray-100");
            placeSelect.classList.remove("bg-white");

            return;
        }

        placeSelect.add(
            new Option("Select place / town", "")
        );

        (keralaPlacesByDistrict[district] || []).forEach(place => {
            placeSelect.add(new Option(place, place));
        });

        placeSelect.disabled = false;
        placeSelect.classList.remove("bg-gray-100");
        placeSelect.classList.add("bg-white");
    }

    districtSelect.addEventListener("change", function () {
        populatePlaces(this.value);
    });

    // Populate places if a district is already selected.
    if (districtSelect.value) {
        populatePlaces(districtSelect.value);
    } else {
        placeSelect.replaceChildren(
            new Option("Select a district first", "")
        );

        placeSelect.disabled = true;
    }
}


// --------------------------------------------------
// SHOW FIELDS BASED ON ROLE
// --------------------------------------------------

function updateRoleFields(role) {
    const volunteerFields = document.getElementById("volunteerFields");
    const coordinatorFields = document.getElementById("coordinatorFields");
    const adminFields = document.getElementById("adminFields");

    volunteerFields?.classList.add("hidden");
    coordinatorFields?.classList.add("hidden");
    adminFields?.classList.add("hidden");

    if (role === "volunteer") {
        volunteerFields?.classList.remove("hidden");

    } else if (role === "coordinator") {
        coordinatorFields?.classList.remove("hidden");

    } else if (role === "admin") {
        adminFields?.classList.remove("hidden");
    }
}


// --------------------------------------------------
// SHOW OR HIDE PASSWORD
// --------------------------------------------------

function togglePassword() {
    const input = document.getElementById("password");
    const icon = document.getElementById("eyeIcon");

    if (!input || !icon) {
        return;
    }

    if (input.type === "password") {
        input.type = "text";
    } else {
        input.type = "password";
    }
}


// --------------------------------------------------
// REGISTRATION AND LOGIN
// --------------------------------------------------

async function handleAuth(event) {
    event.preventDefault();

    const button = document.getElementById("submitBtn");

    if (!button) {
        showAuthToast(
            "Error",
            "The authentication button could not be found."
        );
        return;
    }

    const originalContent = button.innerHTML;

    const role =
        document.querySelector('input[name="role"]:checked')?.value
        || "volunteer";

    const emailElement = document.getElementById("email");
    const passwordElement = document.getElementById("password");

    if (!emailElement || !passwordElement) {
        showAuthToast(
            "Error",
            "The email or password field could not be found."
        );
        return;
    }

    const email = emailElement.value.trim().toLowerCase();
    const password = passwordElement.value;

    if (!email || !password) {
        showAuthToast(
            "Missing Details",
            "Enter your email and password."
        );
        return;
    }

    let endpoint;
    let payload;

    // ----------------------------------------------
    // REGISTRATION
    // ----------------------------------------------

    if (currentMode === "register") {
        if (role === "admin") {
            showAuthToast(
                "Registration Not Allowed",
                "Admin accounts must be created by an authorized administrator."
            );
            return;
        }

        const firstName = getOptionalValue("firstName");
        const lastName = getOptionalValue("lastName");

        if (!firstName || !lastName) {
            showAuthToast(
                "Missing Details",
                "Please enter your first name and last name."
            );
            return;
        }

        endpoint = `${API_URL}/register`;

        payload = {
            email: email,
            password: password,
            role: role,

            first_name: firstName,
            last_name: lastName,

            phone: getOptionalValue("regPhone"),
            district: getOptionalValue("regDistrict"),
            place: getOptionalValue("regPlace"),
            address: getOptionalValue("regAddress"),
            pincode: getOptionalValue("regPincode")
        };

        if (role === "volunteer") {
            const years = getOptionalValue("yoe");

            payload.date_of_birth = getOptionalValue("regDob");
            payload.gender = getOptionalValue("regGender");
            payload.blood_group = getOptionalValue("regBloodGroup");

            payload.skill1 = getOptionalValue("skill1");
            payload.skill2 = getOptionalValue("skill2");
            payload.skill3 = getOptionalValue("skill3");

            payload.years_experience =
                years === null ? null : Number(years);

            payload.previous_experience = getOptionalValue("prevExp");
            payload.available_from = getOptionalValue("availableFrom");
            payload.available_to = getOptionalValue("availableTo");
            payload.languages = getOptionalValue("langs");
        }

        if (role === "coordinator") {
            payload.organization = getOptionalValue("org");
            payload.region = getOptionalValue("region");
        }

    } else {
        // ------------------------------------------
        // LOGIN
        // ------------------------------------------

        endpoint = `${API_URL}/login`;

        payload = {
            email: email,
            password: password,
            role: role
        };
    }

    button.disabled = true;
    button.innerHTML = "<span>Connecting...</span>";

    try {
        const response = await fetch(endpoint, {
            method: "POST",

            // Required for browser cookie authentication.
            credentials: "same-origin",

            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },

            body: JSON.stringify(payload)
        });

        const result = await response.json().catch(() => ({}));

        if (!response.ok) {
            const detail = result.detail;

            const message = Array.isArray(detail)
                ? detail
                    .map(item => item.msg || "Invalid field")
                    .join("; ")
                : detail || "The request failed. Please try again.";

            throw new Error(message);
        }

        // ------------------------------------------
        // REGISTRATION SUCCESS
        // ------------------------------------------

        if (currentMode === "register") {
            showAuthToast(
                "Registration Complete",
                result.message || "Your registration was submitted."
            );

            passwordElement.value = "";

            switchMode("login");

            return;
        }

        // ------------------------------------------
        // LOGIN SUCCESS
        // ------------------------------------------

        if (!result.access_token || !result.user) {
            throw new Error(
                "The server returned incomplete account details."
            );
        }

        localStorage.setItem(
            "cdvh_access_token",
            result.access_token
        );

        localStorage.setItem(
            "cdvh_user_role",
            result.user.role
        );

        localStorage.setItem(
            "cdvh_user",
            JSON.stringify(result.user)
        );

        // These are FastAPI dashboard routes that render
        // the Jinja2 templates on the backend.
        const dashboards = {
            volunteer: "/volunteers/dashboard",
            coordinator: "/coordinator/dashboard",
            admin: "/admin/dashboard"
        };

        const dashboardUrl = dashboards[result.user.role];

        if (!dashboardUrl) {
            throw new Error(
                "No dashboard is configured for this account role."
            );
        }

        showAuthToast(
            "Login Successful",
            "Redirecting to your dashboard..."
        );

        setTimeout(() => {
            window.location.replace(dashboardUrl);
        }, 900);

    } catch (error) {
        console.error("Authentication error:", error);

        showAuthToast(
            "Authentication Failed",
            error.message || "Unable to connect to the server."
        );

    } finally {
        button.disabled = false;
        button.innerHTML = originalContent;

        const label = button.querySelector("span");

        if (label) {
            label.textContent =
                currentMode === "login"
                    ? "Sign In"
                    : "Register Profile";
        }
    }
}


// --------------------------------------------------
// INITIAL LOGIN OR REGISTRATION MODE
// --------------------------------------------------

function getInitialMode() {
    const params = new URLSearchParams(window.location.search);

    const mode = (
        params.get("mode") ||
        params.get("tab") ||
        ""
    ).toLowerCase();

    const hash = window.location.hash.toLowerCase();

    return (
        mode === "register" ||
        hash.includes("register")
    ) ? "register" : "login";
}


// --------------------------------------------------
// PAGE INITIALIZATION
// --------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
    setupDistrictDropdown();

    document
        .querySelectorAll('input[name="role"]')
        .forEach(radio => {
            radio.addEventListener("change", event => {
                updateRoleFields(event.target.value);
            });
        });

    switchMode(getInitialMode());
});


// --------------------------------------------------
// HANDLE LOGIN / REGISTER URL HASHES
// --------------------------------------------------

window.addEventListener("hashchange", () => {
    const hash = window.location.hash.toLowerCase();

    if (hash.includes("register")) {
        switchMode("register");
    } else if (hash.includes("login")) {
        switchMode("login");
    }
});