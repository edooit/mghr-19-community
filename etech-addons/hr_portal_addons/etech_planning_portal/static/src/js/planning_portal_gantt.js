/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import {rpc} from "@web/core/network/rpc";
import {_t} from "@web/core/l10n/translation";

publicWidget.registry.PlanningPortalGantt = publicWidget.Widget.extend({
    selector: '#planning_gantt_container',
    events: {
        'click .gantt-prev-btn': '_onPreviousClick',
        'click .gantt-next-btn': '_onNextClick',
        'click .gantt-view-btn': '_onViewModeClick',
        'click .gantt-slot.editable': '_onSlotClick',
        'click .gantt-create-btn': '_onCreateClick',
        'click .gantt-search-btn': '_onSearchClick',
        'keypress .gantt-search-input': '_onSearchKeyPress',
        'click .gantt-close-modal': '_onCloseModal',
        'click .gantt-delete-btn': '_onDeleteClick',
        'focus .gantt-datetime-input': '_onDateTimeFocus',
        'submit .gantt-slot-form': '_onSlotFormSubmit',
    },

    init: function (parent, options) {
        this._super.apply(this, arguments);
        this.state = {
            slots: [],
            employees: [],
            filteredEmployees: [],
            currentDate: new Date(),
            viewMode: 'week',
            loading: false,
            isManager: false,
            currentEmployeeId: null,
            searchTerm: '',
            showModal: false,
            modalMode: 'create',
            currentSlot: null
        };
        this.searchTimeout = null;
        this.notificationContainer = null;
    },

    start: function () {
        this._createNotificationContainer();
        this._loadInitialData();
        return this._super.apply(this, arguments);
    },

    _createNotificationContainer: function () {
        this.notificationContainer = document.createElement('div');
        this.notificationContainer.className = 'gantt-notification-container';
        document.body.appendChild(this.notificationContainer);
    },

    _loadInitialData: async function () {
        this.state.loading = true;
        this._render();

        try {
            const startDate = this._getViewStartDate();
            const endDate = this._getViewEndDate();

            const data = await rpc('/my/planning/data', {
                start_date: startDate.toISOString().split('T')[0] + ' 00:00:00',
                end_date: endDate.toISOString().split('T')[0] + ' 23:59:59'
            });

            if (data.error) {
                this._showError(data.error);
                return;
            }

            this.state.slots = data.slots || [];
            this.state.isManager = data.is_manager || false;
            this.state.currentEmployeeId = data.current_employee_id;
            this.state.employees = await this._loadEmployees();

            this._sortEmployees();
            this.state.filteredEmployees = [...this.state.employees];

        } catch (error) {
            console.error('Error loading planning data:', error);
            this._showError(_t('Error loading data'));
        } finally {
            this.state.loading = false;
            this._render();
            setTimeout(() => this._initializeScrollSync(), 100);
        }
    },

    _loadEmployees: async function () {
        try {
            const employees = await rpc('/my/planning/employees');
            return employees || [];
        } catch (error) {
            console.error('Error loading employees:', error);
            return [];
        }
    },

    _sortEmployees: function () {
        if (!this.state.currentEmployeeId) return;

        this.state.employees.sort((a, b) => {
            if (a.id === this.state.currentEmployeeId) return -1;
            if (b.id === this.state.currentEmployeeId) return 1;
            return a.name.localeCompare(b.name);
        });
    },

    _render: function () {
        if (!this.$el) return;

        this.$el.html(this._generateGanttHTML());

        if (this.state.showModal) {
            setTimeout(() => this._initializeCustomDatePickers(), 100);
        }
    },

    _generateGanttHTML: function () {
        if (this.state.loading) {
            return `
                <div class="gantt-loading">
                    <div class="spinner-border text-primary" role="status">
                         <span class="visually-hidden">${_t('Loading...')}</span>
                    </div>
                    <div class="gantt-loading-text">${_t('Loading schedule...')}</div>
                </div>
            `;
        }

        return `
            <div class="gantt-container">
                <div class="gantt-header">
                    <div class="gantt-header-left">
                        <div class="gantt-navigation">
                            <button class="btn btn-light gantt-prev-btn">
                                <i class="fa fa-chevron-left"></i>
                            </button>
                            <span class="gantt-period-label">${this._getCurrentPeriodLabel()}</span>
                            <button class="btn btn-light gantt-next-btn">
                                <i class="fa fa-chevron-right"></i>
                            </button>
                        </div>
                        <div class="gantt-view-modes">
                            <button class="btn btn-sm gantt-view-btn ${this.state.viewMode === 'day' ? 'active' : ''}" data-mode="day">
                                 ${_t('Day')}
                            </button>
                            <button class="btn btn-sm gantt-view-btn ${this.state.viewMode === 'week' ? 'active' : ''}" data-mode="week">
                                  ${_t('Week')}
                            </button>
                            <button class="btn btn-sm gantt-view-btn ${this.state.viewMode === 'month' ? 'active' : ''}" data-mode="month">
                                 ${_t('Month')}
                            </button>
                        </div>
                    </div>
                    <div class="gantt-header-right">
                        <div class="gantt-search">
                             <div class="input-group">
                                <input type="text" class="form-control gantt-search-input"
                                       placeholder="${_t('Search by name or employee ID...')}"
                                       value="${this._escapeHtml(this.state.searchTerm)}">
                                <button class="btn btn-etech-outline gantt-search-btn" type="button">
                                    <i class="fa fa-search"></i>
                                </button>
                            </div>
                        </div>
                        ${this.state.isManager ? `
                           <button class="btn btn-etech-outline gantt-create-btn">
                                <i class="fa fa-plus"></i> ${_t('New Slot')}
                            </button>
                        ` : ''}
                    </div>
                </div>

                <!-- MAIN CONTAINER WITH VERTICAL SCROLL -->
                <div class="gantt-scroll-container">
                    <div class="gantt-body">
                        <div class="gantt-sidebar">
                            <div class="gantt-sidebar-header">
                                <div class="gantt-employee-info-header">${_t('Employee')}</div>
                               
                                <div class="gantt-employee-id-header d-none">${_t('Employee ID')}</div>
                            </div>
                            <div class="gantt-sidebar-content">
                                ${this._generateEmployeeList()}
                            </div>
                        </div>

                        <div class="gantt-timeline">
                            <div class="gantt-timeline-header">
                                <div class="gantt-timeline-header-inner">
                                    ${this._generateTimelineHeader()}
                                </div>
                            </div>
                            <div class="gantt-timeline-content">
                                <div class="gantt-timeline-content-inner">
                                    ${this._generateTimelineGrid()}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                ${this.state.showModal ? this._generateModal() : ''}

                <div class="custom-datepicker-overlay" style="display: none;">
                    <div class="custom-datepicker">
                        <div class="custom-datepicker-header">
                            <button class="custom-datepicker-prev"><i class="fa fa-chevron-left"></i></button>
                            <span class="custom-datepicker-title"></span>
                            <button class="custom-datepicker-next"><i class="fa fa-chevron-right"></i></button>
                        </div>
                        <div class="custom-datepicker-body">
                            <div class="custom-datepicker-calendar"></div>
                            <div class="custom-datepicker-time">
                                <div class="custom-time-label">${_t('Time:')}</div>
                                <input type="time" class="custom-time-input">
                            </div>
                        </div>
                        <div class="custom-datepicker-footer">
                            <button class="btn btn-etech-outline custom-datepicker-cancel">${_t('Cancel')}</button>
                            <button class="btn btn-etech-outline custom-datepicker-apply">${_t('Apply')}</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    _generateEmployeeList: function () {
        if (this.state.filteredEmployees.length === 0) {
            return `<div class="gantt-no-data">${_t('No employees found')}</div>`;
        }

        return this.state.filteredEmployees.map(employee => {
            const isCurrentUser = employee.id === this.state.currentEmployeeId;
            const name = this._escapeHtml(employee.name);
            const registrationNumber = this._escapeHtml(employee.registration_number || 'N/A');
            return `
                <div class="gantt-employee-row ${isCurrentUser ? 'gantt-current-user' : ''}"
                     data-employee-id="${employee.id}">
                    <div class="gantt-employee-info">
                        <img src="/web/image/hr.employee/${employee.id}/image_128"
                             class="gantt-employee-avatar"
                             alt="${name}"
                             onerror="this.style.display='none'">
                        <div class="gantt-employee-details">
                            <div class="gantt-employee-name">
                                ${name}
                                ${isCurrentUser ? `<span class="gantt-current-badge">${_t('You')}</span>` : ''}
                            </div>
                            <div class="gantt-employee-id">${registrationNumber}</div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    },

    _escapeHtml: function (value) {
        const div = document.createElement('div');
        div.textContent = value == null ? '' : String(value);
        return div.innerHTML;
    },

    _generateTimelineHeader: function () {
        const dates = this._getTimelineDates();
        return dates.map(date => `
            <div class="gantt-timeline-header-cell ${this._isToday(date) ? 'gantt-today' : ''}">
                <div class="gantt-date-day">${date.toLocaleDateString('fr-FR', {weekday: 'short'})}</div>
                <div class="gantt-date-number">${date.getDate()}</div>
                <div class="gantt-date-month">${date.toLocaleDateString('fr-FR', {month: 'short'})}</div>
            </div>
        `).join('');
    },

    _generateTimelineGrid: function () {
        const dates = this._getTimelineDates();
        return this.state.filteredEmployees.map(employee => {
            const employeeSlots = this.state.slots.filter(slot => slot.employee_id === employee.id);

            return `
                <div class="gantt-timeline-row" data-employee-id="${employee.id}">
                    ${dates.map((date, index) => {
                const daySlots = this._getSlotsForDay(employeeSlots, date);
                return `
                            <div class="gantt-timeline-cell ${this._isToday(date) ? 'gantt-today' : ''}" 
                                 data-date="${date.toISOString().split('T')[0]}"
                                 data-column="${index}">
                                ${this._generateCellSlots(daySlots, date)}
                            </div>
                        `;
            }).join('')}
                </div>
            `;
        }).join('');
    },

    _getSlotsForDay: function (slots, date) {
        const dayStart = new Date(date);
        dayStart.setHours(0, 0, 0, 0);
        const dayEnd = new Date(date);
        dayEnd.setHours(23, 59, 59, 999);

        return slots.filter(slot => {
            const slotStart = new Date(slot.start_datetime);
            const slotEnd = new Date(slot.end_datetime);

            return slotStart <= dayEnd && slotEnd >= dayStart;
        });
    },

    _generateCellSlots: function (slots, date) {
        if (slots.length === 0) return '';

        const dayStart = new Date(date);
        dayStart.setHours(0, 0, 0, 0);
        const dayEnd = new Date(date);
        dayEnd.setHours(23, 59, 59, 999);

        return slots.map((slot, index) => {
            const slotStart = new Date(slot.start_datetime + 'Z');
            const slotEnd = new Date(slot.end_datetime + 'Z');

            const canEdit = this._canEditSlot(slot);
            const slotClass = canEdit ? 'gantt-slot editable' : 'gantt-slot readonly';
            const backgroundColor = this._getEmployeeColor(slot.employee_id);

            const slotStartDay = new Date(slotStart.getFullYear(), slotStart.getMonth(), slotStart.getDate());
            const slotEndDay = new Date(slotEnd.getFullYear(), slotEnd.getMonth(), slotEnd.getDate());
            const currentDay = new Date(date.getFullYear(), date.getMonth(), date.getDate());

            const isFirstDay = slotStartDay.getTime() === currentDay.getTime();
            const isLastDay = slotEndDay.getTime() === currentDay.getTime();
            const isMiddleDay = slotStartDay < currentDay && slotEndDay > currentDay;

            let displayText = '';
            if (isFirstDay && isLastDay) {
                displayText = `${this._formatTime(slot.start_datetime)} - ${this._formatTime(slot.end_datetime)}`;
            } else if (isFirstDay) {
                displayText = `${this._formatTime(slot.start_datetime)} →`;
            } else if (isLastDay) {
                displayText = `← ${this._formatTime(slot.end_datetime)}`;
            } else if (isMiddleDay) {
                displayText = `→ →`;
            }

            return `
                <div class="${slotClass}" 
                     data-slot-id="${slot.id}"
                     style="top: ${10 + (index * 35)}px; background-color: ${backgroundColor};"
                     title="${this._formatTime(slot.start_datetime)} - ${this._formatTime(slot.end_datetime)}">
                    <div class="gantt-slot-content">
                        <div class="gantt-slot-times">${displayText}</div>
                    </div>
                </div>
            `;
        }).join('');
    },

    _generateModal: function () {
        const isEdit = this.state.modalMode === 'edit';
        const slot = this.state.currentSlot;

        const startDateValue = slot ? this._formatDateForInput(slot.start_datetime) : '';
        const endDateValue = slot ? this._formatDateForInput(slot.end_datetime) : '';

        return `
        <div class="gantt-modal-overlay">
            <div class="gantt-modal">
                <div class="gantt-modal-header">
                    <h5 class="gantt-modal-title">
                        <i class="fa fa-${isEdit ? 'edit' : 'plus'} me-2"></i>
                        ${isEdit ? _t('Edit Time Slot') : _t('Create Time Slot')}
                    </h5>
                    <button type="button" class="btn-close gantt-close-modal"></button>
                </div>
                <div class="gantt-modal-body">
                    <form class="gantt-slot-form">
                        <div class="mb-3">
                            <label class="form-label required">${_t('Employee')}</label>
                            <select class="form-select gantt-employee-select" name="employee_id" ${isEdit ? 'disabled' : ''} ${isEdit ? '' : 'required'}>
                                <option value="">${_t('Select an employee')}</option>
                                ${this.state.employees.map(emp => `
                                    <option value="${emp.id}" ${slot && slot.employee_id === emp.id ? 'selected' : ''}>
                                        ${this._escapeHtml(emp.name)} (${this._escapeHtml(emp.registration_number || _t('N/A'))})
                                    </option>
                                `).join('')}
                            </select>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label required">${_t('Start Date and Time')}</label>
                                    <input type="text" 
                                           class="form-control gantt-datetime-input gantt-start-datetime" 
                                           name="start_datetime" 
                                           required
                                           placeholder="${_t('dd/mm/yyyy hh:mm')}"
                                           value="${startDateValue}">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label required">${_t('End Date and Time')}</label>
                                    <input type="text" 
                                           class="form-control gantt-datetime-input gantt-end-datetime" 
                                           name="end_datetime" 
                                           required
                                           placeholder="${_t('dd/mm/yyyy hh:mm')}"
                                           value="${endDateValue}">
                                </div>
                            </div>
                        </div>
                        <div class="gantt-modal-actions">
                            ${isEdit ? `
                                <button type="button" class="btn btn-etech-outline-danger gantt-delete-btn">
                                    <i class="fa fa-trash me-1"></i>${_t('Delete')}
                                </button>
                            ` : ''}
                            <div class="gantt-modal-actions-right">
                                <button type="button" class="btn btn-etech-outline gantt-close-modal">
                                    <i class="fa fa-times me-1"></i>${_t('Cancel')}
                                </button>
                                <button type="submit" class="btn btn-etech-outline">
                                    <i class="fa fa-${isEdit ? 'check' : 'plus'} me-1"></i>
                                    ${isEdit ? _t('Update') : _t('Create')}
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    },

    _initializeCustomDatePickers: function () {
        const startInput = this.$el.find('.gantt-start-datetime')[0];
        const endInput = this.$el.find('.gantt-end-datetime')[0];

        if (startInput) {
            startInput.addEventListener('focus', () => this._showCustomDatePicker(startInput));
        }

        if (endInput) {
            endInput.addEventListener('focus', () => this._showCustomDatePicker(endInput));
        }
    },

    _showCustomDatePicker: function (input) {
        const overlay = this.$el.find('.custom-datepicker-overlay')[0];
        const currentValue = input.value;

        let currentDate = new Date();
        if (currentValue) {
            const parsedDate = this._parseDate(currentValue);
            if (!isNaN(parsedDate.getTime())) {
                currentDate = parsedDate;
            }
        }

        this._renderCustomDatePicker(currentDate, input);
        overlay.style.display = 'flex';
        this.currentDateInput = input;
    },

    _renderCustomDatePicker: function (date, input) {
        const calendarEl = this.$el.find('.custom-datepicker-calendar')[0];
        const titleEl = this.$el.find('.custom-datepicker-title')[0];
        const timeInput = this.$el.find('.custom-time-input')[0];

        if (!calendarEl || !titleEl || !timeInput) return;

        titleEl.textContent = date.toLocaleDateString('fr-FR', {
            month: 'long',
            year: 'numeric'
        });

        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        timeInput.value = `${hours}:${minutes}`;

        this._renderCalendar(calendarEl, date);
        this._setupDatePickerEvents(date, input);
    },

    _renderCalendar: function (container, date) {
        const year = date.getFullYear();
        const month = date.getMonth();

        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const daysInMonth = lastDay.getDate();

        let html = '<div class="custom-datepicker-weekdays">';
        const weekdays = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];
        weekdays.forEach(day => {
            html += `<div class="custom-datepicker-weekday">${day}</div>`;
        });
        html += '</div><div class="custom-datepicker-days">';

        for (let i = 0; i < firstDay.getDay(); i++) {
            html += '<div class="custom-datepicker-day empty"></div>';
        }

        for (let day = 1; day <= daysInMonth; day++) {
            const dayDate = new Date(year, month, day);
            const isToday = new Date().toDateString() === dayDate.toDateString();
            const isSelected = date.getDate() === day;
            const dayClass = `custom-datepicker-day ${isToday ? 'today' : ''} ${isSelected ? 'selected' : ''}`;
            html += `<div class="${dayClass}" data-day="${day}">${day}</div>`;
        }

        html += '</div>';
        container.innerHTML = html;
    },

    _setupDatePickerEvents: function (currentDate, input) {
        const overlay = this.$el.find('.custom-datepicker-overlay')[0];
        const prevBtn = this.$el.find('.custom-datepicker-prev')[0];
        const nextBtn = this.$el.find('.custom-datepicker-next')[0];
        const cancelBtn = this.$el.find('.custom-datepicker-cancel')[0];
        const applyBtn = this.$el.find('.custom-datepicker-apply')[0];
        const timeInput = this.$el.find('.custom-time-input')[0];

        let selectedDate = new Date(currentDate);

        prevBtn.onclick = () => {
            selectedDate.setMonth(selectedDate.getMonth() - 1);
            this._renderCustomDatePicker(selectedDate, input);
        };

        nextBtn.onclick = () => {
            selectedDate.setMonth(selectedDate.getMonth() + 1);
            this._renderCustomDatePicker(selectedDate, input);
        };

        const dayElements = this.$el.find('.custom-datepicker-day');
        dayElements.each((index, dayEl) => {
            const day = dayEl.dataset.day;
            if (day) {
                dayEl.onclick = () => {
                    this.$el.find('.custom-datepicker-day.selected').removeClass('selected');
                    $(dayEl).addClass('selected');
                    selectedDate.setDate(parseInt(day));
                };
            }
        });

        applyBtn.onclick = () => {
            const [hours, minutes] = timeInput.value.split(':');
            selectedDate.setHours(parseInt(hours), parseInt(minutes));

            const formattedDate = this._formatDateForInput(selectedDate);
            input.value = formattedDate;
            overlay.style.display = 'none';
        };

        cancelBtn.onclick = () => {
            overlay.style.display = 'none';
        };

        overlay.onclick = (e) => {
            if (e.target === overlay) {
                overlay.style.display = 'none';
            }
        };
    },

    _getEmployeeColor: function (employeeId) {
        const colors = [
            '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
            '#1abc9c', '#d35400', '#c0392b', '#16a085', '#8e44ad',
            '#27ae60', '#2980b9', '#8e44ad', '#2c3e50', '#f1c40f'
        ];
        return colors[employeeId % colors.length] || '#95a5a6';
    },

    _getTimelineDates: function () {
        const startDate = this._getViewStartDate();
        const dates = [];
        const count = this.state.viewMode === 'day' ? 1 : this.state.viewMode === 'week' ? 7 : 30;

        for (let i = 0; i < count; i++) {
            const date = new Date(startDate);
            date.setDate(startDate.getDate() + i);
            dates.push(date);
        }

        return dates;
    },

    _isToday: function (date) {
        const today = new Date();
        return date.toDateString() === today.toDateString();
    },

    _getViewStartDate: function () {
        const date = new Date(this.state.currentDate);
        switch (this.state.viewMode) {
            case 'day':
                return date;
            case 'week':
                const day = date.getDay();
                const diff = date.getDate() - day + (day === 0 ? -6 : 1);
                return new Date(date.setDate(diff));
            case 'month':
                return new Date(date.getFullYear(), date.getMonth(), 1);
            default:
                return date;
        }
    },

    _getViewEndDate: function () {
        const date = new Date(this.state.currentDate);
        switch (this.state.viewMode) {
            case 'day':
                return new Date(date.setDate(date.getDate() + 1));
            case 'week':
                return new Date(date.setDate(date.getDate() + 7));
            case 'month':
                return new Date(date.getFullYear(), date.getMonth() + 1, 0);
            default:
                return new Date(date.setDate(date.getDate() + 1));
        }
    },

    _getCurrentPeriodLabel: function () {
        const startDate = this._getViewStartDate();
        const userLang = navigator.language || 'fr-FR';

        switch (this.state.viewMode) {
            case 'day':
                return startDate.toLocaleDateString(userLang, {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });
            case 'week':
                const endDate = new Date(startDate);
                endDate.setDate(startDate.getDate() + 6);
                return _t('Week from %s to %s',
                    startDate.toLocaleDateString(userLang),
                    endDate.toLocaleDateString(userLang));
            case 'month':
                return startDate.toLocaleDateString(userLang, {
                    year: 'numeric',
                    month: 'long'
                });
            default:
                return startDate.toLocaleDateString(userLang);
        }
    },

    _formatTime: function (datetimeStr) {
        const date = new Date(datetimeStr);
        const userLang = navigator.language || 'fr-FR';
        return date.toLocaleTimeString(userLang, {
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    _formatDateForInput: function (datetimeStr) {
        let date;
        if (typeof datetimeStr === 'string') {
            date = new Date(datetimeStr);
        } else {
            date = datetimeStr;
        }
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');

        return `${day}/${month}/${year} ${hours}:${minutes}`;
    },

    _parseDate: function (dateString) {
        try {
            const [datePart, timePart] = dateString.split(' ');
            if (!datePart || !timePart) {
                throw new Error('Invalid format');
            }

            const [day, month, year] = datePart.split('/');
            const [hours, minutes] = timePart.split(':');

            const date = new Date(year, month - 1, day, hours, minutes);

            if (isNaN(date.getTime())) {
                throw new Error('Invalid date');
            }

            return date;
        } catch (error) {
            console.error('Error parsing date:', error, dateString);
            return new Date(NaN);
        }
    },

    _formatDateForOdoo: function (date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');

        const formatted = `${year}-${month}-${day} ${hours}:${minutes}:00`;

        return formatted;
    },

    _canEditSlot: function (slot) {
        if (!this.state.isManager) return false;
        return true;
    },

    _filterEmployees: function () {
        const term = this.state.searchTerm.toLowerCase();
        if (!term) {
            this.state.filteredEmployees = [...this.state.employees];
            return;
        }

        this.state.filteredEmployees = this.state.employees.filter(employee =>
            employee.name.toLowerCase().includes(term) ||
            (employee.registration_number && employee.registration_number.toLowerCase().includes(term))
        );
    },

    _showNotification: function (message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `gantt-notification gantt-notification-${type}`;
        notification.innerHTML = `
            <div class="gantt-notification-content">
                <i class="fa fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation-triangle' : 'info'}-circle"></i>
                <span>${message}</span>
            </div>
        `;

        this.notificationContainer.appendChild(notification);

        setTimeout(() => {
            notification.classList.add('gantt-notification-show');
        }, 10);

        setTimeout(() => {
            notification.classList.remove('gantt-notification-show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
    },

    _showError: function (message) {
        this._showNotification(_t(message), 'error');
    },

    _showSuccess: function (message) {
        this._showNotification(_t(message), 'success');
    },

    _onPreviousClick: function (ev) {
        ev.preventDefault();
        const date = new Date(this.state.currentDate);
        switch (this.state.viewMode) {
            case 'day':
                date.setDate(date.getDate() - 1);
                break;
            case 'week':
                date.setDate(date.getDate() - 7);
                break;
            case 'month':
                date.setMonth(date.getMonth() - 1);
                break;
        }
        this.state.currentDate = date;
        this._refreshData();
    },

    _onNextClick: function (ev) {
        ev.preventDefault();
        const date = new Date(this.state.currentDate);
        switch (this.state.viewMode) {
            case 'day':
                date.setDate(date.getDate() + 1);
                break;
            case 'week':
                date.setDate(date.getDate() + 7);
                break;
            case 'month':
                date.setMonth(date.getMonth() + 1);
                break;
        }
        this.state.currentDate = date;
        this._refreshData();
    },

    _onViewModeClick: function (ev) {
        ev.preventDefault();
        const mode = ev.currentTarget.dataset.mode;
        this.state.viewMode = mode;
        this._refreshData();
    },

    _onSlotClick: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const slotId = ev.currentTarget.dataset.slotId;
        const slot = this.state.slots.find(s => s.id === parseInt(slotId));

        if (slot && this._canEditSlot(slot)) {
            this.state.modalMode = 'edit';
            this.state.currentSlot = slot;
            this.state.showModal = true;
            this._render();
        }
    },

    _onCreateClick: function (ev) {
        ev.preventDefault();
        this.state.modalMode = 'create';
        this.state.currentSlot = null;
        this.state.showModal = true;
        this._render();
    },

    _onSearchClick: function (ev) {
        ev.preventDefault();
        const searchInput = this.$el.find('.gantt-search-input')[0];
        this.state.searchTerm = searchInput.value;
        this._filterEmployees();
        this._render();
    },

    _onSearchKeyPress: function (ev) {
        if (ev.key === 'Enter' || ev.keyCode === 13) {
            ev.preventDefault();
            this.state.searchTerm = ev.target.value;
            this._filterEmployees();
            this._render();
        }
    },

    _onDateTimeFocus: function (ev) {
        ev.preventDefault();
        this._showCustomDatePicker(ev.target);
    },

    _onSlotFormSubmit: async function (ev) {
        ev.preventDefault();

        const form = ev.target;
        const formData = new FormData(form);

        const employeeSelect = form.querySelector('.gantt-employee-select');
        const employeeId = employeeSelect.value || (employeeSelect.disabled ? employeeSelect.options[employeeSelect.selectedIndex]?.value : null);

        const startDatetime = formData.get('start_datetime');
        const endDatetime = formData.get('end_datetime');

        if (!employeeId) {
            this._showError(_t('Please select an employee'));
            return;
        }

        if (!startDatetime || !endDatetime) {
            this._showError(_t('Please fill in both start and end dates'));
            return;
        }

        try {
            const startDate = this._parseDate(startDatetime);
            const endDate = this._parseDate(endDatetime);

            if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
                this._showError(_t('Invalid date format. Use dd/mm/yyyy hh:mm format'));
                return;
            }

            if (endDate <= startDate) {
                this._showError(_t('End date must be after start date'));
                return;
            }

            const data = {
                employee_id: parseInt(employeeId),
                start_datetime: this._formatDateForOdoo(startDate),
                end_datetime: this._formatDateForOdoo(endDate),
            };

            let result;
            if (this.state.modalMode === 'create') {
                result = await rpc('/my/planning/slot/create', data);
            } else {
                result = await rpc('/my/planning/slot/update', {
                    slot_id: this.state.currentSlot.id,
                    ...data
                });
            }

            if (result.success) {
                this.state.showModal = false;
                this._showSuccess(this.state.modalMode === 'create' ?
                    _t('Time slot created successfully') :
                    _t('Time slot updated successfully'));
                await this._refreshData();
            } else {
                this._showError(result.error || _t('Error saving data'));
            }
        } catch (error) {
            console.error('Error saving slot:', error);
            this._showError(_t('Error saving time slot'));
        }
    },

    _onDeleteClick: async function (ev) {
        ev.preventDefault();

        const confirmed = await this._showConfirmationModal(
            _t('Delete Confirmation'),
            _t('Are you sure you want to delete this time slot?')
        );

        if (!confirmed) return;

        try {
            const result = await rpc('/my/planning/slot/delete', {
                slot_id: this.state.currentSlot.id
            });

            if (result.success) {
                this.state.showModal = false;
                this._showSuccess(_t('Time slot deleted successfully'));
                await this._refreshData();
            } else {
                this._showError(result.error);
            }
        } catch (error) {
            console.error('Error deleting slot:', error);
            this._showError(_t('Error deleting time slot'));
        }
    },

    _onCloseModal: function (ev) {
        ev.preventDefault();
        this.state.showModal = false;
        this._render();
    },

    _refreshData: async function () {
        await this._loadInitialData();
    },

    _showConfirmationModal: function (title, message) {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'gantt-confirmation-modal-overlay';
            modal.innerHTML = `
                <div class="gantt-confirmation-modal">
                    <div class="gantt-confirmation-header">
                        <h5>${title}</h5>
                    </div>
                    <div class="gantt-confirmation-body">
                        <p>${message}</p>
                    </div>
                    <div class="gantt-confirmation-actions">
                        <button class="btn btn-etech-outline gantt-confirmation-cancel">${_t('Cancel')}</button>
                        <button class="btn btn-etech-outline-danger gantt-confirmation-confirm">${_t('Confirm')}</button>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            const cancelBtn = modal.querySelector('.gantt-confirmation-cancel');
            const confirmBtn = modal.querySelector('.gantt-confirmation-confirm');

            const cleanup = () => {
                if (modal.parentNode) {
                    modal.parentNode.removeChild(modal);
                }
            };

            cancelBtn.onclick = () => {
                cleanup();
                resolve(false);
            };

            confirmBtn.onclick = () => {
                cleanup();
                resolve(true);
            };

            modal.onclick = (e) => {
                if (e.target === modal) {
                    cleanup();
                    resolve(false);
                }
            };
        });
    },

    _initializeScrollSync: function () {
        const scrollContainer = this.$el.find('.gantt-scroll-container')[0];
        const sidebarContent = this.$el.find('.gantt-sidebar-content')[0];
        const timelineContent = this.$el.find('.gantt-timeline-content')[0];
        const timelineHeader = this.$el.find('.gantt-timeline-header')[0];

        if (!scrollContainer || !sidebarContent || !timelineContent || !timelineHeader) return;

        // VERTICAL scroll synchronization
        scrollContainer.addEventListener('scroll', () => {
            const scrollTop = scrollContainer.scrollTop;

            // Sync both contents with main VERTICAL scroll
            sidebarContent.scrollTop = scrollTop;
            timelineContent.scrollTop = scrollTop;
        });

        // HORIZONTAL scroll synchronization
        timelineContent.addEventListener('scroll', () => {
            const scrollLeft = timelineContent.scrollLeft;

            // Sync header with timeline horizontal scroll
            timelineHeader.scrollLeft = scrollLeft;
        });

        // Adjust widths for horizontal scroll to work
        setTimeout(() => {
            const dates = this._getTimelineDates();
            const totalWidth = dates.length * 140; // 140px per column

            // Adjust timeline content width
            const timelineContentInner = this.$el.find('.gantt-timeline-content-inner')[0];
            const timelineHeaderInner = this.$el.find('.gantt-timeline-header-inner')[0];

            if (timelineContentInner) {
                timelineContentInner.style.minWidth = totalWidth + 'px';
            }
            if (timelineHeaderInner) {
                timelineHeaderInner.style.minWidth = totalWidth + 'px';
            }
        }, 100);
    }

});
