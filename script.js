const appState = {
  uploadedFile: null,
  uploadedImageSrc: "",
  processing: false,
  progressTimer: null,
  stepTimer: null,
  defaultBeforeImage: "",
  defaultAfterImage: ""
};

const elements = {
  body: document.body,
  header: document.querySelector(".site-header"),
  navToggle: document.getElementById("navToggle"),
  primaryNav: document.getElementById("primaryNav"),
  particleField: document.getElementById("particleField"),
  imageInput: document.getElementById("imageInput"),
  dropZone: document.getElementById("dropZone"),
  browseButton: document.getElementById("browseButton"),
  fileName: document.getElementById("fileName"),
  fileSize: document.getElementById("fileSize"),
  fileResolution: document.getElementById("fileResolution"),
  fileFormat: document.getElementById("fileFormat"),
  uploadStatus: document.getElementById("uploadStatus"),
  previewImage: document.getElementById("previewImage"),
  resultImage: document.getElementById("resultImage"),
  compareBeforeImage: document.getElementById("compareBeforeImage"),
  compareAfterImage: document.getElementById("compareAfterImage"),
  previewShell: document.getElementById("previewShell"),
  zoomButton: document.getElementById("zoomButton"),
  fullscreenButton: document.getElementById("fullscreenButton"),
  resetButton: document.getElementById("resetButton"),
  cloudCoverage: document.getElementById("cloudCoverage"),
  captureDate: document.getElementById("captureDate"),
  previewResolution: document.getElementById("previewResolution"),
  processingStatus: document.getElementById("processingStatus"),
  processingSummary: document.getElementById("processingSummary"),
  pipelineBadge: document.getElementById("pipelineBadge"),
  processButton: document.getElementById("processButton"),
  progressFill: document.getElementById("progressFill"),
  progressValue: document.getElementById("progressValue"),
  processingSteps: Array.from(document.querySelectorAll(".step-item")),
  compareButton: document.getElementById("compareButton"),
  downloadButton: document.getElementById("downloadButton"),
  uploadAnotherButton: document.getElementById("uploadAnotherButton"),
  comparisonStage: document.getElementById("comparisonStage"),
  comparisonRange: document.getElementById("comparisonRange"),
  contactForm: document.getElementById("contactForm"),
  nameInput: document.getElementById("nameInput"),
  emailInput: document.getElementById("emailInput"),
  messageInput: document.getElementById("messageInput"),
  formFeedback: document.getElementById("formFeedback"),
  successModal: document.getElementById("successModal"),
  closeModalButton: document.getElementById("closeModalButton"),
  toastStack: document.getElementById("toastStack"),
  backToTop: document.getElementById("backToTop"),
  counters: Array.from(document.querySelectorAll(".counter"))
};

document.addEventListener("DOMContentLoaded", init);

function init() {
  appState.defaultBeforeImage = buildPlaceholderScene(true);
  appState.defaultAfterImage = buildPlaceholderScene(false);

  assignInitialImages();
  seedMetadata();
  createParticles();
  bindNavigation();
  bindUpload();
  bindPreviewControls();
  bindProcessing();
  bindComparison();
  bindContactForm();
  bindFooterActions();
  setupRevealAnimations();
  setupCounterAnimations();
  updateComparison(elements.comparisonRange.value);
  updateYearText();
}

function assignInitialImages() {
  elements.previewImage.src = appState.defaultBeforeImage;
  elements.resultImage.src = appState.defaultAfterImage;
  elements.compareBeforeImage.src = appState.defaultBeforeImage;
  elements.compareAfterImage.src = appState.defaultAfterImage;
}

function seedMetadata() {
  elements.cloudCoverage.textContent = "61%";
  elements.captureDate.textContent = "2026-06-24";
  elements.previewResolution.textContent = "5.8 m";
  elements.processingStatus.textContent = "Standby";
  elements.processingSummary.textContent = "Upload an image and run the mock pipeline to generate a cloud-free reconstruction.";
}

