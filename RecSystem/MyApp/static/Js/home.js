document.addEventListener("DOMContentLoaded", () => {
    const header = document.querySelector("header h1");
    header.style.opacity = 0;
    header.style.transition = "opacity 1.5s ease";

    setTimeout(() => {
        header.style.opacity = 1;
    }, 200);
});
