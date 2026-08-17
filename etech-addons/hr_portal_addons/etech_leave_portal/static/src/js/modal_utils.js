/** @odoo-module **/

// Minimal, dependency-free modal show/hide helpers shared by the leave
// portal widgets. Deliberately do not rely on `window.bootstrap` or jQuery
// being available (or on their event-delegation kicking in for modals
// inserted into the DOM after page load) — that was silently breaking the
// close button and the calendar leave-details popup.

let dismissalBound = false;

function bindGlobalDismissal() {
    if (dismissalBound) {
        return;
    }
    dismissalBound = true;

    document.addEventListener("click", (ev) => {
        const dismissTrigger = ev.target.closest('[data-bs-dismiss="modal"]');
        if (dismissTrigger) {
            const modal = dismissTrigger.closest(".modal");
            if (modal) {
                hideModal(modal.id);
            }
            return;
        }
        // Click on the backdrop area of the modal itself (not its dialog content)
        if (ev.target.classList && ev.target.classList.contains("modal") && ev.target.classList.contains("show")) {
            hideModal(ev.target.id);
        }
    });

    document.addEventListener("keydown", (ev) => {
        if (ev.key === "Escape") {
            document.querySelectorAll(".modal.show").forEach((modal) => hideModal(modal.id));
        }
    });
}

export function showModal(modalId) {
    bindGlobalDismissal();
    const modalElement = document.getElementById(modalId);
    if (!modalElement) {
        return;
    }
    modalElement.classList.add("show");
    modalElement.style.display = "block";
    modalElement.removeAttribute("aria-hidden");
    modalElement.setAttribute("aria-modal", "true");
    document.body.classList.add("modal-open");

    if (!document.getElementById(modalId + "_backdrop")) {
        const backdrop = document.createElement("div");
        backdrop.id = modalId + "_backdrop";
        backdrop.className = "modal-backdrop fade show";
        document.body.appendChild(backdrop);
    }
}

export function hideModal(modalId) {
    const modalElement = document.getElementById(modalId);
    if (modalElement) {
        modalElement.classList.remove("show");
        modalElement.style.display = "none";
        modalElement.setAttribute("aria-hidden", "true");
        modalElement.removeAttribute("aria-modal");
    }
    document.body.classList.remove("modal-open");
    const backdrop = document.getElementById(modalId + "_backdrop");
    if (backdrop) {
        backdrop.remove();
    }
}
