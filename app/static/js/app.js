/**
 * FitBuddy - Interactive Frontend Logic
 */

document.addEventListener("DOMContentLoaded", () => {
  initMobileMenu();
  initExerciseChecklist();
  initRestTimers();
  initAiLoaders();
  initFeedbackChips();
  initClipboardButtons();
});

/* ----------------------------------------------------
   1. Mobile Navigation Toggle
---------------------------------------------------- */
function initMobileMenu() {
  const toggleBtn = document.getElementById("mobile-menu-toggle");
  const navLinks = document.getElementById("nav-links");

  if (toggleBtn && navLinks) {
    toggleBtn.addEventListener("click", () => {
      navLinks.classList.toggle("mobile-open");
    });
  }
}

/* ----------------------------------------------------
   2. Exercise Interactive Checklist & Day Progress
---------------------------------------------------- */
function initExerciseChecklist() {
  const exerciseItems = document.querySelectorAll(".exercise-item");

  exerciseItems.forEach((item) => {
    const checkbox = item.querySelector(".exercise-checkbox");
    if (checkbox) {
      checkbox.addEventListener("change", (e) => {
        if (e.target.checked) {
          item.classList.add("completed");
        } else {
          item.classList.remove("completed");
        }
        updateDayProgress(item.closest(".day-card"));
      });
    }
  });
}

function updateDayProgress(dayCard) {
  if (!dayCard) return;
  const total = dayCard.querySelectorAll(".exercise-checkbox").length;
  const checked = dayCard.querySelectorAll(".exercise-checkbox:checked").length;
  const progressBadge = dayCard.querySelector(".day-progress-badge");

  if (progressBadge && total > 0) {
    const pct = Math.round((checked / total) * 100);
    progressBadge.textContent = `${pct}% Done (${checked}/${total})`;
    if (pct === 100) {
      progressBadge.classList.add("badge-primary");
    }
  }
}

/* ----------------------------------------------------
   3. Interactive Rest Timer Modal / Floating Widget
---------------------------------------------------- */
let activeTimerInterval = null;

function initRestTimers() {
  const restBadges = document.querySelectorAll(".rest-timer-trigger");
  restBadges.forEach((badge) => {
    badge.addEventListener("click", () => {
      const seconds = parseInt(badge.getAttribute("data-seconds")) || 60;
      startRestCountdown(seconds, badge.getAttribute("data-exercise") || "Exercise");
    });
  });
}

function startRestCountdown(totalSeconds, exerciseName) {
  let timerModal = document.getElementById("rest-timer-modal");
  if (!timerModal) {
    timerModal = createTimerModal();
  }

  const titleEl = document.getElementById("timer-exercise-name");
  const timeDisplay = document.getElementById("timer-display");
  const barEl = document.getElementById("timer-progress-fill");

  if (titleEl) titleEl.textContent = `Rest after: ${exerciseName}`;
  timerModal.style.display = "flex";

  if (activeTimerInterval) clearInterval(activeTimerInterval);

  let remaining = totalSeconds;
  updateTimerUI(remaining, totalSeconds, timeDisplay, barEl);

  activeTimerInterval = setInterval(() => {
    remaining--;
    updateTimerUI(remaining, totalSeconds, timeDisplay, barEl);

    if (remaining <= 0) {
      clearInterval(activeTimerInterval);
      if (timeDisplay) timeDisplay.textContent = "Time's Up! Next Set 🔥";
      playBeep();
      setTimeout(() => {
        timerModal.style.display = "none";
      }, 3500);
    }
  }, 1000);
}

function updateTimerUI(remaining, total, textEl, barEl) {
  if (textEl) {
    const mins = Math.floor(remaining / 60);
    const secs = remaining % 60;
    textEl.textContent = `${mins}:${secs < 10 ? "0" : ""}${secs}`;
  }
  if (barEl) {
    const pct = Math.max(0, (remaining / total) * 100);
    barEl.style.width = `${pct}%`;
  }
}

