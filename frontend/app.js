/**
 * FAST-NUCES Research Opportunity Portal
 * Frontend Application Controller — Three-Role RBAC
 * Roles: visitor (read-only) | faculty (manage own posts) | admin (manage all)
 */

const API_BASE  = '/api/opportunities';
const AUTH_BASE = '/api/auth';

// ─── Application State ────────────────────────────────────────────────────────
let currentRole  = 'visitor'; // 'visitor' | 'faculty' | 'admin'
let currentUser  = null;      // { username, full_name, email, ... }
let isAdmin      = false;     // legacy flag kept for backward compat
let opportunities    = [];
let departmentsList  = new Set();
let currentFilter    = { search: '', status: 'ALL', department: 'ALL' };
let pendingDeleteId  = null;

// ─── DOM Elements ─────────────────────────────────────────────────────────────
const dbStatusBadge        = document.getElementById('dbStatusBadge');
const authBadge            = document.getElementById('authBadge');
const authBadgeText        = document.getElementById('authBadgeText');
const btnGoToLogin         = document.getElementById('btnGoToLogin');
const btnFacultyLogin      = document.getElementById('btnFacultyLogin');
const btnFacultyDashboard  = document.getElementById('btnFacultyDashboard');
const btnLogoutAdmin       = document.getElementById('btnLogoutAdmin');
const btnLogoutFaculty     = document.getElementById('btnLogoutFaculty');
const roleNoticeBanner     = document.getElementById('roleNoticeBanner');
const bannerMessage        = document.getElementById('bannerMessage');

const opportunitiesContainer = document.getElementById('opportunitiesContainer');
const emptyState             = document.getElementById('emptyState');
const loadingIndicator       = document.getElementById('loadingIndicator');
const searchInput            = document.getElementById('searchInput');
const filterStatus           = document.getElementById('filterStatus');
const filterDepartment       = document.getElementById('filterDepartment');
const btnRefresh             = document.getElementById('btnRefresh');
const btnResetFilters        = document.getElementById('btnResetFilters');

const statTotal     = document.getElementById('statTotal');
const statOpen      = document.getElementById('statOpen');
const statPositions = document.getElementById('statPositions');
const statDepts     = document.getElementById('statDepts');

const opportunityModal  = document.getElementById('opportunityModal');
const modalTitle        = document.getElementById('modalTitle');
const opportunityForm   = document.getElementById('opportunityForm');
const btnOpenCreateModal= document.getElementById('btnOpenCreateModal');
const btnCloseModal     = document.getElementById('btnCloseModal');
const btnCancelModal    = document.getElementById('btnCancelModal');

const oppId          = document.getElementById('oppId');
const oppTitle       = document.getElementById('oppTitle');
const oppFaculty     = document.getElementById('oppFaculty');
const oppDepartment  = document.getElementById('oppDepartment');
const oppArea        = document.getElementById('oppArea');
const oppPositions   = document.getElementById('oppPositions');
const oppDeadline    = document.getElementById('oppDeadline');
const oppStatus      = document.getElementById('oppStatus');
const oppSkills      = document.getElementById('oppSkills');
const oppDescription = document.getElementById('oppDescription');

const detailsModal       = document.getElementById('detailsModal');
const btnCloseDetails    = document.getElementById('btnCloseDetails');
const btnCloseDetailsBtn = document.getElementById('btnCloseDetailsBtn');

const deleteModal      = document.getElementById('deleteModal');
const deleteOppTitle   = document.getElementById('deleteOppTitle');
const btnCancelDelete  = document.getElementById('btnCancelDelete');
const btnConfirmDelete = document.getElementById('btnConfirmDelete');

// ─── Initialisation ───────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  checkApiHealth();
  await checkAuthStatus();
  fetchOpportunities();
  setupEventListeners();
});

// ─── Auth Headers ─────────────────────────────────────────────────────────────
function getAuthHeaders() {
  const adminToken   = localStorage.getItem('admin_token');
  const facultyToken = localStorage.getItem('faculty_token');
  const token        = adminToken || facultyToken;
  const headers      = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return headers;
}

