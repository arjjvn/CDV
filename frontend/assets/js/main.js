// ======================================================================
// CDVH | MAIN.JS — INDEX PAGE SCRIPTS & DEEP LEARNING MODEL CONNECTION
// ======================================================================

const KERALA_DISTRICT_PLACES = {
    "Thiruvananthapuram": [
        "Thiruvananthapuram", "Neyyattinkara", "Attingal", "Nedumangad",
        "Varkala", "Kazhakkoottam", "Kattakada", "Vizhinjam", "Pothencode",
        "Other / nearby locality"
    ],
    "Kollam": [
        "Kollam", "Punalur", "Karunagappally", "Kottarakkara", "Paravur",
        "Anchal", "Kundara", "Chathannoor", "Sasthamkotta", "Other / nearby locality"
    ],
    "Pathanamthitta": [
        "Pathanamthitta", "Thiruvalla", "Adoor", "Ranni", "Kozhencherry",
        "Pandalam", "Konni", "Mallappally", "Other / nearby locality"
    ],
    "Alappuzha": [
        "Alappuzha", "Cherthala", "Kayamkulam", "Haripad", "Mavelikkara",
        "Chengannur", "Ambalappuzha", "Kuttanad", "Aroor", "Other / nearby locality"
    ],
    "Kottayam": [
        "Kottayam", "Changanassery", "Pala", "Vaikom", "Ettumanoor",
        "Kanjirappally", "Erattupetta", "Kumarakom", "Other / nearby locality"
    ],
    "Idukki": [
        "Painavu", "Thodupuzha", "Munnar", "Adimali", "Kattappana",
        "Kumily", "Nedumkandam", "Devikulam", "Other / nearby locality"
    ],
    "Ernakulam": [
        "Kochi", "Kakkanad", "Aluva", "Angamaly", "Perumbavoor",
        "Muvattupuzha", "Kothamangalam", "Tripunithura", "Kalamassery", "Other / nearby locality"
    ],
    "Thrissur": [
        "Thrissur", "Chalakudy", "Kodungallur", "Irinjalakuda", "Guruvayur",
        "Kunnamkulam", "Wadakkanchery", "Chavakkad", "Other / nearby locality"
    ],
    "Palakkad": [
        "Palakkad", "Ottapalam", "Shoranur", "Chittur", "Mannarkkad",
        "Pattambi", "Alathur", "Cherpulassery", "Other / nearby locality"
    ],
    "Malappuram": [
        "Malappuram", "Manjeri", "Tirur", "Ponnani", "Perinthalmanna",
        "Kottakkal", "Nilambur", "Kondotty", "Other / nearby locality"
    ],
    "Kozhikode": [
        "Kozhikode", "Vadakara", "Koyilandy", "Feroke", "Ramanattukara",
        "Kunnamangalam", "Thamarassery", "Beypore", "Other / nearby locality"
    ],
    "Wayanad": [
        "Kalpetta", "Sulthan Bathery", "Mananthavady", "Vythiri", "Meppadi",
        "Pulpally", "Panamaram", "Ambalavayal", "Other / nearby locality"
    ],
    "Kannur": [
        "Kannur", "Thalassery", "Payyanur", "Taliparamba", "Mattannur",
        "Iritty", "Kuthuparamba", "Other / nearby locality"
    ],
    "Kasaragod": [
        "Kasaragod", "Kanhangad", "Nileshwaram", "Uppala", "Manjeshwar",
        "Cheruvathur", "Other / nearby locality"
    ]
};

// ----------------------------------------------------------------------
// 1. DISTRICT -> PLACE CASCADING DROPDOWN
// ----------------------------------------------------------------------

