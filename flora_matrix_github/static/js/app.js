// --- Utilities ---
const showToast = (message, isError = false) => {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.style.borderColor = isError ? 'var(--danger)' : 'var(--accent)';
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 4000);
};

// --- Authentication ---
function toggleAuth(type) {
    const signInBox = document.getElementById('signInBox');
    const signUpBox = document.getElementById('signUpBox');
    if (type === 'signup') {
        signInBox.style.display = 'none';
        signUpBox.style.display = 'block';
    } else {
        signInBox.style.display = 'block';
        signUpBox.style.display = 'none';
    }
}

document.getElementById('signInForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    btn.textContent = 'Signing in...';
    btn.disabled = true;

    const username = document.getElementById('si-username').value;
    const password = document.getElementById('si-password').value;

    try {
        const res = await fetch('/signin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        
        if (data.success) {
            window.location.href = '/dashboard';
        } else {
            showToast(data.message, true);
        }
    } catch (err) {
        showToast('Connection error', true);
    } finally {
        btn.textContent = 'Sign In';
        btn.disabled = false;
    }
});

document.getElementById('signUpForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    btn.textContent = 'Creating account...';
    btn.disabled = true;

    const username = document.getElementById('su-username').value;
    const password = document.getElementById('su-password').value;

    try {
        const res = await fetch('/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        
        if (data.success) {
            showToast(data.message);
            toggleAuth('signin');
            document.getElementById('si-username').value = username;
        } else {
            showToast(data.message, true);
        }
    } catch (err) {
        showToast('Connection error', true);
    } finally {
        btn.textContent = 'Sign Up';
        btn.disabled = false;
    }
});

async function logout() {
    await fetch('/logout', { method: 'POST' });
    window.location.href = '/';
}


// --- Main Dashboard Predictor ---
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

if (dropZone && fileInput) {
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFileUpload(fileInput.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFileUpload(e.target.files[0]);
        }
    });
}

function handleFileUpload(file) {
    if (!file.type.startsWith('image/')) {
        showToast('Please upload an image file.', true);
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    const spinner = document.getElementById('loadingSpinner');
    const resultSection = document.getElementById('resultSection');
    
    spinner.style.display = 'block';
    resultSection.style.display = 'none';

    // Preview
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('uploadedImage').src = e.target.result;
    };
    reader.readAsDataURL(file);

    fetch('/api/predict', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        spinner.style.display = 'none';
        if (data.success) {
            resultSection.style.display = 'flex';
            document.getElementById('diseaseName').textContent = data.remedy ? data.remedy.display_name : data.disease_class;
            document.getElementById('confidenceText').textContent = data.confidence + '%';
            
            setTimeout(() => {
                document.getElementById('confidenceBar').style.width = data.confidence + '%';
                if(data.confidence < 70) {
                    document.getElementById('confidenceBar').style.background = 'linear-gradient(90deg, #e07a7a, #c05a5a)';
                } else {
                    document.getElementById('confidenceBar').style.background = 'linear-gradient(90deg, #4a9a4a, #7ec87e)';
                }
            }, 100);

            if (data.remedy) {
                document.getElementById('remedyPreview').style.display = 'block';
                document.getElementById('remedyTitle').textContent = data.remedy.display_name + " Remedies";
                document.getElementById('remedyDesc').textContent = data.remedy.treatment;
            }
            
            document.getElementById('resultSection').scrollIntoView({ behavior: 'smooth' });
        } else {
            showToast(data.error || 'Prediction Failed', true);
        }
    })
    .catch(err => {
        spinner.style.display = 'none';
        showToast('Server connection error.', true);
    });
}


// --- Remedies Page ---
let allRemedies = [];

async function fetchRemedies() {
    const spinner = document.getElementById('remediesSpinner');
    const container = document.getElementById('remediesContainer');
    
    if(!container) return; // Not on remedies page

    spinner.style.display = 'block';
    
    try {
        const res = await fetch('/api/remedies_data');
        allRemedies = await res.json();
        renderRemedies(allRemedies);
    } catch (err) {
        showToast('Failed to load remedies.', true);
    } finally {
        spinner.style.display = 'none';
    }
}

function renderRemedies(remedies) {
    const container = document.getElementById('remediesContainer');
    container.innerHTML = '';

    if (remedies.length === 0) {
        container.innerHTML = '<p style="text-align:center; grid-column:1/-1; color: var(--text-muted);">No remedies found.</p>';
        return;
    }

    remedies.forEach((remedy, idx) => {
        const isHealthy = remedy.disease.toLowerCase().includes('healthy');
        const borderStyle = isHealthy ? 'border-top: 4px solid var(--success)' : 'border-top: 4px solid var(--danger)';

        const card = document.createElement('div');
        card.className = 'remedy-card glass';
        card.style = borderStyle;
        card.innerHTML = `
            <span class="crop-tag">${remedy.crop}</span>
            <h3>${remedy.display_name}</h3>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-top: 0.5rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                ${remedy.symptoms}
            </p>
            
            <div class="remedy-details">
                <div class="detail-section">
                    <h4>Symptoms</h4>
                    <p>${remedy.symptoms || 'N/A'}</p>
                </div>
                <div class="detail-section">
                    <h4>Treatment</h4>
                    <p>${remedy.treatment || 'N/A'}</p>
                </div>
                <div class="detail-section">
                    <h4>Prevention</h4>
                    <p>${remedy.prevention || 'N/A'}</p>
                </div>
                <div class="detail-section">
                    <h4>Organic Options</h4>
                    <p>${remedy.organic_options || 'N/A'}</p>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 1.5rem; color: var(--accent); font-size: 0.8rem; letter-spacing: 1px; text-transform: uppercase;">
                Click to expand ⌄
            </div>
        `;

        card.addEventListener('click', () => {
            const isExpanded = card.classList.contains('expanded');
            // Close all other cards
            document.querySelectorAll('.remedy-card').forEach(c => c.classList.remove('expanded'));
            
            if (!isExpanded) {
                card.classList.add('expanded');
                // update icon
                card.querySelector('div:last-child').textContent = 'Click to collapse ⌃';
            } else {
                card.querySelector('div:last-child').textContent = 'Click to expand ⌄';
            }
        });

        container.appendChild(card);
    });
}

const searchInput = document.getElementById('searchInput');
if (searchInput) {
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        const filtered = allRemedies.filter(r => 
            r.display_name.toLowerCase().includes(query) || 
            r.crop.toLowerCase().includes(query) ||
            r.disease.toLowerCase().includes(query)
        );
        renderRemedies(filtered);
    });
}
