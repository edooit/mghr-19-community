/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { showModal } from "./modal_utils";

publicWidget.registry.LeavePortalUnified = publicWidget.Widget.extend({
    selector: ".o_etech_leaves_portal",
    events: {
        "click #leave_balance": "_showLeaveBalanceModal",
    },

    start: function () {
        return this._super.apply(this, arguments).then(() => {
            this._createLeaveDetailsModal();
            const calendarEl = this.el.querySelector("#leave_calendar");
            if (calendarEl && calendarEl.offsetParent !== null) {
                this._initCalendar(calendarEl);
            }
        });
    },

    _showLeaveBalanceModal: function (ev) {
        ev.preventDefault();
        showModal("leaveBalanceModal");
    },

    _createLeaveDetailsModal: function () {
        const modalHTML = `
            <div class="modal fade" id="leaveDetailsModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content shadow-lg">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title"><i class="fa fa-calendar-check me-2"></i>Leave Details</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body p-4" id="leaveDetailsContent"></div>
                        <div class="modal-footer border-top-0" id="leaveDetailsActions"></div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML("beforeend", modalHTML);
    },

    _initCalendar: function (calendarEl) {
        if (typeof FullCalendar !== "undefined") {
            this._renderCalendar(calendarEl);
            return;
        }
        // The FullCalendar bundle (etech_leave_portal.assets_calendar) is
        // rendered inline by the template only on this view, right before
        // this widget starts; poll briefly in case script execution hasn't
        // finished registering the global yet.
        let attempts = 0;
        const interval = setInterval(() => {
            attempts += 1;
            if (typeof FullCalendar !== "undefined") {
                clearInterval(interval);
                this._renderCalendar(calendarEl);
            } else if (attempts >= 30) {
                clearInterval(interval);
                this._showCalendarError(calendarEl, "Calendar library failed to load");
            }
        }, 100);
    },

    _renderCalendar: function (calendarEl) {
        try {
            const loadingElement = calendarEl.querySelector(".calendar-loading");
            if (loadingElement) {
                loadingElement.style.display = "none";
            }
            const events = JSON.parse(calendarEl.getAttribute("data-events") || "[]");

            const calendar = new FullCalendar.Calendar(calendarEl, {
                initialView: "dayGridMonth",
                headerToolbar: { left: "prev,next today", center: "title", right: "dayGridMonth,dayGridWeek,dayGridDay" },
                events,
                height: "auto",
                contentHeight: 600,
                eventDisplay: "block",
                navLinks: true,
                dayMaxEvents: 3,
                eventClick: (info) => {
                    info.jsEvent.preventDefault();
                    this._showLeaveDetailsPopup(info.event);
                },
                eventDidMount: (info) => this._decorateEvent(info),
            });
            calendar.render();
            this.calendar = calendar;
        } catch (error) {
            this._showCalendarError(calendarEl, error.message);
        }
    },

    _showCalendarError: function (calendarEl, errorMessage) {
        const loadingElement = calendarEl.querySelector(".calendar-loading");
        if (loadingElement) {
            loadingElement.style.display = "none";
        }
        calendarEl.innerHTML = `
            <div class="alert alert-danger m-3">
                <i class="fa fa-exclamation-triangle me-2"></i>
                Unable to load the calendar view.
                ${errorMessage ? `<br/><small class="text-muted">${errorMessage}</small>` : ""}
                <br/>
                <a href="${window.location.pathname}?view_display=cards" class="btn btn-sm btn-outline-danger mt-2">
                    <i class="fa fa-th-large me-1"></i> Switch to Cards View
                </a>
            </div>
        `;
    },

    _decorateEvent: function (info) {
        // Fixed, tested colors — the bootstrap CSS custom properties
        // (var(--bs-info) etc.) used previously are not reliably defined on
        // this theme's compiled frontend CSS, which left events with a
        // transparent/white background under the forced white event text.
        const statusColors = {
            draft: "#6c757d", confirm: "#0dcaf0", validate1: "#f0ad4e",
            validate: "#198754", refuse: "#dc3545",
        };
        const color = statusColors[info.event.extendedProps.status];
        if (color) {
            info.el.style.backgroundColor = color;
            info.el.style.borderColor = color;
        }
        const { employee, type } = info.event.extendedProps;
        info.el.setAttribute("title", `${employee} - ${type}`);
    },

    _showLeaveDetailsPopup: function (event) {
        const data = event.extendedProps;
        document.getElementById("leaveDetailsContent").innerHTML = this._buildDetailsContent(event, data);
        document.getElementById("leaveDetailsActions").innerHTML = this._buildDetailsActions(event.id, data.status);
        showModal("leaveDetailsModal");
    },

    _buildDetailsContent: function (event, data) {
        const fmt = (d) => new Date(d).toLocaleDateString("fr-FR", { weekday: "long", year: "numeric", month: "long", day: "numeric" });
        const statusLabels = {
            draft: "Draft", confirm: "To Approve", validate1: "To Validate", validate: "Approved", refuse: "Refused",
        };
        return `
            <div class="d-flex align-items-center mb-3">
                <div class="o_etech_employee_avatar_lg bg-primary text-white me-3"><i class="fa fa-user"></i></div>
                <div>
                    <h5 class="mb-1">${data.employee || "Unknown"}</h5>
                    <span class="badge bg-secondary">${statusLabels[data.status] || data.status}</span>
                </div>
            </div>
            <div class="o_etech_leave_meta mb-3">
                <strong>${data.type || ""}</strong>
            </div>
            <div class="o_etech_leave_meta mb-2">
                <i class="fa fa-play-circle text-success me-2"></i>${fmt(event.start)}
            </div>
            <div class="o_etech_leave_meta">
                <i class="fa fa-stop-circle text-danger me-2"></i>${fmt(event.end)}
            </div>
            ${data.description ? `<div class="o_etech_leave_meta mt-3">${data.description}</div>` : ""}
        `;
    },

    _buildDetailsActions: function (leaveId, status) {
        const isTeamView = window.location.href.includes("team_leaves");
        const isMyView = window.location.href.includes("my_leaves");
        let actions = "";
        if (isTeamView && status === "confirm") {
            actions = `
                <a href="/confirm/${leaveId}" class="btn btn-success"><i class="fa fa-check me-1"></i>Approve</a>
                <a href="/refuse/${leaveId}" class="btn btn-outline-danger"><i class="fa fa-times me-1"></i>Refuse</a>
            `;
        } else if (isMyView && ["draft", "confirm"].includes(status)) {
            actions = `
                <a href="/my/leaves/edit/${leaveId}" class="btn btn-info"><i class="fa fa-edit me-1"></i>Edit</a>
                <a href="/leave/cancel/${leaveId}" class="btn btn-outline-danger"><i class="fa fa-trash me-1"></i>Cancel</a>
            `;
        }
        return `${actions}<button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Close</button>`;
    },
});
