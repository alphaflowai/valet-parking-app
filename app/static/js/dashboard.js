document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.dashboard-container')) {
        initializeDashboard();
    }
});

function setupSocketConnection() {
    const socket = io('/valet');
    
    socket.on('connect', () => {
        console.log('Connected to valet namespace');
        socket.emit('join', { room: `valet_${currentUserId}` });
    });

    socket.on('status_update', (data) => {
        updateTicketStatus(data.session_id, data.status);
    });

    socket.on('session_update', (data) => {
        console.log('Received session update:', data);
        updateTicketCard(data.session_id, data.status);
    });

    return socket;
}

function updateTicketCard(sessionId, status) {
    const ticketCard = document.querySelector(`.ticket-card[data-session-id="${sessionId}"]`);
    if (ticketCard) {
        if (status === 'completed') {
            ticketCard.classList.add('fade-out');
            setTimeout(() => {
                ticketCard.remove();
            }, 1000);
        } else {
            const statusElement = ticketCard.querySelector('.ticket-status');
            const actionButton = ticketCard.querySelector('.action-btn');
            
            if (statusElement) {
                statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
                statusElement.className = `ticket-status ${status}`;
            }
            
            if (actionButton) {
                actionButton.textContent = getButtonText(status);
                actionButton.className = `btn action-btn ${getButtonClass(status)}`;
                actionButton.dataset.action = getButtonAction(status);
            }
        }
    }
}

function handleActionButton(event) {
    event.preventDefault();
    const button = event.currentTarget;
    const action = button.dataset.action;
    const sessionId = button.dataset.sessionId;

    if (!action || !sessionId) {
        console.error('Missing required data attributes:', { action, sessionId });
        return;
    }

    console.log('Action button clicked:', { action, sessionId }); // Debug log

    let endpoint;
    let payload = {};
    
    switch(action) {
        case 'assign-space':
            handleAssignSpace(sessionId);
            return;
        case 'retrieving':
            endpoint = `/valet/retrieve_car/${sessionId}`;
            break;
        case 'alert':
            endpoint = `/valet/alert_customer/${sessionId}`;
            break;
        case 'returning':
            endpoint = `/valet/pick_up_car/${sessionId}`;
            break;
        case 'ready':
            endpoint = `/valet/car_ready/${sessionId}`;
            break;
        case 'complete':
            endpoint = `/complete_session/${sessionId}`;
            break;
        default:
            endpoint = `/valet/update_status/${sessionId}`;
            payload.status = action;
    }

    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateTicketCard(sessionId, data.new_status || action);
            showNotification(data.message || 'Status updated successfully', 'success');
        } else {
            console.error('Action failed:', data.message);
            showNotification(data.message || 'Failed to update status', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Failed to update status', 'error');
    });
}

function toggleTicketDetails(button) {
    const card = button.closest('.ticket-card');
    if (!card) return;
    
    const details = card.querySelector('.ticket-details');
    if (!details) return;
    
    const icon = button.querySelector('.fas');
    const isHidden = details.classList.contains('hidden');
    
    details.classList.toggle('hidden');
    
    if (icon) {
        icon.classList.toggle('fa-chevron-down');
        icon.classList.toggle('fa-chevron-up');
    }
    
    if (!details.classList.contains('hidden')) {
        details.style.maxHeight = `${details.scrollHeight}px`;
        card.classList.add('expanded');
    } else {
        details.style.maxHeight = '0';
        card.classList.remove('expanded');
    }
}

