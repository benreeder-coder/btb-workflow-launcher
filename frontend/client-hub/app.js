/**
 * Client Hub - Task Management System
 * Main JavaScript controller
 */

const ClientHub = (function() {
    // ==================== CONFIG ====================
    const API_BASE = window.location.origin;

    // ==================== STATE ====================
    let state = {
        currentView: 'today',
        clients: [],
        settings: null,
        loading: false,
        modalMode: 'create', // 'create' or 'edit'
        editingTaskId: null,
        // Filter state
        filters: {
            priority: '',
            status: '',
            client_id: '',
            search: ''
        }
    };

    // ==================== ICONS ====================
    const icons = {
        today: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
        inbox: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>`,
        pending: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
        overdue: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
        upcoming: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`,
        completed: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
        clients: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
        calendar: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`,
        settings: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`,
        plus: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`,
        check: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>`,
        clock: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
        close: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`,
        flag: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>`,
        user: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
        morning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`,
        afternoon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>`,
        evening: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`,
        chevron: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>`,
        workflows: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="6" height="6" rx="1"/><rect x="15" y="3" width="6" height="6" rx="1"/><rect x="9" y="15" width="6" height="6" rx="1"/><line x1="6" y1="9" x2="6" y2="12"/><line x1="6" y1="12" x2="12" y2="12"/><line x1="12" y1="12" x2="12" y2="15"/><line x1="18" y1="9" x2="18" y2="12"/><line x1="18" y1="12" x2="12" y2="12"/></svg>`,
    };

    // ==================== UTILITY FUNCTIONS ====================
    // Get local date string in YYYY-MM-DD format (avoids UTC conversion issues)
    function getLocalDateString(date) {
        const d = new Date(date);
        return d.getFullYear() + '-' +
               String(d.getMonth() + 1).padStart(2, '0') + '-' +
               String(d.getDate()).padStart(2, '0');
    }

    // ==================== INITIALIZATION ====================
    function init() {
        renderSidebar();
        renderTaskModal();
        loadSettings();
        loadClients();
        navigateTo('today');
        setupEventListeners();
    }

    function setupEventListeners() {
        // Close modal on overlay click
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('task-modal-overlay')) {
                closeTaskModal();
            }
        });

        // Close modal on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeTaskModal();
            }
        });

        // Status change shows/hides pending fields
        document.addEventListener('change', (e) => {
            if (e.target.id === 'task-status') {
                const pendingFields = document.getElementById('pending-fields');
                if (pendingFields) {
                    pendingFields.classList.toggle('show', e.target.value === 'PENDING');
                }
            }
        });
    }

    // ==================== TASK MODAL ====================
    function renderTaskModal() {
        // Check if modal already exists
        if (document.getElementById('task-modal-overlay')) return;

        const modalHtml = `
            <div id="task-modal-overlay" class="task-modal-overlay">
                <div class="task-modal">
                    <div class="task-modal-header">
                        <h2 class="task-modal-title" id="task-modal-title">Add New Task</h2>
                        <button class="task-modal-close" onclick="ClientHub.closeTaskModal()">
                            ${icons.close}
                        </button>
                    </div>
                    <form id="task-form" onsubmit="ClientHub.handleTaskSubmit(event)">
                        <div class="task-modal-body">
                            <div class="task-form-group">
                                <label class="task-form-label">
                                    Title <span class="required">*</span>
                                </label>
                                <input type="text" id="task-title" class="task-form-input" placeholder="What needs to be done?" required />
                            </div>

                            <div class="task-form-group">
                                <label class="task-form-label">Description</label>
                                <textarea id="task-description" class="task-form-textarea" placeholder="Add more details..."></textarea>
                            </div>

                            <div class="task-form-row">
                                <div class="task-form-group">
                                    <label class="task-form-label">Client</label>
                                    <select id="task-client" class="task-form-select">
                                        <option value="">No client</option>
                                    </select>
                                </div>
                                <div class="task-form-group">
                                    <label class="task-form-label">Priority</label>
                                    <select id="task-priority" class="task-form-select">
                                        <option value="P0">P0 - Urgent</option>
                                        <option value="P1">P1 - High</option>
                                        <option value="P2" selected>P2 - Normal</option>
                                        <option value="P3">P3 - Low</option>
                                    </select>
                                </div>
                            </div>

                            <div class="task-form-row">
                                <div class="task-form-group">
                                    <label class="task-form-label">Due Date</label>
                                    <input type="date" id="task-due-date" class="task-form-input" />
                                </div>
                                <div class="task-form-group">
                                    <label class="task-form-label">Due Time</label>
                                    <input type="time" id="task-due-time" class="task-form-input" />
                                </div>
                            </div>

                            <div class="task-form-row-3">
                                <div class="task-form-group">
                                    <label class="task-form-label">Status</label>
                                    <select id="task-status" class="task-form-select">
                                        <option value="NOT_STARTED" selected>Not Started</option>
                                        <option value="IN_PROGRESS">In Progress</option>
                                        <option value="PENDING">Pending/Blocked</option>
                                        <option value="COMPLETED">Completed</option>
                                    </select>
                                </div>
                                <div class="task-form-group">
                                    <label class="task-form-label">Timebox</label>
                                    <select id="task-timebox" class="task-form-select">
                                        <option value="NONE" selected>None</option>
                                        <option value="MORNING">Morning</option>
                                        <option value="AFTERNOON">Afternoon</option>
                                        <option value="EVENING">Evening</option>
                                    </select>
                                </div>
                                <div class="task-form-group">
                                    <label class="task-form-label">Est. Time</label>
                                    <select id="task-estimated" class="task-form-select">
                                        <option value="">Not set</option>
                                        <option value="15">15 min</option>
                                        <option value="30">30 min</option>
                                        <option value="45">45 min</option>
                                        <option value="60">1 hour</option>
                                        <option value="90">1.5 hours</option>
                                        <option value="120">2 hours</option>
                                        <option value="180">3 hours</option>
                                        <option value="240">4 hours</option>
                                    </select>
                                </div>
                            </div>

                            <div id="pending-fields" class="pending-fields">
                                <div class="task-form-group" style="margin-bottom: 0.75rem;">
                                    <label class="task-form-label">Waiting On</label>
                                    <input type="text" id="task-waiting-on" class="task-form-input" placeholder="Who/what are you waiting on?" />
                                </div>
                                <div class="task-form-group" style="margin-bottom: 0;">
                                    <label class="task-form-label">Blocked Reason</label>
                                    <input type="text" id="task-blocked-reason" class="task-form-input" placeholder="Why is this blocked?" />
                                </div>
                            </div>
                        </div>
                        <div class="task-modal-footer">
                            <button type="button" class="task-modal-btn secondary" onclick="ClientHub.closeTaskModal()">
                                Cancel
                            </button>
                            <button type="submit" class="task-modal-btn primary" id="task-submit-btn">
                                ${icons.plus} Add Task
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    function openTaskModal(mode = 'create', task = null) {
        state.modalMode = mode;
        state.editingTaskId = task?.id || null;

        const overlay = document.getElementById('task-modal-overlay');
        const title = document.getElementById('task-modal-title');
        const submitBtn = document.getElementById('task-submit-btn');
        const form = document.getElementById('task-form');

        // Update client dropdown
        updateClientDropdown();

        if (mode === 'edit' && task) {
            title.textContent = 'Edit Task';
            submitBtn.innerHTML = `${icons.check} Save Changes`;

            // Populate form
            document.getElementById('task-title').value = task.title || '';
            document.getElementById('task-description').value = task.description || '';
            document.getElementById('task-client').value = task.client_id || '';
            document.getElementById('task-priority').value = task.priority || 'P2';
            document.getElementById('task-due-date').value = task.due_date || '';
            document.getElementById('task-due-time').value = task.due_time || '';
            document.getElementById('task-status').value = task.status || 'NOT_STARTED';
            document.getElementById('task-timebox').value = task.timebox_bucket || 'NONE';
            document.getElementById('task-estimated').value = task.estimated_minutes || '';
            document.getElementById('task-waiting-on').value = task.waiting_on || '';
            document.getElementById('task-blocked-reason').value = task.blocked_reason || '';

            // Show pending fields if status is PENDING
            document.getElementById('pending-fields').classList.toggle('show', task.status === 'PENDING');
        } else {
            title.textContent = 'Add New Task';
            submitBtn.innerHTML = `${icons.plus} Add Task`;
            form.reset();
            document.getElementById('pending-fields').classList.remove('show');

            // Set default due date to today (using local date)
            document.getElementById('task-due-date').value = getLocalDateString(new Date());
        }

        overlay.classList.add('show');
        document.getElementById('task-title').focus();
    }

    function closeTaskModal() {
        const overlay = document.getElementById('task-modal-overlay');
        overlay.classList.remove('show');
        state.modalMode = 'create';
        state.editingTaskId = null;
    }

    function updateClientDropdown() {
        const select = document.getElementById('task-client');
        if (!select) return;

        select.innerHTML = '<option value="">No client</option>' +
            state.clients.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join('');
    }

    async function handleTaskSubmit(event) {
        event.preventDefault();

        const submitBtn = document.getElementById('task-submit-btn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<div class="spinner" style="width:16px;height:16px;border-width:2px;"></div> Saving...';

        const taskData = {
            title: document.getElementById('task-title').value.trim(),
            description: document.getElementById('task-description').value.trim() || null,
            client_id: document.getElementById('task-client').value || null,
            priority: document.getElementById('task-priority').value,
            due_date: document.getElementById('task-due-date').value || null,
            due_time: document.getElementById('task-due-time').value || null,
            status: document.getElementById('task-status').value,
            timebox_bucket: document.getElementById('task-timebox').value,
            estimated_minutes: document.getElementById('task-estimated').value ? parseInt(document.getElementById('task-estimated').value) : null,
            waiting_on: document.getElementById('task-waiting-on').value.trim() || null,
            blocked_reason: document.getElementById('task-blocked-reason').value.trim() || null,
        };

        try {
            let response;
            if (state.modalMode === 'edit' && state.editingTaskId) {
                response = await fetch(`${API_BASE}/api/hub/tasks/${state.editingTaskId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(taskData)
                });
            } else {
                response = await fetch(`${API_BASE}/api/hub/tasks`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(taskData)
                });
            }

            if (response.ok) {
                closeTaskModal();
                navigateTo(state.currentView);
            } else {
                // Try to parse JSON error, fall back to text
                let errorMessage = 'Unknown error';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || JSON.stringify(errorData);
                } catch {
                    errorMessage = await response.text() || `HTTP ${response.status}`;
                }
                alert('Failed to save task: ' + errorMessage);
            }
        } catch (error) {
            alert('Failed to save task: ' + error.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = state.modalMode === 'edit' ? `${icons.check} Save Changes` : `${icons.plus} Add Task`;
        }
    }

    // ==================== NAVIGATION ====================
    function navigateTo(view, params = {}) {
        state.currentView = view;

        // Update sidebar active state
        document.querySelectorAll('.hub-nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.view === view);
        });

        // Render view content
        const mainContent = document.getElementById('hub-main-content');
        const mainTitle = document.getElementById('hub-main-title');
        const mainSubtitle = document.getElementById('hub-main-subtitle');

        switch (view) {
            case 'today':
                mainTitle.textContent = 'Today';
                mainSubtitle.textContent = formatDate(new Date());
                renderTodayView(mainContent);
                break;
            case 'inbox':
                mainTitle.textContent = 'Inbox';
                mainSubtitle.textContent = 'Tasks needing triage';
                renderInboxView(mainContent);
                break;
            case 'pending':
                mainTitle.textContent = 'Pending';
                mainSubtitle.textContent = 'Tasks waiting on others';
                renderPendingView(mainContent);
                break;
            case 'overdue':
                mainTitle.textContent = 'Overdue';
                mainSubtitle.textContent = 'Past due tasks';
                renderOverdueView(mainContent);
                break;
            case 'upcoming':
                mainTitle.textContent = 'Upcoming';
                mainSubtitle.textContent = 'Next 7 days';
                renderUpcomingView(mainContent, params);
                break;
            case 'completed':
                mainTitle.textContent = 'Completed';
                mainSubtitle.textContent = 'Recently finished';
                renderCompletedView(mainContent);
                break;
            case 'clients':
                mainTitle.textContent = 'Clients';
                mainSubtitle.textContent = 'All clients';
                renderClientsView(mainContent);
                break;
            case 'client-detail':
                mainTitle.textContent = params.name || 'Client';
                mainSubtitle.textContent = 'Client details';
                renderClientDetailView(mainContent, params);
                break;
            case 'calendar':
                mainTitle.textContent = 'Calendar';
                mainSubtitle.textContent = 'Upcoming events';
                renderCalendarView(mainContent);
                break;
            case 'settings':
                mainTitle.textContent = 'Settings';
                mainSubtitle.textContent = 'Preferences';
                renderSettingsView(mainContent);
                break;
            default:
                mainContent.innerHTML = '<div class="empty-state"><p>View not found</p></div>';
        }
    }

    // ==================== SIDEBAR ====================
    function renderSidebar() {
        const sidebar = document.getElementById('hub-sidebar-nav');
        if (!sidebar) return;

        sidebar.innerHTML = `
            <div class="hub-nav-section">
                <div class="hub-nav-item active" data-view="today" onclick="ClientHub.navigateTo('today')">
                    ${icons.today}
                    <span>Today</span>
                </div>
                <div class="hub-nav-item" data-view="inbox" onclick="ClientHub.navigateTo('inbox')">
                    ${icons.inbox}
                    <span>Inbox</span>
                    <span class="badge-count" id="inbox-count" style="display: none;">0</span>
                </div>
                <div class="hub-nav-item" data-view="pending" onclick="ClientHub.navigateTo('pending')">
                    ${icons.pending}
                    <span>Pending</span>
                    <span class="badge-count warning" id="pending-count" style="display: none;">0</span>
                </div>
                <div class="hub-nav-item" data-view="overdue" onclick="ClientHub.navigateTo('overdue')">
                    ${icons.overdue}
                    <span>Overdue</span>
                    <span class="badge-count danger" id="overdue-count" style="display: none;">0</span>
                </div>
                <div class="hub-nav-item" data-view="upcoming" onclick="ClientHub.navigateTo('upcoming')">
                    ${icons.upcoming}
                    <span>Upcoming</span>
                </div>
                <div class="hub-nav-item" data-view="completed" onclick="ClientHub.navigateTo('completed')">
                    ${icons.completed}
                    <span>Completed</span>
                </div>
            </div>
            <div class="hub-nav-section">
                <div class="hub-nav-section-title">Clients</div>
                <div id="client-list" class="client-list"></div>
            </div>
            <div class="hub-nav-section">
                <div class="hub-nav-item" data-view="calendar" onclick="ClientHub.navigateTo('calendar')">
                    ${icons.calendar}
                    <span>Calendar</span>
                </div>
                <div class="hub-nav-item" data-view="settings" onclick="ClientHub.navigateTo('settings')">
                    ${icons.settings}
                    <span>Settings</span>
                </div>
            </div>
        `;
    }

    // ==================== DATA LOADING ====================
    async function loadSettings() {
        try {
            const response = await fetch(`${API_BASE}/api/hub/settings`);
            if (response.ok) {
                state.settings = await response.json();
            }
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    }

    async function loadClients() {
        try {
            const response = await fetch(`${API_BASE}/api/hub/clients`);
            if (response.ok) {
                const data = await response.json();
                state.clients = data.clients || data || [];
                renderClientList();
            }
        } catch (error) {
            console.error('Failed to load clients:', error);
        }
    }

    function renderClientList() {
        const list = document.getElementById('client-list');
        if (!list) return;

        if (state.clients.length === 0) {
            list.innerHTML = '<div class="client-item" style="color: var(--text-tertiary);">No clients yet</div>';
            return;
        }

        list.innerHTML = state.clients.slice(0, 8).map(client => `
            <div class="client-item" onclick="ClientHub.navigateTo('client-detail', { id: '${client.id}', name: '${escapeHtml(client.name)}' })">
                <span class="client-dot" style="background: ${client.color_hex || '#a855f7'}"></span>
                <span>${escapeHtml(client.name)}</span>
            </div>
        `).join('');
    }

    async function updateBadgeCounts() {
        try {
            const [inboxRes, overdueRes, pendingRes] = await Promise.all([
                fetch(`${API_BASE}/api/hub/views/inbox`),
                fetch(`${API_BASE}/api/hub/views/overdue`),
                fetch(`${API_BASE}/api/hub/views/pending`)
            ]);

            if (inboxRes.ok) {
                const data = await inboxRes.json();
                // Inbox returns tasks_missing_client, tasks_missing_due_date, etc.
                const count = (data.tasks_missing_client?.length || 0) +
                              (data.tasks_missing_due_date?.length || 0) +
                              (data.possible_duplicates?.length || 0);
                const badge = document.getElementById('inbox-count');
                if (badge) {
                    badge.textContent = count;
                    badge.style.display = count > 0 ? '' : 'none';
                }
            }

            if (overdueRes.ok) {
                const data = await overdueRes.json();
                // Overdue returns a raw array
                const count = Array.isArray(data) ? data.length : (data.tasks?.length || 0);
                const badge = document.getElementById('overdue-count');
                if (badge) {
                    badge.textContent = count;
                    badge.style.display = count > 0 ? '' : 'none';
                }
            }

            if (pendingRes.ok) {
                const data = await pendingRes.json();
                // Pending returns total_count
                const count = data.total_count || 0;
                const badge = document.getElementById('pending-count');
                if (badge) {
                    badge.textContent = count;
                    badge.style.display = count > 0 ? '' : 'none';
                }
            }
        } catch (error) {
            console.error('Failed to update badge counts:', error);
        }
    }

    // ==================== FILTER BAR ====================
    function renderFilterBar(viewId = 'today') {
        const clientOptions = state.clients.map(c =>
            `<option value="${c.id}" ${state.filters.client_id === c.id ? 'selected' : ''}>${escapeHtml(c.name)}</option>`
        ).join('');

        return `
            <div class="filter-bar" id="filter-bar-${viewId}">
                <div class="filter-group">
                    <input type="text"
                           class="filter-search"
                           placeholder="Search tasks..."
                           value="${escapeHtml(state.filters.search)}"
                           onchange="ClientHub.updateFilter('search', this.value)"
                           onkeyup="if(event.key === 'Enter') ClientHub.applyFilters()" />
                </div>
                <div class="filter-group">
                    <select class="filter-select" onchange="ClientHub.updateFilter('priority', this.value)">
                        <option value="">All Priorities</option>
                        <option value="P0" ${state.filters.priority === 'P0' ? 'selected' : ''}>P0 - Urgent</option>
                        <option value="P1" ${state.filters.priority === 'P1' ? 'selected' : ''}>P1 - High</option>
                        <option value="P2" ${state.filters.priority === 'P2' ? 'selected' : ''}>P2 - Normal</option>
                        <option value="P3" ${state.filters.priority === 'P3' ? 'selected' : ''}>P3 - Low</option>
                    </select>
                </div>
                <div class="filter-group">
                    <select class="filter-select" onchange="ClientHub.updateFilter('status', this.value)">
                        <option value="">All Statuses</option>
                        <option value="NOT_STARTED" ${state.filters.status === 'NOT_STARTED' ? 'selected' : ''}>To Do</option>
                        <option value="IN_PROGRESS" ${state.filters.status === 'IN_PROGRESS' ? 'selected' : ''}>In Progress</option>
                        <option value="PENDING" ${state.filters.status === 'PENDING' ? 'selected' : ''}>Pending</option>
                    </select>
                </div>
                <div class="filter-group">
                    <select class="filter-select" onchange="ClientHub.updateFilter('client_id', this.value)">
                        <option value="">All Clients</option>
                        ${clientOptions}
                    </select>
                </div>
                <button class="filter-clear-btn" onclick="ClientHub.clearFilters()" ${hasActiveFilters() ? '' : 'disabled'}>
                    Clear
                </button>
            </div>
        `;
    }

    function hasActiveFilters() {
        return state.filters.priority || state.filters.status || state.filters.client_id || state.filters.search;
    }

    function updateFilter(key, value) {
        state.filters[key] = value;
        applyFilters();
    }

    function clearFilters() {
        state.filters = { priority: '', status: '', client_id: '', search: '' };
        applyFilters();
    }

    function applyFilters() {
        // Re-render current view with new filters
        const container = document.getElementById('hub-main-content');
        if (container) {
            navigateTo(state.currentView);
        }
    }

    function filterTasks(tasks) {
        return tasks.filter(task => {
            if (state.filters.priority && task.priority !== state.filters.priority) return false;
            if (state.filters.status && task.status !== state.filters.status) return false;
            if (state.filters.client_id && task.client_id !== state.filters.client_id) return false;
            if (state.filters.search) {
                const search = state.filters.search.toLowerCase();
                const title = (task.title || '').toLowerCase();
                const desc = (task.description || '').toLowerCase();
                if (!title.includes(search) && !desc.includes(search)) return false;
            }
            return true;
        });
    }

    // ==================== TODAY VIEW ====================
    async function renderTodayView(container) {
        container.innerHTML = '<div class="hub-loading"><div class="spinner"></div></div>';

        try {
            // Fetch ALL open tasks (not just today's)
            const response = await fetch(`${API_BASE}/api/hub/tasks?limit=500`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const allTasks = await response.json();

            // Also fetch today's view for meetings and capacity
            const todayRes = await fetch(`${API_BASE}/api/hub/views/today`);
            const todayData = todayRes.ok ? await todayRes.json() : {};
            const { meetings = [], capacity_used_minutes = 0, capacity_total_minutes = 360 } = todayData;

            // Filter out completed tasks and apply user filters
            let openTasks = allTasks.filter(t => t.status !== 'COMPLETED' && !t.archived_at);
            openTasks = filterTasks(openTasks);

            // Use local date string for reliable comparison (avoids UTC timezone shift)
            const todayStr = getLocalDateString(new Date());

            // Group open tasks by due date - using string comparison
            const overdue = openTasks.filter(t => t.due_date && t.due_date < todayStr);
            const dueToday = openTasks.filter(t => t.due_date === todayStr);
            const upcoming = openTasks.filter(t => t.due_date && t.due_date > todayStr);
            const noDueDate = openTasks.filter(t => !t.due_date);

            // Sort each group by priority then due date
            const sortTasks = (a, b) => {
                const priorityOrder = { P0: 0, P1: 1, P2: 2, P3: 3 };
                const pDiff = (priorityOrder[a.priority] || 2) - (priorityOrder[b.priority] || 2);
                if (pDiff !== 0) return pDiff;
                if (a.due_date && b.due_date) return new Date(a.due_date) - new Date(b.due_date);
                return 0;
            };
            overdue.sort(sortTasks);
            dueToday.sort(sortTasks);
            upcoming.sort(sortTasks);
            noDueDate.sort(sortTasks);

            let html = `
                <div class="quick-add">
                    <button class="add-task-btn" onclick="ClientHub.openTaskModal()">
                        ${icons.plus} Add Task
                    </button>
                    <span class="quick-add-or">or quick add:</span>
                    <input type="text" id="quick-add-input" class="quick-add-input" placeholder="@client p1 due:tomorrow #morning ~30m" style="flex: 1;" />
                    <button class="quick-add-btn" onclick="ClientHub.quickAddTask()">
                        Add
                    </button>
                </div>

                ${renderFilterBar('today')}

                <div class="task-stats">
                    <div class="stat-card ${overdue.length > 0 ? 'danger' : ''}">
                        <span class="stat-value">${overdue.length}</span>
                        <span class="stat-label">Overdue</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-value">${dueToday.length}</span>
                        <span class="stat-label">Due Today</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-value">${upcoming.length}</span>
                        <span class="stat-label">Upcoming</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-value">${openTasks.length}</span>
                        <span class="stat-label">Total Open</span>
                    </div>
                </div>
            `;

            // Meetings
            if (meetings.length > 0) {
                html += `
                    <div class="meetings-section">
                        <div class="task-section-header">
                            ${icons.calendar}
                            <span class="task-section-title">Today's Meetings</span>
                            <span class="task-section-count">${meetings.length}</span>
                        </div>
                        ${meetings.map(m => renderMeetingCard(m)).join('')}
                    </div>
                `;
            }

            // Overdue tasks
            if (overdue.length > 0) {
                html += renderTaskSection('Overdue', icons.overdue, overdue, 'overdue');
            }

            // Due Today tasks
            if (dueToday.length > 0) {
                html += renderTaskSection('Due Today', icons.today, dueToday, 'due-today');
            }

            // Upcoming tasks
            if (upcoming.length > 0) {
                html += renderTaskSection('Upcoming', icons.upcoming, upcoming, 'upcoming');
            }

            // No Due Date tasks
            if (noDueDate.length > 0) {
                html += renderTaskSection('No Due Date', icons.inbox, noDueDate, 'no-due-date');
            }

            if (openTasks.length === 0) {
                html += `
                    <div class="empty-state">
                        <div class="empty-state-icon">${icons.completed}</div>
                        <h3>All clear!</h3>
                        <p>${hasActiveFilters() ? 'No tasks match your filters.' : 'No open tasks. Click "Add Task" to create one.'}</p>
                    </div>
                `;
            }

            container.innerHTML = html;
            updateBadgeCounts();

        } catch (error) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>Unable to load</h3>
                    <p>${escapeHtml(error.message)}</p>
                </div>
            `;
        }
    }

    function renderTaskSection(title, icon, tasks, sectionId = null) {
        const id = sectionId || title.toLowerCase().replace(/\s+/g, '-');
        return `
            <div class="task-section" id="section-${id}">
                <div class="task-section-header" onclick="ClientHub.toggleSection('${id}')">
                    <span class="collapse-icon">${icons.chevron || '▼'}</span>
                    ${icon}
                    <span class="task-section-title">${title}</span>
                    <span class="task-section-count">${tasks.length}</span>
                </div>
                <div class="task-section-content">
                    <div class="task-list-header">
                        <span></span>
                        <span></span>
                        <span>Task</span>
                        <span>Client</span>
                        <span>Due</span>
                        <span>Status</span>
                        <span>Priority</span>
                    </div>
                    ${tasks.map(t => renderTaskRow(t)).join('')}
                </div>
            </div>
        `;
    }

    function toggleSection(sectionId) {
        const section = document.getElementById(`section-${sectionId}`);
        if (section) {
            section.classList.toggle('collapsed');
        }
    }

    function renderMeetingCard(meeting) {
        const startTime = new Date(meeting.start_time).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
        return `
            <div class="meeting-card">
                <span class="meeting-time">${startTime}</span>
                <span class="meeting-title">${escapeHtml(meeting.title)}</span>
                ${meeting.client ? `<span class="meeting-badge">${escapeHtml(meeting.client.name)}</span>` : ''}
            </div>
        `;
    }

    function renderTaskRow(task) {
        const isCompleted = task.status === 'COMPLETED';
        const isOverdue = task.due_date && new Date(task.due_date) < new Date() && !isCompleted;
        const isPending = task.status === 'PENDING';
        const subtaskCount = task.subtasks?.length || 0;
        const completedSubtasks = task.subtasks?.filter(s => s.status === 'COMPLETED').length || 0;

        let rowClass = 'task-row';
        if (isCompleted) rowClass += ' completed';
        if (isOverdue) rowClass += ' overdue';
        if (isPending) rowClass += ' pending';

        const statusOptions = [
            { value: 'NOT_STARTED', label: 'To Do' },
            { value: 'IN_PROGRESS', label: 'In Progress' },
            { value: 'PENDING', label: 'Pending' },
            { value: 'COMPLETED', label: 'Done' }
        ];

        const priorityOptions = [
            { value: 'P0', label: 'P0' },
            { value: 'P1', label: 'P1' },
            { value: 'P2', label: 'P2' },
            { value: 'P3', label: 'P3' }
        ];

        // Build client select options
        const clientOptions = state.clients.map(c =>
            `<option value="${c.id}" ${task.client_id === c.id ? 'selected' : ''}>${escapeHtml(c.name)}</option>`
        ).join('');

        return `
            <div class="task-row-wrapper" data-task-id="${task.id}">
                <div class="${rowClass}">
                    <div class="task-expand-toggle" onclick="event.stopPropagation(); ClientHub.toggleTaskExpand('${task.id}')">
                        <span class="expand-icon">${icons.chevron}</span>
                        ${subtaskCount > 0 ? `<span class="subtask-count">${completedSubtasks}/${subtaskCount}</span>` : ''}
                    </div>
                    <div class="task-checkbox ${isCompleted ? 'checked' : ''}" onclick="event.stopPropagation(); ClientHub.toggleTaskStatus('${task.id}', '${task.status}')">
                        ${icons.check}
                    </div>
                    <div class="task-title-cell" onclick="ClientHub.startInlineEdit('${task.id}', 'title', this)">
                        <span class="task-title editable-field">${escapeHtml(task.title)}</span>
                        ${task.estimated_minutes ? `<span class="task-time-badge">${task.estimated_minutes}m</span>` : ''}
                    </div>
                    <div class="task-client-cell">
                        <select class="inline-select client-select"
                                onchange="ClientHub.updateTaskField('${task.id}', 'client_id', this.value || null)"
                                onclick="event.stopPropagation()">
                            <option value="">No client</option>
                            ${clientOptions}
                        </select>
                    </div>
                    <div class="task-due-cell ${isOverdue ? 'overdue' : ''}" onclick="event.stopPropagation()">
                        <input type="date" class="inline-date" value="${task.due_date || ''}"
                               onchange="ClientHub.updateTaskField('${task.id}', 'due_date', this.value || null)" />
                        <span class="due-date-display">${task.due_date ? formatDueDate(task.due_date) : '—'}</span>
                    </div>
                    <select class="inline-select status-select ${task.status?.toLowerCase().replace('_', '-')}"
                            onchange="ClientHub.updateTaskField('${task.id}', 'status', this.value)"
                            onclick="event.stopPropagation()">
                        ${statusOptions.map(opt => `<option value="${opt.value}" ${task.status === opt.value ? 'selected' : ''}>${opt.label}</option>`).join('')}
                    </select>
                    <select class="inline-select priority-select ${task.priority?.toLowerCase()}"
                            onchange="ClientHub.updateTaskField('${task.id}', 'priority', this.value)"
                            onclick="event.stopPropagation()">
                        ${priorityOptions.map(opt => `<option value="${opt.value}" ${task.priority === opt.value ? 'selected' : ''}>${opt.label}</option>`).join('')}
                    </select>
                </div>
                <div class="subtasks-container" id="subtasks-${task.id}">
                    <div class="subtasks-list"></div>
                    <div class="add-subtask-row">
                        <input type="text" class="add-subtask-input" placeholder="Add subtask..."
                               onkeydown="if(event.key==='Enter'){ClientHub.addSubtask('${task.id}', this.value); this.value='';}" />
                    </div>
                </div>
            </div>
        `;
    }

    function renderSubtaskRow(subtask, taskId) {
        const isCompleted = subtask.status === 'COMPLETED';
        const isOverdue = subtask.due_date && new Date(subtask.due_date) < new Date() && !isCompleted;

        let rowClass = 'subtask-row';
        if (isCompleted) rowClass += ' completed';
        if (isOverdue) rowClass += ' overdue';

        const statusOptions = [
            { value: 'NOT_STARTED', label: 'To Do' },
            { value: 'IN_PROGRESS', label: 'In Progress' },
            { value: 'PENDING', label: 'Pending' },
            { value: 'COMPLETED', label: 'Done' }
        ];

        const priorityOptions = [
            { value: 'P0', label: 'P0' },
            { value: 'P1', label: 'P1' },
            { value: 'P2', label: 'P2' },
            { value: 'P3', label: 'P3' }
        ];

        return `
            <div class="${rowClass}" data-subtask-id="${subtask.id}">
                <div class="subtask-checkbox ${isCompleted ? 'checked' : ''}" onclick="event.stopPropagation(); ClientHub.toggleSubtaskStatus('${subtask.id}', '${subtask.status}', '${taskId}')">
                    ${icons.check}
                </div>
                <div class="subtask-title-cell" onclick="ClientHub.startSubtaskInlineEdit('${subtask.id}', 'title', this, '${taskId}')">
                    <span class="subtask-title editable-field">${escapeHtml(subtask.title)}</span>
                </div>
                <div class="subtask-due-cell ${isOverdue ? 'overdue' : ''}" onclick="event.stopPropagation()">
                    <input type="date" class="inline-date" value="${subtask.due_date || ''}"
                           onchange="ClientHub.updateSubtaskField('${subtask.id}', 'due_date', this.value || null, '${taskId}')" />
                    <span class="due-date-display">${subtask.due_date ? formatDueDate(subtask.due_date) : '—'}</span>
                </div>
                <select class="inline-select status-select ${subtask.status?.toLowerCase().replace('_', '-')}"
                        onchange="ClientHub.updateSubtaskField('${subtask.id}', 'status', this.value, '${taskId}')"
                        onclick="event.stopPropagation()">
                    ${statusOptions.map(opt => `<option value="${opt.value}" ${subtask.status === opt.value ? 'selected' : ''}>${opt.label}</option>`).join('')}
                </select>
                <select class="inline-select priority-select ${subtask.priority?.toLowerCase() || ''}"
                        onchange="ClientHub.updateSubtaskField('${subtask.id}', 'priority', this.value, '${taskId}')"
                        onclick="event.stopPropagation()">
                    <option value="" ${!subtask.priority ? 'selected' : ''}>—</option>
                    ${priorityOptions.map(opt => `<option value="${opt.value}" ${subtask.priority === opt.value ? 'selected' : ''}>${opt.label}</option>`).join('')}
                </select>
                <button class="subtask-delete-btn" onclick="event.stopPropagation(); ClientHub.deleteSubtask('${subtask.id}', '${taskId}')" title="Delete subtask">×</button>
            </div>
        `;
    }

    async function toggleTaskExpand(taskId) {
        const wrapper = document.querySelector(`.task-row-wrapper[data-task-id="${taskId}"]`);
        if (!wrapper) return;

        const isExpanded = wrapper.classList.contains('expanded');

        if (isExpanded) {
            wrapper.classList.remove('expanded');
        } else {
            wrapper.classList.add('expanded');
            // Load subtasks
            await loadSubtasks(taskId);
        }
    }

    async function loadSubtasks(taskId) {
        const container = document.querySelector(`#subtasks-${taskId} .subtasks-list`);
        if (!container) return;

        try {
            const response = await fetch(`${API_BASE}/api/hub/tasks/${taskId}/subtasks`);
            if (!response.ok) throw new Error('Failed to load subtasks');

            const subtasks = await response.json();

            if (subtasks.length === 0) {
                container.innerHTML = '<div class="no-subtasks">No subtasks yet</div>';
            } else {
                container.innerHTML = subtasks.map(s => renderSubtaskRow(s, taskId)).join('');
            }
        } catch (error) {
            console.error('Failed to load subtasks:', error);
            container.innerHTML = '<div class="subtask-error">Failed to load subtasks</div>';
        }
    }

    async function addSubtask(taskId, title) {
        if (!title.trim()) return;

        try {
            const response = await fetch(`${API_BASE}/api/hub/tasks/${taskId}/subtasks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: title.trim() })
            });

            if (response.ok) {
                await loadSubtasks(taskId);
                // Update subtask count in parent row
                navigateTo(state.currentView);
            }
        } catch (error) {
            console.error('Failed to add subtask:', error);
        }
    }

    async function toggleSubtaskStatus(subtaskId, currentStatus, taskId) {
        const newStatus = currentStatus === 'COMPLETED' ? 'NOT_STARTED' : 'COMPLETED';
        await updateSubtaskField(subtaskId, 'status', newStatus, taskId);
    }

    async function updateSubtaskField(subtaskId, field, value, taskId) {
        try {
            const response = await fetch(`${API_BASE}/api/hub/subtasks/${subtaskId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ [field]: value })
            });

            if (response.ok) {
                await loadSubtasks(taskId);
            }
        } catch (error) {
            console.error('Failed to update subtask:', error);
        }
    }

    async function deleteSubtask(subtaskId, taskId) {
        try {
            const response = await fetch(`${API_BASE}/api/hub/subtasks/${subtaskId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                await loadSubtasks(taskId);
                navigateTo(state.currentView);
            }
        } catch (error) {
            console.error('Failed to delete subtask:', error);
        }
    }

    function startSubtaskInlineEdit(subtaskId, field, cellElement, taskId) {
        event.stopPropagation();

        const titleSpan = cellElement.querySelector('.subtask-title');
        if (!titleSpan) return;

        const currentValue = titleSpan.textContent;

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'inline-title-input';
        input.value = currentValue;

        const saveEdit = async () => {
            const newValue = input.value.trim();
            if (newValue && newValue !== currentValue) {
                await updateSubtaskField(subtaskId, field, newValue, taskId);
            } else {
                await loadSubtasks(taskId);
            }
        };

        input.addEventListener('blur', saveEdit);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                input.blur();
            }
            if (e.key === 'Escape') {
                input.value = currentValue;
                input.blur();
            }
        });

        titleSpan.style.display = 'none';
        cellElement.insertBefore(input, titleSpan);
        input.focus();
        input.select();
    }

    // Keep old renderTaskCard for views that still need it (will phase out)
    function renderTaskCard(task) {
        return renderTaskRow(task);
    }

    function renderSubtaskProgress(subtasks) {
        const completed = subtasks.filter(s => s.status === 'COMPLETED').length;
        const total = subtasks.length;
        const percent = Math.round((completed / total) * 100);

        return `
            <div class="subtask-progress">
                <div class="subtask-bar">
                    <div class="subtask-fill" style="width: ${percent}%"></div>
                </div>
                <span>${completed}/${total}</span>
            </div>
        `;
    }

    // ==================== INBOX VIEW ====================
    async function renderInboxView(container) {
        container.innerHTML = '<div class="hub-loading"><div class="spinner"></div></div>';

        try {
            const response = await fetch(`${API_BASE}/api/hub/views/inbox`);
            if (!response.ok) throw new Error('Failed to load');
            const data = await response.json();

            // Combine all task lists from inbox response
            const missingClient = data.tasks_missing_client || [];
            const missingDue = data.tasks_missing_due_date || [];
            const duplicates = data.possible_duplicates || [];

            let html = `
                <div class="quick-add" style="margin-bottom: 1.5rem;">
                    <button class="add-task-btn" onclick="ClientHub.openTaskModal()">
                        ${icons.plus} Add Task
                    </button>
                </div>
            `;

            const totalCount = missingClient.length + missingDue.length + duplicates.length;

            if (totalCount === 0) {
                html += `
                    <div class="empty-state">
                        <div class="empty-state-icon">${icons.inbox}</div>
                        <h3>Inbox Zero!</h3>
                        <p>All tasks have been triaged.</p>
                    </div>
                `;
            } else {
                if (missingClient.length > 0) {
                    html += `
                        <div class="task-section">
                            <div class="task-section-header">
                                ${icons.user}
                                <span class="task-section-title">Missing Client</span>
                                <span class="task-section-count">${missingClient.length}</span>
                            </div>
                            ${missingClient.map(t => renderTaskCard(t)).join('')}
                        </div>
                    `;
                }

                if (missingDue.length > 0) {
                    html += `
                        <div class="task-section">
                            <div class="task-section-header">
                                ${icons.calendar}
                                <span class="task-section-title">Missing Due Date</span>
                                <span class="task-section-count">${missingDue.length}</span>
                            </div>
                            ${missingDue.map(t => renderTaskCard(t)).join('')}
                        </div>
                    `;
                }

                if (duplicates.length > 0) {
                    html += `
                        <div class="task-section">
                            <div class="task-section-header">
                                ${icons.pending}
                                <span class="task-section-title">Possible Duplicates</span>
                                <span class="task-section-count">${duplicates.length}</span>
                            </div>
                            ${duplicates.map(t => renderTaskCard(t)).join('')}
                        </div>
                    `;
                }
            }

            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = `<div class="empty-state"><p>${escapeHtml(error.message)}</p></div>`;
        }
    }

    // ==================== PENDING VIEW ====================
    async function renderPendingView(container) {
        container.innerHTML = '<div class="hub-loading"><div class="spinner"></div></div>';

        try {
            const response = await fetch(`${API_BASE}/api/hub/views/pending`);
            if (!response.ok) throw new Error('Failed to load');
            const data = await response.json();

            // Use the actual response structure
            const tasksByClient = data.tasks_by_client || {};
            const unassignedTasks = data.unassigned_tasks || [];
            const clients = data.clients || [];
            const totalCount = data.total_count || 0;

            if (totalCount === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">${icons.pending}</div>
                        <h3>Nothing Pending</h3>
                        <p>No tasks are waiting on external input.</p>
                    </div>
                `;
                return;
            }

            let html = '';

            // Render tasks by client
            clients.forEach(client => {
                const clientTasks = tasksByClient[client.id] || [];
                if (clientTasks.length > 0) {
                    html += `
                        <div class="task-section">
                            <div class="task-section-header">
                                ${icons.user}
                                <span class="task-section-title">${escapeHtml(client.name)}</span>
                                <span class="task-section-count">${clientTasks.length}</span>
                            </div>
                            ${clientTasks.map(t => renderTaskCard(t)).join('')}
                        </div>
                    `;
                }
            });

            // Render unassigned tasks
            if (unassignedTasks.length > 0) {
                html += `
                    <div class="task-section">
                        <div class="task-section-header">
                            ${icons.inbox}
                            <span class="task-section-title">No Client</span>
                            <span class="task-section-count">${unassignedTasks.length}</span>
                        </div>
                        ${unassignedTasks.map(t => renderTaskCard(t)).join('')}
                    </div>
                `;
            }

            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = `<div class="empty-state"><p>${escapeHtml(error.message)}</p></div>`;
        }
    }

    // ==================== OVERDUE VIEW ====================
    async function renderOverdueView(container) {
        container.innerHTML = '<div class="hub-loading"><div class="spinner"></div></div>';

        try {
            const response = await fetch(`${API_BASE}/api/hub/views/overdue`);
            if (!response.ok) throw new Error('Failed to load');
            const data = await response.json();

            // Overdue endpoint returns a raw array, not {tasks: [...]}
            let tasks = Array.isArray(data) ? data : (data.tasks || []);
            tasks = filterTasks(tasks);

            let html = renderFilterBar('overdue');

            if (tasks.length === 0) {
                html += `
                    <div class="empty-state">
                        <div class="empty-state-icon">${icons.completed}</div>
                        <h3>All Caught Up!</h3>
                        <p>${hasActiveFilters() ? 'No tasks match your filters.' : 'No overdue tasks.'}</p>
                    </div>
                `;
            } else {
                html += renderTaskSection('Overdue Tasks', icons.overdue, tasks, 'overdue');
            }

            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = `<div class="empty-state"><p>${escapeHtml(error.message)}</p></div>`;
        }
    }

    // ==================== UPCOMING VIEW ====================
    async function renderUpcomingView(container, params) {
        const days = params.days || 7;
        container.innerHTML = '<div class="hub-loading"><div class="spinner"></div></div>';

        try {
            const response = await fetch(`${API_BASE}/api/hub/views/upcoming?days=${days}`);
            if (!response.ok) throw new Error('Failed to load');
            const data = await response.json();

            let tasks = data.tasks || [];
            tasks = filterTasks(tasks);

            let html = `
                <div class="filter-tabs" style="margin-bottom: 1rem;">
                    <button class="filter-tab ${days === 7 ? 'active' : ''}" onclick="ClientHub.navigateTo('upcoming', { days: 7 })">7 Days</button>
                    <button class="filter-tab ${days === 14 ? 'active' : ''}" onclick="ClientHub.navigateTo('upcoming', { days: 14 })">14 Days</button>
                    <button class="filter-tab ${days === 30 ? 'active' : ''}" onclick="ClientHub.navigateTo('upcoming', { days: 30 })">30 Days</button>
                </div>

                ${renderFilterBar('upcoming')}
            `;

            if (tasks.length === 0) {
                html += `
                    <div class="empty-state">
                        <div class="empty-state-icon">${icons.upcoming}</div>
                        <h3>Clear Schedule</h3>
                        <p>${hasActiveFilters() ? 'No tasks match your filters.' : `No tasks in the next ${days} days.`}</p>
                    </div>
                `;
            } else {
                // Group by date
                const grouped = {};
                tasks.forEach(task => {
                    const dateKey = task.due_date || 'No Date';
                    if (!grouped[dateKey]) grouped[dateKey] = [];
                    grouped[dateKey].push(task);
                });

                Object.entries(grouped).forEach(([date, dateTasks], idx) => {
                    html += renderTaskSection(formatDueDate(date), icons.calendar, dateTasks, `upcoming-${idx}`);
                });
            }

            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = `<div class="empty-state"><p>${escapeHtml(error.message)}</p></div>`;
        }
    }

    // ==================== COMPLETED VIEW ====================
    async function renderCompletedView(container) {
        container.innerHTML = '<div class="hub-loading"><div class="spinner"></div></div>';

        try {
            const response = await fetch(`${API_BASE}/api/hub/views/completed?days=7`);
            if (!response.ok) throw new Error('Failed to load');
            const data = await response.json();

            const tasks = data.tasks || [];
            const stats = data.stats || {};

            let html = `
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value success">${stats.completed_count || tasks.length}</div>
                        <div class="stat-label">Completed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${stats.total_minutes || 0}m</div>
                        <div class="stat-label">Time Spent</div>
                    </div>
                </div>
            `;

            if (tasks.length === 0) {
                html += `
                    <div class="empty-state">
                        <div class="empty-state-icon">${icons.completed}</div>
                        <h3>No Recent Completions</h3>
                        <p>Tasks you complete will appear here.</p>
                    </div>
                `;
            } else {
                html += `
                    <div class="task-section">
                        <div class="task-section-header">
                            ${icons.completed}
                            <span class="task-section-title">Recently Completed</span>
                            <span class="task-section-count">${tasks.length}</span>
                        </div>
                        ${tasks.map(t => renderTaskCard(t)).join('')}
                    </div>
                `;
            }

            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = `<div class="empty-state"><p>${escapeHtml(error.message)}</p></div>`;
        }
    }

    // ==================== CLIENTS VIEW ====================
    async function renderClientsView(container) {
        container.innerHTML = '<div class="hub-loading"><div class="spinner"></div></div>';

        try {
            const response = await fetch(`${API_BASE}/api/hub/clients`);
            if (!response.ok) throw new Error('Failed to load');
            const data = await response.json();

            const clients = data.clients || data || [];

            if (clients.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">${icons.clients}</div>
                        <h3>No Clients Yet</h3>
                        <p>Clients will be added when you create tasks or sync calendar events.</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = `
                <div class="stats-grid">
                    ${clients.map(c => `
                        <div class="stat-card" style="cursor: pointer; border-left: 4px solid ${c.color_hex || '#a855f7'};" onclick="ClientHub.navigateTo('client-detail', { id: '${c.id}', name: '${escapeHtml(c.name)}' })">
                            <div class="stat-value">${c.open_task_count || 0}</div>
                            <div class="stat-label">${escapeHtml(c.name)}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        } catch (error) {
            container.innerHTML = `<div class="empty-state"><p>${escapeHtml(error.message)}</p></div>`;
        }
    }

    // ==================== CLIENT DETAIL VIEW ====================
    let clientDetailTab = 'tasks'; // Track current tab: 'tasks' or 'calls'

    async function renderClientDetailView(container, params) {
        container.innerHTML = '<div class="hub-loading"><div class="spinner"></div></div>';

        try {
            // Fetch client, tasks, and calls in parallel
            const [clientRes, tasksRes, callsRes] = await Promise.all([
                fetch(`${API_BASE}/api/hub/clients/${params.id}`),
                fetch(`${API_BASE}/api/hub/tasks?client_id=${params.id}&limit=500`),
                fetch(`${API_BASE}/api/hub/clients/${params.id}/calls?limit=100`)
            ]);

            if (!clientRes.ok) throw new Error('Failed to load client');

            const client = await clientRes.json();
            let allTasks = tasksRes.ok ? await tasksRes.json() : [];
            const callsData = callsRes.ok ? await callsRes.json() : { calls: [] };
            const calls = callsData.calls || [];

            // Inject client info into all tasks (since they all belong to this client)
            allTasks = allTasks.map(t => ({
                ...t,
                client: { id: client.id, name: client.name, color_hex: client.color_hex }
            }));

            // Sort calls by date descending (most recent first)
            calls.sort((a, b) => new Date(b.call_date) - new Date(a.call_date));

            // Use local date string for reliable comparison (avoids UTC timezone shift)
            const todayStr = getLocalDateString(new Date());

            const openTasks = allTasks.filter(t => t.status !== 'COMPLETED' && !t.archived_at);
            const completedTasks = allTasks.filter(t => t.status === 'COMPLETED');

            // Group open tasks by due date - using string comparison to avoid timezone issues
            const overdue = openTasks.filter(t => t.due_date && t.due_date < todayStr);
            const dueToday = openTasks.filter(t => t.due_date === todayStr);
            const upcoming = openTasks.filter(t => t.due_date && t.due_date > todayStr);
            const noDueDate = openTasks.filter(t => !t.due_date);

            // Sort by priority
            const sortByPriority = (a, b) => {
                const order = { P0: 0, P1: 1, P2: 2, P3: 3 };
                return (order[a.priority] || 2) - (order[b.priority] || 2);
            };
            overdue.sort(sortByPriority);
            dueToday.sort(sortByPriority);
            upcoming.sort(sortByPriority);
            noDueDate.sort(sortByPriority);

            let html = `
                <div class="client-header-bar">
                    <div class="client-color-indicator" style="background: ${client.color_hex || '#a855f7'}"></div>
                    <div class="client-info">
                        <span class="client-status-badge ${client.status || 'active'}">${client.status || 'active'}</span>
                    </div>
                    <button class="add-task-btn" onclick="ClientHub.openTaskModal()">
                        ${icons.plus} Add Task
                    </button>
                </div>

                <div class="task-stats">
                    <div class="stat-card ${overdue.length > 0 ? 'danger' : ''}">
                        <span class="stat-value">${overdue.length}</span>
                        <span class="stat-label">Overdue</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-value">${openTasks.length}</span>
                        <span class="stat-label">Open</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-value">${calls.length}</span>
                        <span class="stat-label">Calls</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-value ${client.health_status === 'RED' ? 'danger' : client.health_status === 'YELLOW' ? 'warning' : ''}">${client.health_status || 'GREEN'}</span>
                        <span class="stat-label">Health</span>
                    </div>
                </div>

                <div class="client-tabs">
                    <button class="client-tab ${clientDetailTab === 'tasks' ? 'active' : ''}" onclick="ClientHub.switchClientTab('tasks', '${params.id}', '${escapeHtml(params.name || '')}')">
                        ${icons.inbox} Tasks (${openTasks.length})
                    </button>
                    <button class="client-tab ${clientDetailTab === 'calls' ? 'active' : ''}" onclick="ClientHub.switchClientTab('calls', '${params.id}', '${escapeHtml(params.name || '')}')">
                        ${icons.calendar} Calls (${calls.length})
                    </button>
                </div>
            `;

            if (clientDetailTab === 'tasks') {
                // Tasks Tab Content
                if (openTasks.length === 0 && completedTasks.length === 0) {
                    html += `
                        <div class="empty-state">
                            <div class="empty-state-icon">${icons.inbox}</div>
                            <h3>No Tasks</h3>
                            <p>No tasks for this client yet. Click "Add Task" to create one.</p>
                        </div>
                    `;
                } else {
                    if (overdue.length > 0) {
                        html += renderTaskSection('Overdue', icons.overdue, overdue, 'client-overdue');
                    }
                    if (dueToday.length > 0) {
                        html += renderTaskSection('Due Today', icons.today, dueToday, 'client-today');
                    }
                    if (upcoming.length > 0) {
                        html += renderTaskSection('Upcoming', icons.upcoming, upcoming, 'client-upcoming');
                    }
                    if (noDueDate.length > 0) {
                        html += renderTaskSection('No Due Date', icons.inbox, noDueDate, 'client-nodue');
                    }
                    if (completedTasks.length > 0) {
                        html += `
                            <div class="task-section collapsed" id="section-client-completed">
                                <div class="task-section-header" onclick="ClientHub.toggleSection('client-completed')">
                                    <span class="collapse-icon">${icons.chevron || '▼'}</span>
                                    ${icons.completed}
                                    <span class="task-section-title">Completed</span>
                                    <span class="task-section-count">${completedTasks.length}</span>
                                </div>
                                <div class="task-section-content">
                                    <div class="task-list-header">
                                        <span></span>
                                        <span></span>
                                        <span>Task</span>
                                        <span>Client</span>
                                        <span>Due</span>
                                        <span>Status</span>
                                        <span>Priority</span>
                                    </div>
                                    ${completedTasks.slice(0, 20).map(t => renderTaskRow(t)).join('')}
                                    ${completedTasks.length > 20 ? `<div class="show-more-hint">+ ${completedTasks.length - 20} more completed tasks</div>` : ''}
                                </div>
                            </div>
                        `;
                    }
                }
            } else {
                // Calls Tab Content
                if (calls.length === 0) {
                    html += `
                        <div class="empty-state">
                            <div class="empty-state-icon">${icons.calendar}</div>
                            <h3>No Calls</h3>
                            <p>No call records for this client yet. Calls are imported from Fireflies via n8n.</p>
                        </div>
                    `;
                } else {
                    html += `<div class="calls-list">`;
                    calls.forEach(call => {
                        html += renderCallCard(call);
                    });
                    html += `</div>`;
                }
            }

            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = `<div class="empty-state"><p>${escapeHtml(error.message)}</p></div>`;
        }
    }

    function switchClientTab(tab, clientId, clientName) {
        clientDetailTab = tab;
        navigateTo('client-detail', { id: clientId, name: clientName });
    }

    function renderCallCard(call) {
        const callDate = new Date(call.call_date);
        const dateStr = callDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
        const timeStr = callDate.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
        const duration = call.duration_minutes ? `${call.duration_minutes}m` : '';

        return `
            <div class="call-card" onclick="ClientHub.openCallDetail('${call.id}')">
                <div class="call-card-header">
                    <div class="call-date-time">
                        <span class="call-date">${dateStr}</span>
                        <span class="call-time">${timeStr}</span>
                        ${duration ? `<span class="call-duration">${duration}</span>` : ''}
                    </div>
                    ${call.transcript_url ? `<a href="${call.transcript_url}" target="_blank" class="call-link" onclick="event.stopPropagation()">View Transcript</a>` : ''}
                </div>
                <div class="call-title">${escapeHtml(call.title || 'Untitled Call')}</div>
                ${call.summary ? `<div class="call-summary">${escapeHtml(call.summary.substring(0, 200))}${call.summary.length > 200 ? '...' : ''}</div>` : ''}
                ${call.keywords && call.keywords.length > 0 ? `
                    <div class="call-keywords">
                        ${call.keywords.slice(0, 5).map(k => `<span class="call-keyword">${escapeHtml(k)}</span>`).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }

    function openCallDetail(callId) {
        // For now, just log - could expand to show full call detail modal
        console.log('Open call detail:', callId);
    }

    // ==================== CALENDAR VIEW ====================
    async function renderCalendarView(container) {
        container.innerHTML = '<div class="hub-loading"><div class="spinner"></div></div>';

        try {
            // Use local dates to avoid UTC timezone shift issues
            const now = new Date();
            const today = getLocalDateString(now);
            const nextWeekDate = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
            const nextWeek = getLocalDateString(nextWeekDate);

            const response = await fetch(`${API_BASE}/api/hub/calendar?start=${today}&end=${nextWeek}`);
            if (!response.ok) throw new Error('Failed to load');
            const events = await response.json(); // API returns array directly

            if (events.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">${icons.calendar}</div>
                        <h3>No Upcoming Events</h3>
                        <p>Calendar events will appear here once synced via n8n.</p>
                    </div>
                `;
                return;
            }

            // Group by date using local time (not UTC)
            const grouped = {};
            events.forEach(event => {
                const dateKey = getLocalDateString(new Date(event.start_time));
                if (!grouped[dateKey]) grouped[dateKey] = [];
                grouped[dateKey].push(event);
            });

            let html = '';
            Object.entries(grouped).forEach(([date, dateEvents]) => {
                html += `
                    <div class="task-section">
                        <div class="task-section-header">
                            ${icons.calendar}
                            <span class="task-section-title">${formatDueDate(date)}</span>
                            <span class="task-section-count">${dateEvents.length}</span>
                        </div>
                        ${dateEvents.map(e => renderMeetingCard(e)).join('')}
                    </div>
                `;
            });

            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = `<div class="empty-state"><p>${escapeHtml(error.message)}</p></div>`;
        }
    }

    // ==================== SETTINGS VIEW ====================
    async function renderSettingsView(container) {
        if (!state.settings) {
            await loadSettings();
        }

        const s = state.settings || {};

        container.innerHTML = `
            <form id="settings-form" onsubmit="ClientHub.saveSettings(event)">
                <div class="task-section">
                    <div class="task-section-header">
                        ${icons.settings}
                        <span class="task-section-title">General</span>
                    </div>
                    <div style="padding: 1rem; background: var(--bg-elevated); border-radius: 10px;">
                        <div style="margin-bottom: 1rem;">
                            <label style="display: block; font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.5rem;">Timezone</label>
                            <input type="text" id="setting-timezone" class="quick-add-input" value="${escapeHtml(s.timezone || 'America/New_York')}" style="margin: 0;" />
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <label style="display: block; font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.5rem;">Daily Capacity (minutes)</label>
                            <input type="number" id="setting-capacity" class="quick-add-input" value="${s.capacity_minutes_per_day || 360}" style="margin: 0;" />
                        </div>
                    </div>
                </div>
                <button type="submit" class="quick-add-btn" style="margin-top: 1rem;">Save Settings</button>
            </form>
        `;
    }

    async function saveSettings(event) {
        event.preventDefault();

        const timezone = document.getElementById('setting-timezone').value;
        const capacity = parseInt(document.getElementById('setting-capacity').value);

        try {
            const response = await fetch(`${API_BASE}/api/hub/settings`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    timezone,
                    capacity_minutes_per_day: capacity
                })
            });

            if (response.ok) {
                state.settings = await response.json();
                alert('Settings saved!');
            } else {
                throw new Error('Failed to save');
            }
        } catch (error) {
            alert('Failed to save settings: ' + error.message);
        }
    }

    // ==================== TASK ACTIONS ====================
    async function quickAddTask() {
        const input = document.getElementById('quick-add-input');
        if (!input) return;

        const text = input.value.trim();
        if (!text) return;

        const parsed = parseQuickAdd(text);

        try {
            const response = await fetch(`${API_BASE}/api/hub/tasks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(parsed)
            });

            if (response.ok) {
                input.value = '';
                navigateTo(state.currentView);
            } else {
                const error = await response.json();
                alert('Failed to add task: ' + (error.detail || 'Unknown error'));
            }
        } catch (error) {
            alert('Failed to add task: ' + error.message);
        }
    }

    function parseQuickAdd(text) {
        let title = text;
        const task = {
            title: '',
            priority: 'P2',
            status: 'NOT_STARTED',
        };

        // Extract @client
        const clientMatch = text.match(/@(\w+)/);
        if (clientMatch) {
            const clientName = clientMatch[1];
            const client = state.clients.find(c => c.name.toLowerCase().includes(clientName.toLowerCase()));
            if (client) {
                task.client_id = client.id;
            }
            title = title.replace(/@\w+\s*/g, '');
        }

        // Extract priority
        const priorityMatch = text.match(/\bp([0-3])\b/i);
        if (priorityMatch) {
            task.priority = `P${priorityMatch[1]}`;
            title = title.replace(/\bp[0-3]\b\s*/gi, '');
        }

        // Extract due date
        const dueMatch = text.match(/due:(\S+)/i);
        if (dueMatch) {
            const dueStr = dueMatch[1].toLowerCase();
            const today = new Date();

            if (dueStr === 'today') {
                task.due_date = getLocalDateString(today);
            } else if (dueStr === 'tomorrow') {
                today.setDate(today.getDate() + 1);
                task.due_date = getLocalDateString(today);
            } else if (/^\d{4}-\d{2}-\d{2}$/.test(dueStr)) {
                task.due_date = dueStr;
            }
            title = title.replace(/due:\S+\s*/gi, '');
        }

        // Extract time estimate
        const timeMatch = text.match(/~(\d+)(m|h)/i);
        if (timeMatch) {
            const value = parseInt(timeMatch[1]);
            const unit = timeMatch[2].toLowerCase();
            task.estimated_minutes = unit === 'h' ? value * 60 : value;
            title = title.replace(/~\d+[mh]\s*/gi, '');
        }

        // Extract timebox
        const timeboxMatch = text.match(/#(morning|afternoon|evening)/i);
        if (timeboxMatch) {
            task.timebox_bucket = timeboxMatch[1].toUpperCase();
            title = title.replace(/#(morning|afternoon|evening)\s*/gi, '');
        }

        task.title = title.trim();
        return task;
    }

    async function toggleTaskStatus(taskId, currentStatus) {
        const newStatus = currentStatus === 'COMPLETED' ? 'NOT_STARTED' : 'COMPLETED';

        try {
            const response = await fetch(`${API_BASE}/api/hub/tasks/${taskId}/status`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: newStatus })
            });

            if (response.ok) {
                navigateTo(state.currentView);
            }
        } catch (error) {
            console.error('Failed to toggle task status:', error);
        }
    }

    async function openTask(taskId) {
        // Fetch task details and open edit modal
        try {
            const response = await fetch(`${API_BASE}/api/hub/tasks/${taskId}`);
            if (response.ok) {
                const task = await response.json();
                openTaskModal('edit', task);
            }
        } catch (error) {
            console.error('Failed to load task:', error);
        }
    }

    async function updateTaskField(taskId, field, value) {
        try {
            const response = await fetch(`${API_BASE}/api/hub/tasks/${taskId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ [field]: value })
            });

            if (!response.ok) {
                throw new Error('Failed to update');
            }

            // Refresh the current view
            navigateTo(state.currentView);
        } catch (error) {
            console.error('Failed to update task field:', error);
            // Refresh to restore original value
            navigateTo(state.currentView);
        }
    }

    function startInlineEdit(taskId, field, cellElement) {
        event.stopPropagation();

        // Get the current text
        const titleSpan = cellElement.querySelector('.task-title');
        if (!titleSpan) return;

        const currentValue = titleSpan.textContent;

        // Replace with input
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'inline-title-input';
        input.value = currentValue;

        // Save on blur or Enter
        const saveEdit = async () => {
            const newValue = input.value.trim();
            if (newValue && newValue !== currentValue) {
                await updateTaskField(taskId, field, newValue);
            } else {
                // Restore original if empty or unchanged
                navigateTo(state.currentView);
            }
        };

        input.addEventListener('blur', saveEdit);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                input.blur();
            }
            if (e.key === 'Escape') {
                input.value = currentValue;
                input.blur();
            }
        });

        // Replace content
        titleSpan.style.display = 'none';
        cellElement.insertBefore(input, titleSpan);
        input.focus();
        input.select();
    }

    // ==================== UTILITIES ====================
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }

    function formatDate(date) {
        return date.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    function formatDueDate(dateStr) {
        if (!dateStr || dateStr === 'No Date') return 'No Date';

        const date = new Date(dateStr + 'T00:00:00');
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const diff = Math.floor((date - today) / (1000 * 60 * 60 * 24));

        if (diff < 0) return `${Math.abs(diff)}d overdue`;
        if (diff === 0) return 'Today';
        if (diff === 1) return 'Tomorrow';
        if (diff < 7) return date.toLocaleDateString('en-US', { weekday: 'short' });

        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }

    // ==================== PUBLIC API ====================
    return {
        init,
        navigateTo,
        openTaskModal,
        closeTaskModal,
        handleTaskSubmit,
        quickAddTask,
        toggleTaskStatus,
        openTask,
        saveSettings,
        toggleSection,
        updateTaskField,
        startInlineEdit,
        // Subtask functions
        toggleTaskExpand,
        addSubtask,
        toggleSubtaskStatus,
        updateSubtaskField,
        deleteSubtask,
        startSubtaskInlineEdit,
        // Filter functions
        updateFilter,
        clearFilters,
        applyFilters,
        // Client detail functions
        switchClientTab,
        openCallDetail,
    };
})();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const hubContainer = document.getElementById('tab-client-hub');
    if (hubContainer) {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.target.classList.contains('active')) {
                    ClientHub.init();
                    observer.disconnect();
                }
            });
        });

        observer.observe(hubContainer, { attributes: true, attributeFilter: ['class'] });

        if (hubContainer.classList.contains('active')) {
            ClientHub.init();
        }
    }
});
