/**
 * RecruitAI - Main JavaScript File
 * Contains all the functionality for the RecruitAI web application
 */

// Global configuration
const API_BASE_URL = 'http://localhost:8000'; // Base URL for API endpoints

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    initializeFileUploads();
    initializeFormSubmissions();
    loadSelectionOptions();
    addDarkModeToggle();
});

/**
 * Initialize mobile navigation functionality
 */
function initializeNavigation() {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }
}

/**
 * Initialize file upload areas with drag and drop functionality
 */
function initializeFileUploads() {
    const uploadAreas = document.querySelectorAll('.upload-area');
    
    uploadAreas.forEach(area => {
        const input = area.querySelector('input[type="file"]');
        const fileNameDisplay = area.querySelector('.file-name');
        const fileList = document.querySelector('.file-list');
        
        if (!input) return;
        
        // Click on upload area to trigger file input
        area.addEventListener('click', function() {
            input.click();
        });
        
        // Drag and drop functionality
        area.addEventListener('dragover', function(e) {
            e.preventDefault();
            area.classList.add('dragover');
        });
        
        area.addEventListener('dragleave', function(e) {
            e.preventDefault();
            area.classList.remove('dragover');
        });
        
        area.addEventListener('drop', function(e) {
            e.preventDefault();
            area.classList.remove('dragover');
            
            if (e.dataTransfer.files.length) {
                input.files = e.dataTransfer.files;
                updateFileList(input.files, fileList);
                
                if (fileNameDisplay) {
                    if (input.files.length === 1) {
                        fileNameDisplay.textContent = input.files[0].name;
                    } else {
                        fileNameDisplay.textContent = `${input.files.length} files selected`;
                    }
                }
            }
        });
        
        // File selection change
        input.addEventListener('change', function() {
            if (fileNameDisplay) {
                if (input.files.length === 1) {
                    fileNameDisplay.textContent = input.files[0].name;
                } else if (input.files.length > 1) {
                    fileNameDisplay.textContent = `${input.files.length} files selected`;
                } else {
                    fileNameDisplay.textContent = '';
                }
            }
            
            if (fileList) {
                updateFileList(input.files, fileList);
            }
        });
    });
}

/**
 * Update the file list display with selected files
 */
