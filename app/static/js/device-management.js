async function manageInterface(deviceId, interfaceName, action, buttonElement) {
    try {
        // Enhanced loading state
        const originalText = buttonElement.textContent;
        const loadingText = action === 'enable' ? '🔄 Enabling...' : '🔄 Disabling...';
        
        buttonElement.textContent = loadingText;
        buttonElement.classList.add('btn-loading');
        buttonElement.disabled = true;

        const response = await fetch(`/api/devices/${deviceId}/interfaces/${interfaceName}/manage?action=${action}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Success state
            buttonElement.textContent = action === 'enable' ? '✅ Enabled!' : '✅ Disabled!';
            buttonElement.style.background = 'var(--gradient-success)';
            
            showNotification(`✅ Interface ${interfaceName} ${action}d successfully on device ${deviceId}!`, 'success');
            
            // Reload after short delay
            setTimeout(() => {
                location.reload();
            }, 1500);
        } else {
            // Error state
            buttonElement.textContent = '❌ Failed';
            buttonElement.style.background = 'var(--gradient-danger)';
            showNotification(`❌ Failed to ${action} interface: ${result.detail}`, 'error');
            
            // Reset after delay
            setTimeout(() => {
                buttonElement.textContent = originalText;
                buttonElement.style.background = '';
                buttonElement.disabled = false;
                buttonElement.classList.remove('btn-loading');
            }, 2000);
        }
    } catch (error) {
        buttonElement.textContent = '❌ Error';
        showNotification(`❌ Network error: ${error.message}`, 'error');
        setTimeout(() => location.reload(), 2000);
    }
}

window.manageInterface = manageInterface;