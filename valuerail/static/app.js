const API_BASE = '/api/v1';
let allAccounts = [];
let allTransactions = [];

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
    if (tabName === 'dashboard') {
        loadDashboard();
    } else if (tabName === 'accounts') {
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
    }, 4000);
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

// Load dashboard
async function loadDashboard() {
    try {
        const [accounts, transactionsResponse] = await Promise.all([
            apiCall('/accounts'),
            apiCall('/transactions')
        ]);
        
        const transactions = transactionsResponse.transactions || [];
        allAccounts = accounts;
        allTransactions = transactions;
        
        // Update header stats
        updateHeaderStats(accounts, transactions);
        
        // Update dashboard stats
        updateDashboardStats(accounts, transactions);
        
        // Show recent transactions
        showRecentTransactions(transactions.slice(0, 5));
        
        // Show top accounts
        showTopAccounts(accounts);
    } catch (error) {
        showNotification(`Failed to load dashboard: ${error.message}`, 'error');
    }
}

// Update header stats from accounts only
function updateHeaderStatsFromAccounts(accounts) {
    const totalBalance = accounts.reduce((sum, acc) => sum + acc.balance, 0);
    const accountsEl = document.getElementById('total-accounts');
    const balanceEl = document.getElementById('total-balance');
    
    if (accountsEl) accountsEl.textContent = accounts.length;
    if (balanceEl) balanceEl.textContent = `$${(totalBalance / 100).toFixed(2)}`;
}

// Update header stats from accounts and transactions
function updateHeaderStats(accounts, transactions) {
    const totalBalance = accounts.reduce((sum, acc) => sum + acc.balance, 0);
    const accountsEl = document.getElementById('total-accounts');
    const balanceEl = document.getElementById('total-balance');
    const transactionsEl = document.getElementById('total-transactions');
    
    if (accountsEl) accountsEl.textContent = accounts.length;
    if (balanceEl) balanceEl.textContent = `$${(totalBalance / 100).toFixed(2)}`;
    if (transactionsEl) transactionsEl.textContent = transactions.length;
}

// Update dashboard stats
function updateDashboardStats(accounts, transactions) {
    const totalBalance = accounts.reduce((sum, acc) => sum + acc.balance, 0);
    const mintCount = transactions.filter(tx => tx.type === 'MINT').length;
    const transferCount = transactions.filter(tx => tx.type === 'TRANSFER').length;
    const totalMinted = transactions
        .filter(tx => tx.type === 'MINT')
        .reduce((sum, tx) => sum + tx.amount, 0);
    
    const statsEl = document.getElementById('dashboard-stats');
    statsEl.innerHTML = `
        <div class="stat-item">
            <div class="stat-item-value">${accounts.length}</div>
            <div class="stat-item-label">Total Accounts</div>
        </div>
        <div class="stat-item">
            <div class="stat-item-value">$${(totalBalance / 100).toFixed(2)}</div>
            <div class="stat-item-label">Total Value</div>
        </div>
        <div class="stat-item">
            <div class="stat-item-value">${mintCount}</div>
            <div class="stat-item-label">Mint Operations</div>
        </div>
        <div class="stat-item">
            <div class="stat-item-value">${transferCount}</div>
            <div class="stat-item-label">Transfers</div>
        </div>
    `;
}

// Show recent transactions
function showRecentTransactions(transactions) {
    const el = document.getElementById('recent-transactions');
    
    if (transactions.length === 0) {
        el.innerHTML = '<div class="empty-state">No transactions yet</div>';
        return;
    }
    
    el.innerHTML = transactions.map(tx => {
        const amount = `$${(tx.amount / 100).toFixed(2)}`;
        const txClass = tx.type === 'MINT' ? 'mint' : 'transfer';
        const typeLabel = tx.type === 'MINT' ? 'MINT' : 'TRANSFER';
        
        return `
            <div class="transaction-item ${txClass}">
                <div class="transaction-header">
                    <span class="transaction-type">${typeLabel}</span>
                    <span class="transaction-amount">${amount}</span>
                </div>
                <div class="transaction-details">
                    ${tx.description || 'No description'}<br>
                    <small>${new Date(tx.created_at).toLocaleString()}</small>
                </div>
            </div>
        `;
    }).join('');
}

