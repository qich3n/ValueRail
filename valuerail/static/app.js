const API_BASE = '/api/v1';
let allAccounts = [];
let allTransactions = [];

// Theme management
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    showNotification(
        `Switched to ${newTheme} mode`,
        'info'
    );
}

// Load saved theme on page load
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

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
    event.target.closest('.tab-button').classList.add('active');
    
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

// Copy to clipboard
function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    const text = element.textContent;
    
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard!', 'success');
    }).catch(() => {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showNotification('Copied to clipboard!', 'success');
    });
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
    
    if (accountsEl) {
        animateValue(accountsEl, parseInt(accountsEl.textContent) || 0, accounts.length);
    }
    if (balanceEl) {
        const current = parseFloat(balanceEl.textContent.replace('$', '')) || 0;
        animateValue(balanceEl, current, totalBalance / 100, true);
    }
    if (transactionsEl) {
        animateValue(transactionsEl, parseInt(transactionsEl.textContent) || 0, transactions.length);
    }
}

// Animate value changes
function animateValue(element, start, end, isCurrency = false) {
    const duration = 500;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = start + (end - start) * easeOutCubic(progress);
        
        if (isCurrency) {
            element.textContent = `$${current.toFixed(2)}`;
        } else {
            element.textContent = Math.round(current);
        }
        
        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            if (isCurrency) {
                element.textContent = `$${end.toFixed(2)}`;
            } else {
                element.textContent = end;
            }
        }
    }
    
    requestAnimationFrame(update);
}

function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
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
        <div class="account-card" onclick="showAccountModal('${account.id}')">
            <h3>${account.name}</h3>
            <div class="account-id">
                <span class="account-id-text">ID: ${account.id.substring(0, 20)}...</span>
                <button class="btn-copy" onclick="event.stopPropagation(); copyToClipboard('account-id-${account.id}')" title="Copy ID">
                    📋
                </button>
            </div>
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
        <div class="account-card" onclick="showAccountModal('${account.id}')">
            <h3>${account.name}</h3>
            <div class="account-id">
                <span class="account-id-text" id="account-id-${account.id}">${account.id}</span>
                <button class="btn-copy" onclick="event.stopPropagation(); copyToClipboard('account-id-${account.id}')" title="Copy ID">
                    📋
                </button>
            </div>
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

