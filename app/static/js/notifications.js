function showNotification(message, type) {
    const existing = document.querySelectorAll('.notification');
    existing.forEach(n => n.remove());
    
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.setAttribute('role', 'alert');
    notification.setAttribute('aria-live', 'assertive');
    
    const colors = {
        success: '#059669',
        error: '#dc2626', 
        warning: '#d97706',
        info: '#2563eb'
    };
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        background: ${colors[type]};
        color: white;
        padding: 12px 20px;
        border-radius: var(--border-radius);
        font-weight: 600;
        font-size: 0.9rem;
        box-shadow: var(--shadow-subtle);
        transform: translateX(350px);
        transition: var(--transition-fast);
        max-width: 300px;
    `;
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => { notification.style.transform = 'translateX(0)'; }, 10);
    setTimeout(() => {
        notification.style.transform = 'translateX(350px)';
        setTimeout(() => notification.remove(), 150);
    }, 3000);
}

// Add this line at the end
window.showNotification = showNotification;