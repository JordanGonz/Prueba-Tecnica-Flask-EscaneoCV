/**
 * AI Recruitment System - Main JavaScript Application
 * Provides client-side functionality for enhanced user experience
 */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // Initialize all components
    initializeTooltips();
    initializePopovers();
    initializeFormValidation();
    initializeAnimations();
    initializeUtilities();
    
    console.log('AI Recruitment System initialized successfully');
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize Bootstrap popovers
 */
function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Initialize form validation and enhancements
 */
function initializeFormValidation() {
    // Add real-time validation feedback
    const forms = document.querySelectorAll('form');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Focus on first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                    showNotification('Please check the form for errors', 'warning');
                }
            } else {
                // Show loading state for valid forms
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    showButtonLoading(submitBtn);
                }
            }
            
            form.classList.add('was-validated');
        }, false);
        
        // Real-time validation on input
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(function(input) {
            input.addEventListener('blur', function() {
                validateField(input);
            });
            
            input.addEventListener('input', function() {
                if (input.classList.contains('is-invalid')) {
                    validateField(input);
                }
            });
        });
    });
}

/**
 * Validate individual form field
 */
function validateField(field) {
    if (field.checkValidity()) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
        
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.style.display = 'none';
        }
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
        
        let feedback = field.parentNode.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentNode.appendChild(feedback);
        }
        
        feedback.textContent = field.validationMessage;
        feedback.style.display = 'block';
    }
}

/**
 * Show button loading state
 */
function showButtonLoading(button) {
    const originalText = button.innerHTML;
    const loadingText = button.dataset.loading || 'Loading...';
    
    button.disabled = true;
    button.innerHTML = `
        <div class="spinner-border spinner-border-sm me-2" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        ${loadingText}
    `;
    
    // Store original text for restoration
    button.dataset.originalText = originalText;
}

/**
 * Restore button from loading state
 */
function restoreButtonLoading(button) {
    if (button.dataset.originalText) {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText;
        delete button.dataset.originalText;
    }
}

/**
 * Initialize animations and visual effects
 */
function initializeAnimations() {
    // Fade in elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe elements with animation class
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    animatedElements.forEach(function(el) {
        observer.observe(el);
    });
    
    // Add hover effects to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(function(card) {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.transition = 'transform 0.3s ease, box-shadow 0.3s ease';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

/**
 * Initialize utility functions and features
 */
function initializeUtilities() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Add confirmation to dangerous actions
    const dangerousActions = document.querySelectorAll('[data-confirm]');
    dangerousActions.forEach(function(element) {
        element.addEventListener('click', function(event) {
            const message = this.dataset.confirm || 'Are you sure?';
            if (!confirm(message)) {
                event.preventDefault();
                return false;
            }
        });
    });
    
    // Initialize search functionality enhancements
    initializeSearchFeatures();
    
    // Initialize file upload enhancements
    initializeFileUploadFeatures();
    
    // Initialize table features
    initializeTableFeatures();
}

/**
 * Enhanced search functionality
 */
function initializeSearchFeatures() {
    const searchInput = document.getElementById('search_query');
    if (searchInput) {
        // Add search suggestions and history
        let searchHistory = getSearchHistory();
        
        // Create suggestions dropdown
        const suggestionsContainer = document.createElement('div');
        suggestionsContainer.className = 'position-absolute w-100 bg-dark border rounded mt-1 d-none';
        suggestionsContainer.style.zIndex = '1000';
        searchInput.parentNode.appendChild(suggestionsContainer);
        
        searchInput.addEventListener('focus', function() {
            showSearchSuggestions(suggestionsContainer, searchHistory);
        });
        
        searchInput.addEventListener('blur', function() {
            // Delay hiding to allow clicking on suggestions
            setTimeout(function() {
                suggestionsContainer.classList.add('d-none');
            }, 200);
        });
        
        // Save search query on form submit
        const searchForm = searchInput.closest('form');
        if (searchForm) {
            searchForm.addEventListener('submit', function() {
                const query = searchInput.value.trim();
                if (query) {
                    saveSearchHistory(query);
                }
            });
        }
    }
}

