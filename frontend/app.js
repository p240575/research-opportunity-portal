/**
 * FAST-NUCES Research Opportunity Portal
 * Frontend Application Controller
 * Handles REST API communication, Role-Based Access Control (RBAC),
 * public visitor view, admin authentication, CRUD operations, and validations.
 */

const API_BASE = '/api/opportunities';
const AUTH_BASE = '/api/auth';

// Application State
let isAdmin = false;
let currentAdminUser = null;
let opportunities = [];
let departmentsList = new Set();
let currentFilter = {
  search: '',
  status: 'ALL',
  department: 'ALL'
};
let pendingDeleteId = null;

// DOM Elements - Navigation & Auth
const dbStatusBadge = document.getElementById('dbStatusBadge');
const authBadge = document.getElementById('authBadge');
const authBadgeText = document.getElementById('authBadgeText');
const btnGoToLogin = document.getElementById('btnGoToLogin');
const btnLogoutAdmin = document.getElementById('btnLogoutAdmin');
const roleNoticeBanner = document.getElementById('roleNoticeBanner');
const bannerMessage = document.getElementById('bannerMessage');

// DOM Elements - Content & Filters
const opportunitiesContainer = document.getElementById('opportunitiesContainer');
const emptyState = document.getElementById('emptyState');
const loadingIndicator = document.getElementById('loadingIndicator');
const searchInput = document.getElementById('searchInput');
const filterStatus = document.getElementById('filterStatus');
const filterDepartment = document.getElementById('filterDepartment');
const btnRefresh = document.getElementById('btnRefresh');
const btnResetFilters = document.getElementById('btnResetFilters');

// Metrics Elements
const statTotal = document.getElementById('statTotal');
const statOpen = document.getElementById('statOpen');
const statPositions = document.getElementById('statPositions');
const statDepts = document.getElementById('statDepts');

// Form Modal Elements (Admin Only)
const opportunityModal = document.getElementById('opportunityModal');
const modalTitle = document.getElementById('modalTitle');
const opportunityForm = document.getElementById('opportunityForm');
const btnOpenCreateModal = document.getElementById('btnOpenCreateModal');
const btnCloseModal = document.getElementById('btnCloseModal');
const btnCancelModal = document.getElementById('btnCancelModal');

// Form Input Elements
const oppId = document.getElementById('oppId');
const oppTitle = document.getElementById('oppTitle');
const oppFaculty = document.getElementById('oppFaculty');
const oppDepartment = document.getElementById('oppDepartment');
const oppArea = document.getElementById('oppArea');
const oppPositions = document.getElementById('oppPositions');
const oppDeadline = document.getElementById('oppDeadline');
const oppStatus = document.getElementById('oppStatus');
const oppSkills = document.getElementById('oppSkills');
const oppDescription = document.getElementById('oppDescription');

// Detail Modal Elements (Public & Admin)
const detailsModal = document.getElementById('detailsModal');
const btnCloseDetails = document.getElementById('btnCloseDetails');
const btnCloseDetailsBtn = document.getElementById('btnCloseDetailsBtn');

// Delete Modal Elements (Admin Only)
const deleteModal = document.getElementById('deleteModal');
const deleteOppTitle = document.getElementById('deleteOppTitle');
const btnCancelDelete = document.getElementById('btnCancelDelete');
const btnConfirmDelete = document.getElementById('btnConfirmDelete');

// ==============================================================
// INITIALIZATION
// ==============================================================
document.addEventListener('DOMContentLoaded', async () => {
  checkApiHealth();
  await checkAuthStatus();
  fetchOpportunities();
  setupEventListeners();
});