// ─── Auth Status ──────────────────────────────────────────────────────────────
async function checkAuthStatus() {
  try {
    const res  = await fetch(`${AUTH_BASE}/status`, {
      headers: getAuthHeaders(),
      credentials: 'include'
    });
    const data = await res.json();

    if (res.ok && data.authenticated) {
      currentRole = data.role;   // 'admin' or 'faculty'
      currentUser = data;
      isAdmin     = currentRole === 'admin';
      updateRoleUI();
    } else {
      currentRole = 'visitor';
      currentUser = null;
      isAdmin     = false;
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_user');
      localStorage.removeItem('faculty_token');
      localStorage.removeItem('faculty_user');
      updateRoleUI();
    }
  } catch {
    currentRole = 'visitor';
    isAdmin     = false;
    updateRoleUI();
  }
}

// ─── Role UI ──────────────────────────────────────────────────────────────────
function updateRoleUI() {
  const adminEls   = document.querySelectorAll('.admin-only');
  const facultyEls = document.querySelectorAll('.faculty-only');
  const visitorEls = document.querySelectorAll('.visitor-only');

  // Reset all
  adminEls.forEach(el   => el.classList.add('hidden'));
  facultyEls.forEach(el => el.classList.add('hidden'));
  visitorEls.forEach(el => el.classList.remove('hidden'));

  if (currentRole === 'admin') {
    adminEls.forEach(el   => el.classList.remove('hidden'));
    visitorEls.forEach(el => el.classList.add('hidden'));

    authBadge.className = 'auth-role-badge admin';
    authBadge.innerHTML = `<span class="role-icon">🛡️</span><span>Admin: ${escapeHtml(currentUser?.username || 'admin')}</span>`;

    roleNoticeBanner.className = 'role-banner admin-banner';
    bannerMessage.innerHTML    = `<strong>Administrator Mode</strong> — You are authenticated as <strong>${escapeHtml(currentUser?.username || 'admin')}</strong>. You have full CRUD access over all research opportunities.`;

  } else if (currentRole === 'faculty') {
    facultyEls.forEach(el => el.classList.remove('hidden'));
    visitorEls.forEach(el => el.classList.add('hidden'));

    authBadge.className = 'auth-role-badge faculty';
    authBadge.innerHTML = `<span class="role-icon">🎓</span><span>Faculty: ${escapeHtml(currentUser?.full_name || currentUser?.email || '')}</span>`;

    roleNoticeBanner.className = 'role-banner faculty-banner';
    bannerMessage.innerHTML    = `<strong>Faculty Mode</strong> — Welcome, <strong>${escapeHtml(currentUser?.full_name || '')}</strong>. Go to your <a href="/faculty/dashboard" style="color:#06b6d4;font-weight:600;">Dashboard</a> to post and manage your own research opportunities.`;

  } else {
    // Visitor
    authBadge.className = 'auth-role-badge visitor';
    authBadge.innerHTML = `<span class="role-icon">👤</span><span>Visitor (Read-Only)</span>`;

    roleNoticeBanner.className = 'role-banner visitor-banner';
    bannerMessage.innerHTML    = `You are browsing as a <strong>Visitor (Read-Only)</strong>. <a href="/faculty/register" style="color:#06b6d4;font-weight:600;">Register as faculty</a> to post research opportunities, or <a href="/faculty/login" style="color:#06b6d4;font-weight:600;">sign in</a> if you already have an account.`;
  }
}

// ─── Logout Handlers ──────────────────────────────────────────────────────────
async function handleAdminLogout() {
  try {
    await fetch(`${AUTH_BASE}/logout`, {
      method: 'POST', headers: getAuthHeaders(), credentials: 'include'
    });
  } catch {}
  localStorage.removeItem('admin_token');
  localStorage.removeItem('admin_user');
  currentRole = 'visitor'; currentUser = null; isAdmin = false;
  updateRoleUI();
  renderFilteredOpportunities();
  showToast('Administrator logged out. Switched to visitor mode.', 'info');
}

async function handleFacultyLogout() {
  try {
    await fetch('/api/faculty/logout', {
      method: 'POST', headers: getAuthHeaders(), credentials: 'include'
    });
  } catch {}
  localStorage.removeItem('faculty_token');
  localStorage.removeItem('faculty_user');
  currentRole = 'visitor'; currentUser = null; isAdmin = false;
  updateRoleUI();
  renderFilteredOpportunities();
  showToast('Logged out. Switched to visitor mode.', 'info');
}

