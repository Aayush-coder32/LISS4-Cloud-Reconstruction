const elements = {
  body: document.body,
  header: document.querySelector(".site-header"),
  navToggle: document.getElementById("navToggle"),
  primaryNav: document.getElementById("primaryNav"),
  particleField: document.getElementById("particleField"),
  registrationForm: document.getElementById("registrationForm"),
  registerName: document.getElementById("registerName"),
  registerEmail: document.getElementById("registerEmail"),
  registerPhone: document.getElementById("registerPhone"),
  registerOrg: document.getElementById("registerOrg"),
  registerRole: document.getElementById("registerRole"),
  registerRegion: document.getElementById("registerRegion"),
  registerPassword: document.getElementById("registerPassword"),
  registerConfirmPassword: document.getElementById("registerConfirmPassword"),
  registerGoal: document.getElementById("registerGoal"),
  registerConsent: document.getElementById("registerConsent"),
  consentRow: document.getElementById("consentRow"),
  registerFeedback: document.getElementById("registerFeedback"),
  successModal: document.getElementById("successModal"),
  closeModalButton: document.getElementById("closeModalButton"),
  toastStack: document.getElementById("toastStack"),
  backToTop: document.getElementById("backToTop")
};

document.addEventListener("DOMContentLoaded", init);

function init() {
  createParticles();
  bindNavigation();
  bindRegistrationForm();
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

function bindRegistrationForm() {
  const textFields = [
    elements.registerName,
    elements.registerEmail,
    elements.registerPhone,
    elements.registerOrg,
    elements.registerPassword,
    elements.registerConfirmPassword,
    elements.registerGoal
  ];

  textFields.forEach((field) => {
    field.addEventListener("input", () => clearFieldState(field));
  });

  [elements.registerRole, elements.registerRegion].forEach((field) => {
    field.addEventListener("change", () => clearFieldState(field));
  });

  elements.registerConsent.addEventListener("change", () => {
    elements.consentRow.classList.remove("invalid");
  });

  elements.registrationForm.addEventListener("submit", (event) => {
    event.preventDefault();

    clearFeedback();

    const values = {
      name: elements.registerName.value.trim(),
      email: elements.registerEmail.value.trim(),
      phone: elements.registerPhone.value.trim(),
      organization: elements.registerOrg.value.trim(),
      role: elements.registerRole.value,
      region: elements.registerRegion.value,
      password: elements.registerPassword.value,
      confirmPassword: elements.registerConfirmPassword.value,
      goal: elements.registerGoal.value.trim(),
      consent: elements.registerConsent.checked
    };

    const validations = [
      {
        valid: values.name.length >= 3,
        field: elements.registerName,
        message: "Please enter your full name."
      },
      {
        valid: isValidEmail(values.email),
        field: elements.registerEmail,
        message: "Please enter a valid email address."
      },
      {
        valid: isValidPhone(values.phone),
        field: elements.registerPhone,
        message: "Please enter a valid mobile number."
      },
      {
        valid: values.organization.length >= 3,
        field: elements.registerOrg,
        message: "Please enter your organization or college name."
      },
      {
        valid: values.role !== "",
        field: elements.registerRole,
        message: "Please select your primary role."
      },
      {
        valid: values.region !== "",
        field: elements.registerRegion,
        message: "Please select a region of interest."
      },
      {
        valid: values.password.length >= 8,
        field: elements.registerPassword,
        message: "Password must be at least 8 characters long."
      },
      {
        valid: values.confirmPassword === values.password && values.confirmPassword.length >= 8,
        field: elements.registerConfirmPassword,
        message: "Confirm password must match your password."
      },
      {
        valid: values.goal.length >= 15,
        field: elements.registerGoal,
        message: "Please add a short project goal for the demo."
      }
    ];

    const firstInvalid = validations.find((item) => !item.valid);

    if (firstInvalid) {
      firstInvalid.field.classList.add("invalid");
      setFeedback(firstInvalid.message, false);
      showToast(firstInvalid.message, "warn");
      firstInvalid.field.focus();
      return;
    }

    if (!values.consent) {
      elements.consentRow.classList.add("invalid");
      setFeedback("Please accept the demo registration terms to continue.", false);
      showToast("Please accept the registration terms.", "warn");
      elements.registerConsent.focus();
      return;
    }

    elements.registrationForm.reset();
    elements.consentRow.classList.remove("invalid");
    setFeedback("Registration submitted successfully. This is a mock frontend confirmation.", true);
    showToast("Registration submitted successfully.", "info");
    openModal();
  });
}

function clearFieldState(field) {
  field.classList.remove("invalid");
  clearFeedback();
}

function clearFeedback() {
  elements.registerFeedback.textContent = "";
  elements.registerFeedback.classList.remove("success");
}

function setFeedback(message, success) {
  elements.registerFeedback.textContent = message;
  elements.registerFeedback.classList.toggle("success", success);
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

function isValidEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function isValidPhone(value) {
  const digitsOnly = value.replace(/\D/g, "");
  return digitsOnly.length >= 10 && digitsOnly.length <= 15;
}
