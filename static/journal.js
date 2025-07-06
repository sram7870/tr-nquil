// journal.js

// === GLOBAL STATE ===
let quill;
let currentDate = null;
let currentEntry = null;
let goals = [];
let moods = ["happy","calm","neutral","sad","anxious","angry"];
let habits = ["meditation","exercise","journal","mindfulness"];

// DOM Elements
const dateInput = document.getElementById("currentDate");
const loadEntryBtn = document.getElementById("loadEntryBtn");
const saveBtn = document.getElementById("saveBtn");
const clearBtn = document.getElementById("clearBtn");
const recordBtn = document.getElementById("recordVoiceBtn");

const moodSelector = document.getElementById("moodSelector");
const tagsInput = document.getElementById("tags");
const habitTracker = document.getElementById("habitTracker");

const newGoalInput = document.getElementById("newGoalInput");
const addGoalBtn = document.getElementById("addGoalBtn");
const goalsList = document.getElementById("goalsList");

const searchInput = document.getElementById("search");
const searchBtn = document.getElementById("searchBtn");
const showAllBtn = document.getElementById("showAllBtn");
const searchResults = document.getElementById("searchResults");

const visibilitySelect = document.getElementById("journalVisibility");
const shareControls = document.getElementById("shareControls");
const shareWithInput = document.getElementById("shareWith");

const sentimentBtn = document.getElementById("sentimentBtn");
const summaryBtn = document.getElementById("summaryBtn");
const moodTrendBtn = document.getElementById("moodTrendBtn");
const aiOutput = document.getElementById("aiOutput");

// === INITIALIZATION ===

// Init Quill editor
quill = new Quill("#editor", {
    theme: "snow",
    placeholder: "Write your journal entry here..."
});

// Set default date to today
const todayISO = new Date().toISOString().slice(0, 10);
dateInput.value = todayISO;
currentDate = todayISO;
saveBtn.disabled = true;

// --- UTILITIES ---

// Format Date string YYYY-MM-DD to readable e.g. June 21, 2025
function formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString(undefined, {
        year: "numeric",
        month: "long",
        day: "numeric"
    });
}

// Show message in AI output area
function showAIOutput(text) {
    aiOutput.textContent = text;
}

// Disable or enable save button depending on state
function setSaveBtnState(enabled) {
    saveBtn.disabled = !enabled;
}

// Clear form fields and state
function clearForm() {
    quill.setText("");
    tagsInput.value = "";
    // Clear mood selection
    document.querySelectorAll(".mood-btn.selected").forEach(btn => btn.classList.remove("selected"));
    // Clear habits
    habitTracker.querySelectorAll("input[type=checkbox]").forEach(cb => cb.checked = false);
    // Clear goals list UI
    goals = [];
    renderGoals();
    currentEntry = null;
    setSaveBtnState(false);
    aiOutput.textContent = "";
}

// Render goals list
function renderGoals() {
    goalsList.innerHTML = "";
    goals.forEach((goal, idx) => {
        const li = document.createElement("li");
        li.className = "flex items-center justify-between gap-3 p-2 rounded border border-calmGray hover:shadow";

        const label = document.createElement("label");
        label.className = "flex items-center gap-2 cursor-pointer flex-grow";

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = goal.completed || false;
        checkbox.addEventListener("change", () => {
            goals[idx].completed = checkbox.checked;
            saveBtn.disabled = false;
        });

        const span = document.createElement("span");
        span.textContent = goal.text;

        label.appendChild(checkbox);
        label.appendChild(span);

        const delBtn = document.createElement("button");
        delBtn.textContent = "✕";
        delBtn.title = "Delete Goal";
        delBtn.className = "text-primaryGreen-dark hover:text-primaryGreen cursor-pointer font-bold text-xl";
        delBtn.addEventListener("click", () => {
            goals.splice(idx, 1);
            renderGoals();
            saveBtn.disabled = false;
        });

        li.appendChild(label);
        li.appendChild(delBtn);

        goalsList.appendChild(li);
    });
}

