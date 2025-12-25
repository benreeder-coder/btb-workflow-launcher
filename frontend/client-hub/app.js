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
        flag: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>`,
        user: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
        morning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`,
        afternoon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>`,
        evening: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`,
    };

    // ==================== INITIALIZATION ====================
    function init() {
        renderSidebar();
        loadSettings();
        loadClients();
        navigateTo('today');
        setupQuickAdd();
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
                state.clients = data.clients || [];
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
            // Get inbox count
            const inboxResponse = await fetch(`${API_BASE}/api/hub/views/inbox`);
            if (inboxResponse.ok) {
                const data = await inboxResponse.json();
                const count = data.tasks?.length || 0;
                const badge = document.getElementById('inbox-count');
                if (badge) {
                    badge.textContent = count;
                    badge.style.display = count > 0 ? '' : 'none';
                }
            }

            // Get overdue count
            const overdueResponse = await fetch(`${API_BASE}/api/hub/views/overdue`);
            if (overdueResponse.ok) {
                const data = await overdueResponse.json();
                const count = data.tasks?.length || 0;
                const badge = document.getElementById('overdue-count');
                if (badge) {
                    badge.textContent = count;
                    badge.style.display = count > 0 ? '' : 'none';
                }
            }

            // Get pending count
            const pendingResponse = await fetch(`${API_BASE}/api/hub/views/pending`);
            if (pendingResponse.ok) {
                const data = await pendingResponse.json();
                const count = data.tasks?.length || 0;
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

    // ==================== TODAY VIEW ====================
    async function renderTodayView(container) {
        container.innerHTML = '<div class="hub-loading"><div class="spinner"></div></div>';

        try {
            const response = await fetch(`${API_BASE}/api/hub/views/today`);
            if (!response.ok) throw new Error('Failed to load');
            const data = await response.json();

            const { meetings = [], morning_tasks = [], afternoon_tasks = [], evening_tasks = [], unscheduled_tasks = [], capacity_used = 0, capacity_total = 360 } = data;

            let html = `
                <div class="quick-add">
                    <input type="text" id="quick-add-input" class="quick-add-input" placeholder="Add task: @client p1 due:tomorrow #morning ~30m" />
                    <button class="quick-add-btn" onclick="ClientHub.quickAddTask()">
                        ${icons.plus} Add
                    </button>
                </div>

                <div class="capacity-meter">
                    <div class="capacity-header">
                        <span class="capacity-label">Today's Capacity</span>
                        <span class="capacity-value">${Math.round(capacity_used / 60)}h / ${Math.round(capacity_total / 60)}h</span>
                    </div>
                    <div class="capacity-bar">
                        <div class="capacity-fill ${capacity_used > capacity_total ? 'danger' : capacity_used > capacity_total * 0.8 ? 'warning' : ''}" style="width: ${Math.min(100, (capacity_used / capacity_total) * 100)}%"></div>
                    </div>
                </div>
            `;

            // Meetings
            if (meetings.length > 0) {
                html += `
                    <div class="meetings-section">
                        <div class="task-section-header">
                            ${icons.calendar}
                            <span class="task-section-title">Meetings</span>
                            <span class="task-section-count">${meetings.length}</span>
                        </div>
                        ${meetings.map(m => renderMeetingCard(m)).join('')}
                    </div>
                `;
            }

            // Morning tasks
            if (morning_tasks.length > 0) {
                html += renderTaskSection('Morning', icons.morning, morning_tasks);
            }

            // Afternoon tasks
            if (afternoon_tasks.length > 0) {
                html += renderTaskSection('Afternoon', icons.afternoon, afternoon_tasks);
            }

            // Evening tasks
            if (evening_tasks.length > 0) {
                html += renderTaskSection('Evening', icons.evening, evening_tasks);
            }

            // Unscheduled
            if (unscheduled_tasks.length > 0) {
                html += renderTaskSection('Unscheduled', icons.inbox, unscheduled_tasks);
            }

            if (meetings.length === 0 && morning_tasks.length === 0 && afternoon_tasks.length === 0 && evening_tasks.length === 0 && unscheduled_tasks.length === 0) {
                html += `
                    <div class="empty-state">
                        <div class="empty-state-icon">${icons.completed}</div>
                        <h3>All clear!</h3>
                        <p>No tasks for today. Enjoy your day or add some tasks above.</p>
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

    function renderTaskSection(title, icon, tasks) {
        return `
            <div class="task-section">
                <div class="task-section-header">
                    ${icon}
                    <span class="task-section-title">${title}</span>
                    <span class="task-section-count">${tasks.length}</span>
                </div>
                ${tasks.map(t => renderTaskCard(t)).join('')}
            </div>
        `;
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

    function renderTaskCard(task) {
        const isCompleted = task.status === 'COMPLETED';
        const isOverdue = task.due_date && new Date(task.due_date) < new Date() && !isCompleted;
        const isPending = task.status === 'PENDING';

        let cardClass = 'task-card';
        if (isCompleted) cardClass += ' completed';
        if (isOverdue && isPending) cardClass += ' overdue-pending';
        else if (isOverdue) cardClass += ' overdue';
        else if (isPending) cardClass += ' pending';

        const priorityClass = `priority ${task.priority?.toLowerCase() || 'p2'}`;

        return `
            <div class="${cardClass}" onclick="ClientHub.openTask('${task.id}')">
                <div class="task-card-header">
                    <div class="task-checkbox ${isCompleted ? 'checked' : ''}" onclick="event.stopPropagation(); ClientHub.toggleTaskStatus('${task.id}', '${task.status}')">
                        ${icons.check}
                    </div>
                    <span class="task-title">${escapeHtml(task.title)}</span>
                </div>
                <div class="task-meta">
                    <span class="task-badge ${priorityClass}">${task.priority || 'P2'}</span>
                    ${task.due_date ? `<span class="task-badge due ${isOverdue ? 'overdue' : task.due_date === new Date().toISOString().split('T')[0] ? 'today' : ''}">${icons.clock} ${formatDueDate(task.due_date)}</span>` : ''}
                    ${task.client ? `<span class="task-badge client">${escapeHtml(task.client.name)}</span>` : ''}
                    ${task.estimated_minutes ? `<span class="task-badge time">${task.estimated_minutes}m</span>` : ''}
                </div>
                ${task.subtasks?.length > 0 ? renderSubtaskProgress(task.subtasks) : ''}
            </div>
        `;
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

            const tasks = data.tasks || [];

            if (tasks.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">${icons.inbox}</div>
                        <h3>Inbox Zero!</h3>
                        <p>All tasks have been triaged.</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = `
                <div class="task-section">
                    <div class="task-section-header">
                        ${icons.inbox}
                        <span class="task-section-title">Needs Triage</span>
                        <span class="task-section-count">${tasks.length}</span>
                    </div>
                    ${tasks.map(t => renderTaskCard(t)).join('')}
                </div>
            `;
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

            const tasks = data.tasks || [];

            if (tasks.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">${icons.pending}</div>
                        <h3>Nothing Pending</h3>
                        <p>No tasks are waiting on external input.</p>
                    </div>
                `;
                return;
            }

            // Group by client
            const grouped = {};
            tasks.forEach(task => {
                const key = task.client?.name || 'No Client';
                if (!grouped[key]) grouped[key] = [];
                grouped[key].push(task);
            });

            let html = '';
            Object.entries(grouped).forEach(([clientName, clientTasks]) => {
                html += `
                    <div class="task-section">
                        <div class="task-section-header">
                            ${icons.user}
                            <span class="task-section-title">${escapeHtml(clientName)}</span>
                            <span class="task-section-count">${clientTasks.length}</span>
                        </div>
                        ${clientTasks.map(t => renderTaskCard(t)).join('')}
                    </div>
                `;
            });

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

            const tasks = data.tasks || [];

            if (tasks.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">${icons.completed}</div>
                        <h3>All Caught Up!</h3>
                        <p>No overdue tasks.</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = `
                <div class="task-section">
                    <div class="task-section-header">
                        ${icons.overdue}
                        <span class="task-section-title">Overdue</span>
                        <span class="task-section-count">${tasks.length}</span>
                    </div>
                    ${tasks.map(t => renderTaskCard(t)).join('')}
                </div>
            `;
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

            const tasks = data.tasks || [];

            let html = `
                <div class="filter-tabs">
                    <button class="filter-tab ${days === 7 ? 'active' : ''}" onclick="ClientHub.navigateTo('upcoming', { days: 7 })">7 Days</button>
                    <button class="filter-tab ${days === 14 ? 'active' : ''}" onclick="ClientHub.navigateTo('upcoming', { days: 14 })">14 Days</button>
                    <button class="filter-tab ${days === 30 ? 'active' : ''}" onclick="ClientHub.navigateTo('upcoming', { days: 30 })">30 Days</button>
                </div>
            `;

            if (tasks.length === 0) {
                html += `
                    <div class="empty-state">
                        <div class="empty-state-icon">${icons.upcoming}</div>
                        <h3>Clear Schedule</h3>
                        <p>No tasks in the next ${days} days.</p>
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

                Object.entries(grouped).forEach(([date, dateTasks]) => {
                    html += `
                        <div class="task-section">
                            <div class="task-section-header">
                                ${icons.calendar}
                                <span class="task-section-title">${formatDueDate(date)}</span>
                                <span class="task-section-count">${dateTasks.length}</span>
                            </div>
                            ${dateTasks.map(t => renderTaskCard(t)).join('')}
                        </div>
                    `;
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

            const clients = data.clients || [];

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
    async function renderClientDetailView(container, params) {
        container.innerHTML = '<div class="hub-loading"><div class="spinner"></div></div>';

        try {
            const [clientRes, tasksRes] = await Promise.all([
                fetch(`${API_BASE}/api/hub/clients/${params.id}`),
                fetch(`${API_BASE}/api/hub/tasks?client_id=${params.id}`)
            ]);

            if (!clientRes.ok) throw new Error('Failed to load client');

            const client = await clientRes.json();
            const tasksData = tasksRes.ok ? await tasksRes.json() : { tasks: [] };
            const tasks = tasksData.tasks || [];

            let html = `
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">${tasks.filter(t => t.status !== 'COMPLETED').length}</div>
                        <div class="stat-label">Open Tasks</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value success">${tasks.filter(t => t.status === 'COMPLETED').length}</div>
                        <div class="stat-label">Completed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value ${client.health_status === 'RED' ? 'danger' : client.health_status === 'YELLOW' ? 'warning' : 'success'}">${client.health_status || 'GREEN'}</div>
                        <div class="stat-label">Health</div>
                    </div>
                </div>
            `;

            if (tasks.length === 0) {
                html += `
                    <div class="empty-state">
                        <div class="empty-state-icon">${icons.inbox}</div>
                        <h3>No Tasks</h3>
                        <p>No tasks for this client yet.</p>
                    </div>
                `;
            } else {
                html += `
                    <div class="task-section">
                        <div class="task-section-header">
                            ${icons.inbox}
                            <span class="task-section-title">Tasks</span>
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

    // ==================== CALENDAR VIEW ====================
    async function renderCalendarView(container) {
        container.innerHTML = '<div class="hub-loading"><div class="spinner"></div></div>';

        try {
            const today = new Date().toISOString().split('T')[0];
            const nextWeek = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

            const response = await fetch(`${API_BASE}/api/hub/calendar?start_date=${today}&end_date=${nextWeek}`);
            if (!response.ok) throw new Error('Failed to load');
            const data = await response.json();

            const events = data.events || [];

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

            // Group by date
            const grouped = {};
            events.forEach(event => {
                const dateKey = new Date(event.start_time).toISOString().split('T')[0];
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
    function setupQuickAdd() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.target.id === 'quick-add-input') {
                e.preventDefault();
                quickAddTask();
            }
        });
    }

    async function quickAddTask() {
        const input = document.getElementById('quick-add-input');
        if (!input) return;

        const text = input.value.trim();
        if (!text) return;

        // Parse quick add syntax
        const parsed = parseQuickAdd(text);

        try {
            const response = await fetch(`${API_BASE}/api/hub/tasks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(parsed)
            });

            if (response.ok) {
                input.value = '';
                navigateTo(state.currentView); // Refresh current view
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

        // Extract priority (p0, p1, p2, p3)
        const priorityMatch = text.match(/\bp([0-3])\b/i);
        if (priorityMatch) {
            task.priority = `P${priorityMatch[1]}`;
            title = title.replace(/\bp[0-3]\b\s*/gi, '');
        }

        // Extract due date (due:tomorrow, due:monday, due:2024-01-15)
        const dueMatch = text.match(/due:(\S+)/i);
        if (dueMatch) {
            const dueStr = dueMatch[1].toLowerCase();
            const today = new Date();

            if (dueStr === 'today') {
                task.due_date = today.toISOString().split('T')[0];
            } else if (dueStr === 'tomorrow') {
                today.setDate(today.getDate() + 1);
                task.due_date = today.toISOString().split('T')[0];
            } else if (/^\d{4}-\d{2}-\d{2}$/.test(dueStr)) {
                task.due_date = dueStr;
            }
            title = title.replace(/due:\S+\s*/gi, '');
        }

        // Extract time estimate (~30m, ~1h)
        const timeMatch = text.match(/~(\d+)(m|h)/i);
        if (timeMatch) {
            const value = parseInt(timeMatch[1]);
            const unit = timeMatch[2].toLowerCase();
            task.estimated_minutes = unit === 'h' ? value * 60 : value;
            title = title.replace(/~\d+[mh]\s*/gi, '');
        }

        // Extract timebox (#morning, #afternoon, #evening)
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

    function openTask(taskId) {
        // TODO: Implement task detail modal/view
        console.log('Open task:', taskId);
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

        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);

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
        quickAddTask,
        toggleTaskStatus,
        openTask,
        saveSettings,
    };
})();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if we're on the Client Hub tab
    const hubContainer = document.getElementById('tab-client-hub');
    if (hubContainer) {
        // Delay init until tab is first shown
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.target.classList.contains('active')) {
                    ClientHub.init();
                    observer.disconnect();
                }
            });
        });

        observer.observe(hubContainer, { attributes: true, attributeFilter: ['class'] });

        // Also init if already active
        if (hubContainer.classList.contains('active')) {
            ClientHub.init();
        }
    }
});
