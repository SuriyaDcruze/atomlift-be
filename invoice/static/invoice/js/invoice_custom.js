// invoice_custom.js - Custom JavaScript for Invoice management

let currentModalType = '';
let currentEditId = null;
let itemCounter = 0;
let isEditMode = false;
let submitUrl = '';
let adminHomeUrl = '';

// Initialize the invoice form
function initializeInvoiceForm() {
  isEditMode = window.isEditMode || false;
  submitUrl = window.submitUrl || '';
  adminHomeUrl = window.adminHomeUrl || '';
  
  loadCustomers();
  loadAmcTypes();
  loadItems();
  setupRadioButtonInteractions();
  setupItemCalculations();
  
  // If in edit mode, populate existing items
  if (isEditMode) {
    populateExistingItems();
  }
}

function setupRadioButtonInteractions() {
  const paymentTermRadios = document.querySelectorAll('input[name="payment_term"]');
  const statusRadios = document.querySelectorAll('input[name="status"]');

  paymentTermRadios.forEach(radio => radio.addEventListener('change', updateRadioSelection));
  statusRadios.forEach(radio => radio.addEventListener('change', updateRadioSelection));
}

function updateRadioSelection() {
  document.querySelectorAll('.form-radio-option').forEach(option => {
    const radio = option.querySelector('input[type="radio"]');
    option.classList.toggle('selected', radio.checked);
  });
}

function setupItemCalculations() {
  document.addEventListener('input', function(e) {
    if (e.target.matches('input[name*="[rate]"], input[name*="[qty]"], input[name*="[tax]"]')) {
      calculateItemTotal(e.target.closest('tr'));
    }
  });
}

function calculateItemTotal(row) {
  const rate = parseFloat(row.querySelector('input[name*="[rate]"]').value) || 0;
  const qty = parseFloat(row.querySelector('input[name*="[qty]"]').value) || 0;
  const tax = parseFloat(row.querySelector('input[name*="[tax]"]').value) || 0;
  
  const total = rate * qty * (1 + (tax / 100));
  row.querySelector('.item-total').textContent = total.toFixed(2);
}

async function fetchOptions(endpoint, selectId, currentId) {
  try {
    const response = await fetch(`/invoice/api/${endpoint}/`, {
      headers: { 'X-CSRFToken': getCsrfToken() }
    });
    if (!response.ok) throw new Error(`Failed to load ${endpoint}`);
    const data = await response.json();
    const select = document.getElementById(selectId);
    select.innerHTML = '<option value="">Select ' + selectId.charAt(0).toUpperCase() + selectId.slice(1).replace('_', ' ') + '</option>';
    data.forEach(item => {
      const option = document.createElement('option');
      option.value = item.id;
      option.textContent = item.site_name || item.name || item.name;
      if (currentId && item.id === currentId) option.selected = true;
      select.appendChild(option);
    });
  } catch (error) {
    console.error(`Error loading ${endpoint}:`, error);
    document.getElementById(selectId).innerHTML = `<option value="">Error loading ${selectId}s</option>`;
  }
}

function loadCustomers() { 
  const currentCustomerId = window.currentCustomerId || null;
  fetchOptions('customers', 'customer', currentCustomerId); 
}

function loadAmcTypes() { 
  const currentAmcTypeId = window.currentAmcTypeId || null;
  fetchOptions('amc-types', 'amc_type', currentAmcTypeId); 
}

function loadItems() { 
  fetchOptions('items', 'item', null); 
}

function addInvoiceItem() {
  const tbody = document.getElementById('itemsTableBody');
  const row = document.createElement('tr');
  row.innerHTML = `
    <td>
      <select name="items[${itemCounter}][item]" class="form-input form-select">
        <option value="">Select Item</option>
      </select>
    </td>
    <td><input type="number" name="items[${itemCounter}][rate]" step="0.01" class="form-input" /></td>
    <td><input type="number" name="items[${itemCounter}][qty]" value="1" class="form-input" /></td>
    <td><input type="number" name="items[${itemCounter}][tax]" step="0.01" class="form-input" /></td>
    <td><span class="item-total">0.00</span></td>
    <td><button type="button" class="btn btn-danger" onclick="removeInvoiceItem(this)">Remove</button></td>
  `;
  
  // Populate item dropdown
  populateItemDropdown(row.querySelector('select[name*="[item]"]'));
  tbody.appendChild(row);
  itemCounter++;
}

function removeInvoiceItem(button) {
  button.closest('tr').remove();
}

function populateItemDropdown(select) {
  fetch('/invoice/api/items/')
    .then(response => response.json())
    .then(data => {
      data.forEach(item => {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = `${item.name} - ₹${item.sale_price}`;
        select.appendChild(option);
      });
    })
    .catch(error => console.error('Error loading items:', error));
}

function populateExistingItems() {
  // This function would populate existing items in edit mode
  // The template already handles this with Django template tags
}

