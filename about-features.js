const infoElements = {
  body: document.body,
  header: document.querySelector(".info-header"),
  navToggle: document.getElementById("infoNavToggle"),
  navLinks: document.getElementById("infoPrimaryNav"),
  links: Array.from(document.querySelectorAll(".info-nav-links a")),
  revealItems: Array.from(document.querySelectorAll(".reveal"))
};

document.addEventListener("DOMContentLoaded", initInfoPage);

function initInfoPage() {
  bindInfoNavigation();
  setupRevealAnimations();
  syncHeaderState();
}

function bindInfoNavigation() {
  if (!infoElements.navToggle || !infoElements.navLinks) {
    return;
  }

  infoElements.navToggle.addEventListener("click", () => {
    const open = infoElements.body.classList.toggle("nav-open");
    infoElements.navToggle.setAttribute("aria-expanded", String(open));
  });

  infoElements.links.forEach((link) => {
    link.addEventListener("click", () => {
      infoElements.body.classList.remove("nav-open");
      infoElements.navToggle.setAttribute("aria-expanded", "false");
    });
  });

  window.addEventListener("scroll", syncHeaderState, { passive: true });
}

function syncHeaderState() {
  if (!infoElements.header) {
    return;
  }

  infoElements.header.classList.toggle("scrolled", window.scrollY > 12);
}

function setupRevealAnimations() {
  if (!("IntersectionObserver" in window)) {
    infoElements.revealItems.forEach((item) => item.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    {
      threshold: 0.16,
      rootMargin: "0px 0px -32px 0px"
    }
  );

  infoElements.revealItems.forEach((item) => observer.observe(item));
}