// ─── API Health ───────────────────────────────────────────────────────────────
async function checkApiHealth() {
  try {
    const res  = await fetch('/api/health');
    const data = await res.json();
    if (data.status === 'online') {
      dbStatusBadge.className = 'connection-status connected';
      dbStatusBadge.innerHTML = `<span class="status-dot"></span><span class="status-text">API Online</span>`;
    } else {
      dbStatusBadge.className = 'connection-status disconnected';
      dbStatusBadge.innerHTML = `<span class="status-dot"></span><span class="status-text">DB Offline</span>`;
    }
  } catch {
    dbStatusBadge.className = 'connection-status disconnected';
    dbStatusBadge.innerHTML = `<span class="status-dot"></span><span class="status-text">API Offline</span>`;
  }
}

// ─── Event Listeners ──────────────────────────────────────────────────────────
function setupEventListeners() {
  searchInput.addEventListener('input', e => {
    currentFilter.search = e.target.value.toLowerCase().trim();
    renderFilteredOpportunities();
  });
  filterStatus.addEventListener('change', e => {
    currentFilter.status = e.target.value;
    renderFilteredOpportunities();
  });
  filterDepartment.addEventListener('change', e => {
    currentFilter.department = e.target.value;
    renderFilteredOpportunities();
  });
  btnRefresh.addEventListener('click', () => {
    fetchOpportunities();
    showToast('Refreshing research opportunities...', 'info');
  });
  btnResetFilters.addEventListener('click', () => {
    searchInput.value = ''; filterStatus.value = 'ALL'; filterDepartment.value = 'ALL';
    currentFilter = { search: '', status: 'ALL', department: 'ALL' };
    renderFilteredOpportunities();
  });

  if (btnLogoutAdmin)   btnLogoutAdmin.addEventListener('click', handleAdminLogout);
  if (btnLogoutFaculty) btnLogoutFaculty.addEventListener('click', handleFacultyLogout);

  if (btnOpenCreateModal) {
    btnOpenCreateModal.addEventListener('click', () => {
      if (currentRole !== 'admin') {
        showToast('Administrative privileges required.', 'error');
        return;
      }
      openCreateModal();
    });
  }

  btnCloseModal.addEventListener('click', () => closeModal(opportunityModal));
  btnCancelModal.addEventListener('click', () => closeModal(opportunityModal));
  btnCloseDetails.addEventListener('click', () => closeModal(detailsModal));
  btnCloseDetailsBtn.addEventListener('click', () => closeModal(detailsModal));
  btnCancelDelete.addEventListener('click', () => closeModal(deleteModal));
  btnConfirmDelete.addEventListener('click', handleConfirmDelete);

  opportunityForm.addEventListener('submit', handleFormSubmit);

  window.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      closeModal(opportunityModal);
      closeModal(detailsModal);
      closeModal(deleteModal);
    }
  });
  [opportunityModal, detailsModal, deleteModal].forEach(m => {
    m.addEventListener('click', e => { if (e.target === m) closeModal(m); });
  });
}

// ─── Fetch Opportunities ──────────────────────────────────────────────────────
async function fetchOpportunities() {
  loadingIndicator.classList.remove('hidden');
  opportunitiesContainer.innerHTML = '';
  emptyState.classList.add('hidden');

  try {
    const res  = await fetch(API_BASE);
    const data = await res.json();
    if (res.ok) {
      opportunities = data.data || [];
      buildDepartmentFilter();
      updateMetrics();
      renderFilteredOpportunities();
    } else {
      showToast('Failed to load opportunities.', 'error');
    }
  } catch {
    showToast('Network error. Could not load opportunities.', 'error');
  } finally {
    loadingIndicator.classList.add('hidden');
  }
}

// ─── Metrics ──────────────────────────────────────────────────────────────────
function updateMetrics() {
  const open   = opportunities.filter(o => o.status === 'Open');
  const seats  = opportunities.reduce((s, o) => s + (parseInt(o.available_positions) || 0), 0);
  departmentsList = new Set(opportunities.map(o => o.department).filter(Boolean));
  statTotal.textContent    = opportunities.length;
  statOpen.textContent     = open.length;
  statPositions.textContent= seats;
  statDepts.textContent    = departmentsList.size;
}

