/**
 * History module: Search, filtering, pagination, edit modal, delete confirmation.
 */

let deleteTargetId = null;

document.addEventListener('DOMContentLoaded', () => {
  initHistoryControls();
  initEditModalCalculations();
});

function initHistoryControls() {
  const searchInput = document.getElementById('historySearchInput');
  if (searchInput) {
    searchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        applyFilters();
      }
    });
  }

  const categorySelect = document.getElementById('historyCategoryFilter');
  if (categorySelect) {
    categorySelect.addEventListener('change', applyFilters);
  }

  const sortSelect = document.getElementById('historySortBy');
  if (sortSelect) {
    sortSelect.addEventListener('change', applyFilters);
  }
}

function applyFilters() {
  const search = document.getElementById('historySearchInput')?.value || '';
  const category = document.getElementById('historyCategoryFilter')?.value || 'All';
  const sort = document.getElementById('historySortBy')?.value || 'created_at-DESC';
  
  const [sortBy, sortOrder] = sort.split('-');

  const url = new URL(window.location.href);
  if (search) url.searchParams.set('search', search);
  else url.searchParams.delete('search');

  if (category && category !== 'All') url.searchParams.set('category', category);
  else url.searchParams.delete('category');

  if (sortBy) url.searchParams.set('sort_by', sortBy);
  if (sortOrder) url.searchParams.set('sort_order', sortOrder);
  url.searchParams.set('page', '1');

  window.location.href = url.toString();
}

/* ==========================================================================
   Edit Record Modal
   ========================================================================== */
async function openEditModal(recordId) {
  try {
    const response = await fetch(`/api/records/${recordId}`);
    const data = await response.json();

    if (!data.success || !data.record) {
      showToast('Failed to load record details.', 'danger');
      return;
    }

    const r = data.record;
    document.getElementById('edit_record_id').value = r.id;
    document.getElementById('edit_system_name').value = r.system_name;
    document.getElementById('edit_category').value = r.category || 'General Software';
    document.getElementById('edit_operating_time').value = r.operating_time;
    document.getElementById('edit_failures').value = r.failures;
    document.getElementById('edit_repair_time').value = r.repair_time;
    document.getElementById('edit_notes').value = r.notes || '';

    recalculateEditMetrics();
    openModal('editRecordModal');
  } catch (error) {
    showToast('Network error while retrieving record.', 'danger');
  }
}

function initEditModalCalculations() {
  const op = document.getElementById('edit_operating_time');
  const fail = document.getElementById('edit_failures');
  const rep = document.getElementById('edit_repair_time');

  [op, fail, rep].forEach(input => {
    if (input) input.addEventListener('input', recalculateEditMetrics);
  });

  const editForm = document.getElementById('editRecordForm');
  if (editForm) {
    editForm.addEventListener('submit', handleEditSubmit);
  }
}

function recalculateEditMetrics() {
  const op = parseFloat(document.getElementById('edit_operating_time')?.value) || 0;
  const fail = parseInt(document.getElementById('edit_failures')?.value) || 0;
  const rep = parseFloat(document.getElementById('edit_repair_time')?.value) || 0;

  let mtbf = fail > 0 ? (op / fail) : op;
  let mttr = fail > 0 ? (rep / fail) : 0;
  let fr = op > 0 ? (fail / op) : 0;
  let avail = (op + rep) > 0 ? (op / (op + rep)) * 100 : (fail === 0 ? 100 : 0);

  const preview = document.getElementById('editMetricsPreview');
  if (preview) {
    preview.innerHTML = `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.85rem; padding: 0.75rem; background: var(--primary-light); border-radius: var(--radius-sm);">
        <div><b>MTBF:</b> ${mtbf.toFixed(2)} hrs</div>
        <div><b>MTTR:</b> ${mttr.toFixed(2)} hrs</div>
        <div><b>Failure Rate:</b> ${fr.toFixed(6)}/hr</div>
        <div><b>Availability:</b> <span style="color: var(--primary); font-weight: 700;">${avail.toFixed(3)}%</span></div>
      </div>
    `;
  }
}

async function handleEditSubmit(e) {
  e.preventDefault();
  const recordId = document.getElementById('edit_record_id').value;

  const payload = {
    system_name: document.getElementById('edit_system_name').value.trim(),
    category: document.getElementById('edit_category').value.trim(),
    operating_time: parseFloat(document.getElementById('edit_operating_time').value),
    failures: parseInt(document.getElementById('edit_failures').value),
    repair_time: parseFloat(document.getElementById('edit_repair_time').value),
    notes: document.getElementById('edit_notes').value.trim()
  };

  try {
    const response = await fetch(`/api/records/${recordId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await response.json();

    if (result.success) {
      closeModal('editRecordModal');
      showToast('Record updated successfully!', 'success');
      setTimeout(() => window.location.reload(), 800);
    } else {
      showToast(result.error || 'Failed to update record.', 'danger');
    }
  } catch (err) {
    showToast('An unexpected error occurred during update.', 'danger');
  }
}

/* ==========================================================================
   Delete Record Modal
   ========================================================================== */
function confirmDeleteRecord(recordId, systemName) {
  deleteTargetId = recordId;
  const label = document.getElementById('deleteTargetSystemName');
  if (label) label.textContent = systemName;
  openModal('deleteConfirmModal');
}

async function executeDelete() {
  if (!deleteTargetId) return;

  try {
    const response = await fetch(`/api/records/${deleteTargetId}`, {
      method: 'DELETE'
    });
    const result = await response.json();

    if (result.success) {
      closeModal('deleteConfirmModal');
      showToast('Record deleted successfully.', 'success');
      setTimeout(() => window.location.reload(), 700);
    } else {
      showToast(result.error || 'Failed to delete record.', 'danger');
    }
  } catch (err) {
    showToast('Failed to delete record.', 'danger');
  }
}