function getAuthHeaders() {
  const token = localStorage.getItem('admin_token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

// ==============================================================
// AUTHENTICATION & ROLE MANAGEMENT
// ==============================================================

async function checkAuthStatus() {
  try {
    const res = await fetch(`${AUTH_BASE}/status`, {
      headers: getAuthHeaders(),
      credentials: 'include'
    });
    const data = await res.json();

    if (res.ok && data.authenticated) {
      isAdmin = true;
      currentAdminUser = { username: data.username || 'admin' };
      updateRoleUI(true);
    } else {
      isAdmin = false;
      currentAdminUser = null;
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_user');
      updateRoleUI(false);
    }
  } catch (err) {
    console.warn('Could not verify auth status:', err);
    isAdmin = false;
    updateRoleUI(false);
  }
}

function updateRoleUI(adminLoggedIn) {
  const adminOnlyElements = document.querySelectorAll('.admin-only');
  const visitorOnlyElements = document.querySelectorAll('.visitor-only');

  if (adminLoggedIn) {
    // Show admin controls
    adminOnlyElements.forEach(el => el.classList.remove('hidden'));
    visitorOnlyElements.forEach(el => el.classList.add('hidden'));

    authBadge.className = 'auth-role-badge admin';
    authBadge.innerHTML = `<span class="role-icon">🛡️</span><span>Admin: ${escapeHtml(currentAdminUser?.username || 'admin')}</span>`;

    if (roleNoticeBanner && bannerMessage) {
      roleNoticeBanner.className = 'role-banner admin-banner';
      bannerMessage.innerHTML = `Administrator Mode Active: You are authenticated as <strong>${escapeHtml(currentAdminUser?.username || 'admin')}</strong> with full management permissions (Create, Edit, Close/Reopen, and Delete).`;
    }
  } else {
    // Visitor Mode (Strict Read-Only)
    adminOnlyElements.forEach(el => el.classList.add('hidden'));
    visitorOnlyElements.forEach(el => el.classList.remove('hidden'));

    authBadge.className = 'auth-role-badge visitor';
    authBadge.innerHTML = `<span class="role-icon">👤</span><span>Visitor (Read-Only)</span>`;

    if (roleNoticeBanner && bannerMessage) {
      roleNoticeBanner.className = 'role-banner visitor-banner';
      bannerMessage.innerHTML = `You are currently browsing research opportunities as a <strong>Visitor (Read-Only)</strong>. No login or registration required. Administrative CRUD controls are restricted to the verified portal administrator.`;
    }
  }
}

async function handleAdminLogout() {
  try {
    const res = await fetch(`${AUTH_BASE}/logout`, {
      method: 'POST',
      headers: getAuthHeaders(),
      credentials: 'include'
    });
    
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');
    isAdmin = false;
    currentAdminUser = null;
    updateRoleUI(false);
    renderFilteredOpportunities();
    showToast('Administrator logged out. Switched to public visitor mode.', 'info');
  } catch (err) {
    showToast('Logout encountered an issue.', 'error');
  }
}

// ==============================================================
// EVENT LISTENERS
// ==============================================================

function setupEventListeners() {
  // Search & Filters
  searchInput.addEventListener('input', (e) => {
    currentFilter.search = e.target.value.toLowerCase().trim();
    renderFilteredOpportunities();
  });

  filterStatus.addEventListener('change', (e) => {
    currentFilter.status = e.target.value;
    renderFilteredOpportunities();
  });

  filterDepartment.addEventListener('change', (e) => {
    currentFilter.department = e.target.value;
    renderFilteredOpportunities();
  });

  btnRefresh.addEventListener('click', () => {
    fetchOpportunities();
    showToast('Refreshing research opportunities...', 'info');
  });

  btnResetFilters.addEventListener('click', () => {
    searchInput.value = '';
    filterStatus.value = 'ALL';
    filterDepartment.value = 'ALL';
    currentFilter = { search: '', status: 'ALL', department: 'ALL' };
    renderFilteredOpportunities();
  });

  // Admin Logout
  if (btnLogoutAdmin) {
    btnLogoutAdmin.addEventListener('click', handleAdminLogout);
  }

  // Modal Open/Close
  if (btnOpenCreateModal) {
    btnOpenCreateModal.addEventListener('click', () => {
      if (!isAdmin) {
        showToast('Administrative privileges required to post opportunities.', 'error');
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
  btnConfirmDelete.addEventListener('click', () => handleConfirmDelete());

  // Form Submit
  opportunityForm.addEventListener('submit', handleFormSubmit);

  // Close modals on escape key or clicking backdrop
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeModal(opportunityModal);
      closeModal(detailsModal);
      closeModal(deleteModal);
    }
  });

  [opportunityModal, detailsModal, deleteModal].forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeModal(modal);
      }
    });
  });
}

