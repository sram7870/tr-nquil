document.getElementById('generate-plan').addEventListener('click', async () => {
    const outputDiv = document.getElementById('generated-plan');
    const wellnessInput = document.getElementById('wellness-input').value.trim();

    if (!wellnessInput) {
        outputDiv.textContent = "Please provide some information about your wellness before generating a plan.";
        return;
    }

    outputDiv.textContent = "Generating your personalized nutrition & exercise plan...";

    // Build the prompt - you can customize this as needed
    const prompt = `Based on the following wellness information, create a personalized nutrition and exercise plan:

${wellnessInput}

Please provide detailed recommendations including diet, exercise types, frequency, and tips.`;

    try {
        const response = await fetch('/exercise-plan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })  // Note: we'll tweak the backend to accept this prompt
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        outputDiv.textContent = data.exercise_plan;

    } catch (err) {
        console.error(err);
        outputDiv.textContent = "Sorry, something went wrong while generating your plan.";
    }
});