function buildDepartmentFilter() {
  const depts = new Set(opportunities.map(o => o.department).filter(Boolean));
  const current = filterDepartment.value;
  filterDepartment.innerHTML = '<option value="ALL">All Departments</option>';
  depts.forEach(d => {
    const opt = document.createElement('option');
    opt.value = d; opt.textContent = d;
    if (d === current) opt.selected = true;
    filterDepartment.appendChild(opt);
  });
}

// ─── Render Cards ─────────────────────────────────────────────────────────────
function renderFilteredOpportunities() {
  const filtered = opportunities.filter(o => {
    const s = currentFilter.search;
    const matchSearch = !s ||
      (o.title || '').toLowerCase().includes(s) ||
      (o.faculty_name || '').toLowerCase().includes(s) ||
      (o.required_skills || '').toLowerCase().includes(s) ||
      (o.department || '').toLowerCase().includes(s) ||
      (o.research_area || '').toLowerCase().includes(s);
    const matchStatus = currentFilter.status === 'ALL' || o.status === currentFilter.status;
    const matchDept   = currentFilter.department === 'ALL' || o.department === currentFilter.department;
    return matchSearch && matchStatus && matchDept;
  });

  opportunitiesContainer.innerHTML = '';
  if (!filtered.length) {
    emptyState.classList.remove('hidden');
    return;
  }
  emptyState.classList.add('hidden');
  filtered.forEach(o => opportunitiesContainer.appendChild(buildCard(o)));
}

function buildCard(o) {
  const card = document.createElement('article');
  card.className = 'opp-card';

  // Determine if current user can edit/delete this card
  // Admin: all cards | Faculty: only their own (matched by faculty_id or faculty_email)
  let showEdit = false;
  if (currentRole === 'admin') {
    showEdit = true;
  } else if (currentRole === 'faculty' && currentUser) {
    showEdit = (o.faculty_id && o.faculty_id === currentUser.id) ||
               (o.faculty_email && o.faculty_email === currentUser.email);
  }

  const statusClass = (o.status === 'Open') ? 'open' : 'closed';

  // Skills chips
  const skillsList = (o.required_skills || '').split(',').map(s => s.trim()).filter(Boolean);
  const skillsHtml = skillsList.slice(0, 4)
    .map(s => `<span class="skill-pill">${escapeHtml(s)}</span>`).join('');

  card.innerHTML = `
    <div>
      <div class="card-top">
        <div style="display:flex;align-items:center;gap:0.4rem;flex-wrap:wrap;">
          <span class="dept-badge">${escapeHtml(o.department || 'General')}</span>
          <span style="font-size:0.72rem;color:var(--text-dim);font-weight:600;">#${o.id}</span>
        </div>
        <div style="display:flex;align-items:center;gap:0.45rem;flex-wrap:wrap;">
          <span class="status-badge ${statusClass}">${escapeHtml(o.status)}</span>
        </div>
      </div>

      <h3 class="card-title">${escapeHtml(o.title)}</h3>
      
      <div class="card-area">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="2" y1="12" x2="22" y2="12"></line>
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
        </svg>
        ${escapeHtml(o.research_area || 'General Research')}
      </div>

      <p class="card-desc">${escapeHtml(o.description || '')}</p>

      <div class="card-meta-list">
        <div class="meta-row">
          <span class="meta-label-dim">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            Supervisor
          </span>
          <span class="meta-val-highlight">${escapeHtml(o.faculty_name)}</span>
        </div>

        <div class="meta-row">
          <span class="meta-label-dim">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="16" y1="2" x2="16" y2="6"></line>
              <line x1="8" y1="2" x2="8" y2="6"></line>
              <line x1="3" y1="10" x2="21" y2="10"></line>
            </svg>
            Deadline
          </span>
          <span class="meta-val-highlight">${escapeHtml(o.deadline || 'N/A')}</span>
        </div>

        <div class="meta-row">
          <span class="meta-label-dim">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
            Positions
          </span>
          <span class="meta-val-highlight text-cyan">${o.available_positions} ${o.available_positions == 1 ? 'seat' : 'seats'}</span>
        </div>
      </div>

      <div class="skills-preview">
        ${skillsHtml}
      </div>
    </div>

    <div class="card-actions">
      <div class="action-group-left">
        <button class="btn btn-secondary btn-sm" onclick="openDetailsModal(${o.id})">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
            <circle cx="12" cy="12" r="3"></circle>
          </svg>
          View Details
        </button>
        ${showEdit ? `
          <button class="btn btn-secondary btn-sm" onclick="openEditModal(${o.id})">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
            Edit
          </button>
          ${o.status === 'Open' ? `
            <button class="btn btn-secondary btn-sm" onclick="toggleOpportunityStatus(${o.id}, 'Closed')" title="Click to close this opening" style="border-color:rgba(244,63,94,0.35);color:#fda4af;">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="15" y1="9" x2="9" y2="15"></line>
                <line x1="9" y1="9" x2="15" y2="15"></line>
              </svg>
              Close
            </button>
          ` : `
            <button class="btn btn-secondary btn-sm" onclick="toggleOpportunityStatus(${o.id}, 'Open')" title="Click to reopen this opening" style="border-color:rgba(16,185,129,0.35);color:#6ee7b7;">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
              Reopen
            </button>
          `}
        ` : ''}
      </div>
      ${showEdit ? `
        <button class="btn btn-danger btn-sm" title="Delete Opportunity" onclick="openDeleteModal(${o.id})">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      ` : ''}
    </div>
  `;

  return card;
}

