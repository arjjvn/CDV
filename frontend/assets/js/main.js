 document.getElementById('heroEmergencyForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const location = document.getElementById('incidentLoc').value;
            const text = document.getElementById('incidentDesc').value.toLowerCase();
            const alertBox = document.getElementById('heroAlertStatus');
            const alertText = document.getElementById('heroAlertText');
            
            const btn = this.querySelector('button');
            const originalBtnText = btn.innerHTML;
            
            // Loading state
            btn.innerHTML = `<svg class="animate-spin w-4 h-4 mr-2" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Processing NLP...`;
            btn.disabled = true;

            // Simulate server processing time for NLP Intent Detection
            setTimeout(() => {
                let intent = "General Request";
                
                if(text.includes('injur') || text.includes('medic') || text.includes('bleed')) {
                    intent = "Medical Emergency";
                } else if(text.includes('food') || text.includes('water')) {
                    intent = "Relief Supplies";
                } else if(text.includes('trapped') || text.includes('rescue')) {
                    intent = "Search & Rescue";
                }

                alertBox.classList.remove('hidden');
                alertText.innerHTML = `
                    <span class="block mb-1 text-gray-800"><strong class="text-brand-navy">NLP Result:</strong> Intent classified as <strong>${intent}</strong> at ${location}.</span>
                    <span class="block">Pinged FastAPI backend. Routing to Scikit-learn matching module...</span>
                `;
                
                // Reset button state
                btn.innerHTML = originalBtnText;
                btn.disabled = false;
                
                // Clear form fields
                document.getElementById('incidentLoc').value = '';
                document.getElementById('incidentDesc').value = '';
                
            }, 1500);
        });

        // --- RAG Chatbot Logic ---
        let isChatOpen = false;
        
        function toggleChat() {
            const window = document.getElementById('chatWindow');
            isChatOpen = !isChatOpen;
            
            if(isChatOpen) {
                window.classList.remove('hidden');
                window.classList.add('flex');
            } else {
                window.classList.add('hidden');
                window.classList.remove('flex');
            }
        }

        // Simulated Vector Database for RAG (Retrieval-Augmented Generation)
        const ragDatabase = {
            "flood": "In a flood scenario, move to higher ground immediately. Do not walk or drive through floodwaters. Disconnect electrical appliances if safe to do so.",
            "fire": "If there is a fire, evacuate immediately. Stay low to the ground to avoid inhaling smoke. Call emergency services and do not re-enter the building.",
            "medical": "Ensure the scene is safe first. If someone is bleeding, apply direct firm pressure. If unconscious but breathing normally, place in the recovery position.",
            "volunteer": "As a volunteer, always report to your designated coordinator first. Do not self-deploy to danger zones. Keep your ID and protective gear on at all times."
        };

        // Chat Form Submission
        document.getElementById('chatForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const input = document.getElementById('chatInput');
            const msg = input.value.trim();
            if(!msg) return;

            // Add user message to UI
            addChatMessage(msg, 'user');
            input.value = '';

            // Simulate RAG Retrieval & LLM Generation delay
            setTimeout(() => {
                let reply = "Searching vector database... Based on general guidelines, please stay calm and await instructions from local authorities.";
                
                const lowerMsg = msg.toLowerCase();
                for (const [key, context] of Object.entries(ragDatabase)) {
                    if (lowerMsg.includes(key)) {
                        reply = `<strong class="text-brand-navy text-[10px] uppercase tracking-widest block mb-1">[Context Retrieved via FAISS]</strong>${context}`;
                        break;
                    }
                }
                
                // Add bot message to UI
                addChatMessage(reply, 'bot');
            }, 800);
        });

        // Helper function to append messages
        function addChatMessage(text, sender) {
            const chatArea = document.getElementById('chatMessages');
            const div = document.createElement('div');
            
            if (sender === 'user') {
                div.className = "bg-brand-navy text-white p-3 rounded-lg rounded-tr-none text-sm self-end max-w-[85%] shadow-sm animate-slide-up";
            } else {
                div.className = "bg-white p-3 rounded-lg rounded-tl-none border border-gray-200 text-sm text-gray-700 self-start max-w-[85%] shadow-sm animate-slide-up";
            }
            
            div.innerHTML = text;
            chatArea.appendChild(div);
            
            // Auto-scroll to bottom
            chatArea.scrollTop = chatArea.scrollHeight;
        }