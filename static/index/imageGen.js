document.addEventListener('DOMContentLoaded', () => {
    // 🎨 Emotional Art Generator Logic
    const emotionTextarea = document.getElementById('emotion-description');
    const generateArtBtn = document.getElementById('generate-art-btn');
    const artContainer = document.getElementById('generated-art-container');
    const artImage = document.getElementById('generated-art');

    if (generateArtBtn && emotionTextarea && artContainer && artImage) {
        generateArtBtn.addEventListener('click', async () => {
            const emotion = emotionTextarea.value.trim();
            if (!emotion) {
                alert('Please describe how you feel.');
                return;
            }

            generateArtBtn.disabled = true;
            generateArtBtn.textContent = 'Generating...';

            try {
                const response = await fetch('/generate-art', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({emotion})
                });

                const data = await response.json();

                if (response.ok && data.imageUrl) {
                    artImage.src = data.imageUrl;
                    artImage.alt = data.prompt || "Emotional artwork";
                    artContainer.classList.remove('hidden');
                } else {
                    alert(data.error || "Failed to generate art. Please try again.");
                }
            } catch (err) {
                console.error("[Art Gen Error]", err);
                alert("Network error. Please try again.");
            } finally {
                generateArtBtn.disabled = false;
                generateArtBtn.textContent = 'Generate';
            }
        });
    }
});