// Script untuk melakukan proses validasi file upload
document.addEventListener('DOMContentLoaded', function() {
    console.log('Loading Aplikasi Analisis Bank Indonesia');
    
    // Validasi form upload
    const form = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    
    if (form && fileInput) {
        // Validasi saat form disubmit
        form.addEventListener('submit', function(e) {
            if (fileInput.files.length === 0) {
                e.preventDefault();
                showAlert('Silakan pilih file terlebih dahulu.', 'warning');
                return false;
            }
            
            const file = fileInput.files[0];
            const fileExt = file.name.split('.').pop().toLowerCase();
            
            if (fileExt !== 'csv' && fileExt !== 'txt') {
                e.preventDefault();
                showAlert('Format file tidak didukung. Harap unggah file CSV atau TXT.', 'danger');
                return false;
            }
            
            // Validasi ukuran file (max 5MB)
            if (file.size > 8 * 1024 * 1024) {
                e.preventDefault();
                showAlert('Ukuran file terlalu besar. Maksimal 5MB.', 'danger');
                return false;
            }
            
            // Tampilkan loading indicator
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Memproses...';
                submitBtn.disabled = true;
            }
        });
        
        // Validasi saat file dipilih
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                const file = this.files[0];
                const fileExt = file.name.split('.').pop().toLowerCase();
                
                if (fileExt !== 'csv' && fileExt !== 'txt') {
                    showAlert('Format file tidak didukung. Harap unggah file CSV atau TXT.', 'danger');
                    this.value = '';
                } else if (file.size > 8 * 1024 * 1024) {
                    showAlert('Ukuran file terlalu besar. Maksimal 8 MB.', 'danger');
                    this.value = '';
                } else {
                    showAlert(`File "${file.name}" siap diupload.`, 'success', 3000);
                }
            }
        });
    }
    
    // Fungsi untuk menampilkan alert
    function showAlert(message, type, timeout = 5000) {
        // Hapus alert sebelumnya
        const existingAlert = document.getElementById('fileAlert');
        if (existingAlert) {
            existingAlert.remove();
        }
        
        // Buat alert baru
        const alertDiv = document.createElement('div');
        alertDiv.id = 'fileAlert';
        alertDiv.className = `alert alert-${type} alert-dismissible fade show mt-3`;
        alertDiv.innerHTML = `
            <i class="bi ${type === 'success' ? 'bi-check-circle-fill' : 
                          type === 'warning' ? 'bi-exclamation-triangle-fill' : 
                          'bi-exclamation-octagon-fill'}"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Tempatkan alert setelah file input
        if (fileInput && fileInput.parentNode) {
            fileInput.parentNode.appendChild(alertDiv);
        }
        
        if (timeout > 0) {
            setTimeout(() => {
                if (alertDiv) {
                    const bsAlert = new bootstrap.Alert(alertDiv);
                    bsAlert.close();
                }
            }, timeout);
        }
    }
    
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });
});