// Show top accounts
function showTopAccounts(accounts) {
    const sorted = [...accounts].sort((a, b) => b.balance - a.balance).slice(0, 3);
    const el = document.getElementById('top-accounts');
    
    if (sorted.length === 0) {
        el.innerHTML = '<div class="empty-state">No accounts yet</div>';
        return;
    }
    
    el.innerHTML = sorted.map(account => `
        <div class="account-card">
            <h3>${account.name}</h3>
            <div class="account-id">ID: ${account.id.substring(0, 20)}...</div>
            <div class="balance">${(account.balance / 100).toFixed(2)}</div>
        </div>
    `).join('');
}

// Load accounts
async function loadAccounts() {
    const listEl = document.getElementById('accounts-list');
    if (listEl) {
        listEl.innerHTML = '<div class="loading">Loading accounts...</div>';
    }
    
    try {
        const accounts = await apiCall('/accounts');
        allAccounts = accounts;
        
        // Update header stats
        updateHeaderStatsFromAccounts(accounts);
        
        if (listEl) {
            if (accounts.length === 0) {
                listEl.innerHTML = '<div class="empty-state">No accounts yet. Create one to get started!</div>';
                return;
            }
            
            displayAccounts(accounts);
        }
    } catch (error) {
        if (listEl) {
            listEl.innerHTML = `<div class="empty-state">Error: ${error.message}</div>`;
        }
        showNotification(`Failed to load accounts: ${error.message}`, 'error');
    }
}

// Display accounts
function displayAccounts(accounts) {
    const listEl = document.getElementById('accounts-list');
    listEl.innerHTML = accounts.map(account => `
        <div class="account-card">
            <h3>${account.name}</h3>
            <div class="account-id">ID: ${account.id}</div>
            <div class="balance">${(account.balance / 100).toFixed(2)}</div>
        </div>
    `).join('');
}

// Filter accounts
function filterAccounts() {
    const searchTerm = document.getElementById('account-search').value.toLowerCase();
    const filtered = allAccounts.filter(acc => 
        acc.name.toLowerCase().includes(searchTerm) ||
        acc.id.toLowerCase().includes(searchTerm)
    );
    displayAccounts(filtered);
}

