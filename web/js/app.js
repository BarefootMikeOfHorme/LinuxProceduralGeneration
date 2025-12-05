/**
 * VaultMind Forge - Main Application
 * Initializes UI, connects to API, manages state
 */

// Application state
const appState = {
    connected: false,
    agents: [],
    activeTab: 'generation',
    currentJob: null,
    lineageRecords: [],
    stats: {
        totalGenerated: 0,
        validated: 0,
        rejected: 0,
        avgScore: 0
    }
};

// Settings
const settings = {
    apiUrl: 'http://localhost:5084',
    backend: 'local', // local, huggingface, nvidia, replicate
    agentAutonomy: true,
    autonomyThreshold: 75,
    autoValidate: true,
    outputDir: './output',
    // Cloud API keys (stored in localStorage, not sent to server)
    hf_token: '',
    nvidia_api_key: '',
    replicate_token: ''
};

/**
 * Initialize application
 */
async function initApp() {
    console.log('🔥 VaultMind Forge - Initializing...');

    // Load settings from localStorage
    loadSettings();

    // Setup UI event listeners
    setupEventListeners();

    // Connect to API
    await connectToAPI();

    // Initialize agents
    await initAgents();

    // Load recent lineage
    await loadLineage();

    // Start polling for updates
    startPolling();

    console.log('✅ VaultMind Forge - Ready!');
}

/**
 * Connect to Node.js API
 */
async function connectToAPI() {
    showLoading('Connecting to API...');

    try {
        api.baseUrl = settings.apiUrl;

        const result = await api.testConnection();

        if (result.success) {
            appState.connected = true;
            updateConnectionStatus(true);
            showNotification('success', 'Connected to VaultMind Forge API');

            // Get version info
            const version = await api.getVersion();
            console.log('API Version:', version);
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        appState.connected = false;
        updateConnectionStatus(false);
        showNotification('error', `Connection failed: ${error.message}`);
        console.error('Connection error:', error);
    } finally {
        hideLoading();
    }
}

/**
 * Initialize agents display
 */
async function initAgents() {
    // VaultMind Forge specialist agents
    appState.agents = [
        {
            id: 'quality_guardian',
            name: 'Quality Guardian',
            status: 'idle',
            autonomy: 0.75,
            tasks: 0
        },
        {
            id: 'prompt_refiner',
            name: 'Prompt Refiner',
            status: 'idle',
            autonomy: 0.85,
            tasks: 0
        },
        {
            id: 'parameter_optimizer',
            name: 'Parameter Optimizer',
            status: 'idle',
            autonomy: 0.70,
            tasks: 0
        },
        {
            id: 'material_specialist',
            name: 'Material Specialist',
            status: 'idle',
            autonomy: 0.75,
            tasks: 0
        },
        {
            id: 'resolution_expert',
            name: 'Resolution Expert',
            status: 'idle',
            autonomy: 0.80,
            tasks: 0
        }
    ];

    renderAgents();
    updateAgentCount();
}

/**
 * Render agents list
 */
function renderAgents() {
    const container = document.getElementById('agentsList');
    container.innerHTML = '';

    appState.agents.forEach(agent => {
        const card = document.createElement('div');
        card.className = `agent-card ${agent.status === 'running' ? 'active' : ''}`;
        card.dataset.agentId = agent.id;

        card.innerHTML = `
            <div class="agent-header">
                <span class="agent-name">${agent.name}</span>
                <span class="agent-status ${agent.status}">${agent.status.toUpperCase()}</span>
            </div>
            <div class="agent-autonomy">
                Autonomy: ${(agent.autonomy * 100).toFixed(0)}%
                <div class="autonomy-bar">
                    <div class="autonomy-fill" style="width: ${agent.autonomy * 100}%"></div>
                </div>
            </div>
        `;

        card.addEventListener('click', () => selectAgent(agent.id));

        container.appendChild(card);
    });
}

/**
 * Update agent count badge
 */
function updateAgentCount() {
    const activeCount = appState.agents.filter(a => a.status === 'running').length;
    const totalCount = appState.agents.length;

    document.getElementById('activeAgentCount').textContent = `${activeCount}/${totalCount} Active`;
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(connected) {
    const indicator = document.getElementById('apiStatus');

    if (connected) {
        indicator.classList.add('connected');
        indicator.querySelector('.status-text').textContent = 'Connected';
    } else {
        indicator.classList.remove('connected');
        indicator.querySelector('.status-text').textContent = 'Disconnected';
    }
}

/**
 * Setup UI event listeners
 */
function setupEventListeners() {
    // Top bar actions
    document.getElementById('newGenerationBtn').addEventListener('click', () => switchTab('generation'));
    document.getElementById('workflowBtn').addEventListener('click', () => switchTab('workflow'));
    document.getElementById('settingsBtn').addEventListener('click', openSettings);

    // Generation controls
    document.getElementById('generateBtn').addEventListener('click', handleGenerate);
    document.getElementById('multiPassBtn').addEventListener('click', handleMultiPassGenerate);
    document.getElementById('refinePromptBtn').addEventListener('click', refinePrompt);
    document.getElementById('loadTemplateBtn').addEventListener('click', loadTemplate);

    // Settings
    document.getElementById('closeSettings').addEventListener('click', closeSettings);
    document.getElementById('saveSettingsBtn').addEventListener('click', saveSettings);
    document.getElementById('testConnectionBtn').addEventListener('click', connectToAPI);

    // Tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            const tabName = e.currentTarget.dataset.tab;
            switchTab(tabName);
        });
    });

    // Settings inputs
    document.getElementById('autonomyThresholdInput').addEventListener('input', (e) => {
        e.target.nextElementSibling.textContent = `${e.target.value}%`;
    });
}