// ==============================================================
// API CALLS (RESEARCH OPPORTUNITIES)
// ==============================================================

async function checkApiHealth() {
  try {
    const res = await fetch('/api/health');
    const data = await res.json();
    if (res.ok && data.status === 'online') {
      dbStatusBadge.className = 'connection-status online';
      dbStatusBadge.querySelector('.status-text').textContent = 'API & MySQL Connected';
    } else {
      dbStatusBadge.className = 'connection-status offline';
      dbStatusBadge.querySelector('.status-text').textContent = 'Database Offline';
    }
  } catch (err) {
    dbStatusBadge.className = 'connection-status offline';
    dbStatusBadge.querySelector('.status-text').textContent = 'API Unreachable';
  }
}

async function fetchOpportunities() {
  showLoading(true);
  try {
    const response = await fetch(API_BASE);
    if (!response.ok) {
      throw new Error(`Server returned HTTP ${response.status}`);
    }
    const result = await response.json();
    opportunities = result.data || [];
    updateDepartmentFilterOptions();
    updateMetrics();
    renderFilteredOpportunities();
  } catch (error) {
    console.error('Fetch error:', error);
    showToast(`Error connecting to API: ${error.message}`, 'error');
    opportunities = [];
    renderFilteredOpportunities();
  } finally {
    showLoading(false);
  }
}

async function fetchSingleOpportunity(id) {
  try {
    const response = await fetch(`${API_BASE}/${id}`);
    if (!response.ok) {
      throw new Error(`Opportunity not found (Status: ${response.status})`);
    }
    const result = await response.json();
    return result.data;
  } catch (error) {
    showToast(error.message, 'error');
    return null;
  }
}

// ==============================================================
// RENDERING & UI UPDATES
// ==============================================================

function renderFilteredOpportunities() {
  const filtered = opportunities.filter(item => {
    const matchesSearch = !currentFilter.search || 
      item.title.toLowerCase().includes(currentFilter.search) ||
      item.faculty_name.toLowerCase().includes(currentFilter.search) ||
      item.research_area.toLowerCase().includes(currentFilter.search) ||
      item.required_skills.toLowerCase().includes(currentFilter.search);

    const matchesStatus = currentFilter.status === 'ALL' || item.status === currentFilter.status;
    const matchesDept = currentFilter.department === 'ALL' || item.department === currentFilter.department;

    return matchesSearch && matchesStatus && matchesDept;
  });

  opportunitiesContainer.innerHTML = '';

  if (filtered.length === 0) {
    emptyState.classList.remove('hidden');
    return;
  }

  emptyState.classList.add('hidden');

  filtered.forEach(opp => {
    const card = createOpportunityCard(opp);
    opportunitiesContainer.appendChild(card);
  });
}

