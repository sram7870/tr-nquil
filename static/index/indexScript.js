document.addEventListener('DOMContentLoaded', () => {

    const carousel = document.getElementById("carousel");
    const dots = document.querySelectorAll(".dot");
    const leftArrow = document.getElementById("left-arrow");
    const rightArrow = document.getElementById("right-arrow");
    const cardWidth = carousel.offsetWidth;

    feather.replace();

    function updateDots() {
        const scrollLeft = carousel.scrollLeft;
        const scrollFraction = scrollLeft / cardWidth;
        const index = Math.round(scrollFraction);

        dots.forEach((dot, i) => {
            dot.classList.remove("active");
            dot.setAttribute("aria-selected", "false");
        });

        if (index >= 0 && index < dots.length) {
            dots[index].classList.add("active");
            dots[index].setAttribute("aria-selected", "true");
        }
    }

    carousel.addEventListener("scroll", updateDots);
    updateDots();

    function scrollCarousel(direction) {
        carousel.scrollBy({ left: direction * cardWidth, behavior: 'smooth' });
    }

    leftArrow.addEventListener("click", () => scrollCarousel(-1));
    rightArrow.addEventListener("click", () => scrollCarousel(1));

    dots.forEach((dot, i) => {
        dot.addEventListener("click", () => {
            carousel.scrollTo({ left: cardWidth * i, behavior: 'smooth' });
        });
    });
});
