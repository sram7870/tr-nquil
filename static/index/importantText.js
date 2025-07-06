document.addEventListener('DOMContentLoaded', () => {
    const promptEl = document.getElementById('daily-prompt');
    const quoteEl = document.getElementById('daily-quote');
    const activitiesEl = document.getElementById('daily-activities');
    const tipEl = document.getElementById('daily-tip');
    const affirmationEl = document.getElementById('daily-affirmation');
    const regenerateBtn = document.getElementById('regenerate-boost');

    if (!promptEl || !quoteEl || !activitiesEl || !tipEl || !affirmationEl) return;

    function setLoadingState() {
        [promptEl, quoteEl, tipEl, affirmationEl].forEach(el => {
            el.textContent = '';
            el.classList.add('animate-pulse', 'bg-green-100', 'rounded-md', 'h-6', 'w-full', 'mb-4');
        });

        activitiesEl.innerHTML = `
            <li class="animate-pulse bg-green-100 rounded-md h-6 w-full mb-2"></li>
            <li class="animate-pulse bg-green-100 rounded-md h-6 w-5/6 mb-2"></li>
            <li class="animate-pulse bg-green-100 rounded-md h-6 w-2/3"></li>
        `;
    }

    function clearLoadingState() {
        [promptEl, quoteEl, tipEl, affirmationEl].forEach(el => {
            el.classList.remove('animate-pulse', 'bg-green-100', 'rounded-md', 'h-6', 'w-full', 'mb-4');
        });
    }

    function setDailyContent({ prompt, quote, activities, tip, affirmation }) {
        promptEl.textContent = prompt || "Take a moment to reflect.";
        quoteEl.textContent = quote || "You are stronger than you think.";
        tipEl.textContent = tip || "Pause, breathe deeply, and anchor your awareness in the present moment.";
        affirmationEl.textContent = affirmation || "You’ve come so far already. Be proud of how you continue to grow with compassion and strength.";

        activitiesEl.innerHTML = '';

        const activityArray = Array.isArray(activities) && activities.length
            ? activities
            : ["Breathe deeply for 1 minute", "Send a kind message to someone", "Write in your journal"];

        activityArray.forEach((activity, index) => {
            const li = document.createElement('li');
            li.classList.add('flex', 'items-start', 'space-x-3');

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.classList.add('mt-1', 'accent-blue-600', 'focus:ring-blue-500');
            checkbox.id = `activity${index + 1}`;

            const label = document.createElement('label');
            label.htmlFor = checkbox.id;
            label.classList.add('flex-1', 'text-gray-700');
            label.textContent = activity;

            li.appendChild(checkbox);
            li.appendChild(label);
            activitiesEl.appendChild(li);
        });
    }

    function fadeOut(elements) {
        elements.forEach(el => {
            el.classList.add('opacity-0', 'transition-opacity', 'duration-500');
            el.classList.remove('opacity-100');
        });
    }

    function fadeIn(elements) {
        elements.forEach(el => {
            el.classList.remove('opacity-0');
            el.classList.add('opacity-100');
        });
    }

    async function loadDailyMentalBoost(forceRefresh = false) {
        if (regenerateBtn) regenerateBtn.textContent = 'Loading...';

        const fadeTargets = [promptEl, quoteEl, activitiesEl, tipEl, affirmationEl];
        fadeOut(fadeTargets);
        setLoadingState();

        try {
            const res = await fetch('/daily-mental-boost' + (forceRefresh ? '?refresh=1' : ''));
            const data = await res.json();

            clearLoadingState();

            setTimeout(() => {
                setDailyContent(data);
                fadeIn(fadeTargets);
            }, 500);
        } catch (err) {
            console.error('[Daily Boost Error]', err);
            clearLoadingState();

            setTimeout(() => {
                setDailyContent({
                    prompt: "Reflect on one small thing that went well today.",
                    quote: "You’ve survived 100% of your worst days.",
                    tip: "When your mind feels crowded, return to your breath. It’s always here to ground you.",
                    affirmation: "You are doing your best, and that is more than enough. Trust in your path and your progress.",
                    activities: null
                });
                fadeIn(fadeTargets);
            }, 500);
        } finally {
            if (regenerateBtn) regenerateBtn.textContent = '🔄 Regenerate';
        }
    }

    loadDailyMentalBoost();

    if (regenerateBtn) {
        regenerateBtn.addEventListener('click', () => {
            loadDailyMentalBoost(true);
        });
    }
});
