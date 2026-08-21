// Initialize variables
const ui = {
    time: document.getElementById('current-time'),
    cpuFill: document.getElementById('cpu-fill'),
    cpuVal: document.getElementById('cpu-val'),
    ramFill: document.getElementById('ram-fill'),
    ramVal: document.getElementById('ram-val'),
    batFill: document.getElementById('bat-fill'),
    batVal: document.getElementById('bat-val'),
    netVal: document.getElementById('net-val'),
    log: document.getElementById('activity-log'),
    userText: document.querySelector('#user-transcript .text'),
    jarvisText: document.querySelector('#jarvis-transcript .text'),
    statusText: document.getElementById('ai-status'),
    coreRadius: document.getElementById('ai-core'),
    input: document.getElementById('manual-input'),
    btn: document.getElementById('send-btn')
};

// --- Clock Sync ---
setInterval(() => {
    const now = new Date();
    ui.time.textContent = now.toTimeString().split(' ')[0];
}, 1000);

// --- Realtime Eel Callbacks ---

eel.expose(update_system_stats);
function update_system_stats(stats) {
    ui.cpuFill.style.width = stats.cpu + '%';
    ui.cpuVal.textContent = stats.cpu + '%';

    ui.ramFill.style.width = stats.ram + '%';
    ui.ramVal.textContent = stats.ram + '%';

    ui.batFill.style.width = stats.battery + '%';
    ui.batVal.textContent = stats.battery + '%';

    ui.netVal.textContent = stats.network;
}

eel.expose(update_activity_log);
function update_activity_log(message, type="action") {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    
    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0];
    
    entry.textContent = `[${timeStr}] > ${message}`;
    
    ui.log.appendChild(entry);
    
    // Auto scroll to bottom
    if (ui.log.children.length > 50) {
        ui.log.removeChild(ui.log.firstChild);
    }
    ui.log.scrollTop = ui.log.scrollHeight;
}

eel.expose(update_voice_transcript);
function update_voice_transcript(speaker, text) {
    if (speaker.toLowerCase() === 'user') {
        ui.userText.textContent = text;
        ui.statusText.textContent = "PROCESSING...";
        ui.coreRadius.style.filter = "hue-rotate(90deg)"; // Change color temporarily
    } else {
        ui.jarvisText.textContent = text;
        ui.statusText.textContent = "AWAITING INPUT";
        ui.coreRadius.style.filter = "none";
    }
}

// --- Manual Input Handling ---

function submitQuery() {
    const text = ui.input.value.trim();
    if (text) {
        update_activity_log("Manual override triggered: " + text, "system");
        update_voice_transcript('User', text);
        ui.input.value = '';
        
        // Call Python
        eel.process_user_query(text)(function(response) {
            update_activity_log("Task complete", "system");
            update_voice_transcript('Jarvis', response);
        });
    }
}

ui.btn.addEventListener('click', submitQuery);
ui.input.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        submitQuery();
    }
});

// Log readiness
window.onload = () => {
    setTimeout(() => {
        update_activity_log("Voice interface linked.", "system");
        update_activity_log("Awaiting command.", "system");
    }, 1000);
};