function createParticles() {
  const count = 24;

  for (let index = 0; index < count; index += 1) {
    const particle = document.createElement("span");
    const size = (Math.random() * 3.2 + 1.2).toFixed(2);
    particle.style.left = `${Math.random() * 100}%`;
    particle.style.width = `${size}px`;
    particle.style.height = `${size}px`;
    particle.style.animationDuration = `${Math.random() * 16 + 18}s`;
    particle.style.animationDelay = `${Math.random() * -20}s`;
    particle.style.opacity = `${Math.random() * 0.65 + 0.2}`;
    elements.particleField.appendChild(particle);
  }
}

function bindNavigation() {
  const setNavState = (open) => {
    elements.body.classList.toggle("nav-open", open);
    elements.navToggle.setAttribute("aria-expanded", String(open));
  };

  elements.navToggle.addEventListener("click", (event) => {
    event.stopPropagation();
    setNavState(!elements.body.classList.contains("nav-open"));
  });

  elements.primaryNav.addEventListener("click", (event) => {
    event.stopPropagation();
  });

  document.querySelectorAll(".nav-links a, .brand, .hero-actions a, .footer-links a").forEach((link) => {
    link.addEventListener("click", () => {
      setNavState(false);
    });
  });

  document.addEventListener("click", (event) => {
    if (!elements.body.classList.contains("nav-open")) {
      return;
    }

    if (!elements.primaryNav.contains(event.target) && !elements.navToggle.contains(event.target)) {
      setNavState(false);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      setNavState(false);
    }
  });

  window.addEventListener("scroll", () => {
    elements.header.classList.toggle("scrolled", window.scrollY > 18);
    elements.backToTop.classList.toggle("visible", window.scrollY > 320);
  });
}

function bindUpload() {
  elements.browseButton.addEventListener("click", () => elements.imageInput.click());
  elements.imageInput.addEventListener("change", (event) => {
    const [file] = event.target.files;
    if (file) {
      processSelectedFile(file);
    }
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    elements.dropZone.addEventListener(eventName, (event) => {
      event.preventDefault();
      elements.dropZone.classList.add("dragging");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    elements.dropZone.addEventListener(eventName, (event) => {
      event.preventDefault();
      elements.dropZone.classList.remove("dragging");
    });
  });

  elements.dropZone.addEventListener("drop", (event) => {
    const [file] = Array.from(event.dataTransfer.files || []);
    if (file) {
      processSelectedFile(file);
    }
  });

  elements.dropZone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      elements.imageInput.click();
    }
  });
}

function processSelectedFile(file) {
  const validTypes = ["image/png", "image/jpeg", "image/jpg"];
  const maxSize = 12 * 1024 * 1024;

  if (!validTypes.includes(file.type)) {
    showToast("Please upload a PNG or JPG satellite image.", "warn");
    return;
  }

  if (file.size > maxSize) {
    showToast("File is larger than the 12 MB demo limit.", "warn");
    return;
  }

  const reader = new FileReader();
  reader.onload = () => {
    const image = new Image();
    image.onload = () => {
      appState.uploadedFile = file;
      appState.uploadedImageSrc = reader.result;

      elements.previewImage.src = reader.result;
      elements.resultImage.src = reader.result;
      elements.compareBeforeImage.src = reader.result;
      elements.compareAfterImage.src = reader.result;

      elements.fileName.textContent = file.name;
      elements.fileSize.textContent = formatFileSize(file.size);
      elements.fileResolution.textContent = `${image.naturalWidth} x ${image.naturalHeight}`;
      elements.fileFormat.textContent = file.type.replace("image/", "").toUpperCase();
      elements.uploadStatus.textContent = "Image loaded";
      elements.uploadStatus.className = "status-pill status-success";

      const mockCoverage = randomBetween(34, 78);
      const mockDate = buildRecentDate();
      const resolutionValue = `${(Math.random() * 2.5 + 3.5).toFixed(1)} m`;

      elements.cloudCoverage.textContent = `${mockCoverage}%`;
      elements.captureDate.textContent = mockDate;
      elements.previewResolution.textContent = resolutionValue;
      elements.processingStatus.textContent = "Ready";
      elements.processingSummary.textContent = "Image preview loaded. The prototype is ready to simulate cloud removal.";

      resetPipelineState();
      showToast("Satellite frame uploaded and previewed successfully.", "info");
    };
    image.src = reader.result;
  };

  reader.readAsDataURL(file);
}