function handleAlertCustomer(event) {
    event.preventDefault();
    const button = event.currentTarget;
    const sessionId = button.dataset.sessionId;

    if (!sessionId) {
        console.error('Session ID not found');
        return;
    }

    fetch(`/valet/alert_customer/${sessionId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('Customer has been notified', 'success');
        } else {
            showNotification(data.message || 'Failed to notify customer', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Failed to notify customer', 'error');
    });
}

function initializeTicketCards() {
    // Handle action buttons
    document.querySelectorAll('.action-btn').forEach(btn => {
        // Remove any existing event listeners
        btn.removeEventListener('click', handleActionButton);
        
        // Skip buttons that have their own onclick handlers
        if (btn.hasAttribute('onclick')) {
            return;
        }
        
        // Add click event listener
        btn.addEventListener('click', handleActionButton);
    });

    // Initialize ticket details
    document.querySelectorAll('.ticket-details').forEach(details => {
        details.classList.add('hidden');
    });
}

function initializeDashboard() {
    const socket = setupSocketConnection();
    initializeTicketCards();
}

async function assignSpace(sessionId) {
    const card = document.querySelector(`.ticket-card[data-session-id="${sessionId}"]`);
    const spaceSelect = card.querySelector('.parking-space-select');
    const space = spaceSelect.value;
    
    if (!space) {
        showNotification('Please select a parking space', 'warning');
        return;
    }

    try {
        const response = await fetch(`/valet/assign_space/${sessionId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ parking_space: space })
        });
        
        const data = await response.json();
        if (data.success) {
            updateTicketCard(sessionId, 'parked');
            showNotification('Space assigned successfully', 'success');
        } else {
            showNotification(data.message || 'Failed to assign space', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Failed to assign space', 'error');
    }
}

function handleAssignSpace(sessionId) {
    const card = document.querySelector(`.ticket-card[data-session-id="${sessionId}"]`);
    if (!card) {
        console.error('Card not found for session:', sessionId);
        return;
    }

    const spaceSelect = card.querySelector('.parking-space-select');
    if (!spaceSelect) {
        console.error('Space select not found for session:', sessionId);
        return;
    }

    const space = spaceSelect.value;
    if (!space) {
        showNotification('Please select a parking space', 'warning');
        return;
    }

    console.log('Assigning space:', { sessionId, space }); // Debug log

    fetch(`/valet/assign_space/${sessionId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ parking_space: space })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateTicketCard(sessionId, 'parked');
            showNotification('Space assigned successfully', 'success');
            // Refresh the page to update available spaces
            window.location.reload();
        } else {
            showNotification(data.message || 'Failed to assign space', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Failed to assign space', 'error');
    });
}

function getButtonText(status) {
    const textMap = {
        'parking': 'Assign Parking Space',
        'parked': 'Retrieve Car',
        'retrieving': 'Pick up Car',
        'returning': 'Tell Customer Car is Ready',
        'ready': 'Complete Session'
    };
    return textMap[status] || '';
}

function getButtonClass(status) {
    const classMap = {
        'parking': 'bg-blue-600',
        'parked': 'bg-purple-600',
        'retrieving': 'bg-yellow-600',
        'returning': 'bg-green-600',
        'ready': 'bg-indigo-600'
    };
    return classMap[status] || 'bg-gray-600';
}

function getButtonAction(status) {
    const actionMap = {
        'parking': 'assign-space',
        'parked': 'retrieving',
        'retrieving': 'returning',
        'returning': 'ready',
        'ready': 'complete'
    };
    return actionMap[status] || '';
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    setTimeout(() => {
        notification.classList.add('notification-hide');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function getNotificationIcon(type) {
    const icons = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    return icons[type] || icons.info;
}

function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

function completeSession(sessionId) {
    fetch(`/complete_session/${sessionId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateTicketCard(sessionId, 'completed');
            showNotification('Session completed successfully', 'success');
        } else {
            showNotification(data.message || 'Failed to complete session', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Failed to complete session', 'error');
    });
}

function markCarReady(sessionId) {
    fetch(`/valet/car_ready/${sessionId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateTicketCard(sessionId, 'ready');
            showNotification('Customer has been notified', 'success');
        } else {
            showNotification(data.message || 'Failed to mark car as ready', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Failed to mark car as ready', 'error');
    });
}