function createTimerModal() {
  const modal = document.createElement("div");
  modal.id = "rest-timer-modal";
  modal.style.cssText = `
    position: fixed; bottom: 25px; right: 25px; z-index: 9999;
    background: #111827; border: 1px solid rgba(16, 185, 129, 0.4);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8), 0 0 20px rgba(16, 185, 129, 0.2);
    border-radius: 16px; padding: 1.25rem 1.5rem; width: 280px;
    display: none; flex-direction: column; gap: 0.75rem;
    font-family: 'Outfit', sans-serif; backdrop-filter: blur(10px);
  `;
  modal.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <span style="font-size:0.85rem; color:#9ca3af; text-transform:uppercase; font-weight:700;">⏱️ Rest Timer</span>
      <button id="close-timer-btn" style="background:none; border:none; color:#9ca3af; cursor:pointer; font-size:1.2rem;">&times;</button>
    </div>
    <div id="timer-exercise-name" style="font-size:0.85rem; color:#e5e7eb; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;"></div>
    <div id="timer-display" style="font-size:2.4rem; font-weight:800; color:#10b981; text-align:center; line-height:1;">60</div>
    <div style="height:6px; background:#1f2937; border-radius:9999px; overflow:hidden;">
      <div id="timer-progress-fill" style="height:100%; width:100%; background:linear-gradient(90deg, #10b981, #06b6d4); transition:width 1s linear;"></div>
    </div>
  `;
  document.body.appendChild(modal);

  document.getElementById("close-timer-btn").addEventListener("click", () => {
    if (activeTimerInterval) clearInterval(activeTimerInterval);
    modal.style.display = "none";
  });

  return modal;
}

function playBeep() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.type = "sine";
    osc.frequency.setValueAtTime(800, ctx.currentTime);
    gain.gain.setValueAtTime(0.2, ctx.currentTime);
    osc.start();
    osc.stop(ctx.currentTime + 0.35);
  } catch (e) {
    // Audio context not allowed or not supported
  }
}

/* ----------------------------------------------------
   4. AI Loading Overlay with Rotating Fitness Tips
---------------------------------------------------- */
const fitnessTips = [
  "Formulating biomechanically balanced push-pull-leg ratios...",
  "Calibrating recovery intervals and nervous system fatigue...",
  "Synthesizing progressive overload strategies...",
  "Filtering exercises to ensure joint and limitation safety...",
  "Optimizing protein absorption windows and hydration targets...",
  "Aligning caloric targets with metabolic adaptations..."
];

function initAiLoaders() {
  const forms = document.querySelectorAll(".ai-trigger-form");
  const loaderOverlay = document.getElementById("ai-loader-overlay");
  const tipEl = document.getElementById("loader-rotating-tip");

  forms.forEach((form) => {
    form.addEventListener("submit", () => {
      if (loaderOverlay) {
        loaderOverlay.classList.add("active");
        let tipIdx = 0;
        setInterval(() => {
          tipIdx = (tipIdx + 1) % fitnessTips.length;
          if (tipEl) tipEl.textContent = fitnessTips[tipIdx];
        }, 2500);
      }
    });
  });
}

/* ----------------------------------------------------
   5. Quick Feedback Chips
---------------------------------------------------- */
function initFeedbackChips() {
  const chips = document.querySelectorAll(".feedback-chip");
  const textarea = document.getElementById("feedback-textarea");

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const text = chip.getAttribute("data-text");
      if (textarea && text) {
        if (textarea.value.trim().length > 0) {
          textarea.value += " " + text;
        } else {
          textarea.value = text;
        }
        textarea.focus();
      }
    });
  });
}

/* ----------------------------------------------------
   6. Copy Plan & Print
---------------------------------------------------- */
function initClipboardButtons() {
  const copyBtn = document.getElementById("copy-plan-btn");
  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      const planTitle = document.querySelector(".plan-title")?.innerText || "FitBuddy Workout Plan";
      const days = document.querySelectorAll(".day-card");
      let planText = `🏋️ ${planTitle}\n====================\n\n`;

      days.forEach((day) => {
        const title = day.querySelector("h3")?.innerText || "";
        const focus = day.querySelector(".day-focus-badge")?.innerText || "";
        planText += `\n[${title} - ${focus}]\n`;

        const exercises = day.querySelectorAll(".exercise-item");
        exercises.forEach((ex) => {
          const name = ex.querySelector(".exercise-name")?.innerText || "";
          const badges = Array.from(ex.querySelectorAll(".badge")).map((b) => b.innerText).join(" | ");
          planText += `  • ${name} (${badges})\n`;
        });
      });

      planText += `\n-- Generated via FitBuddy AI Fitness Platform --`;

      navigator.clipboard.writeText(planText).then(() => {
        const original = copyBtn.innerHTML;
        copyBtn.innerHTML = `<span>✓ Copied to Clipboard</span>`;
        setTimeout(() => {
          copyBtn.innerHTML = original;
        }, 2200);
      });
    });
  }

  const printBtn = document.getElementById("print-plan-btn");
  if (printBtn) {
    printBtn.addEventListener("click", () => {
      window.print();
    });
  }
}