function bindPreviewControls() {
  elements.zoomButton.addEventListener("click", () => {
    const zoomed = elements.previewShell.classList.toggle("zoomed");
    elements.zoomButton.textContent = zoomed ? "Zoom Out" : "Zoom";
  });

  elements.fullscreenButton.addEventListener("click", () => {
    showToast("Fullscreen is a UI-only control in this prototype.", "info");
  });

  elements.resetButton.addEventListener("click", resetAllVisuals);
}

function bindProcessing() {
  elements.processButton.addEventListener("click", () => {
    if (appState.processing) {
      return;
    }

    if (!appState.uploadedImageSrc) {
      showToast("No uploaded file detected. Running the demo with the default LISS-IV scene.", "info");
    }

    runMockPipeline();
  });
}

function runMockPipeline() {
  resetPipelineState();
  appState.processing = true;
  elements.processButton.disabled = true;
  elements.processButton.textContent = "Processing...";
  elements.pipelineBadge.textContent = "Running";
  elements.pipelineBadge.className = "status-pill status-busy";
  elements.processingStatus.textContent = "Processing";
  elements.processingSummary.textContent = "Mock AI pipeline is detecting clouds and reconstructing terrain.";

  const stepThresholds = [12, 24, 40, 58, 74, 90, 100];
  let progress = 0;

  elements.processingSteps.forEach((step) => {
    step.classList.remove("active", "completed");
  });

  appState.progressTimer = window.setInterval(() => {
    progress += 1;
    elements.progressFill.style.width = `${progress}%`;
    elements.progressValue.textContent = `${progress}%`;

    const activeIndex = stepThresholds.findIndex((threshold) => progress < threshold);

    elements.processingSteps.forEach((step, index) => {
      step.classList.remove("active", "completed");

      if (progress >= stepThresholds[index]) {
        step.classList.add("completed");
      } else if (index === activeIndex || (activeIndex === -1 && index === stepThresholds.length - 1)) {
        step.classList.add("active");
      }
    });

    if (progress >= 100) {
      window.clearInterval(appState.progressTimer);
      finishMockPipeline();
    }
  }, 32);
}

function finishMockPipeline() {
  appState.processing = false;
  elements.processButton.disabled = false;
  elements.processButton.textContent = "Run Again";
  elements.pipelineBadge.textContent = "Completed";
  elements.pipelineBadge.className = "status-pill status-success";
  elements.processingStatus.textContent = "Completed";
  elements.processingSummary.textContent = "Cloud removal simulation finished. Review the reconstructed output and compare it with the original.";

  const finalImage = appState.uploadedImageSrc || appState.defaultAfterImage;
  elements.resultImage.src = finalImage;
  elements.compareAfterImage.src = finalImage;

  showToast("Mock cloud reconstruction completed.", "info");
  document.getElementById("result").scrollIntoView({ behavior: "smooth", block: "start" });
}

function resetPipelineState() {
  appState.processing = false;
  window.clearInterval(appState.progressTimer);
  window.clearInterval(appState.stepTimer);
  elements.processButton.disabled = false;
  elements.processButton.textContent = "Remove Clouds";
  elements.pipelineBadge.textContent = "Ready";
  elements.pipelineBadge.className = "status-pill status-idle";
  elements.progressFill.style.width = "0%";
  elements.progressValue.textContent = "0%";
  elements.processingSteps.forEach((step) => step.classList.remove("active", "completed"));
}

function resetAllVisuals() {
  appState.uploadedFile = null;
  appState.uploadedImageSrc = "";
  elements.imageInput.value = "";
  elements.previewShell.classList.remove("zoomed");
  elements.zoomButton.textContent = "Zoom";
  elements.uploadStatus.textContent = "Awaiting image";
  elements.uploadStatus.className = "status-pill status-idle";

  assignInitialImages();
  elements.fileName.textContent = "Demo-LISS4-Capture.png";
  elements.fileSize.textContent = "4.8 MB";
  elements.fileResolution.textContent = "4096 x 4096";
  elements.fileFormat.textContent = "PNG";
  seedMetadata();
  resetPipelineState();
  showToast("The dashboard has been reset to the demo state.", "info");
}