function updateFileList(files, fileListElement) {
    if (!fileListElement) return;
    
    // Clear current list
    fileListElement.innerHTML = '';
    
    if (files.length === 0) {
        fileListElement.innerHTML = `
            <div class="text-center text-gray-500 py-4">
                <p>No files selected yet</p>
            </div>
        `;
        return;
    }
    
    // Add each file to the list
    Array.from(files).forEach(file => {
        const fileSize = formatFileSize(file.size);
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <i class="fas fa-file-alt text-indigo-500"></i>
            <div class="file-name">${file.name}</div>
            <div class="file-size">${fileSize}</div>
        `;
        fileListElement.appendChild(fileItem);
    });
}

/**
 * Format file size to human-readable format
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Initialize form submissions with API endpoints
 */
function initializeFormSubmissions() {
    const forms = document.querySelectorAll('form[data-api-submit]');
    
    forms.forEach(form => {
        const endpoint = form.getAttribute('data-api-submit');
        const successRedirect = form.getAttribute('data-success-redirect');
        const messageContainer = form.querySelector('.message-container') || 
                               document.querySelector('.alert-container');
        
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Show loading state
            if (messageContainer) {
                messageContainer.innerHTML = `
                    <div class="flex items-center justify-center p-4 bg-indigo-50 rounded-md">
                        <div class="spinner mr-3"></div>
                        <p class="text-indigo-700">Processing request...</p>
                    </div>
                `;
            }
            
            try {
                const formData = new FormData(form);
                const response = await fetch(`${API_BASE_URL}/${endpoint}`, {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    // Success message
                    if (messageContainer) {
                        messageContainer.innerHTML = `
                            <div class="alert alert-success">
                                <i class="fas fa-check-circle mr-2"></i>
                                ${result.message || 'Success! Your request has been processed.'}
                            </div>
                        `;
                    }
                    
                    // Clear form
                    form.reset();
                    const fileList = form.querySelector('.file-list');
                    if (fileList) {
                        updateFileList([], fileList);
                    }
                    
                    // Redirect if specified
                    if (successRedirect) {
                        setTimeout(() => {
                            window.location.href = successRedirect;
                        }, 1000);
                    }
                } else {
                    // Error message
                    if (messageContainer) {
                        messageContainer.innerHTML = `
                            <div class="alert alert-error">
                                <i class="fas fa-exclamation-circle mr-2"></i>
                                ${result.detail || 'An error occurred. Please try again.'}
                            </div>
                        `;
                    }
                }
            } catch (error) {
                // Network or other errors
                if (messageContainer) {
                    messageContainer.innerHTML = `
                        <div class="alert alert-error">
                            <i class="fas fa-exclamation-circle mr-2"></i>
                            Network error. Please check your connection and try again.
                        </div>
                    `;
                }
                console.error('Form submission error:', error);
            }
        });
    });

    // Match form specific handling
    const matchForm = document.getElementById('match-form');
    if (matchForm) {
        matchForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const jobId = matchForm.querySelector('select[name="job_id"]').value;
            const candidateId = matchForm.querySelector('select[name="candidate_id"]').value;
            
            if (!jobId || !candidateId) {
                alert('Please select both a job description and a candidate.');
                return;
            }
            
            const resultContainer = document.getElementById('match-result-container');
            if (resultContainer) {
                resultContainer.innerHTML = `
                    <div class="text-center py-12">
                        <div class="spinner mx-auto"></div>
                        <p class="mt-4 text-gray-600">Calculating match score...</p>
                    </div>
                `;
                
                try {
                    const response = await fetch(`${API_BASE_URL}/match?job_id=${jobId}&candidate_id=${candidateId}`);
                    const result = await response.json();
                    
                    if (response.ok) {
                        // Determine score class based on value
                        let scoreClass = 'match-score-low';
                        let progressClass = 'match-progress-bar-low';
                        
                        if (result.match_score >= 80) {
                            scoreClass = 'match-score-high';
                            progressClass = 'match-progress-bar-high';
                        } else if (result.match_score >= 60) {
                            scoreClass = 'match-score-medium';
                            progressClass = 'match-progress-bar-medium';
                        }
                        
                        // Format matched skills
                        const matchedSkills = result.matched_skills.split(',').map(skill => 
                            `<span class="inline-block bg-indigo-100 text-indigo-800 px-2 py-1 rounded-full text-xs font-medium mr-2 mb-2">${skill.trim()}</span>`
                        ).join('');
                        
                        // Display match results
                        resultContainer.innerHTML = `
                            <div class="bg-white shadow overflow-hidden sm:rounded-lg">
                                <div class="px-4 py-5 sm:px-6 flex justify-between items-center">
                                    <div>
                                        <h3 class="text-lg leading-6 font-medium text-gray-900">
                                            Match Results
                                        </h3>
                                        <p class="mt-1 max-w-2xl text-sm text-gray-500">
                                            ${result.candidate_name} for ${result.job_title}
                                        </p>
                                    </div>
                                    <button onclick="scheduleInterviewRedirect(${jobId}, ${candidateId})" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                                        <i class="fas fa-calendar-alt mr-2"></i>
                                        Schedule Interview
                                    </button>
                                </div>
                                <div class="border-t border-gray-200">
                                    <div class="p-6">
                                        <div class="text-center mb-6">
                                            <div class="${scoreClass} match-score">${result.match_score}%</div>
                                            <div class="text-sm text-gray-500">Match Score</div>
                                            
                                            <div class="match-progress mt-2">
                                                <div class="match-progress-bar ${progressClass}" style="width: ${result.match_score}%"></div>
                                            </div>
                                        </div>
                                        
                                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                                            <div>
                                                <h4 class="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">
                                                    Candidate Information
                                                </h4>
                                                <p class="text-sm text-gray-900 mb-1">
                                                    <span class="font-medium">Name:</span> ${result.candidate_name}
                                                </p>
                                                <p class="text-sm text-gray-900 mb-1">
                                                    <span class="font-medium">Email:</span> ${result.candidate_email}
                                                </p>
                                                <p class="text-sm text-gray-900 mb-3">
                                                    <span class="font-medium">Phone:</span> ${result.candidate_phone || 'N/A'}
                                                </p>
                                                
                                                <h4 class="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">
                                                    Skills
                                                </h4>
                                                <div class="text-sm text-gray-900">
                                                    ${matchedSkills}
                                                </div>
                                            </div>
                                            
                                            <div>
                                                <h4 class="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">
                                                    Match Analysis
                                                </h4>
                                                <div class="bg-gray-50 p-3 rounded-md">
                                                    <p class="text-sm text-gray-700">
                                                        ${result.match_analysis || 'This candidate has a good match with the required skills for this position.'}
                                                    </p>
                                                </div>
                                                
                                                <h4 class="text-sm font-medium text-gray-500 uppercase tracking-wider mt-4 mb-3">
                                                    Job Details
                                                </h4>
                                                <p class="text-sm text-gray-900 mb-1">
                                                    <span class="font-medium">Title:</span> ${result.job_title}
                                                </p>
                                                <p class="text-sm text-gray-900 mb-1">
                                                    <span class="font-medium">Company:</span> ${result.company || 'Your Company'}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    } else {
                        resultContainer.innerHTML = `
                            <div class="alert alert-error">
                                <i class="fas fa-exclamation-circle mr-2"></i>
                                ${result.detail || 'An error occurred while calculating the match score.'}
                            </div>
                        `;
                    }
                } catch (error) {
                    resultContainer.innerHTML = `
                        <div class="alert alert-error">
                            <i class="fas fa-exclamation-circle mr-2"></i>
                            Network error. Please try again.
                        </div>
                    `;
                }
            }
        });
    }

    // Schedule interview form handling
    const scheduleForm = document.getElementById('schedule-interview-form');
    if (scheduleForm) {
        scheduleForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const messageContainer = document.querySelector('.alert-container');
            
            // Show loading state
            if (messageContainer) {
                messageContainer.innerHTML = `
                    <div class="flex items-center justify-center p-4 bg-indigo-50 rounded-md">
                        <div class="spinner mr-3"></div>
                        <p class="text-indigo-700">Scheduling interview...</p>
                    </div>
                `;
            }
            
            try {
                const formData = new FormData(scheduleForm);
                const response = await fetch(`${API_BASE_URL}/schedule-interview`, {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    // Success message
                    if (messageContainer) {
                        messageContainer.innerHTML = `
                            <div class="alert alert-success">
                                <i class="fas fa-check-circle mr-2"></i>
                                ${result.message || 'Interview scheduled successfully!'}
                            </div>
                        `;
                    }
                    
                    // Clear form
                    scheduleForm.reset();
                    
                    // Reload upcoming interviews
                    setTimeout(() => {
                        loadUpcomingInterviews();
                    }, 1000);
                } else {
                    // Error message
                    if (messageContainer) {
                        messageContainer.innerHTML = `
                            <div class="alert alert-error">
                                <i class="fas fa-exclamation-circle mr-2"></i>
                                ${result.detail || 'An error occurred while scheduling the interview.'}
                            </div>
                        `;
                    }
                }
            } catch (error) {
                // Network or other errors
                if (messageContainer) {
                    messageContainer.innerHTML = `
                        <div class="alert alert-error">
                            <i class="fas fa-exclamation-circle mr-2"></i>
                            Network error. Please check your connection and try again.
                        </div>
                    `;
                }
            }
        });
    }
}

