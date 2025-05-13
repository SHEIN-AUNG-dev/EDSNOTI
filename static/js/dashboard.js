/**
 * Dashboard scripts for EDS Alarm Monitor
 */

document.addEventListener('DOMContentLoaded', function() {
    // Update API status in nav bar
    function updateApiStatus() {
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                // Update EDS status
                const edsStatusBadge = document.getElementById('eds-status');
                if (edsStatusBadge) {
                    const statusSpan = edsStatusBadge.querySelector('span');
                    if (data.eds === 'Connected') {
                        edsStatusBadge.className = 'badge rounded-pill bg-success';
                        statusSpan.textContent = 'Connected';
                    } else if (data.eds === 'Failed') {
                        edsStatusBadge.className = 'badge rounded-pill bg-danger';
                        statusSpan.textContent = 'Failed';
                    } else {
                        edsStatusBadge.className = 'badge rounded-pill bg-secondary';
                        statusSpan.textContent = data.eds;
                    }
                }
                
                // Update Twilio status
                const twilioStatusBadge = document.getElementById('twilio-status');
                if (twilioStatusBadge) {
                    const statusSpan = twilioStatusBadge.querySelector('span');
                    if (data.twilio === 'Connected') {
                        twilioStatusBadge.className = 'badge rounded-pill bg-success';
                        statusSpan.textContent = 'Connected';
                    } else if (data.twilio === 'Failed') {
                        twilioStatusBadge.className = 'badge rounded-pill bg-danger';
                        statusSpan.textContent = 'Failed';
                    } else {
                        twilioStatusBadge.className = 'badge rounded-pill bg-secondary';
                        statusSpan.textContent = data.twilio;
                    }
                }
            })
            .catch(error => {
                console.error('Error updating API status:', error);
            });
    }
    
    // Set up periodic status updates
    updateApiStatus();
    setInterval(updateApiStatus, 60000); // Update every minute
    
    // Form validation for contact numbers
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('blur', function() {
            // Basic validation for international phone format
            const value = this.value.trim();
            if (value && !value.startsWith('+')) {
                this.value = `+${value}`;
            }
        });
    });
    
    // Password visibility toggle
    const togglePasswordButtons = document.querySelectorAll('.toggle-password');
    togglePasswordButtons.forEach(button => {
        button.addEventListener('click', function() {
            const passwordInput = document.querySelector(this.getAttribute('data-target'));
            if (passwordInput) {
                if (passwordInput.type === 'password') {
                    passwordInput.type = 'text';
                    this.innerHTML = '<i class="fas fa-eye-slash"></i>';
                } else {
                    passwordInput.type = 'password';
                    this.innerHTML = '<i class="fas fa-eye"></i>';
                }
            }
        });
    });
});