// Load account options for dropdowns
async function loadAccountOptions() {
    try {
        const accounts = await apiCall('/accounts');
        allAccounts = accounts;
        
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
    const button = event.target.querySelector('button[type="submit"]');
    const originalText = button.innerHTML;
    
    button.innerHTML = '<span>⏳</span> Creating...';
    button.disabled = true;
    
    try {
        const account = await apiCall('/accounts', 'POST', { name });
        showNotification(`Account "${account.name}" created successfully!`, 'success');
        document.getElementById('create-account-form').reset();
        await loadAccounts();
        loadAccountOptions();
        loadHeaderStats(); // Update header stats
        if (document.getElementById('dashboard-tab').classList.contains('active')) {
            loadDashboard();
        }
    } catch (error) {
        showNotification(`Failed to create account: ${error.message}`, 'error');
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// Mint value
async function mintValue(event) {
    event.preventDefault();
    const accountId = document.getElementById('mint-account-id').value;
    const amount = parseInt(document.getElementById('mint-amount').value);
    const description = document.getElementById('mint-description').value;
    const button = event.target.querySelector('button[type="submit"]');
    const originalText = button.innerHTML;
    
    if (!accountId) {
        showNotification('Please select an account', 'error');
        return;
    }
    
    button.innerHTML = '<span>⏳</span> Minting...';
    button.disabled = true;
    
    try {
        const transaction = await apiCall('/transactions/mint', 'POST', {
            account_id: accountId,
            amount: amount,
            description: description,
            idempotency_key: `mint-${Date.now()}`
        });
        
        showNotification(`Successfully minted $${(amount / 100).toFixed(2)} to account!`, 'success');
        document.getElementById('mint-form').reset();
        await loadAccounts();
        loadAccountOptions();
        loadHeaderStats(); // Update header stats
        if (document.getElementById('dashboard-tab').classList.contains('active')) {
            loadDashboard();
        }
    } catch (error) {
        showNotification(`Failed to mint: ${error.message}`, 'error');
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// Transfer value
async function transferValue(event) {
    event.preventDefault();
    const fromAccountId = document.getElementById('from-account-id').value;
    const toAccountId = document.getElementById('to-account-id').value;
    const amount = parseInt(document.getElementById('transfer-amount').value);
    const description = document.getElementById('transfer-description').value;
    const button = event.target.querySelector('button[type="submit"]');
    const originalText = button.innerHTML;
    
    if (!fromAccountId || !toAccountId) {
        showNotification('Please select both accounts', 'error');
        return;
    }
    
    if (fromAccountId === toAccountId) {
        showNotification('Cannot transfer to the same account', 'error');
        return;
    }
    
    button.innerHTML = '<span>⏳</span> Transferring...';
    button.disabled = true;
    
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
        await loadAccounts();
        loadAccountOptions();
        await loadTransactions();
        loadHeaderStats(); // Update header stats
        if (document.getElementById('dashboard-tab').classList.contains('active')) {
            loadDashboard();
        }
    } catch (error) {
        showNotification(`Failed to transfer: ${error.message}`, 'error');
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// Load transactions
async function loadTransactions() {
    const listEl = document.getElementById('transactions-list');
    if (listEl) {
        listEl.innerHTML = '<div class="loading">Loading transactions...</div>';
    }
    
    try {
        const response = await apiCall('/transactions');
        const transactions = response.transactions || [];
        allTransactions = transactions;
        
        // Update header stats
        const transactionsEl = document.getElementById('total-transactions');
        if (transactionsEl) transactionsEl.textContent = transactions.length;
        
        if (listEl) {
            if (transactions.length === 0) {
                listEl.innerHTML = '<div class="empty-state">No transactions yet.</div>';
                return;
            }
            
            displayTransactions(transactions);
        }
    } catch (error) {
        if (listEl) {
            listEl.innerHTML = `<div class="empty-state">Error: ${error.message}</div>`;
        }
        showNotification(`Failed to load transactions: ${error.message}`, 'error');
    }
}

// Display transactions
function displayTransactions(transactions) {
    const listEl = document.getElementById('transactions-list');
    listEl.innerHTML = transactions.map(tx => {
        const amount = `$${(tx.amount / 100).toFixed(2)}`;
        const txClass = tx.type === 'MINT' ? 'mint' : 'transfer';
        const typeLabel = tx.type === 'MINT' ? 'MINT' : 'TRANSFER';
        
        let details = '';
        if (tx.type === 'MINT') {
            details = `To: ${tx.to_account_id ? tx.to_account_id.substring(0, 12) + '...' : 'N/A'}`;
        } else {
            details = `From: ${tx.from_account_id ? tx.from_account_id.substring(0, 12) + '...' : 'N/A'} → To: ${tx.to_account_id ? tx.to_account_id.substring(0, 12) + '...' : 'N/A'}`;
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
}

// Filter transactions
function filterTransactions() {
    const filter = document.getElementById('transaction-filter').value;
    let filtered = allTransactions;
    
    if (filter !== 'all') {
        filtered = allTransactions.filter(tx => tx.type === filter);
    }
    
    displayTransactions(filtered);
}

// Load header stats on page load
async function loadHeaderStats() {
    try {
        const [accounts, transactionsResponse] = await Promise.all([
            apiCall('/accounts'),
            apiCall('/transactions')
        ]);
        
        const transactions = transactionsResponse.transactions || [];
        updateHeaderStats(accounts, transactions);
    } catch (error) {
        console.error('Failed to load header stats:', error);
        // Set default values on error
        const accountsEl = document.getElementById('total-accounts');
        const balanceEl = document.getElementById('total-balance');
        const transactionsEl = document.getElementById('total-transactions');
        
        if (accountsEl) accountsEl.textContent = '0';
        if (balanceEl) balanceEl.textContent = '$0.00';
        if (transactionsEl) transactionsEl.textContent = '0';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Load header stats immediately
    loadHeaderStats();
    
    // Load dashboard if on dashboard tab
    if (document.getElementById('dashboard-tab').classList.contains('active')) {
        loadDashboard();
    }
    
    // Load account options for dropdowns
    loadAccountOptions();
});