/**
 * Load selection options for dropdowns
 */
function loadSelectionOptions() {
    // Job selection dropdowns
    const jobSelects = document.querySelectorAll('select[name="job_id"], #shortlisted-job-select');
    if (jobSelects.length > 0) {
        fetchAndPopulateSelect(jobSelects, 'jobs', 'id', 'title');
    }
    
    // Candidate selection dropdowns
    const candidateSelects = document.querySelectorAll('select[name="candidate_id"]');
    if (candidateSelects.length > 0) {
        fetchAndPopulateSelect(candidateSelects, 'candidates', 'id', 'name');
    }
}

/**
 * Fetch data and populate select elements
 */
async function fetchAndPopulateSelect(selectElements, endpoint, valueKey, textKey) {
    try {
        const response = await fetch(`${API_BASE_URL}/${endpoint}`);
        const data = await response.json();
        
        if (response.ok && Array.isArray(data)) {
            const options = data.map(item => {
                return `<option value="${item[valueKey]}">${item[textKey]}</option>`;
            }).join('');
            
            selectElements.forEach(select => {
                // Preserve the first option (usually "Select a...")
                const firstOption = select.querySelector('option:first-child').outerHTML;
                select.innerHTML = firstOption + options;
            });
        }
    } catch (error) {
        console.error(`Error loading ${endpoint}:`, error);
    }
}