// Set mood selection UI
function setMood(mood) {
    document.querySelectorAll(".mood-btn").forEach(btn => {
        if (btn.dataset.mood === mood) {
            btn.classList.add("selected");
        } else {
            btn.classList.remove("selected");
        }
    });
}

// Get currently selected mood or null
function getSelectedMood() {
    const btn = document.querySelector(".mood-btn.selected");
    return btn ? btn.dataset.mood : null;
}

// Set habit checkboxes
function setHabits(habitStates) {
    habitTracker.querySelectorAll("input[type=checkbox]").forEach(cb => {
        cb.checked = habitStates[cb.dataset.habit] || false;
    });
}

// Get habit states from checkboxes as object
function getHabits() {
    const states = {};
    habitTracker.querySelectorAll("input[type=checkbox]").forEach(cb => {
        states[cb.dataset.habit] = cb.checked;
    });
    return states;
}

// Enable save button when content changes
function markDirty() {
    setSaveBtnState(true);
}

// --- API Helpers ---

async function fetchEntry(date) {
    try {
        const res = await fetch(`/api/journal/${date}`);
        if (res.status === 404) return null; // no entry for date
        if (!res.ok) throw new Error("Failed to fetch entry");
        return await res.json();
    } catch (err) {
        console.error(err);
        alert("Error fetching journal entry");
        return null;
    }
}