// ─── Direct Status Toggle ─────────────────────────────────────────────────────
async function toggleOpportunityStatus(id, newStatus) {
  try {
    const res = await fetch(`${API_BASE}/${id}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify({ status: newStatus })
    });
    const data = await res.json();
    if (res.ok) {
      showToast(`Opportunity #${id} marked as ${newStatus}.`, 'success');
      const opp = opportunities.find(o => o.id === id);
      if (opp) opp.status = newStatus;
      updateMetrics();
      renderFilteredOpportunities();
    } else {
      showToast(data.message || `Failed to update status to ${newStatus}.`, 'error');
    }
  } catch (err) {
    showToast('Network error while updating status.', 'error');
  }
}

// ─── Modal Logic ──────────────────────────────────────────────────────────────
function openModal(modal)  { modal.classList.remove('hidden'); document.body.style.overflow = 'hidden'; }
function closeModal(modal) { modal.classList.add('hidden');    document.body.style.overflow = ''; }

function clearFormErrors() {
  ['err_oppTitle','err_oppFaculty','err_oppDepartment','err_oppArea',
   'err_oppPositions','err_oppDeadline','err_oppStatus','err_oppSkills','err_oppDescription']
    .forEach(id => { const el = document.getElementById(id); if (el) el.textContent = ''; });
}

function openCreateModal() {
  clearFormErrors();
  oppId.value = ''; opportunityForm.reset();
  modalTitle.textContent = 'Post New Research Opportunity';
  openModal(opportunityModal);
}

function openEditModal(id) {
  const o = opportunities.find(x => x.id === id);
  if (!o) return;
  clearFormErrors();
  oppId.value          = o.id;
  oppTitle.value       = o.title       || '';
  oppFaculty.value     = o.faculty_name|| '';
  oppDepartment.value  = o.department  || '';
  oppArea.value        = o.research_area || '';
  oppPositions.value   = o.available_positions || '';
  oppDeadline.value    = o.deadline    || '';
  oppStatus.value      = o.status      || 'Open';
  oppSkills.value      = o.required_skills || '';
  oppDescription.value = o.description || '';
  modalTitle.textContent = 'Edit Research Opportunity';
  openModal(opportunityModal);
}

function openDeleteModal(id) {
  const o = opportunities.find(x => x.id === id);
  if (!o) return;
  pendingDeleteId = id;
  deleteOppTitle.textContent = o.title;
  openModal(deleteModal);
}

