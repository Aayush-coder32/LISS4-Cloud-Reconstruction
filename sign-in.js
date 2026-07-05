const elements = {
  body: document.body,
  header: document.querySelector(".site-header"),
  navToggle: document.getElementById("navToggle"),
  primaryNav: document.getElementById("primaryNav"),
  particleField: document.getElementById("particleField"),
  signInForm: document.getElementById("signInForm"),
  usernameInput: document.getElementById("usernameInput"),
  passwordInput: document.getElementById("passwordInput"),
  signInFeedback: document.getElementById("signInFeedback"),
  successModal: document.getElementById("successModal"),
  closeModalButton: document.getElementById("closeModalButton"),
  toastStack: document.getElementById("toastStack"),
  backToTop: document.getElementById("backToTop")
};

document.addEventListener("DOMContentLoaded", init);

function init() {
  createParticles();
  bindNavigation();
  bindSignInForm();
  bindModal();
  syncScrollState();
}

function createParticles() {
  const count = 18;

  for (let index = 0; index < count; index += 1) {
    const particle = document.createElement("span");
    const size = (Math.random() * 3 + 1.1).toFixed(2);
    particle.style.left = `${Math.random() * 100}%`;
    particle.style.width = `${size}px`;
    particle.style.height = `${size}px`;
    particle.style.animationDuration = `${Math.random() * 14 + 18}s`;
    particle.style.animationDelay = `${Math.random() * -18}s`;
    particle.style.opacity = `${Math.random() * 0.65 + 0.2}`;
    elements.particleField.appendChild(particle);
  }
}

function bindNavigation() {
  elements.navToggle.addEventListener("click", () => {
    const open = elements.body.classList.toggle("nav-open");
    elements.navToggle.setAttribute("aria-expanded", String(open));
  });

  document.querySelectorAll(".nav-links a, .brand, .footer-links a").forEach((link) => {
    link.addEventListener("click", () => {
      elements.body.classList.remove("nav-open");
      elements.navToggle.setAttribute("aria-expanded", "false");
    });
  });

  elements.backToTop.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  window.addEventListener("scroll", syncScrollState);
}

function syncScrollState() {
  elements.header.classList.toggle("scrolled", window.scrollY > 18);
  elements.backToTop.classList.toggle("visible", window.scrollY > 320);
}

function bindSignInForm() {
  [elements.usernameInput, elements.passwordInput].forEach((field) => {
    field.addEventListener("input", () => {
      field.classList.remove("invalid");
      clearFeedback();
    });
  });

  elements.signInForm.addEventListener("submit", (event) => {
    event.preventDefault();
    clearFeedback();

    const username = elements.usernameInput.value.trim();
    const password = elements.passwordInput.value.trim();

    if (username.length < 3) {
      elements.usernameInput.classList.add("invalid");
      setFeedback("Please enter a valid username.", false);
      showToast("Please enter a valid username.", "warn");
      elements.usernameInput.focus();
      return;
    }

    if (password.length < 6) {
      elements.passwordInput.classList.add("invalid");
      setFeedback("Password must be at least 6 characters long.", false);
      showToast("Password must be at least 6 characters long.", "warn");
      elements.passwordInput.focus();
      return;
    }

    elements.signInForm.reset();
    setFeedback("Signed in successfully in this prototype flow.", true);
    showToast("Sign in successful.", "info");
    openModal();
  });
}

function clearFeedback() {
  elements.signInFeedback.textContent = "";
  elements.signInFeedback.classList.remove("success");
}

function setFeedback(message, success) {
  elements.signInFeedback.textContent = message;
  elements.signInFeedback.classList.toggle("success", success);
}

function bindModal() {
  elements.closeModalButton.addEventListener("click", closeModal);

  elements.successModal.addEventListener("click", (event) => {
    if (event.target === elements.successModal) {
      closeModal();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && elements.successModal.classList.contains("open")) {
      closeModal();
    }
  });
}

function openModal() {
  elements.successModal.classList.add("open");
  elements.successModal.setAttribute("aria-hidden", "false");
}

function closeModal() {
  elements.successModal.classList.remove("open");
  elements.successModal.setAttribute("aria-hidden", "true");
}

function showToast(message, variant = "info") {
  const toast = document.createElement("div");
  toast.className = `toast ${variant === "warn" ? "warn" : ""}`.trim();
  toast.textContent = message;
  elements.toastStack.appendChild(toast);

  window.setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(8px)";
    window.setTimeout(() => toast.remove(), 220);
  }, 2400);
}