function openModal(type, editId = null, editValue = '') {
  currentModalType = type;
  currentEditId = editId;
  const modal = document.getElementById('optionModal');
  const modalTitle = document.getElementById('modalTitle');
  const modalInput = document.getElementById('modalInput');
  const saveBtn = document.getElementById('saveOptionBtn');

  modalTitle.textContent = editId ? `Edit ${type.charAt(0).toUpperCase() + type.slice(1)}` : `Add New ${type.charAt(0).toUpperCase() + type.slice(1)}`;
  modalInput.value = editValue;
  saveBtn.textContent = editId ? `Update ${type.charAt(0).toUpperCase() + type.slice(1)}` : `Add ${type.charAt(0).toUpperCase() + type.slice(1)}`;
  saveBtn.disabled = !editValue.trim();
  modal.classList.add('active');
  loadExistingOptions(type);
}

function closeModal() {
  document.getElementById('optionModal').classList.remove('active');
  document.getElementById('modalInput').value = '';
  document.getElementById('modalError').style.display = 'none';
  currentEditId = null;
}

async function loadExistingOptions(type) {
  try {
    const response = await fetch(`/invoice/api/${type}s/`, {
      headers: { 'X-CSRFToken': getCsrfToken() }
    });
    if (!response.ok) throw new Error(`Failed to load ${type}s`);
    const data = await response.json();
    const tbody = document.getElementById('optionTableBody');
    tbody.innerHTML = data.length ? data.map(item => `
      <tr>
        <td>${item.site_name || item.name || item.name}</td>
        <td class="text-right">
          <button type="button" class="btn btn-edit" onclick="openModal('${type}', ${item.id}, '${(item.site_name || item.name || item.name).replace(/'/g, "\\'")}')">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button type="button" class="btn btn-delete" onclick="deleteOption('${type}', ${item.id})">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5-4h4M7 7h10m-9 3v8m4-8v8m4-8v8" />
            </svg>
          </button>
        </td>
      </tr>
    `).join('') : `<tr><td colspan="2" class="text-center text-gray-500">No ${type}s found</td></tr>`;
  } catch (error) {
    console.error(`Error loading ${type}s:`, error);
    document.getElementById('optionTableBody').innerHTML = `<tr><td colspan="2" class="text-center text-gray-500">Error loading ${type}s</td></tr>`;
  }
}

async function saveOption() {
  const value = document.getElementById('modalInput').value.trim();
  const modalError = document.getElementById('modalError');
  if (!value) {
    modalError.textContent = `Please enter a ${currentModalType}`;
    modalError.style.display = 'block';
    return;
  }

  try {
    const method = currentEditId ? 'PUT' : 'POST';
    const url = currentEditId ? `/invoice/api/${currentModalType}s/${currentEditId}/` : `/invoice/api/${currentModalType}s/`;
    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken()
      },
      body: JSON.stringify({ 
        site_name: value,
        name: value 
      })
    });
    const data = await response.json();
    if (data.success) {
      const select = document.getElementById(currentModalType);
      if (!currentEditId) {
        const option = new Option(data.site_name || data.name, data.id);
        select.appendChild(option);
        select.value = data.id;
      } else {
        const option = select.querySelector(`option[value="${currentEditId}"]`);
        if (option) option.textContent = data.site_name || data.name;
      }
      closeModal();
      showMessage('success', `${currentModalType.charAt(0).toUpperCase() + currentModalType.slice(1)} ${currentEditId ? 'updated' : 'added'} successfully`);
      loadExistingOptions(currentModalType);
      fetchOptions(`${currentModalType}s`, currentModalType, select.value);
    } else {
      modalError.textContent = data.error || `Failed to ${currentEditId ? 'update' : 'add'} ${currentModalType}`;
      modalError.style.display = 'block';
    }
  } catch (error) {
    console.error(`Error ${currentEditId ? 'updating' : 'adding'} ${currentModalType}:`, error);
    modalError.textContent = `Failed to ${currentEditId ? 'update' : 'add'} ${currentModalType}`;
    modalError.style.display = 'block';
  }
}

async function deleteOption(type, id) {
  if (!confirm(`Are you sure you want to delete this ${type}?`)) return;

  try {
    const response = await fetch(`/invoice/api/${type}s/${id}/`, {
      method: 'DELETE',
      headers: { 'X-CSRFToken': getCsrfToken() }
    });
    const data = await response.json();
    if (data.success) {
      const select = document.getElementById(type);
      const option = select.querySelector(`option[value="${id}"]`);
      if (option) option.remove();
      showMessage('success', `${type.charAt(0).toUpperCase() + type.slice(1)} deleted successfully`);
      loadExistingOptions(type);
      fetchOptions(`${type}s`, type, select.value);
    } else {
      showMessage('error', data.error || `Failed to delete ${type}`);
    }
  } catch (error) {
    console.error(`Error deleting ${type}:`, error);
    showMessage('error', `Failed to delete ${type}`);
  }
}