async function saveEntry(data) {
    try {
        const res = await fetch(`/api/journal/${data.date}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error("Failed to save entry");
        return await res.json();
    } catch (err) {
        console.error(err);
        alert("Error saving journal entry");
        return null;
    }
}

async function fetchSearch(query) {
    try {
        const res = await fetch(`/api/journal/search?q=${encodeURIComponent(query)}`);
        if (!res.ok) throw new Error("Failed to search entries");
        return await res.json();
    } catch (err) {
        console.error(err);
        alert("Error searching entries");
        return [];
    }
}

async function fetchAllEntries() {
    try {
        const res = await fetch(`/api/journal/all`);
        if (!res.ok) throw new Error("Failed to fetch all entries");
        return await res.json();
    } catch (err) {
        console.error(err);
        alert("Error fetching all entries");
        return [];
    }
}

async function analyzeSentiment(text) {
    try {
        const res = await fetch(`/api/ai/sentiment`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });
        if (!res.ok) throw new Error("Sentiment analysis failed");
        const data = await res.json();
        return data.sentiment;
    } catch (err) {
        console.error(err);
        alert("Error during sentiment analysis");
        return "Unknown";
    }
}

async function generateSummary(text) {
    try {
        const res = await fetch(`/api/ai/summary`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });
        if (!res.ok) throw new Error("Summary generation failed");
        const data = await res.json();
        return data.summary;
    } catch (err) {
        console.error(err);
        alert("Error during summary generation");
        return "";
    }
}

async function fetchMoodTrend(days=7) {
    try {
        const res = await fetch(`/api/analytics/moodtrend?days=${days}`);
        if (!res.ok) throw new Error("Mood trend fetch failed");
        return await res.json();
    } catch (err) {
        console.error(err);
        alert("Error fetching mood trends");
        return null;
    }
}

// --- RENDER SEARCH RESULTS ---
function renderSearchResults(entries) {
    searchResults.innerHTML = "";
    if (!entries.length) {
        searchResults.textContent = "No entries found.";
        return;
    }

    entries.forEach(entry => {
        const li = document.createElement("li");
        li.className = "border border-calmGray rounded p-3 bg-offwhite cursor-pointer hover:shadow";
        li.title = formatDate(entry.date);

        const dateStr = formatDate(entry.date);
        const snippet = (entry.content || "").substring(0, 120).replace(/\n/g, " ") + (entry.content.length > 120 ? "..." : "");

        li.innerHTML = `<strong>${dateStr}</strong> - Mood: ${entry.mood || "N/A"}<br>${snippet}`;

        li.addEventListener("click", () => {
            // Load this entry into the editor
            loadEntryBtn.disabled = false;
            dateInput.value = entry.date;
            currentDate = entry.date;
            loadEntry(entry.date);
            // Scroll up
            window.scrollTo({top:0, behavior:"smooth"});
        });

        searchResults.appendChild(li);
    });
}

// --- LOAD ENTRY INTO FORM ---
async function loadEntry(date) {
    const entry = await fetchEntry(date);
    if (!entry) {
        // New empty entry for date
        quill.setText("");
        tagsInput.value = "";
        setMood(null);
        setHabits({});
        goals = [];
        renderGoals();
        currentEntry = null;
        currentDate = date;
        setSaveBtnState(false);
        aiOutput.textContent = "";
        return;
    }
    currentEntry = entry;
    currentDate = date;

    // Load content to editor
    if (entry.content) quill.setContents(quill.clipboard.convert(entry.content));
    else quill.setText("");

    tagsInput.value = (entry.tags || []).join(", ");

    setMood(entry.mood || null);
    setHabits(entry.habits || {});

    goals = entry.goals || [];
    renderGoals();

    setSaveBtnState(false);
    aiOutput.textContent = "";
}

// --- SAVE CURRENT ENTRY ---
async function saveCurrentEntry() {
    if (!currentDate) {
        alert("Please select a date");
        return;
    }

    const contentHtml = quill.root.innerHTML;
    const contentText = quill.getText().trim();

    if (!contentText) {
        if (!confirm("Your journal entry is empty. Save anyway?")) {
            return;
        }
    }

    const entryData = {
        date: currentDate,
        content: contentHtml,
        mood: getSelectedMood(),
        tags: tagsInput.value
            .split(",")
            .map(t => t.trim())
            .filter(t => t.length > 0),
        habits: getHabits(),
        goals: goals
    };

    const saved = await saveEntry(entryData);
    if (saved) {
        currentEntry = entryData;
        setSaveBtnState(false);
        alert("Journal entry saved successfully.");
    }
}



// --- ADD NEW GOAL ---
function addGoal() {
    const text = newGoalInput.value.trim();
    if (!text) return;
    goals.push({ text, completed: false });
    renderGoals();
    newGoalInput.value = "";
    saveBtn.disabled = false;
}

// --- SEARCH ENTRIES ---
async function searchEntries() {
    const query = searchInput.value.trim();
    if (!query) {
        alert("Please enter a search term.");
        return;
    }
    const results = await fetchSearch(query);
    renderSearchResults(results);
}

// --- SHOW ALL ENTRIES ---
async function showAllEntries() {
    const results = await fetchAllEntries();
    renderSearchResults(results);
}

// --- AI TOOL HANDLERS ---
async function handleSentiment() {
    if (!currentEntry || !currentEntry.content) {
        alert("Load or create a journal entry first.");
        return;
    }
    showAIOutput("Analyzing sentiment...");
    const sentiment = await analyzeSentiment(currentEntry.content);
    showAIOutput(`Sentiment: ${sentiment}`);
}

async function handleSummary() {
    if (!currentEntry || !currentEntry.content) {
        alert("Load or create a journal entry first.");
        return;
    }
    showAIOutput("Generating summary...");
    const summary = await generateSummary(currentEntry.content);
    showAIOutput(summary || "No summary available.");
}

async function handleMoodTrend() {
    showAIOutput("Fetching mood trend...");
    const trend = await fetchMoodTrend(7);
    if (!trend) {
        showAIOutput("No mood trend data available.");
        return;
    }
    renderMoodChart(trend);
}

// --- MOOD CHART SETUP ---
let moodChart = null;
function renderMoodChart(data) {
    // data: [{date: "2025-06-15", mood: "happy"}, ...]

    aiOutput.innerHTML = '<canvas id="moodChart" style="max-width:100%; max-height:200px;"></canvas>';
    const ctx = document.getElementById("moodChart").getContext("2d");

    // Map moods to numeric values for charting
    const moodMap = { happy: 5, calm: 4, neutral: 3, sad: 2, anxious: 1, angry: 0 };
    const labels = data.map(d => formatDate(d.date));
    const values = data.map(d => moodMap[d.mood] ?? 3);

    if (moodChart) moodChart.destroy();

    moodChart = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Mood Level (0=Angry, 5=Happy)",
                data: values,
                borderColor: "#256d3b",
                backgroundColor: "rgba(37,109,59,0.2)",
                fill: true,
                tension: 0.3,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            scales: {
                y: {
                    min: 0,
                    max: 5,
                    ticks: {
                        stepSize: 1,
                        callback: v => {
                            const moodsLabels = ["Angry","Anxious","Sad","Neutral","Calm","Happy"];
                            return moodsLabels[v];
                        }
                    }
                }
            },
            plugins: {
                legend: { display: true },
                tooltip: {
                    callbacks: {
                        label: ctx => {
                            const val = ctx.parsed.y;
                            const moodsLabels = ["Angry","Anxious","Sad","Neutral","Calm","Happy"];
                            return moodsLabels[val] || "Unknown";
                        }
                    }
                }
            },
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

let recognition;
let isRecording = false;

if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = function (event) {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            transcript += <event className=""></event>
            results[i][0].transcript;
        }

        // Append to editor (keep existing content)
        const currentText = quill.getText().trim();
        quill.setText((currentText + ' ' + transcript).trim());
        saveBtn.disabled = false;
    };

    recognition.onerror = function (event) {
        alert("Speech recognition error: " + event.error);
        isRecording = false;
        recordBtn.textContent = "🎤 Start Voice Journal";
    };
} else {
    recordBtn.disabled = true;
    recordBtn.title = "Speech recognition is not supported in this browser.";
}

// Toggle recording
recordBtn.addEventListener('click', () => {
    if (!recognition) return;

    if (!isRecording) {
        recognition.start();
        isRecording = true;
        recordBtn.textContent = '🛑 Stop Recording';
    } else {
        recognition.stop();
        isRecording = false;
        recordBtn.textContent = '🎤 Start Voice Journal';
    }
});

// === EVENT LISTENERS ===

// Load/Create entry
loadEntryBtn.addEventListener("click", async () => {
    const d = dateInput.value;
    if (!d) {
        alert("Please select a date");
        return;
    }
    currentDate = d;
    await loadEntry(d);
});

// Save entry
saveBtn.addEventListener("click", async () => {
    await saveCurrentEntry();
});

visibilitySelect.addEventListener("change", () => {
    if (visibilitySelect.value === "share" || visibilitySelect.value === "group") {
        shareControls.classList.remove("hidden");
    } else {
        shareControls.classList.add("hidden");
    }
});

// Clear editor
clearBtn.addEventListener("click", () => {
    if (confirm("Clear all fields? Unsaved changes will be lost.")) {
        clearForm();
    }
});

// Mood selection buttons
moodSelector.querySelectorAll(".mood-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        setMood(btn.dataset.mood);
        saveBtn.disabled = false;
    });
});

// Habit checkboxes
habitTracker.querySelectorAll("input[type=checkbox]").forEach(cb => {
    cb.addEventListener("change", () => {
        saveBtn.disabled = false;
    });
});

// Detect editor changes for save enabling
quill.on("text-change", () => {
    saveBtn.disabled = false;
});

// Tags input change
tagsInput.addEventListener("input", () => {
    saveBtn.disabled = false;
});

// Goals add button
addGoalBtn.addEventListener("click", addGoal);

// Search buttons
searchBtn.addEventListener("click", searchEntries);
showAllBtn.addEventListener("click", showAllEntries);

// AI tools buttons
sentimentBtn.addEventListener("click", handleSentiment);
summaryBtn.addEventListener("click", handleSummary);
moodTrendBtn.addEventListener("click", handleMoodTrend);

// --- INITIAL LOAD ---
loadEntry(todayISO);