/**
 * Get search history from localStorage
 */
function getSearchHistory() {
    try {
        const history = localStorage.getItem('recruitmentSearchHistory');
        return history ? JSON.parse(history) : [];
    } catch (e) {
        console.warn('Could not load search history:', e);
        return [];
    }
}

/**
 * Save search query to history
 */
function saveSearchHistory(query) {
    try {
        let history = getSearchHistory();
        
        // Remove duplicate if exists
        history = history.filter(item => item !== query);
        
        // Add to beginning
        history.unshift(query);
        
        // Keep only last 10 searches
        history = history.slice(0, 10);
        
        localStorage.setItem('recruitmentSearchHistory', JSON.stringify(history));
    } catch (e) {
        console.warn('Could not save search history:', e);
    }
}

/**
 * Show search suggestions
 */
function showSearchSuggestions(container, history) {
    if (history.length === 0) {
        container.classList.add('d-none');
        return;
    }
    
    const suggestions = history.slice(0, 5).map(query => 
        `<div class="p-2 border-bottom cursor-pointer suggestion-item" data-query="${escapeHtml(query)}">
            <i class="fas fa-history me-2 text-muted"></i>
            ${escapeHtml(query)}
        </div>`
    ).join('');
    
    container.innerHTML = suggestions;
    container.classList.remove('d-none');
    
    // Add click handlers
    const suggestionItems = container.querySelectorAll('.suggestion-item');
    suggestionItems.forEach(function(item) {
        item.addEventListener('click', function() {
            const query = this.dataset.query;
            const searchInput = document.getElementById('search_query');
            if (searchInput) {
                searchInput.value = query;
                searchInput.focus();
            }
            container.classList.add('d-none');
        });
    });
}

/**
 * Enhanced file upload functionality
 */
function initializeFileUploadFeatures() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(function(input) {
        // Add file size validation
        input.addEventListener('change', function() {
            const files = this.files;
            const maxSize = 16 * 1024 * 1024; // 16MB
            
            for (let i = 0; i < files.length; i++) {
                if (files[i].size > maxSize) {
                    showNotification('File size must be less than 16MB', 'error');
                    this.value = '';
                    return;
                }
            }
        });
    });
    
    // Add progress indication for file uploads
    const uploadForms = document.querySelectorAll('form[enctype="multipart/form-data"]');
    uploadForms.forEach(function(form) {
        form.addEventListener('submit', function() {
            showUploadProgress();
        });
    });
}

/**
 * Show upload progress indication
 */
function showUploadProgress() {
    const progressHtml = `
        <div class="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center" 
             style="background: rgba(0,0,0,0.7); z-index: 9999;" id="uploadProgress">
            <div class="card">
                <div class="card-body text-center">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Uploading...</span>
                    </div>
                    <h5>Processing CV...</h5>
                    <p class="text-muted mb-0">Please wait while we extract and analyze the content.</p>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', progressHtml);
}

/**
 * Initialize table enhancements
 */
function initializeTableFeatures() {
    const tables = document.querySelectorAll('table');
    
    tables.forEach(function(table) {
        // Add row highlighting
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(function(row) {
            row.addEventListener('mouseenter', function() {
                this.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
            });
            
            row.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '';
            });
        });
        
        // Add sorting capability to sortable columns
        const sortableHeaders = table.querySelectorAll('th[data-sortable]');
        sortableHeaders.forEach(function(header) {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                sortTable(table, this);
            });
        });
    });
}

/**
 * Simple table sorting
 */
function sortTable(table, header) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const headerIndex = Array.from(header.parentNode.children).indexOf(header);
    const isAscending = !header.classList.contains('sort-asc');
    
    // Remove existing sort classes
    header.parentNode.querySelectorAll('th').forEach(function(th) {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Add new sort class
    header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
    
    // Sort rows
    rows.sort(function(a, b) {
        const aText = a.children[headerIndex].textContent.trim();
        const bText = b.children[headerIndex].textContent.trim();
        
        const comparison = aText.localeCompare(bText, undefined, { numeric: true });
        return isAscending ? comparison : -comparison;
    });
    
    // Reorder rows
    rows.forEach(function(row) {
        tbody.appendChild(row);
    });
}

/**
 * Show notification to user
 */
function showNotification(message, type = 'info', duration = 5000) {
    const alertClass = type === 'error' ? 'danger' : type;
    const icon = getNotificationIcon(type);
    
    const notificationHtml = `
        <div class="alert alert-${alertClass} alert-dismissible fade show position-fixed" 
             style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;" 
             id="notification-${Date.now()}">
            <i class="${icon} me-2"></i>
            ${escapeHtml(message)}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', notificationHtml);
    
    // Auto-dismiss after duration
    const notification = document.body.lastElementChild;
    setTimeout(function() {
        if (notification && notification.parentNode) {
            const bsAlert = new bootstrap.Alert(notification);
            bsAlert.close();
        }
    }, duration);
}