function bindComparison() {
  elements.comparisonRange.addEventListener("input", (event) => {
    updateComparison(event.target.value);
  });

  elements.compareButton.addEventListener("click", () => {
    document.getElementById("comparison").scrollIntoView({ behavior: "smooth", block: "start" });
  });

  elements.uploadAnotherButton.addEventListener("click", () => {
    document.getElementById("upload").scrollIntoView({ behavior: "smooth", block: "start" });
    elements.imageInput.click();
  });

  elements.downloadButton.addEventListener("click", () => {
    showToast("Download is a prototype-only action in this frontend demo.", "info");
  });
}

function updateComparison(value) {
  elements.comparisonStage.style.setProperty("--split", `${value}%`);
}

function bindContactForm() {
  const fields = [elements.nameInput, elements.emailInput, elements.messageInput];

  fields.forEach((field) => {
    field.addEventListener("input", () => field.classList.remove("invalid"));
  });

  elements.contactForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const name = elements.nameInput.value.trim();
    const email = elements.emailInput.value.trim();
    const message = elements.messageInput.value.trim();
    let valid = true;

    fields.forEach((field) => field.classList.remove("invalid"));
    elements.formFeedback.textContent = "";

    if (name.length < 2) {
      valid = false;
      elements.nameInput.classList.add("invalid");
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      valid = false;
      elements.emailInput.classList.add("invalid");
    }

    if (message.length < 10) {
      valid = false;
      elements.messageInput.classList.add("invalid");
    }

    if (!valid) {
      elements.formFeedback.textContent = "Please enter a valid name, email, and a message of at least 10 characters.";
      showToast("Contact form validation failed. Please review the highlighted fields.", "warn");
      return;
    }

    elements.contactForm.reset();
    elements.successModal.classList.add("open");
    elements.successModal.setAttribute("aria-hidden", "false");
    showToast("Mock contact message submitted successfully.", "info");
  });

  elements.closeModalButton.addEventListener("click", closeModal);
  elements.successModal.addEventListener("click", (event) => {
    if (event.target === elements.successModal) {
      closeModal();
    }
  });
}

function closeModal() {
  elements.successModal.classList.remove("open");
  elements.successModal.setAttribute("aria-hidden", "true");
}

function bindFooterActions() {
  elements.backToTop.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  ["githubLink", "linkedinLink", "emailLink"].forEach((id) => {
    document.getElementById(id).addEventListener("click", (event) => {
      event.preventDefault();
      showToast("This social action is included as UI-only in the prototype.", "info");
    });
  });
}

function setupRevealAnimations() {
  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          revealObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.14 }
  );

  document.querySelectorAll(".reveal").forEach((item) => revealObserver.observe(item));
}

function setupCounterAnimations() {
  const counterObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          counterObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.35 }
  );

  elements.counters.forEach((counter) => counterObserver.observe(counter));
}

function animateCounter(counter) {
  const targetValue = Number(counter.dataset.target);
  const prefix = counter.dataset.prefix || "";
  const suffix = counter.dataset.suffix || "";
  const decimals = Number.isInteger(targetValue) ? 0 : 1;
  const duration = 1400;
  const startTime = performance.now();

  function update(currentTime) {
    const progress = Math.min((currentTime - startTime) / duration, 1);
    const currentValue = targetValue * easeOutCubic(progress);
    counter.textContent = `${prefix}${currentValue.toFixed(decimals)}${suffix}`;

    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }

  requestAnimationFrame(update);
}

function showToast(message, variant) {
  const toast = document.createElement("div");
  toast.className = `toast ${variant === "warn" ? "warn" : ""}`.trim();
  toast.textContent = message;
  elements.toastStack.appendChild(toast);

  window.setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(8px)";
    window.setTimeout(() => toast.remove(), 220);
  }, 2800);
}

