// Script untuk menangani interaksi pengguna
document.addEventListener('DOMContentLoaded', function() {
    // Validasi form upload
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const fileInput = document.getElementById('fileInput');
            if (fileInput.files.length === 0) {
                e.preventDefault();
                alert('Silakan pilih file terlebih dahulu.');
            }
        });
    }
    
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});