function createOpportunityCard(opp) {
  const card = document.createElement('div');
  card.className = 'opp-card';
  card.id = `opp-card-${opp.id}`;

  const isOpen = opp.status === 'Open';
  const statusClass = isOpen ? 'open' : 'closed';
  const toggleBtnText = isOpen ? 'Close Opening' : 'Reopen';

  // Skills chips
  const skillsArray = opp.required_skills
    ? opp.required_skills.split(',').map(s => s.trim()).filter(Boolean)
    : [];
  const skillsHtml = skillsArray.slice(0, 3)
    .map(s => `<span class="skill-pill">${escapeHtml(s)}</span>`)
    .join('') + (skillsArray.length > 3 ? `<span class="skill-pill">+${skillsArray.length - 3} more</span>` : '');

  // Role-based action bar
  let actionButtonsHtml = '';
  if (isAdmin) {
    // Authenticated Admin: Full CRUD and status toggle controls
    actionButtonsHtml = `
      <div class="card-actions">
        <div class="action-group-left">
          <button class="btn btn-secondary btn-sm" onclick="viewDetails(${opp.id})">Details</button>
          <button class="btn btn-secondary btn-sm" onclick="openEditModal(${opp.id})">Edit</button>
          <button class="btn-toggle-status" onclick="toggleOpportunityStatus(${opp.id}, '${opp.status}')">
            ${toggleBtnText}
          </button>
        </div>
        <button class="btn btn-danger btn-sm" title="Delete Opportunity" onclick="promptDelete(${opp.id}, '${escapeQuote(opp.title)}')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      </div>
    `;
  } else {
    // Public Visitor Mode: Only "View Details" button, zero CRUD actions
    actionButtonsHtml = `
      <div class="card-actions">
        <div class="action-group-left">
          <button class="btn btn-secondary btn-sm" onclick="viewDetails(${opp.id})">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
              <circle cx="12" cy="12" r="3"></circle>
            </svg>
            View Details
          </button>
        </div>
      </div>
    `;
  }

  card.innerHTML = `
    <div>
      <div class="card-top">
        <span class="dept-badge">${escapeHtml(opp.department)}</span>
        <span class="status-badge ${statusClass}">${escapeHtml(opp.status)}</span>
      </div>

      <h3 class="card-title">${escapeHtml(opp.title)}</h3>
      
      <div class="card-area">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="2" y1="12" x2="22" y2="12"></line>
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
        </svg>
        ${escapeHtml(opp.research_area)}
      </div>

      <p class="card-desc">${escapeHtml(opp.description)}</p>

      <div class="card-meta-list">
        <div class="meta-row">
          <span class="meta-label-dim">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            Supervisor
          </span>
          <span class="meta-val-highlight">${escapeHtml(opp.faculty_name)}</span>
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
          <span class="meta-val-highlight">${escapeHtml(opp.deadline)}</span>
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
          <span class="meta-val-highlight text-cyan">${opp.available_positions} ${opp.available_positions === 1 ? 'seat' : 'seats'}</span>
        </div>
      </div>

      <div class="skills-preview">
        ${skillsHtml}
      </div>
    </div>

    ${actionButtonsHtml}
  `;

  return card;
}

function updateMetrics() {
  statTotal.textContent = opportunities.length;
  statOpen.textContent = opportunities.filter(o => o.status === 'Open').length;
  statPositions.textContent = opportunities.reduce((acc, curr) => acc + (parseInt(curr.available_positions) || 0), 0);
  
  const depts = new Set(opportunities.map(o => o.department).filter(Boolean));
  statDepts.textContent = depts.size;
}

function updateDepartmentFilterOptions() {
  const currentSelected = filterDepartment.value;
  departmentsList = new Set(opportunities.map(o => o.department).filter(Boolean));

  filterDepartment.innerHTML = '<option value="ALL">All Departments</option>';
  Array.from(departmentsList).sort().forEach(dept => {
    const opt = document.createElement('option');
    opt.value = dept;
    opt.textContent = dept;
    if (dept === currentSelected) opt.selected = true;
    filterDepartment.appendChild(opt);
  });
}

function showLoading(show) {
  if (show) {
    loadingIndicator.classList.remove('hidden');
    opportunitiesContainer.classList.add('hidden');
  } else {
    loadingIndicator.classList.add('hidden');
    opportunitiesContainer.classList.remove('hidden');
  }
}

// ==============================================================
// MODAL CONTROLS & CRUD OPERATIONS
// ==============================================================

function openCreateModal() {
  if (!isAdmin) {
    showToast('Administrator privileges required.', 'error');
    return;
  }
  clearFormErrors();
  opportunityForm.reset();
  oppId.value = '';
  modalTitle.textContent = 'Post New Research Opportunity';
  oppStatus.value = 'Open';
  
  // Set default deadline to +30 days from today
  const nextMonth = new Date();
  nextMonth.setDate(nextMonth.getDate() + 30);
  oppDeadline.value = nextMonth.toISOString().split('T')[0];

  openModal(opportunityModal);
}