function setupDistrictPlaceDropdowns() {
    const districtSelect = document.getElementById("incidentDistrict");
    const placeSelect = document.getElementById("incidentPlace");

    if (!districtSelect || !placeSelect) return;

    districtSelect.addEventListener("change", function () {
        const selectedDistrict = this.value;
        placeSelect.innerHTML = "";

        if (!selectedDistrict || !KERALA_DISTRICT_PLACES[selectedDistrict]) {
            placeSelect.disabled = true;
            placeSelect.className = placeSelect.className.replace("bg-white", "bg-gray-100");
            placeSelect.innerHTML = `<option value="">Select district first</option>`;
            return;
        }

        placeSelect.disabled = false;
        placeSelect.className = placeSelect.className.replace("bg-gray-100", "bg-white");

        const defaultOption = document.createElement("option");
        defaultOption.value = "";
        defaultOption.textContent = "Select locality / town";
        placeSelect.appendChild(defaultOption);

        const localities = KERALA_DISTRICT_PLACES[selectedDistrict];
        localities.forEach(locality => {
            const opt = document.createElement("option");
            opt.value = locality;
            opt.textContent = locality;
            placeSelect.appendChild(opt);
        });
    });
}

// ----------------------------------------------------------------------
// 2. CONNECT DEEP LEARNING MODEL TO HERO EMERGENCY MESSAGE BOX
// ----------------------------------------------------------------------

function setupLiveRiskDetection() {
    const descInput = document.getElementById("incidentDesc");
    const riskIndicator = document.getElementById("liveRiskIndicator");
    if (!descInput || !riskIndicator) return;

    let debounceTimer = null;

    descInput.addEventListener("input", function () {
        const text = this.value.trim();
        clearTimeout(debounceTimer);

        if (text.length < 8) {
            riskIndicator.classList.add("hidden");
            return;
        }

        debounceTimer = setTimeout(async () => {
            try {
                const res = await fetch("/api/emergency/analyze", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: text })
                });

                if (!res.ok) return;

                const data = await res.json();
                const analysis = data.analysis || {};
                const urgency = (analysis.urgency || "low").toLowerCase();
                const skill = analysis.skill || "Relief";
                const disaster = analysis.disaster || "General";

                riskIndicator.classList.remove("hidden");

                if (urgency === "high") {
                    riskIndicator.className = "mt-2 p-2.5 rounded text-xs bg-red-50 text-red-800 border-2 border-red-300 flex items-center justify-between animate-fade-in";
                    riskIndicator.innerHTML = `
                        <div class="flex items-center gap-1.5 font-medium">
                            <span>🚨</span>
                            <span><strong>Critical Risk Detected:</strong> Immediate field deployment needed (${skill} · ${disaster})</span>
                        </div>
                        <span class="text-[10px] font-bold uppercase bg-red-600 text-white px-2 py-0.5 rounded tracking-wide shrink-0">
                            High Priority (${Math.round((analysis.urgency_conf || 0.99) * 100)}%)
                        </span>
                    `;
                } else if (urgency === "medium") {
                    riskIndicator.className = "mt-2 p-2.5 rounded text-xs bg-amber-50 text-amber-800 border-2 border-amber-300 flex items-center justify-between animate-fade-in";
                    riskIndicator.innerHTML = `
                        <div class="flex items-center gap-1.5 font-medium">
                            <span>⚠️</span>
                            <span><strong>Moderate Risk Detected:</strong> Support required within hours (${skill})</span>
                        </div>
                        <span class="text-[10px] font-bold uppercase bg-amber-500 text-white px-2 py-0.5 rounded tracking-wide shrink-0">
                            Medium Priority (${Math.round((analysis.urgency_conf || 0.8) * 100)}%)
                        </span>
                    `;
                } else {
                    riskIndicator.className = "mt-2 p-2.5 rounded text-xs bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center justify-between animate-fade-in";
                    riskIndicator.innerHTML = `
                        <div class="flex items-center gap-1.5 font-medium">
                            <span>🟢</span>
                            <span><strong>Low Risk Advisory:</strong> General assistance & relief inquiry</span>
                        </div>
                        <span class="text-[10px] font-bold uppercase bg-emerald-600 text-white px-2 py-0.5 rounded tracking-wide shrink-0">
                            Routine Priority
                        </span>
                    `;
                }

                // Also preview in the DL Engine demo section
                updateNlpEngineCard(text, analysis);

            } catch (err) {
                console.error("Live risk detection error:", err);
            }
        }, 500);
    });
}

