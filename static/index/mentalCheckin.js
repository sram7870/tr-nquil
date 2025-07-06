document.addEventListener("DOMContentLoaded", function () {
    const checkinOverlay = document.getElementById("mental-health-checkin");

    if (!checkinOverlay) return;

    // Check if wellness check was done today
    const lastCompleted = localStorage.getItem("wellnessCheckLastCompleted");
    const today = new Date().toISOString().split("T")[0];
    /*
    if (lastCompleted === today) {
        // Hide overlay if already completed today
        checkinOverlay.style.display = "none";
        return;
    }
    */

    const steps = checkinOverlay.querySelectorAll(".step");
    const stepCurrentElem = document.getElementById("step-current");
    const backBtn = document.getElementById("back-btn");
    const nextBtn = document.getElementById("next-btn");
    const moodSlider = document.getElementById("mood-slider");
    const moodLabel = document.getElementById("mood-label");
    const closeBtn = document.getElementById("close-btn");

    let currentStep = 0;
    const moodLabels = ["Very Sad", "Sad", "Neutral", "Happy", "Very Happy"];

    const responses = {
        mood: 3,
        stressors: [],
        coping: []
    };

    function showStep(index) {
        steps.forEach((step, i) => {
            step.classList.toggle("hidden", i !== index);
        });
        stepCurrentElem.textContent = index + 1;

        backBtn.disabled = index === 0;
        nextBtn.textContent = index === steps.length - 1 ? "Finish" : "Next";
    }

    function getCheckedValues(name) {
        return Array.from(
            document.querySelectorAll(`input[name="${name}"]:checked`)
        ).map(i => i.value);
    }

    moodSlider.addEventListener("input", () => {
        const val = parseInt(moodSlider.value, 10);
        moodLabel.textContent = moodLabels[val - 1];
    });

    function markWellnessCheckCompleted() {
        localStorage.setItem("wellnessCheckLastCompleted", today);
    }

    nextBtn.addEventListener("click", () => {
        if (currentStep === 0) {
            responses.mood = parseInt(moodSlider.value, 10);
        } else if (currentStep === 1) {
            responses.stressors = getCheckedValues("stressors");
        } else if (currentStep === 2) {
            responses.coping = getCheckedValues("coping");
        } else if (currentStep === 3) {
            alert("Thank you for checking in! Your responses have been saved.");
            markWellnessCheckCompleted();
            checkinOverlay.remove();
            return;
        }

        currentStep++;
        showStep(currentStep);
    });

    backBtn.addEventListener("click", () => {
        if (currentStep > 0) {
            currentStep--;
            showStep(currentStep);
        }
    });

    closeBtn.addEventListener("click", () => {
        checkinOverlay.remove();
    });

    // Initial state
    showStep(currentStep);
    moodLabel.textContent = moodLabels[moodSlider.value - 1];
});