async function openEditModal(id) {
  if (!isAdmin) {
    showToast('Administrator privileges required.', 'error');
    return;
  }
  clearFormErrors();
  const opp = opportunities.find(o => o.id === id) || await fetchSingleOpportunity(id);
  if (!opp) return;

  oppId.value = opp.id;
  oppTitle.value = opp.title;
  oppFaculty.value = opp.faculty_name;
  oppDepartment.value = opp.department;
  oppArea.value = opp.research_area;
  oppPositions.value = opp.available_positions;
  oppDeadline.value = opp.deadline;
  oppStatus.value = opp.status;
  oppSkills.value = opp.required_skills;
  oppDescription.value = opp.description;

  modalTitle.textContent = `Update Opportunity #${opp.id}`;
  openModal(opportunityModal);
}

async function viewDetails(id) {
  const opp = opportunities.find(o => o.id === id) || await fetchSingleOpportunity(id);
  if (!opp) return;

  document.getElementById('detailId').textContent = `#${opp.id}`;
  document.getElementById('detailTitle').textContent = opp.title;
  document.getElementById('detailFaculty').textContent = opp.faculty_name;
  document.getElementById('detailDepartment').textContent = opp.department;
  document.getElementById('detailArea').textContent = opp.research_area;
  document.getElementById('detailPositions').textContent = opp.available_positions;
  document.getElementById('detailDeadline').textContent = opp.deadline;
  document.getElementById('detailDescription').textContent = opp.description;

  const badge = document.getElementById('detailStatusBadge');
  badge.textContent = opp.status;
  badge.className = `status-badge ${opp.status === 'Open' ? 'open' : 'closed'}`;

  const skillsContainer = document.getElementById('detailSkillsChips');
  skillsContainer.innerHTML = '';
  const skills = opp.required_skills ? opp.required_skills.split(',').map(s => s.trim()).filter(Boolean) : [];
  skills.forEach(skill => {
    const chip = document.createElement('span');
    chip.className = 'skill-pill';
    chip.textContent = skill;
    skillsContainer.appendChild(chip);
  });

  openModal(detailsModal);
}