function setupEmergencyReportForm() {
    const form = document.getElementById("heroEmergencyForm");
    if (!form) return;

    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        const district = document.getElementById("incidentDistrict")?.value || "";
        const place = document.getElementById("incidentPlace")?.value || "";
        const descriptionInput = document.getElementById("incidentDesc");
        const description = descriptionInput ? descriptionInput.value.trim() : "";
        const riskIndicator = document.getElementById("liveRiskIndicator");

        const alertBox = document.getElementById("heroAlertStatus");
        const alertText = document.getElementById("heroAlertText");
        const submitBtn = document.getElementById("emergencySubmitBtn");

        if (!description) {
            alert("Please provide the emergency details.");
            return;
        }

        const originalBtnContent = submitBtn ? submitBtn.innerHTML : "Send Alert";

        if (submitBtn) {
            submitBtn.innerHTML = `
                <svg class="animate-spin w-4 h-4 mr-2 inline" viewBox="0 0 24 24" fill="none">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Evaluating Risk via Deep Learning...
            `;
            submitBtn.disabled = true;
        }

        try {
            const response = await fetch("/api/emergency/report", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({
                    message: description,
                    description: description,
                    district: district,
                    place: place
                })
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || `Server responded with status ${response.status}`);
            }

            const data = await response.json();
            const analysis = data.analysis || {};

            const urgencyLabel = (analysis.urgency || "high").toUpperCase();
            const urgencyBadge = analysis.urgency === "high" ? "bg-red-600 text-white" :
                (analysis.urgency === "medium" ? "bg-amber-500 text-white" : "bg-emerald-600 text-white");

            // Hide the typing preview indicator
            if (riskIndicator) riskIndicator.classList.add("hidden");

            // Format comprehensive result badge
            if (alertBox && alertText) {
                alertBox.className = "mx-6 mb-6 p-4 bg-white border-2 border-brand-red rounded shadow-lg block animate-fade-in";
                alertText.innerHTML = `
                    <div class="space-y-3">
                        <div class="flex items-center justify-between border-b pb-2">
                            <span class="text-xs font-bold uppercase tracking-wider text-brand-navy flex items-center gap-1.5">
                                <span class="w-2 h-2 rounded-full bg-brand-red animate-ping"></span>
                                Deep Learning Risk & Urgency Analysis
                            </span>
                            <span class="text-[10px] font-bold px-2.5 py-0.5 rounded ${urgencyBadge} uppercase tracking-wider">
                                ${urgencyLabel} RISK (${Math.round((analysis.urgency_conf || 0.99) * 100)}%)
                            </span>
                        </div>

                        <div class="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                            <div class="bg-gray-50 p-2.5 rounded border border-gray-100">
                                <span class="text-[10px] text-gray-400 font-bold uppercase block mb-0.5">Disaster Type</span>
                                <strong class="text-brand-navy capitalize">${analysis.disaster || "General"} (${Math.round((analysis.disaster_conf || 0.95) * 100)}%)</strong>
                            </div>
                            <div class="bg-gray-50 p-2.5 rounded border border-gray-100">
                                <span class="text-[10px] text-gray-400 font-bold uppercase block mb-0.5">Skill Needed</span>
                                <strong class="text-brand-red">${analysis.skill || "Relief"} (${Math.round((analysis.skill_conf || 0.98) * 100)}%)</strong>
                            </div>
                            <div class="bg-gray-50 p-2.5 rounded border border-gray-100 col-span-2 sm:col-span-1">
                                <span class="text-[10px] text-gray-400 font-bold uppercase block mb-0.5">Staging Location</span>
                                <strong class="text-gray-800">${data.location || place || district || "Kerala"}</strong>
                            </div>
                        </div>

                        <div class="text-[11px] text-gray-700 bg-green-50 border border-green-200 p-2.5 rounded flex items-center gap-2">
                            <svg class="w-4 h-4 text-green-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                            </svg>
                            <span>Disaster #${data.disaster_id} registered in PostgreSQL. Task #${data.task_id} generated. <strong>${data.matched_count || 0} approved volunteers</strong> matched via ML.</span>
                        </div>
                    </div>
                `;
            }

            // Sync with Deep Learning Engine demo section on the page
            updateNlpEngineCard(description, analysis);

            // Reset description input
            if (descriptionInput) descriptionInput.value = "";

        } catch (error) {
            console.error("Emergency report failed:", error);
            if (alertBox && alertText) {
                alertBox.className = "mx-6 mb-6 p-4 bg-red-50 border border-red-200 rounded block";
                alertText.innerHTML = `
                    <div class="text-xs text-red-700">
                        <strong>Dispatch Notice:</strong> ${error.message || "Unable to reach server. Please try calling the 112 emergency hotline."}
                    </div>
                `;
            }
        } finally {
            if (submitBtn) {
                submitBtn.innerHTML = originalBtnContent;
                submitBtn.disabled = false;
            }
        }
    });
}