/**
 * Switch active tab
 */
function switchTab(tabName) {
    appState.activeTab = tabName;

    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => {
        if (tab.dataset.tab === tabName) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        if (content.dataset.tabContent === tabName) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
}

/**
 * Handle asset generation
 */
async function handleGenerate() {
    const prompt = document.getElementById('promptInput').value.trim();

    if (!prompt) {
        showNotification('warning', 'Please enter a generation prompt');
        return;
    }

    showLoading('Generating asset...');

    try {
        const config = {
            prompt,
            width: parseInt(document.getElementById('widthInput').value),
            height: parseInt(document.getElementById('heightInput').value),
            num_inference_steps: parseInt(document.getElementById('stepsInput').value),
            batch_size: parseInt(document.getElementById('batchInput').value),
            output_type: document.getElementById('outputTypeSelect').value,
            id: document.getElementById('jobIdInput').value || undefined,
            backend: settings.backend
        };

        // Add API keys if using cloud backends
        if (settings.backend === 'huggingface') {
            config.hf_token = settings.hf_token;
        } else if (settings.backend === 'nvidia') {
            config.nvidia_api_key = settings.nvidia_api_key;
        } else if (settings.backend === 'replicate') {
            config.replicate_token = settings.replicate_token;
        }

        const result = await api.generateWithLineage(config);

        if (result.success) {
            showNotification('success', 'Generation completed!');
            displayGenerationResults(result.data);
            updateStats();
            await loadLineage();
        } else {
            throw new Error(result.error || 'Generation failed');
        }
    } catch (error) {
        showNotification('error', `Generation failed: ${error.message}`);
        console.error('Generation error:', error);
    } finally {
        hideLoading();
    }
}

/**
 * Display generation results
 */
function displayGenerationResults(data) {
    const resultsGrid = document.getElementById('resultsGrid');
    resultsGrid.innerHTML = '';

    if (!data.assets || data.assets.length === 0) {
        resultsGrid.innerHTML = '<div class="empty-state">No results generated</div>';
        return;
    }

    data.assets.forEach((asset, index) => {
        const card = document.createElement('div');
        card.className = 'result-card';

        const isWinner = asset.asset_path === data.winner;

        card.innerHTML = `
            <img
                src="${api.baseUrl}/output/${data.jobId}/${asset.asset_path.split(/[\\/]/).pop()}"
                alt="Generated asset ${index + 1}"
                class="result-image"
                onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22><rect fill=%22%23333%22 width=%22100%22 height=%22100%22/><text fill=%22%23999%22 x=%2250%%22 y=%2250%%22 text-anchor=%22middle%22 dy=%22.3em%22>No Image</text></svg>'"
            />
            <div class="result-info">
                <div class="result-score">
                    ${isWinner ? '🏆 ' : ''}
                    Score: ${(asset.metrics?.score || 0).toFixed(4)}
                </div>
                <div class="result-meta">
                    ${isWinner ? 'Winner • ' : ''}
                    ${asset.validated ? 'Validated' : 'Not validated'}
                </div>
            </div>
        `;

        resultsGrid.appendChild(card);
    });
}

/**
 * Load lineage records
 */
async function loadLineage() {
    try {
        const result = await api.queryLineage({ limit: 100 });

        if (result.success && result.data) {
            appState.lineageRecords = result.data;
            // TODO: Update LineageViewer React component
        }
    } catch (error) {
        console.error('Failed to load lineage:', error);
    }
}

/**
 * Update stats display
 */
function updateStats() {
    if (appState.lineageRecords.length === 0) return;

    const stats = {
        totalGenerated: appState.lineageRecords.length,
        validated: appState.lineageRecords.filter(r => r.validated).length,
        rejected: appState.lineageRecords.filter(r => r.status === 'rejected').length,
        avgScore: 0
    };

    const scores = appState.lineageRecords
        .map(r => r.quality_score)
        .filter(s => s != null);

    if (scores.length > 0) {
        stats.avgScore = scores.reduce((sum, s) => sum + s, 0) / scores.length;
    }

    document.getElementById('statTotalGenerated').textContent = stats.totalGenerated;
    document.getElementById('statValidated').textContent = stats.validated;
    document.getElementById('statRejected').textContent = stats.rejected;
    document.getElementById('statAvgScore').textContent = stats.avgScore.toFixed(2);

    appState.stats = stats;
}

/**
 * Settings management
 */
function loadSettings() {
    const stored = localStorage.getItem('vaultmind_settings');

    if (stored) {
        try {
            Object.assign(settings, JSON.parse(stored));
        } catch (e) {
            console.error('Failed to load settings:', e);
        }
    }

    applySettings();
}

function applySettings() {
    // Apply settings to UI
    document.getElementById('apiUrlInput').value = settings.apiUrl;
    document.getElementById('agentAutonomyToggle').checked = settings.agentAutonomy;
    document.getElementById('autonomyThresholdInput').value = settings.autonomyThreshold;
    document.getElementById('autoValidateToggle').checked = settings.autoValidate;
    document.getElementById('outputDirInput').value = settings.outputDir;

    // Update API client
    api.baseUrl = settings.apiUrl;
    api.setBackend(settings.backend);
}

function saveSettings() {
    // Read from UI
    settings.apiUrl = document.getElementById('apiUrlInput').value;
    settings.agentAutonomy = document.getElementById('agentAutonomyToggle').checked;
    settings.autonomyThreshold = parseInt(document.getElementById('autonomyThresholdInput').value);
    settings.autoValidate = document.getElementById('autoValidateToggle').checked;
    settings.outputDir = document.getElementById('outputDirInput').value;

    // Save to localStorage
    localStorage.setItem('vaultmind_settings', JSON.stringify(settings));

    applySettings();
    showNotification('success', 'Settings saved');
}

function openSettings() {
    document.getElementById('settingsPanel').classList.add('active');
}

function closeSettings() {
    document.getElementById('settingsPanel').classList.remove('active');
}

/**
 * UI helpers
 */
function showLoading(message = 'Loading...') {
    const overlay = document.getElementById('loadingOverlay');
    document.getElementById('loadingText').textContent = message;
    overlay.classList.add('active');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
}

function showNotification(type, message) {
    const container = document.getElementById('notificationsContainer');

    const notif = document.createElement('div');
    notif.className = `notification ${type}`;
    notif.textContent = message;

    container.appendChild(notif);

    setTimeout(() => {
        notif.style.opacity = '0';
        setTimeout(() => notif.remove(), 300);
    }, 4000);
}

function selectAgent(agentId) {
    console.log('Selected agent:', agentId);
    // TODO: Show agent details/terminal
}

function refinePrompt() {
    showNotification('info', 'Prompt refinement coming soon!');
    // TODO: Call AI to refine prompt
}

function loadTemplate() {
    showNotification('info', 'Templates coming soon!');
    // TODO: Show template selector
}

function handleMultiPassGenerate() {
    showNotification('info', 'Multi-pass generation - using batch size from parameters');
    handleGenerate(); // Uses batch_size parameter
}

/**
 * Polling for updates
 */
function startPolling() {
    setInterval(async () => {
        if (appState.connected) {
            try {
                const status = await api.getStatus();
                // Update UI based on status if needed
            } catch (error) {
                // Connection lost
                if (appState.connected) {
                    appState.connected = false;
                    updateConnectionStatus(false);
                    showNotification('warning', 'Connection to API lost');
                }
            }
        }
    }, 5000);
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initApp);