/**
 * Get icon for notification type
 */
function getNotificationIcon(type) {
    const icons = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-triangle',
        'warning': 'fas fa-exclamation-circle',
        'info': 'fas fa-info-circle'
    };
    return icons[type] || icons.info;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function() {
            showNotification('Copied to clipboard', 'success', 2000);
        }).catch(function() {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

/**
 * Fallback copy to clipboard for older browsers
 */
function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showNotification('Copied to clipboard', 'success', 2000);
    } catch (err) {
        showNotification('Could not copy to clipboard', 'error', 3000);
    }
    
    document.body.removeChild(textArea);
}

/**
 * Debounce function to limit rapid function calls
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

/**
 * Throttle function to limit function calls frequency
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Check if user prefers reduced motion
 */
function prefersReducedMotion() {
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Smooth scroll to element
 */
function scrollToElement(element, offset = 0) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    
    if (element) {
        const elementPosition = element.offsetTop - offset;
        
        if (prefersReducedMotion()) {
            window.scrollTo(0, elementPosition);
        } else {
            window.scrollTo({
                top: elementPosition,
                behavior: 'smooth'
            });
        }
    }
}

/**
 * Global utility functions available to all pages
 */
window.RecruitmentApp = {
    showNotification: showNotification,
    copyToClipboard: copyToClipboard,
    formatFileSize: formatFileSize,
    scrollToElement: scrollToElement,
    debounce: debounce,
    throttle: throttle,
    showButtonLoading: showButtonLoading,
    restoreButtonLoading: restoreButtonLoading
};

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Page is hidden, pause non-critical operations
        console.log('Page hidden - pausing operations');
    } else {
        // Page is visible, resume operations
        console.log('Page visible - resuming operations');
    }
});

// Handle online/offline status
window.addEventListener('online', function() {
    showNotification('Connection restored', 'success', 3000);
});

window.addEventListener('offline', function() {
    showNotification('Connection lost - some features may not work', 'warning', 5000);
});

// Performance monitoring
window.addEventListener('load', function() {
    // Log performance metrics
    if (window.performance && window.performance.timing) {
        const loadTime = window.performance.timing.loadEventEnd - window.performance.timing.navigationStart;
        console.log(`Page load time: ${loadTime}ms`);
        
        // Log slow loads
        if (loadTime > 3000) {
            console.warn('Slow page load detected');
        }
    }
});

// Error handling
window.addEventListener('error', function(event) {
    console.error('JavaScript error:', event.error);
    
    // Don't show error notifications for minor issues
    if (event.error && event.error.message && !event.error.message.includes('Script error')) {
        showNotification('An error occurred. Please refresh the page if problems persist.', 'error', 8000);
    }
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    event.preventDefault(); // Prevent default browser error handling
});
