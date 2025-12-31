const API_BASE = '/api/v1';

// Tab switching
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    event.target.classList.add('active');
    
    // Load data when switching to certain tabs
    if (tabName === 'accounts') {
        loadAccounts();
    } else if (tabName === 'transactions') {
        loadTransactions();
    } else if (tabName === 'mint' || tabName === 'transfer') {
        loadAccountOptions();
    }
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// API helper
async function apiCall(endpoint, method = 'GET', body = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        if (body) {
            options.body = JSON.stringify(body);
        }
        
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || data.detail || 'An error occurred');
        }
        
        return data;
    } catch (error) {
        throw error;
    }
}

// Load accounts
async function loadAccounts() {
    const listEl = document.getElementById('accounts-list');
    listEl.innerHTML = '<div class="loading">Loading accounts...</div>';
    
    try {
        const accounts = await apiCall('/accounts');
        
        if (accounts.length === 0) {
            listEl.innerHTML = '<div class="empty-state">No accounts yet. Create one to get started!</div>';
            return;
        }
        
        listEl.innerHTML = accounts.map(account => `
            <div class="account-card">
                <h3>${account.name}</h3>
                <div class="account-id">ID: ${account.id}</div>
                <div class="balance">Balance: $${(account.balance / 100).toFixed(2)}</div>
            </div>
        `).join('');
    } catch (error) {
        listEl.innerHTML = `<div class="empty-state">Error: ${error.message}</div>`;
        showNotification(`Failed to load accounts: ${error.message}`, 'error');
    }
}

// Load account options for dropdowns
async function loadAccountOptions() {
    try {
        const accounts = await apiCall('/accounts');
        
        const options = accounts.map(acc => 
            `<option value="${acc.id}">${acc.name} ($${(acc.balance / 100).toFixed(2)})</option>`
        ).join('');
        
        document.getElementById('mint-account-id').innerHTML = '<option value="">Select Account...</option>' + options;
        document.getElementById('from-account-id').innerHTML = '<option value="">From Account...</option>' + options;
        document.getElementById('to-account-id').innerHTML = '<option value="">To Account...</option>' + options;
    } catch (error) {
        showNotification(`Failed to load accounts: ${error.message}`, 'error');
    }
}

// Create account
async function createAccount(event) {
    event.preventDefault();
    const name = document.getElementById('account-name').value;
    
    try {
        const account = await apiCall('/accounts', 'POST', { name });
        showNotification(`Account "${account.name}" created successfully!`, 'success');
        document.getElementById('create-account-form').reset();
        loadAccounts();
        loadAccountOptions();
    } catch (error) {
        showNotification(`Failed to create account: ${error.message}`, 'error');
    }
}

// Mint value
async function mintValue(event) {
    event.preventDefault();
    const accountId = document.getElementById('mint-account-id').value;
    const amount = parseInt(document.getElementById('mint-amount').value);
    const description = document.getElementById('mint-description').value;
    
    if (!accountId) {
        showNotification('Please select an account', 'error');
        return;
    }
    
    try {
        const transaction = await apiCall('/transactions/mint', 'POST', {
            account_id: accountId,
            amount: amount,
            description: description,
            idempotency_key: `mint-${Date.now()}`
        });
        
        showNotification(`Successfully minted $${(amount / 100).toFixed(2)} to account!`, 'success');
        document.getElementById('mint-form').reset();
        loadAccounts();
        loadAccountOptions();
    } catch (error) {
        showNotification(`Failed to mint: ${error.message}`, 'error');
    }
}

// Transfer value
async function transferValue(event) {
    event.preventDefault();
    const fromAccountId = document.getElementById('from-account-id').value;
    const toAccountId = document.getElementById('to-account-id').value;
    const amount = parseInt(document.getElementById('transfer-amount').value);
    const description = document.getElementById('transfer-description').value;
    
    if (!fromAccountId || !toAccountId) {
        showNotification('Please select both accounts', 'error');
        return;
    }
    
    if (fromAccountId === toAccountId) {
        showNotification('Cannot transfer to the same account', 'error');
        return;
    }
    
    try {
        const transaction = await apiCall('/transactions/transfer', 'POST', {
            from_account_id: fromAccountId,
            to_account_id: toAccountId,
            amount: amount,
            description: description,
            idempotency_key: `transfer-${Date.now()}`
        });
        
        showNotification(`Successfully transferred $${(amount / 100).toFixed(2)}!`, 'success');
        document.getElementById('transfer-form').reset();
        loadAccounts();
        loadAccountOptions();
        loadTransactions();
    } catch (error) {
        showNotification(`Failed to transfer: ${error.message}`, 'error');
    }
}

// Load transactions
async function loadTransactions() {
    const listEl = document.getElementById('transactions-list');
    listEl.innerHTML = '<div class="loading">Loading transactions...</div>';
    
    try {
        const response = await apiCall('/transactions');
        const transactions = response.transactions || [];
        
        if (transactions.length === 0) {
            listEl.innerHTML = '<div class="empty-state">No transactions yet.</div>';
            return;
        }
        
        listEl.innerHTML = transactions.map(tx => {
            const amount = `$${(tx.amount / 100).toFixed(2)}`;
            const txClass = tx.type === 'MINT' ? 'mint' : 'transfer';
            const typeLabel = tx.type === 'MINT' ? 'MINT' : 'TRANSFER';
            
            let details = '';
            if (tx.type === 'MINT') {
                details = `To: ${tx.to_account_id ? tx.to_account_id.substring(0, 8) + '...' : 'N/A'}`;
            } else {
                details = `From: ${tx.from_account_id ? tx.from_account_id.substring(0, 8) + '...' : 'N/A'} → To: ${tx.to_account_id ? tx.to_account_id.substring(0, 8) + '...' : 'N/A'}`;
            }
            
            return `
                <div class="transaction-item ${txClass}">
                    <div class="transaction-header">
                        <span class="transaction-type">${typeLabel}</span>
                        <span class="transaction-amount">${amount}</span>
                    </div>
                    <div class="transaction-details">
                        ${tx.description || 'No description'}<br>
                        ${details}<br>
                        <small>${new Date(tx.created_at).toLocaleString()}</small>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        listEl.innerHTML = `<div class="empty-state">Error: ${error.message}</div>`;
        showNotification(`Failed to load transactions: ${error.message}`, 'error');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadAccounts();
    loadAccountOptions();
});

