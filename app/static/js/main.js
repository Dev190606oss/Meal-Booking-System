/**
 * Meal Booking System - Interactive Frontend Handlers
 * Clean, lightweight vanilla JavaScript for smooth UI micro-interactions
 */

document.addEventListener("DOMContentLoaded", () => {
  initMobileNav();
  initCartHandlers();
  initModals();
});

// --------------------------------------------------------------------------
// Mobile Navigation Toggle
// --------------------------------------------------------------------------
function initMobileNav() {
  const toggleBtn = document.querySelector(".mobile-toggle");
  const navLinks = document.querySelector(".nav-links");

  if (toggleBtn && navLinks) {
    toggleBtn.addEventListener("click", () => {
      navLinks.classList.toggle("mobile-open");
      const icon = toggleBtn.querySelector("i");
      if (icon) {
        icon.classList.toggle("fa-bars");
        icon.classList.toggle("fa-xmark");
      }
    });
  }
}

// --------------------------------------------------------------------------
// Toast Notification Engine
// --------------------------------------------------------------------------
function showToast(message, type = "info") {
  let container = document.querySelector(".toast-container");
  if (!container) {
    container = document.createElement("div");
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  const iconClass = type === "success" ? "fa-circle-check" :
                    type === "danger" ? "fa-circle-exclamation" : "fa-bell";

  toast.innerHTML = `
    <i class="fa-solid ${iconClass} toast-icon"></i>
    <span>${message}</span>
  `;

  container.appendChild(toast);

  // Trigger animation
  setTimeout(() => toast.classList.add("show"), 10);

  // Remove after 3.5s
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// --------------------------------------------------------------------------
// Cart AJAX Handlers
// --------------------------------------------------------------------------
function initCartHandlers() {
  // Quick Add to Cart from cards
  document.querySelectorAll(".btn-add-cart").forEach((button) => {
    button.addEventListener("click", async (e) => {
      e.preventDefault();
      const mealId = button.dataset.mealId;
      const mealName = button.dataset.mealName || "Meal";

      try {
        const formData = new FormData();
        formData.append("meal_id", mealId);
        formData.append("quantity", 1);

        const response = await fetch("/cart/add", {
          method: "POST",
          body: formData,
          headers: {
            "X-Requested-With": "XMLHttpRequest",
          },
        });

        const data = await response.json();

        if (response.status === 409) {
          // Restaurant conflict modal
          if (confirm(data.message)) {
            // User agreed to reset cart
            const clearForm = new FormData();
            await fetch("/cart/clear", { method: "POST", body: clearForm });
            // Add meal to new cart
            const retryRes = await fetch("/cart/add", {
              method: "POST",
              body: formData,
              headers: { "X-Requested-With": "XMLHttpRequest" }
            });
            const retryData = await retryRes.json();
            updateCartBadge(retryData.cart_count);
            showToast(`Started new order with ${mealName}!`, "success");
          }
          return;
        }

        if (data.success) {
          updateCartBadge(data.cart_count);
          showToast(data.message, "success");
        } else {
          showToast(data.message || "Failed to add item", "danger");
        }
      } catch (err) {
        console.error("Cart error:", err);
        showToast("Error updating cart.", "danger");
      }
    });
  });

  // Cart Page Quantity Controls (+ / -)
  document.querySelectorAll(".cart-qty-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const mealId = btn.dataset.mealId;
      const action = btn.dataset.action;
      const qtySpan = document.getElementById(`qty-${mealId}`);
      if (!qtySpan) return;

      let currentQty = parseInt(qtySpan.textContent);
      let newQty = action === "inc" ? currentQty + 1 : currentQty - 1;

      const formData = new FormData();
      formData.append("meal_id", mealId);
      formData.append("quantity", newQty);

      try {
        const res = await fetch("/cart/update", {
          method: "POST",
          body: formData,
          headers: { "X-Requested-With": "XMLHttpRequest" },
        });
        const data = await res.json();
        if (data.success) {
          window.location.reload(); // Reload to update totals cleanly
        }
      } catch (err) {
        console.error(err);
      }
    });
  });
}

function updateCartBadge(count) {
  const badge = document.querySelector(".cart-badge");
  if (badge) {
    badge.textContent = count;
    badge.style.display = count > 0 ? "inline-block" : "none";
  }
}

// --------------------------------------------------------------------------
// Modal Dialog Engine
// --------------------------------------------------------------------------
function initModals() {
  document.querySelectorAll("[data-modal-target]").forEach((trigger) => {
    trigger.addEventListener("click", () => {
      const targetId = trigger.dataset.modalTarget;
      const modal = document.getElementById(targetId);
      if (modal) {
        modal.classList.add("open");
      }
    });
  });

  document.querySelectorAll(".modal-close, .modal-backdrop").forEach((close) => {
    close.addEventListener("click", () => {
      const modal = close.closest(".modal-overlay");
      if (modal) {
        modal.classList.remove("open");
      }
    });
  });

  // Close modals on Escape key press
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.querySelectorAll(".modal-overlay.open").forEach((modal) => {
        modal.classList.remove("open");
      });
    }
  });
}