// ----------------------------------------------------------------------
// 3. UPDATE NLP ENGINE DEMO CARD
// ----------------------------------------------------------------------

function updateNlpEngineCard(rawText, analysis) {
    const rawEl = document.getElementById("nlpDemoInputText");
    const intentEl = document.getElementById("nlpIntentVal");
    const urgencyEl = document.getElementById("nlpUrgencyVal");
    const skillEl = document.getElementById("nlpSkillVal");
    const confEl = document.getElementById("nlpConfidenceVal");

    if (rawEl) rawEl.textContent = `"${rawText}"`;
    if (intentEl) intentEl.textContent = `${analysis.skill || "Emergency"} Request (${analysis.disaster || "General"})`;
    if (urgencyEl) {
        urgencyEl.textContent = `${(analysis.urgency || "medium").toUpperCase()} Priority`;
        urgencyEl.className = analysis.urgency === "high" ? "text-sm font-bold text-brand-red" : "text-sm font-bold text-amber-500";
    }
    if (skillEl) skillEl.textContent = analysis.skill || "General Relief";
    if (confEl) {
        const avgConf = Math.round(((analysis.skill_conf || 0.9) + (analysis.urgency_conf || 0.9) + (analysis.disaster_conf || 0.9)) / 3 * 100);
        confEl.textContent = `${avgConf}% Neural Net Conf.`;
    }
}

// ----------------------------------------------------------------------
// 4. INTERACTIVE DEEP LEARNING MODEL DEMO PILLS
// ----------------------------------------------------------------------

function setupInteractiveNlpDemo() {
    const sampleButtons = document.querySelectorAll(".nlp-sample-btn");
    sampleButtons.forEach(btn => {
        btn.addEventListener("click", async function () {
            const sampleText = this.getAttribute("data-sample") || this.textContent.trim();
            try {
                this.classList.add("opacity-50");
                const res = await fetch("/api/emergency/analyze", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: sampleText })
                });
                const data = await res.json();
                if (data.success && data.analysis) {
                    updateNlpEngineCard(sampleText, data.analysis);
                }
            } catch (err) {
                console.error("NLP demo analysis failed:", err);
            } finally {
                this.classList.remove("opacity-50");
            }
        });
    });
}

// ----------------------------------------------------------------------
// 5. INITIALIZE ON DOM LOAD
// ----------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
    setupDistrictPlaceDropdowns();
    setupEmergencyReportForm();
    setupInteractiveNlpDemo();
});