/**
 * Navigate to interview scheduling page with pre-selected job and candidate
 */
function scheduleInterviewRedirect(jobId, candidateId) {
    window.location.href = `schedule-interview.html?job_id=${jobId}&candidate_id=${candidateId}`;
}

/**
 * Load parameters from URL and pre-select options
 */
function loadUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    const jobId = urlParams.get('job_id');
    const candidateId = urlParams.get('candidate_id');
    
    if (jobId) {
        const jobSelect = document.querySelector('select[name="job_id"]');
        if (jobSelect) {
            jobSelect.value = jobId;
        }
    }
    
    if (candidateId) {
        const candidateSelect = document.querySelector('select[name="candidate_id"]');
        if (candidateSelect) {
            candidateSelect.value = candidateId;
        }
    }
}

// Call this function when URL parameters should be processed
window.addEventListener('load', loadUrlParams);

// Dark Mode Toggle
function addDarkModeToggle() {
    // Create toggle button HTML
    const toggleButton = document.createElement('button');
    toggleButton.classList.add('dark-mode-toggle');
    toggleButton.innerHTML = '<i class="fas fa-moon"></i>';
    toggleButton.setAttribute('title', 'Toggle Dark Mode');
    toggleButton.setAttribute('aria-label', 'Toggle Dark Mode');
    
    // Style the button
    toggleButton.style.position = 'fixed';
    toggleButton.style.bottom = '20px';
    toggleButton.style.right = '20px';
    toggleButton.style.width = '50px';
    toggleButton.style.height = '50px';
    toggleButton.style.borderRadius = '25px';
    toggleButton.style.backgroundColor = 'var(--color-accent-primary)';
    toggleButton.style.color = 'white';
    toggleButton.style.border = 'none';
    toggleButton.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.2)';
    toggleButton.style.cursor = 'pointer';
    toggleButton.style.zIndex = '9999';
    toggleButton.style.display = 'flex';
    toggleButton.style.alignItems = 'center';
    toggleButton.style.justifyContent = 'center';
    toggleButton.style.fontSize = '1.2rem';
    
    // Add to body
    document.body.appendChild(toggleButton);
    
    // Always stay in dark mode as per requirements
    // This just changes the icon if someone clicks it
    toggleButton.addEventListener('click', function() {
        if (toggleButton.innerHTML.includes('fa-moon')) {
            toggleButton.innerHTML = '<i class="fas fa-sun"></i>';
        } else {
            toggleButton.innerHTML = '<i class="fas fa-moon"></i>';
        }
        
        // Show a toast message
        showToast('MARN AI is in permanent dark mode');
    });
}

// Show a toast message
function showToast(message) {
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.style.position = 'fixed';
    toast.style.bottom = '80px';
    toast.style.right = '20px';
    toast.style.backgroundColor = 'var(--color-bg-secondary)';
    toast.style.color = 'var(--color-text-primary)';
    toast.style.padding = '10px 20px';
    toast.style.borderRadius = '4px';
    toast.style.zIndex = '10000';
    toast.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.2)';
    toast.style.transition = 'opacity 0.5s ease';
    toast.style.opacity = '0';
    
    document.body.appendChild(toast);
    
    // Fade in
    setTimeout(() => {
        toast.style.opacity = '1';
    }, 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 500);
    }, 3000);
} 