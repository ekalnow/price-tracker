// Main JavaScript functionality for the application

document.addEventListener('DOMContentLoaded', function() {
    // Enable tooltips everywhere
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Enable toasts
    const toastElList = [].slice.call(document.querySelectorAll('.toast'));
    toastElList.map(function (toastEl) {
        return new bootstrap.Toast(toastEl);
    });

    // Confirmation dialog for delete actions
    const confirmDeleteForms = document.querySelectorAll('.confirm-delete-form');
    confirmDeleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
                return false;
            }
            return true;
        });
    });

    // URL validation
    const urlInputs = document.querySelectorAll('input[type="url"]');
    urlInputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateURL(this);
        });
    });

    // Arabic numeral conversion for any input fields that need it
    const numberInputs = document.querySelectorAll('.arabic-numeral-convert');
    numberInputs.forEach(input => {
        input.addEventListener('blur', function() {
            this.value = convertArabicToEnglishNumerals(this.value);
        });
    });

    // Dynamic form field visibility based on selection
    setupDynamicFormVisibility();
});

// URL validation helper
function validateURL(inputElement) {
    const url = inputElement.value.trim();
    
    // Basic URL validation
    if (!url) return;
    
    // Simple regex to check for Salla or Zid URLs
    const validDomains = /(salla\.sa|salla\.com|zid\.store|zid\.sa)/i;
    
    if (!validDomains.test(url)) {
        // Add error styling
        inputElement.classList.add('is-invalid');
        
        // Look for or create error message element
        let errorElement = inputElement.nextElementSibling;
        if (!errorElement || !errorElement.classList.contains('invalid-feedback')) {
            errorElement = document.createElement('div');
            errorElement.className = 'invalid-feedback';
            inputElement.parentNode.insertBefore(errorElement, inputElement.nextSibling);
        }
        
        errorElement.innerText = 'URL must be from Salla or Zid platforms.';
    } else {
        // Remove error styling
        inputElement.classList.remove('is-invalid');
        inputElement.classList.add('is-valid');
        
        // Remove error message if it exists
        const errorElement = inputElement.nextElementSibling;
        if (errorElement && errorElement.classList.contains('invalid-feedback')) {
            errorElement.remove();
        }
    }
}

// Convert Arabic numerals to English numerals
function convertArabicToEnglishNumerals(text) {
    if (!text) return text;
    
    const arabicNumerals = '٠١٢٣٤٥٦٧٨٩';
    const englishNumerals = '0123456789';
    
    let result = '';
    for (let i = 0; i < text.length; i++) {
        const index = arabicNumerals.indexOf(text[i]);
        if (index !== -1) {
            result += englishNumerals[index];
        } else {
            result += text[i];
        }
    }
    
    return result;
}

// Set up dynamic form field visibility based on selection
function setupDynamicFormVisibility() {
    // For price alert form: show/hide target price or percentage field
    const alertTypeSelect = document.getElementById('alert_type');
    
    if (alertTypeSelect) {
        const targetPriceField = document.getElementById('target_price')?.parentNode;
        const percentageField = document.getElementById('percentage_threshold')?.parentNode;
        
        if (targetPriceField && percentageField) {
            function updateAlertFields() {
                if (alertTypeSelect.value === 'percentage_change') {
                    targetPriceField.style.display = 'none';
                    percentageField.style.display = 'block';
                } else {
                    targetPriceField.style.display = 'block';
                    percentageField.style.display = 'none';
                }
            }
            
            alertTypeSelect.addEventListener('change', updateAlertFields);
            updateAlertFields(); // Initialize
        }
    }
    
    // For scheduler form: show/hide custom interval
    const intervalSelect = document.getElementById('interval');
    
    if (intervalSelect) {
        const customIntervalField = document.getElementById('custom_interval')?.parentNode;
        
        if (customIntervalField) {
            function updateIntervalFields() {
                if (intervalSelect.value === 'custom') {
                    customIntervalField.style.display = 'block';
                } else {
                    customIntervalField.style.display = 'none';
                }
            }
            
            intervalSelect.addEventListener('change', updateIntervalFields);
            updateIntervalFields(); // Initialize
        }
    }
}
