/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { showModal } from "./modal_utils";

// Shared widget for both the "create leave" and "edit leave" portal forms —
// same fields, same behavior, only the container class differs.
publicWidget.registry.LeaveFormPortal = publicWidget.Widget.extend({
    selector: ".o_portal_create_leave, .o_portal_edit_leave",
    events: {
        "change #half_day": "_onHalfDayChange",
        "change #leave_type": "_onLeaveTypeChange",
        "change #emp_name": "_onEmployeeChange",
        "change #start_date": "_onDateChange",
        "change #end_date": "_onDateChange",
    },

    start: function () {
        return this._super.apply(this, arguments).then(() => {
            this._onHalfDayChange();
            this._onLeaveTypeChange();
            this._showErrorModalIfAny();
            this._disableFormIfReadOnly();
            const defaultEmployee = this.$("#emp_name").val();
            if (defaultEmployee) {
                this._updateBalance(defaultEmployee);
            }
        });
    },

    _disableFormIfReadOnly: function () {
        const submitButton = this.$('button[type="submit"]');
        if (submitButton.length && submitButton.prop("disabled")) {
            this.$("input, select, textarea").not("button").prop("disabled", true);
            this.$(".form-control, .form-select").addClass("bg-light");
        }
    },

    _onHalfDayChange: function () {
        const isHalfDay = this.$("#half_day").is(":checked");
        const halfDayOptions = this.$("#half_day_options");
        const endDateInput = this.$("#end_date");
        const endDateWrapper = this.$("#div_end_date");

        if (isHalfDay) {
            halfDayOptions.slideDown(200);
            const startDate = this.$("#start_date").val();
            if (startDate) {
                endDateInput.val(startDate);
            }
            endDateInput.prop("disabled", true).prop("required", false);
            endDateWrapper.addClass("d-none");
        } else {
            halfDayOptions.slideUp(200);
            endDateInput.prop("disabled", false).prop("required", true);
            endDateWrapper.removeClass("d-none");
        }
    },

    _onLeaveTypeChange: function () {
        const requiresDocument = this.$("#leave_type option:selected").data("support-document");
        const attachmentsSection = this.$("#attachments_section");
        const attachmentInput = this.$("#attachment");

        if (requiresDocument) {
            attachmentsSection.slideDown(200);
            attachmentInput.prop("required", true);
        } else {
            attachmentsSection.slideUp(200);
            attachmentInput.prop("required", false);
        }
    },

    _onEmployeeChange: function () {
        const employeeId = this.$("#emp_name").val();
        if (employeeId) {
            this._updateBalance(employeeId);
        }
    },

    _onDateChange: function (ev) {
        const isHalfDay = this.$("#half_day").is(":checked");
        if (!isHalfDay) {
            return;
        }
        const startDate = this.$("#start_date").val();
        if (startDate) {
            this.$("#end_date").val(startDate);
        }
    },

    _updateBalance: function (employeeId) {
        rpc("/get_leave_details", { employee_id: employeeId })
            .then((result) => this._displayBalance(result || {}))
            .catch(() => this._displayBalance({}));
    },

    _displayBalance: function (balanceData) {
        const balance = Number(balanceData.leave_balance) || 0;
        const taken = Number(balanceData.leave_taken) || 0;
        const allocations = Number(balanceData.leave_allocations) || 0;

        this.$el.find("#leave-balance").text(balance.toFixed(2));
        this.$el.find("#total-balance").text(balance.toFixed(2));
        this.$el.find("#leave-taken").text(taken.toFixed(2));
        this.$el.find("#total-sold").text(allocations.toFixed(2));

        const balanceCircle = this.$el.find(".o_etech_balance_circle");
        balanceCircle.addClass("is-pulsing");
        setTimeout(() => balanceCircle.removeClass("is-pulsing"), 600);
    },

    _showErrorModalIfAny: function () {
        if (this.$("#errorModal").length) {
            showModal("errorModal");
        }
    },
});