// --------------------------------------------------------------
// CREATE & UPDATE HANDLER (ADMIN ONLY)
// --------------------------------------------------------------
async function handleFormSubmit(e) {
  e.preventDefault();
  clearFormErrors();

  if (!isAdmin) {
    showToast('Authentication required. Only administrator can modify data.', 'error');
    closeModal(opportunityModal);
    return;
  }

  const id = oppId.value;
  const isEditing = Boolean(id);

  // Validate form fields client-side
  let hasErrors = false;

  const payload = {
    title: oppTitle.value.trim(),
    faculty_name: oppFaculty.value.trim(),
    department: oppDepartment.value.trim(),
    research_area: oppArea.value.trim(),
    available_positions: parseInt(oppPositions.value, 10),
    deadline: oppDeadline.value.trim(),
    status: oppStatus.value,
    required_skills: oppSkills.value.trim(),
    description: oppDescription.value.trim()
  };

  if (!payload.title) {
    setError('err_oppTitle', 'Research Title is required.');
    hasErrors = true;
  }
  if (!payload.faculty_name) {
    setError('err_oppFaculty', 'Faculty Member Name is required.');
    hasErrors = true;
  }
  if (!payload.department) {
    setError('err_oppDepartment', 'Department is required.');
    hasErrors = true;
  }
  if (!payload.research_area) {
    setError('err_oppArea', 'Research Area is required.');
    hasErrors = true;
  }
  if (isNaN(payload.available_positions) || payload.available_positions <= 0) {
    setError('err_oppPositions', 'Positions must be at least 1.');
    hasErrors = true;
  }
  if (!payload.deadline) {
    setError('err_oppDeadline', 'Valid application deadline is required.');
    hasErrors = true;
  }
  if (!payload.required_skills) {
    setError('err_oppSkills', 'Please specify required skills.');
    hasErrors = true;
  }
  if (!payload.description) {
    setError('err_oppDescription', 'Research Description is required.');
    hasErrors = true;
  }

  if (hasErrors) return;

  const submitBtn = document.getElementById('btnSubmitOpp');
  submitBtn.disabled = true;
  submitBtn.textContent = isEditing ? 'Updating...' : 'Saving...';

  try {
    const url = isEditing ? `${API_BASE}/${id}` : API_BASE;
    const method = isEditing ? 'PUT' : 'POST';

    const response = await fetch(url, {
      method: method,
      headers: getAuthHeaders(),
      credentials: 'include',
      body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (response.status === 401) {
      showToast('Admin session expired. Please log in again.', 'error');
      isAdmin = false;
      updateRoleUI(false);
      renderFilteredOpportunities();
      closeModal(opportunityModal);
      return;
    }

    if (!response.ok) {
      throw new Error(data.message || `Server error ${response.status}`);
    }

    closeModal(opportunityModal);
    showToast(isEditing ? 'Opportunity updated successfully!' : 'New research opportunity published!', 'success');
    await fetchOpportunities();

  } catch (error) {
    showToast(`Failed: ${error.message}`, 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Save Opportunity';
  }
}

// --------------------------------------------------------------
// QUICK STATUS TOGGLE (ADMIN ONLY)
// --------------------------------------------------------------
async function toggleOpportunityStatus(id, currentStatus) {
  if (!isAdmin) {
    showToast('Administrator privileges required to change opportunity status.', 'error');
    return;
  }

  const newStatus = currentStatus === 'Open' ? 'Closed' : 'Open';
  try {
    const response = await fetch(`${API_BASE}/${id}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      credentials: 'include',
      body: JSON.stringify({ status: newStatus })
    });

    const data = await response.json();
    if (response.status === 401) {
      showToast('Unauthorized. Session expired.', 'error');
      isAdmin = false;
      updateRoleUI(false);
      renderFilteredOpportunities();
      return;
    }

    if (!response.ok) {
      throw new Error(data.message || 'Status update failed.');
    }

    showToast(`Opportunity #${id} is now ${newStatus}`, 'success');
    await fetchOpportunities();
  } catch (error) {
    showToast(`Could not update status: ${error.message}`, 'error');
  }
}

// --------------------------------------------------------------
// DELETE ACTIONS (ADMIN ONLY)
// --------------------------------------------------------------
function promptDelete(id, title) {
  if (!isAdmin) {
    showToast('Administrator privileges required to delete opportunities.', 'error');
    return;
  }
  pendingDeleteId = id;
  deleteOppTitle.textContent = `"${title}"`;
  openModal(deleteModal);
}

async function handleConfirmDelete() {
  if (!isAdmin || !pendingDeleteId) return;

  const btnConfirm = document.getElementById('btnConfirmDelete');
  btnConfirm.disabled = true;
  btnConfirm.textContent = 'Deleting...';

  try {
    const response = await fetch(`${API_BASE}/${pendingDeleteId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
      credentials: 'include'
    });

    const data = await response.json();
    if (response.status === 401) {
      showToast('Unauthorized. Session expired.', 'error');
      isAdmin = false;
      updateRoleUI(false);
      closeModal(deleteModal);
      return;
    }

    if (!response.ok) {
      throw new Error(data.message || 'Failed to delete opportunity.');
    }

    closeModal(deleteModal);
    showToast(`Opportunity #${pendingDeleteId} deleted permanently.`, 'success');
    pendingDeleteId = null;
    await fetchOpportunities();

  } catch (error) {
    showToast(`Delete failed: ${error.message}`, 'error');
  } finally {
    btnConfirm.disabled = false;
    btnConfirm.textContent = 'Confirm Delete';
  }
}

// ==============================================================
// HELPERS, MODAL CONTROLLER & TOASTS
// ==============================================================

function openModal(modal) {
  modal.classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeModal(modal) {
  modal.classList.add('hidden');
  document.body.style.overflow = '';
}

function setError(elementId, message) {
  const el = document.getElementById(elementId);
  if (el) el.textContent = message;
}

function clearFormErrors() {
  document.querySelectorAll('.field-error').forEach(el => el.textContent = '');
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const iconSvg = type === 'success' 
    ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>`
    : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`;

  toast.innerHTML = `
    ${iconSvg}
    <span>${escapeHtml(message)}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(30px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function escapeQuote(str) {
  if (!str) return '';
  return String(str).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}