function getCsrfToken() {
  return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

function showMessage(type, message, description = '') {
  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.innerHTML = `
    <div class="toast-content">
      <div class="toast-message">
        <strong>${type.charAt(0).toUpperCase() + type.slice(1)}:</strong> ${message}
        ${description ? `<div>${description}</div>` : ''}
      </div>
      <button class="toast-close" onclick="this.parentElement.parentElement.remove()">×</button>
    </div>
  `;
  const toastContainer = document.getElementById('toastContainer');
  toastContainer.appendChild(toast);
  setTimeout(() => {
    if (toast.parentElement) toast.remove();
  }, type === 'success' ? 3000 : 5000);
}

function validateForm() {
  const errors = {};
  const customer = document.getElementById('customer').value;
  const startDate = document.getElementById('start_date').value;
  const dueDate = document.getElementById('due_date').value;

  if (!customer) errors.customer = 'Customer is required';
  if (!startDate) errors.startDate = 'Start date is required';
  if (!dueDate) errors.dueDate = 'Due date is required';

  document.getElementById('customerError').textContent = errors.customer || '';
  document.getElementById('customerError').style.display = errors.customer ? 'block' : 'none';
  document.getElementById('startDateError').textContent = errors.startDate || '';
  document.getElementById('startDateError').style.display = errors.startDate ? 'block' : 'none';
  document.getElementById('dueDateError').textContent = errors.dueDate || '';
  document.getElementById('dueDateError').style.display = errors.dueDate ? 'block' : 'none';

  return Object.keys(errors).length === 0;
}

function createFormData() {
  const form = document.getElementById('invoiceForm');
  const data = {};
  const formData = new FormData(form);
  
  // Process regular fields
  for (const [key, value] of formData.entries()) {
    if (key.startsWith('items[')) {
      // Handle items separately
      continue;
    }
    if (key === 'discount') {
      data[key] = parseFloat(value) || 0;
    } else if (key === 'customer' || key === 'amc_type') {
      data[key] = value ? parseInt(value) : null;
    } else {
      data[key] = value;
    }
  }
  
  // Process items
  const items = [];
  const itemRows = document.querySelectorAll('#itemsTableBody tr');
  itemRows.forEach((row, index) => {
    const item = {};
    const inputs = row.querySelectorAll('input, select');
    inputs.forEach(input => {
      const name = input.name;
      if (name.includes('[item]')) {
        item.item = input.value ? parseInt(input.value) : null;
      } else if (name.includes('[rate]')) {
        item.rate = parseFloat(input.value) || 0;
      } else if (name.includes('[qty]')) {
        item.qty = parseInt(input.value) || 1;
      } else if (name.includes('[tax]')) {
        item.tax = parseFloat(input.value) || 0;
      }
    });
    if (item.item) { // Only add items that have an item selected
      items.push(item);
    }
  });
  data.items = items;
  
  return data;
}

async function handleFormSubmit() {
  if (!validateForm()) return;

  const submitButton = document.getElementById('submitBtn');
  const originalText = submitButton.textContent;
  submitButton.textContent = 'Saving...';
  submitButton.disabled = true;

  try {
    const data = createFormData();
    const response = await fetch(submitUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken()
      },
      body: JSON.stringify(data)
    });
    const result = await response.json();
    submitButton.textContent = originalText;
    submitButton.disabled = false;

    if (result.success) {
      showMessage('success', result.message || (isEditMode ? 'Invoice updated successfully' : 'Invoice created successfully'));
      setTimeout(() => {
        window.location.href = adminHomeUrl;
      }, 2000);
    } else {
      showMessage('error', result.error || 'Failed to save invoice');
    }
  } catch (error) {
    console.error('Error saving invoice:', error);
    submitButton.textContent = originalText;
    submitButton.disabled = false;
    showMessage('error', 'An error occurred while saving the invoice');
  }
}

function handleCancel() {
  document.getElementById('invoiceForm').reset();
  document.getElementById('customerError').style.display = 'none';
  document.getElementById('startDateError').style.display = 'none';
  document.getElementById('dueDateError').style.display = 'none';
  window.history.back();
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
  initializeInvoiceForm();
  
  // Modal event listeners
  const optionModal = document.getElementById('optionModal');
  if (optionModal) {
    optionModal.addEventListener('click', (e) => {
      if (e.target === optionModal) closeModal();
    });
  }
  
  const modalInput = document.getElementById('modalInput');
  if (modalInput) {
    modalInput.addEventListener('input', (e) => {
      const saveBtn = document.getElementById('saveOptionBtn');
      if (saveBtn) saveBtn.disabled = !e.target.value.trim();
    });
  }
});

// Make functions globally available
window.addInvoiceItem = addInvoiceItem;
window.removeInvoiceItem = removeInvoiceItem;
window.openModal = openModal;
window.closeModal = closeModal;
window.saveOption = saveOption;
window.deleteOption = deleteOption;
window.handleFormSubmit = handleFormSubmit;
window.handleCancel = handleCancel;