function openDetailsModal(id) {
  const o = opportunities.find(x => x.id === id);
  if (!o) return;
  document.getElementById('detailStatusBadge').className = `status-badge ${o.status === 'Open' ? 'open' : 'closed'}`;
  document.getElementById('detailStatusBadge').textContent = o.status;
  document.getElementById('detailTitle').textContent       = o.title;
  document.getElementById('detailFaculty').textContent     = o.faculty_name;
  document.getElementById('detailDepartment').textContent  = o.department;
  document.getElementById('detailArea').textContent        = o.research_area;
  document.getElementById('detailPositions').textContent   = `${o.available_positions} position${o.available_positions != 1 ? 's' : ''}`;
  document.getElementById('detailDeadline').textContent    = o.deadline || 'N/A';
  document.getElementById('detailId').textContent          = `#${o.id}`;
  document.getElementById('detailDescription').textContent = o.description;

  const chipsContainer = document.getElementById('detailSkillsChips');
  chipsContainer.innerHTML = (o.required_skills || '').split(',')
    .map(s => `<span class="skill-pill">${escapeHtml(s.trim())}</span>`).join('');

  openModal(detailsModal);
}

// ─── Form Submit (Create / Update) ────────────────────────────────────────────
async function handleFormSubmit(e) {
  e.preventDefault();
  clearFormErrors();

  const id       = oppId.value;
  const payload  = {
    title:               oppTitle.value.trim(),
    faculty_name:        oppFaculty.value.trim(),
    department:          oppDepartment.value.trim(),
    research_area:       oppArea.value.trim(),
    available_positions: parseInt(oppPositions.value),
    deadline:            oppDeadline.value,
    status:              oppStatus.value,
    required_skills:     oppSkills.value.trim(),
    description:         oppDescription.value.trim()
  };

  // Validate
  let valid = true;
  const setErr = (elId, msg) => { const el = document.getElementById(elId); if (el) { el.textContent = msg; valid = false; } };
  if (!payload.title)               setErr('err_oppTitle',       'Title is required.');
  if (!payload.faculty_name)        setErr('err_oppFaculty',     'Faculty name is required.');
  if (!payload.department)          setErr('err_oppDepartment',  'Department is required.');
  if (!payload.research_area)       setErr('err_oppArea',        'Research area is required.');
  if (!payload.available_positions || payload.available_positions <= 0)
                                    setErr('err_oppPositions',   'Must be a positive number.');
  if (!payload.deadline)            setErr('err_oppDeadline',    'Deadline is required.');
  if (!payload.required_skills)     setErr('err_oppSkills',      'Required skills are required.');
  if (!payload.description)         setErr('err_oppDescription', 'Description is required.');
  if (!valid) return;

  const isEdit = !!id;
  const url    = isEdit ? `${API_BASE}/${id}` : API_BASE;
  const method = isEdit ? 'PUT' : 'POST';

  const submitBtn = document.getElementById('btnSubmitOpp');
  submitBtn.disabled = true;

  try {
    const res  = await fetch(url, {
      method, headers: getAuthHeaders(), credentials: 'include',
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (!res.ok) {
      showToast(data.message || 'Operation failed.', 'error');
      return;
    }

    closeModal(opportunityModal);
    showToast(isEdit ? 'Opportunity updated!' : 'Opportunity created!', 'success');
    await fetchOpportunities();
  } catch {
    showToast('Network error. Please try again.', 'error');
  } finally {
    submitBtn.disabled = false;
  }
}

// ─── Delete ───────────────────────────────────────────────────────────────────
async function handleConfirmDelete() {
  if (!pendingDeleteId) return;
  btnConfirmDelete.disabled = true;

  try {
    const res  = await fetch(`${API_BASE}/${pendingDeleteId}`, {
      method: 'DELETE', headers: getAuthHeaders(), credentials: 'include'
    });
    const data = await res.json();

    if (!res.ok) {
      showToast(data.message || 'Delete failed.', 'error');
      return;
    }
    closeModal(deleteModal);
    showToast('Opportunity deleted successfully.', 'success');
    pendingDeleteId = null;
    await fetchOpportunities();
  } catch {
    showToast('Network error. Please try again.', 'error');
  } finally {
    btnConfirmDelete.disabled = false;
  }
}

// ─── Toast ────────────────────────────────────────────────────────────────────
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const iconMap = {
    success: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`,
    error:   `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
    info:    `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`
  };

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `${iconMap[type] || iconMap.info}<span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'all .3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ─── Utility ──────────────────────────────────────────────────────────────────
function escapeHtml(str) {
  const d = document.createElement('div');
  d.textContent = str || '';
  return d.innerHTML;
}