// Show account modal
async function showAccountModal(accountId) {
    try {
        const account = await apiCall(`/accounts/${accountId}`);
        const balance = await apiCall(`/accounts/${accountId}/balance`);
        const transactions = allTransactions.filter(tx => 
            tx.from_account_id === accountId || tx.to_account_id === accountId
        ).slice(0, 10);
        
        document.getElementById('modal-account-name').textContent = account.name;
        document.getElementById('modal-account-id').textContent = account.id;
        document.getElementById('modal-account-balance').textContent = `$${(balance.balance / 100).toFixed(2)}`;
        document.getElementById('modal-account-created').textContent = new Date(account.created_at).toLocaleString();
        
        const modalTxEl = document.getElementById('modal-transactions');
        if (transactions.length === 0) {
            modalTxEl.innerHTML = '<div class="empty-state">No transactions for this account</div>';
        } else {
            modalTxEl.innerHTML = transactions.map(tx => {
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
        
        document.getElementById('account-modal').classList.add('show');
    } catch (error) {
        showNotification(`Failed to load account details: ${error.message}`, 'error');
    }
}

// Close account modal
function closeAccountModal() {
    document.getElementById('account-modal').classList.remove('show');
}

// Close modal on outside click
document.addEventListener('click', (e) => {
    const modal = document.getElementById('account-modal');
    if (e.target === modal) {
        closeAccountModal();
    }
});

// Load account options for dropdowns
async function loadAccountOptions() {
    try {
        const accounts = await apiCall('/accounts');
        allAccounts = accounts;
        
        const options = accounts.map(acc => 
            `<option value="${acc.id}" data-balance="${acc.balance}">${acc.name} ($${(acc.balance / 100).toFixed(2)})</option>`
        ).join('');
        
        document.getElementById('mint-account-id').innerHTML = '<option value="">Select Account...</option>' + options;
        document.getElementById('from-account-id').innerHTML = '<option value="">From Account...</option>' + options;
        document.getElementById('to-account-id').innerHTML = '<option value="">To Account...</option>' + options;
        
        updateTransferBalance();
    } catch (error) {
        showNotification(`Failed to load accounts: ${error.message}`, 'error');
    }
}

// Update transfer balance previews
function updateTransferBalance() {
    const fromId = document.getElementById('from-account-id').value;
    const toId = document.getElementById('to-account-id').value;
    
    const fromBalanceEl = document.getElementById('from-balance');
    const toBalanceEl = document.getElementById('to-balance');
    
    if (fromId) {
        const account = allAccounts.find(acc => acc.id === fromId);
        if (account && fromBalanceEl) {
            fromBalanceEl.textContent = `Balance: $${(account.balance / 100).toFixed(2)}`;
            fromBalanceEl.style.display = 'block';
        }
    } else if (fromBalanceEl) {
        fromBalanceEl.style.display = 'none';
    }
    
    if (toId) {
        const account = allAccounts.find(acc => acc.id === toId);
        if (account && toBalanceEl) {
            toBalanceEl.textContent = `Balance: $${(account.balance / 100).toFixed(2)}`;
            toBalanceEl.style.display = 'block';
        }
    } else if (toBalanceEl) {
        toBalanceEl.style.display = 'none';
    }
}

// Update amount displays
function updateTransferAmount() {
    const amount = parseInt(document.getElementById('transfer-amount').value) || 0;
    const displayEl = document.getElementById('transfer-amount-display');
    if (displayEl) {
        displayEl.textContent = (amount / 100).toFixed(2);
    }
}

// Update mint amount display
document.addEventListener('DOMContentLoaded', () => {
    const mintAmountInput = document.getElementById('mint-amount');
    if (mintAmountInput) {
        mintAmountInput.addEventListener('input', () => {
            const amount = parseInt(mintAmountInput.value) || 0;
            const displayEl = document.getElementById('mint-amount-display');
            if (displayEl) {
                displayEl.textContent = (amount / 100).toFixed(2);
            }
        });
    }
});

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
        document.getElementById('mint-amount-display').textContent = '0.00';
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
    
    const fromAccount = allAccounts.find(acc => acc.id === fromAccountId);
    if (fromAccount && amount > fromAccount.balance) {
        showNotification(`Insufficient balance. Available: $${(fromAccount.balance / 100).toFixed(2)}`, 'error');
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
        document.getElementById('transfer-amount-display').textContent = '0.00';
        document.getElementById('from-balance').style.display = 'none';
        document.getElementById('to-balance').style.display = 'none';
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
        if (transactionsEl) {
            animateValue(transactionsEl, parseInt(transactionsEl.textContent) || 0, transactions.length);
        }
        
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
    listEl.innerHTML = transactions.map((tx, index) => {
        const amount = `$${(tx.amount / 100).toFixed(2)}`;
        const txClass = tx.type === 'MINT' ? 'mint' : 'transfer';
        const typeLabel = tx.type === 'MINT' ? 'MINT' : 'TRANSFER';
        
        let details = '';
        if (tx.type === 'MINT') {
            const account = allAccounts.find(acc => acc.id === tx.to_account_id);
            details = `To: ${account ? account.name : tx.to_account_id.substring(0, 12) + '...'}`;
        } else {
            const fromAccount = allAccounts.find(acc => acc.id === tx.from_account_id);
            const toAccount = allAccounts.find(acc => acc.id === tx.to_account_id);
            details = `From: ${fromAccount ? fromAccount.name : tx.from_account_id.substring(0, 12) + '...'} → To: ${toAccount ? toAccount.name : tx.to_account_id.substring(0, 12) + '...'}`;
        }
        
        return `
            <div class="transaction-item ${txClass}" style="animation-delay: ${index * 0.05}s">
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
    // Load theme preference
    loadTheme();
    
    // Load header stats immediately
    loadHeaderStats();
    
    // Load dashboard if on dashboard tab
    if (document.getElementById('dashboard-tab').classList.contains('active')) {
        loadDashboard();
    }
    
    // Load account options for dropdowns
    loadAccountOptions();
});