function buildPlaceholderScene(withClouds) {
  const clouds = withClouds
    ? `
      <g opacity="0.95">
        <ellipse cx="256" cy="172" rx="96" ry="38" fill="rgba(244,248,255,0.78)"/>
        <ellipse cx="336" cy="194" rx="116" ry="42" fill="rgba(244,248,255,0.68)"/>
        <ellipse cx="446" cy="160" rx="88" ry="34" fill="rgba(244,248,255,0.58)"/>
      </g>
    `
    : `
      <g opacity="0.3">
        <ellipse cx="300" cy="170" rx="102" ry="32" fill="rgba(244,248,255,0.18)"/>
      </g>
    `;

  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 760">
      <defs>
        <linearGradient id="sky" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#071423"/>
          <stop offset="50%" stop-color="#10345A"/>
          <stop offset="100%" stop-color="#183E5F"/>
        </linearGradient>
        <linearGradient id="terrainA" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#1F874F"/>
          <stop offset="100%" stop-color="#58C273"/>
        </linearGradient>
        <linearGradient id="terrainB" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#166088"/>
          <stop offset="100%" stop-color="#3E92CC"/>
        </linearGradient>
        <linearGradient id="terrainC" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#4B733B"/>
          <stop offset="100%" stop-color="#8FBF5A"/>
        </linearGradient>
      </defs>
      <rect width="1200" height="760" fill="url(#sky)"/>
      <circle cx="930" cy="130" r="84" fill="rgba(0,229,255,0.16)"/>
      <rect x="-30" y="350" width="1260" height="500" fill="#0A1A23"/>
      <path d="M0 352 L292 248 L480 316 L708 236 L950 324 L1200 252 L1200 760 L0 760 Z" fill="url(#terrainA)"/>
      <path d="M0 458 L212 392 L400 464 L610 378 L824 460 L1056 390 L1200 438 L1200 760 L0 760 Z" fill="url(#terrainB)" opacity="0.86"/>
      <path d="M0 514 L154 464 L324 526 L520 446 L742 548 L908 492 L1200 564 L1200 760 L0 760 Z" fill="url(#terrainC)" opacity="0.92"/>
      <path d="M124 334 L292 278" stroke="rgba(255,255,255,0.18)" stroke-width="4"/>
      <path d="M334 290 L478 336" stroke="rgba(255,255,255,0.18)" stroke-width="4"/>
      <path d="M506 296 L708 248" stroke="rgba(255,255,255,0.18)" stroke-width="4"/>
      <path d="M760 266 L934 334" stroke="rgba(255,255,255,0.18)" stroke-width="4"/>
      ${clouds}
      <rect x="850" y="60" width="170" height="18" rx="9" fill="rgba(163,238,255,0.42)"/>
      <rect x="850" y="98" width="170" height="18" rx="9" fill="rgba(163,238,255,0.42)"/>
      <rect x="760" y="72" width="68" height="54" rx="12" fill="#E6FBFF"/>
      <path d="M792 126 L734 210" stroke="#8CEBFF" stroke-width="10" stroke-linecap="round"/>
      <circle cx="730" cy="216" r="20" fill="#A1F3FF"/>
      <path d="M730 216 L590 310" stroke="rgba(0,255,198,0.55)" stroke-width="4" stroke-dasharray="14 10"/>
      <text x="72" y="90" fill="#D8F8FF" font-family="Orbitron, Arial, sans-serif" font-size="38" font-weight="700">LISS-IV DEMO FRAME</text>
    </svg>
  `;

  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

function formatFileSize(bytes) {
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function randomBetween(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function buildRecentDate() {
  const date = new Date();
  date.setDate(date.getDate() - randomBetween(3, 42));
  return date.toISOString().slice(0, 10);
}

function easeOutCubic(value) {
  return 1 - Math.pow(1 - value, 3);
}

function updateYearText() {
  const footerCopy = document.querySelector(".footer-bottom p");
  footerCopy.textContent = `Copyright ${new Date().getFullYear()} Generative AI-Based Cloud Removal and Reconstruction for LISS-IV Satellite Imagery`;
}
