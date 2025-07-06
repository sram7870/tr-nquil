document.addEventListener("DOMContentLoaded", () => {
    // Helper: Load image from API into target img element
    function loadImage(endpoint, elementId) {
        fetch(endpoint)
            .then((res) => res.json())
            .then((data) => {
                document.getElementById(elementId).src = `data:image/png;base64,${data.image}`;
            })
            .catch((err) => {
                console.error(`Failed to load ${endpoint}:`, err);
                document.getElementById(elementId).alt = "Error loading chart.";
            });
    }

    // Load AI Summary
    fetch("/api/ai_summary")
        .then((res) => res.json())
        .then((data) => {
            document.getElementById("aiSummary").textContent = data.summary;
        })
        .catch((err) => {
            console.error("Failed to load summary:", err);
            document.getElementById("aiSummary").textContent = "Error loading summary.";
        });
});
