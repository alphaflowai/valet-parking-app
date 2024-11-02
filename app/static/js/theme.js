let processingAction = false;

function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

document.addEventListener('DOMContentLoaded', function() {
    // Theme-related functionality
    const body = document.body;
    const themeToggle = document.getElementById('themeToggle');

    // Skip theme initialization on login page
    if (!body.classList.contains('login-portal') && themeToggle) {
        // Load saved theme
        const savedTheme = localStorage.getItem('theme') || 'light';
        body.classList.toggle('dark-theme', savedTheme === 'dark');
        updateThemeIcon(savedTheme === 'dark');

        // Theme toggle click handler
        themeToggle.addEventListener('click', function() {
            const isDark = body.classList.toggle('dark-theme');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
            updateThemeIcon(isDark);
            updateStatusSection(isDark);
        });
    }

    function updateThemeIcon(isDark) {
        if (themeToggle) {
            const icon = themeToggle.querySelector('i');
            if (icon) {
                icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
            }
        }
    }

    function updateStatusSection(isDark) {
        const statusSections = document.querySelectorAll('.status-container, #statusSection, #statusSectionDetails');
        statusSections.forEach(section => {
            if (isDark) {
                section.style.backgroundColor = 'var(--background-color)';
                section.style.color = 'var(--text-color)';
            } else {
                section.style.backgroundColor = '';
                section.style.color = '';
            }
            section.style.border = 'none';
            section.style.boxShadow = 'none';
        });
    }

    // Language-related functionality
    const languageToggle = document.getElementById('languageToggle');
    if (languageToggle) {
        const currentLanguage = localStorage.getItem('language') || 'en';
        languageToggle.value = currentLanguage;

        languageToggle.addEventListener('change', function() {
            const selectedLanguage = this.value;
            localStorage.setItem('language', selectedLanguage);
            location.reload();
        });
    }

    // Valet dashboard functionality
    if (document.querySelector('.dashboard-container')) {
        const socket = io('/valet');
        let processingAction = false;

        // Handle assign space form submission
        document.querySelectorAll('.assign-space-form').forEach(form => {
            form.addEventListener('submit', async function(e) {
                e.preventDefault();
                if (processingAction) return;
                
                processingAction = true;
                const sessionId = this.dataset.sessionId;
                const spaceSelect = this.querySelector('.parking-space-select');
                const selectedSpace = spaceSelect.value;
                
                if (!selectedSpace) {
                    showNotification('Please select a parking space', 'warning');
                    processingAction = false;
                    return;
                }

                try {
                    const response = await fetch(`/valet/assign_space/${sessionId}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                        },
                        body: JSON.stringify({ parking_space: selectedSpace })
                    });

                    if (!response.ok) throw new Error('Failed to assign parking space');
                    
                    const data = await response.json();
                    if (data.success) {
                        updateTicketStatus(sessionId, 'parked', selectedSpace);
                        showNotification(`Space ${selectedSpace} assigned successfully`, 'success');
                    }
                } catch (error) {
                    console.error('Error assigning space:', error);
                    showNotification('Error assigning parking space', 'error');
                } finally {
                    processingAction = false;
                }
            });
        });

        // Handle all ticket action buttons
        document.addEventListener('click', async function(e) {
            const actionButton = e.target.closest('.action-btn');
            if (!actionButton || processingAction) return;

            processingAction = true;
            const sessionId = actionButton.closest('.ticket-card').dataset.sessionId;
            const action = actionButton.dataset.action;

            try {
                switch (action) {
                    case 'retrieve-car':
                        await handleRetrieveCar(sessionId);
                        break;
                    case 'pick-up-car':
                        await handlePickUpCar(sessionId);
                        break;
                    case 'car-ready':
                        await handleCarReady(sessionId);
                        break;
                    case 'complete-session':
                        await handleCompleteSession(sessionId);
                        break;
                }
            } catch (error) {
                console.error('Action failed:', error);
                showNotification('Error: ' + error.message, 'error');
            } finally {
                processingAction = false;
            }
        });

        // Handle Alert Customer button clicks
        document.querySelectorAll('.alert-customer-btn').forEach(button => {
            button.addEventListener('click', async function() {
                if (processingAction) return;
                
                processingAction = true;
                const sessionId = this.dataset.sessionId;

                try {
                    const response = await fetch(`/valet/alert_customer/${sessionId}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                        }
                    });

                    if (!response.ok) throw new Error('Failed to alert customer');
                    
                    const data = await response.json();
                    showNotification(data.message, 'success');
                } catch (error) {
                    console.error('Error alerting customer:', error);
                    showNotification('Error alerting customer', 'error');
                } finally {
                    processingAction = false;
                }
            });
        });

        // Action Handlers
        async function handleRetrieveCar(sessionId) {
            const response = await fetch(`/valet/retrieve_car/${sessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                }
            });

            if (!response.ok) throw new Error('Failed to initiate car retrieval');
            
            updateTicketStatus(sessionId, 'retrieving');
        }

        async function handlePickUpCar(sessionId) {
            const response = await fetch(`/valet/pick_up_car/${sessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                }
            });

            if (!response.ok) throw new Error('Failed to pick up car');
            
            updateTicketStatus(sessionId, 'returning');
        }

        async function handleCarReady(sessionId) {
            const response = await fetch(`/valet/car_ready/${sessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                }
            });

            if (!response.ok) throw new Error('Failed to mark car as ready');
            
            updateTicketStatus(sessionId, 'ready');
        }

        async function handleCompleteSession(sessionId) {
            try {
                const response = await fetch(`/complete_session/${sessionId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({}) // Send an empty object if no data is needed
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                if (data.status === 'success') {
                    console.log('Session completed successfully:', data);
                    showNotification('Session completed successfully', 'success');
                    // Update UI as needed
                } else {
                    throw new Error(data.message || 'Failed to complete session');
                }
            } catch (error) {
                console.error('Error completing session:', error);
                showNotification('Failed to complete session: ' + error.message, 'error');
            }
        }

        // UI Update Functions
        function updateTicketStatus(sessionId, status, parkingSpace = null) {
            const ticketCard = document.querySelector(`.ticket-card[data-session-id="${sessionId}"]`);
            if (!ticketCard) return;

            const statusElement = ticketCard.querySelector('.ticket-status');
            const actionsContainer = ticketCard.querySelector('.ticket-actions');

            if (statusElement) {
                statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
                statusElement.className = `ticket-status ${status}`;
            }

            if (parkingSpace !== null) {
                const parkingSpaceElement = ticketCard.querySelector('.parking-space');
                if (parkingSpaceElement) {
                    parkingSpaceElement.textContent = parkingSpace;
                }
            }

            if (actionsContainer) {
                const actionButtons = generateActionButtons(status, sessionId);
                actionsContainer.innerHTML = actionButtons;
                initializeButtonListeners(actionsContainer);
            }
        }

        function generateActionButtons(status, sessionId) {
            let buttons = '';
            
            switch (status) {
                case 'parked':
                    buttons += `<button class="btn btn-primary action-btn" data-action="retrieve-car"><i class="fas fa-car"></i> Retrieve Car</button>`;
                    break;
                case 'retrieving':
                    buttons += `<button class="btn btn-primary action-btn" data-action="pick-up-car"><i class="fas fa-walking"></i> Pick up Car</button>`;
                    break;
                case 'returning':
                    buttons += `<button class="btn btn-primary action-btn" data-action="car-ready"><i class="fas fa-check"></i> Car is Ready</button>`;
                    break;
                case 'ready':
                    buttons += `<button class="btn btn-primary action-btn" data-action="complete-session"><i class="fas fa-flag-checkered"></i> Complete Session</button>`;
                    break;
            }

            buttons += `
                <button class="btn btn-warning alert-customer-btn" data-session-id="${sessionId}">
                    <i class="fas fa-bell"></i> Alert Customer
                </button>
                <a href="/valet/ticket_details/${sessionId}" class="btn btn-info view-details-btn">
                    <i class="fas fa-info-circle"></i> View Details
                </a>`;

            return buttons;
        }

        function initializeButtonListeners(container) {
            // Reattach event listeners for new buttons
            container.querySelectorAll('.action-btn').forEach(button => {
                button.addEventListener('click', async function(e) {
                    if (processingAction) return;
                    
                    processingAction = true;
                    const sessionId = this.closest('.ticket-card').dataset.sessionId;
                    const action = this.dataset.action;

                    try {
                        switch (action) {
                            case 'retrieve-car':
                                await handleRetrieveCar(sessionId);
                                break;
                            case 'pick-up-car':
                                await handlePickUpCar(sessionId);
                                break;
                            case 'car-ready':
                                await handleCarReady(sessionId);
                                break;
                            case 'complete-session':
                                await handleCompleteSession(sessionId);
                                break;
                        }
                    } catch (error) {
                        console.error('Action failed:', error);
                        showNotification('Error: ' + error.message, 'error');
                    } finally {
                        processingAction = false;
                    }
                });
            });
            
            container.querySelectorAll('.alert-customer-btn').forEach(button => {
                button.addEventListener('click', handleAlertCustomer);
            });
        }

        function showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `alert alert-${type} notification`;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(() => notification.remove(), 5000);
        }

        // Socket Event Handlers
        socket.on('status_update', function(data) {
            updateTicketStatus(data.sessionId, data.status, data.parkingSpace);
        });

        socket.on('session_completed', function(data) {
            const ticketCard = document.querySelector(`.ticket-card[data-session-id="${data.sessionId}"]`);
            if (ticketCard) {
                ticketCard.remove();
            }
        });

        // Inside the existing socket.on('session_update') handler
        socket.on('session_update', function(data) {
            if (data.update_type === 'car_requested') {
                showNotification(`Car requested for ticket ${data.session_id}`, 'info');
                updateTicketStatus(data.session_id, 'retrieving');
                flashReceiveButton();
                playNotificationSound();
            }
            // ... handle other update types
        });

       

        socket.on('car_request', function(data) {
            playNotificationSound();
            showNotification(`Customer requested car for Ticket #${data.ticket_number} in Space ${data.parking_space}`, 'info');
            
            const ticketCard = document.querySelector(`.ticket-card[data-session-id="${data.session_id}"]`);
            if (ticketCard) {
                ticketCard.classList.add('highlight-card');
                const pickUpButton = ticketCard.querySelector('.pick-up-car-btn');
                if (pickUpButton) {
                    pickUpButton.classList.add('pulsing-red');
                }
            }
        });

        function updateTicketCard(sessionId, status) {
            const ticketCard = document.querySelector(`.ticket-card[data-session-id="${sessionId}"]`);
            if (ticketCard) {
                if (status === 'completed') {
                    ticketCard.classList.add('fade-out');
                    setTimeout(() => {
                        ticketCard.remove();
                    }, 1000); // Remove after fade animation
                } else {
                    const statusElement = ticketCard.querySelector('.ticket-status');
                    const actionButton = ticketCard.querySelector('.action-btn');
                    const alertCustomerButton = ticketCard.querySelector('.alert-customer-btn');
                    
                    if (statusElement) statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
                    
                    if (actionButton) {
                        actionButton.textContent = getButtonText(status);
                        actionButton.className = `btn action-btn ${getButtonClass(status)}`;
                        actionButton.dataset.action = getButtonAction(status);
                    }

                    if (alertCustomerButton) {
                        alertCustomerButton.removeEventListener('click', handleAlertCustomer);
                        alertCustomerButton.addEventListener('click', handleAlertCustomer);
                    }
                }
            }
        }

        function getButtonText(status) {
            const texts = {
                'parked': 'Retrieve Car',
                'retrieving': 'Pick up Car',
                'returning': 'Car is Ready',
                'ready': 'Complete Session'
            };
            return texts[status] || '';
        }

        function getButtonClass(status) {
            const classes = {
                'parked': 'btn-primary',
                'retrieving': 'btn-warning pulsing-red',
                'returning': 'btn-info',
                'ready': 'btn-success'
            };
            return classes[status] || 'btn-secondary';
        }

        function getButtonAction(status) {
            const actions = {
                'parked': 'retrieve-car',
                'retrieving': 'pick-up-car',
                'returning': 'car-ready',
                'ready': 'complete-session'
            };
            return actions[status] || '';
        }

        socket.on('session_update', function(data) {
            updateTicketCard(data.session_id, data.status);
        });

        socket.on('update_space_count', function(data) {
            const statValue = document.querySelector('.stat-card.primary .stat-value');
            if (statValue) {
                statValue.textContent = `${data.occupied_spaces}/${data.total_spaces}`;
            }
        });
    }

    // UI update functions
    function showNotification(message) {
        let notificationElement = document.getElementById('notifications');
        if (!notificationElement) {
            notificationElement = document.createElement('div');
            notificationElement.id = 'notifications';
            notificationElement.className = 'alert alert-info';
            document.body.insertBefore(notificationElement, document.body.firstChild);
        }
        notificationElement.textContent = message;
        notificationElement.style.display = 'block';
        setTimeout(function() {
            notificationElement.style.display = 'none';
        }, 5000);
    }

    function flashReceiveButton() {
        const receiveButton = document.querySelector('.flashing-button');
        if (receiveButton) {
            receiveButton.classList.add('flashing');
            receiveButton.style.backgroundColor = '#ff0000';
            receiveButton.style.fontWeight = 'bold';
            receiveButton.style.color = 'white';
        }
    }

    function playNotificationSound() {
        const audio = new Audio("/static/sounds/notification.mp3");
        audio.play().catch(error => {
            console.log("Playback prevented. Waiting for user interaction.");
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-info';
            alertDiv.innerHTML = `
                <p>Playback prevented. Click the button to play the sound.</p>
                <button>Play Notification Sound</button>
            `;
            alertDiv.querySelector('button').onclick = () => {
                audio.play();
                alertDiv.remove();
            };
            document.querySelector('.container-fluid').insertAdjacentElement('afterbegin', alertDiv);
        });
    }

    // Fade effects
    setTimeout(applyFadeEffects, 5000);

    function applyFadeEffects() {
        const fadeSlowElements = document.getElementsByClassName('fade-out-slow');
        const fadePulseElements = document.getElementsByClassName('fade-out-pulse');
        
        Array.from(fadeSlowElements).forEach(function(element) {
            fadeElement(element, 'opacity 6s', '0', 'opacity 25s', '1');
        });
        
        Array.from(fadePulseElements).forEach(fadePulse);
    }

    function fadeElement(element, initialTransition, initialOpacity, finalTransition, finalOpacity) {
        element.style.transition = initialTransition;
        element.style.opacity = initialOpacity;
        setTimeout(function() {
            element.style.transition = finalTransition;
            element.style.opacity = finalOpacity;
        }, 4000);
    }

    function fadePulse(element) {
        function fadeIn() {
            element.style.transition = 'opacity 4s';
            element.style.opacity = '1';
            setTimeout(fadeOut, 4000);
        }
        
        function fadeOut() {
            element.style.transition = 'opacity 4s';
            element.style.opacity = '0.3';
            setTimeout(fadeIn, 4000);
        }
        
        fadeIn();
    }

    // Update ticket status

    function updateTicketStatus(sessionId, status) {
        const ticketCard = document.querySelector(`.ticket-card[data-session-id="${sessionId}"]`);
        if (ticketCard) {
            const statusSpan = ticketCard.querySelector('.ticket-status');
            statusSpan.textContent = status.charAt(0).toUpperCase() + status.slice(1);
            statusSpan.className = `ticket-status ${status}`;
            
            const actionButton = ticketCard.querySelector('.action-btn:not(.btn-warning)');
            if (actionButton) {
                actionButton.dataset.action = getNextAction(status);
                actionButton.innerHTML = `<i class="${getButtonIcon(status)}"></i> ${getButtonText(status)}`;
            }

            // Update time parked
            const timeParkedSpan = ticketCard.querySelector('.time-parked');
            if (timeParkedSpan) {
                fetch(`/get_time_parked/${sessionId}`)
                    .then(response => response.json())
                    .then(data => {
                        timeParkedSpan.textContent = data.time_parked;
                    });
            }
        }
    }

    // Update ticket status helper functions update UI
    function getNextAction(status) {
        const actionMap = {
            'parking': 'assign-space',
            'parked': 'pick_up_car',
            'retrieving': 'pick_up_car',
            'returning': 'car_ready',
            'ready': 'complete_session'
        };
        return actionMap[status] || '';
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

    function getButtonIcon(status) {
        const iconMap = {
            'parking': 'fas fa-parking',
            'parked': 'fas fa-car',
            'retrieving': 'fas fa-walking',
            'returning': 'fas fa-check',
            'ready': 'fas fa-flag-checkered'
        };
        return iconMap[status] || 'fas fa-question';
    }

    function handleAlertCustomer(event) {
        event.preventDefault();
        const sessionId = event.target.closest('.ticket-card').dataset.sessionId;
        alertCustomer(sessionId);
    }

    async function alertCustomer(sessionId) {
        if (processingAction) return;
        processingAction = true;

        try {
            const response = await fetch(`/valet/alert_customer/${sessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                }
            });

            const data = await response.json();
            if (response.ok) {
                showNotification('Customer alerted successfully', 'success');
            } else {
                throw new Error(data.message || 'Failed to alert customer');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Failed to alert customer: ' + error.message, 'error');
        } finally {
            processingAction = false;
        }
    }

    function updateTimeParkeds() {
        document.querySelectorAll('.time-parked').forEach(element => {
            const sessionId = element.dataset.sessionId;
            if (!sessionId) return;

            fetch(`/get_time_parked/${sessionId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.time_parked) {
                        element.textContent = data.time_parked;
                    }
                })
                .catch(error => {
                    console.error('Error updating time parked:', error);
                });
        });
    }

    // Update time every minute
    setInterval(updateTimeParkeds, 60000);

    // Initial update when page loads
    document.addEventListener('DOMContentLoaded', updateTimeParkeds);

    // Add this function after your other initialization code
    function adjustTicketNumberSize() {
        const ticketNumbers = document.querySelectorAll('.ticket-number');
        ticketNumbers.forEach(number => {
            if (number.textContent.trim().length > 6) {
                number.classList.add('long-number');
            } else {
                number.classList.remove('long-number');
            }
        });
    }

    // Call it initially
    adjustTicketNumberSize();

    // Call it after any ticket updates
    const observer = new MutationObserver(adjustTicketNumberSize);
    const dashboardContainer = document.querySelector('.dashboard-grid');
    if (dashboardContainer) {
        observer.observe(dashboardContainer, {
            childList: true,
            subtree: true,
            characterData: true
        });
    }

    // Near the top of the file, add these functions
    function updateTimeParked(sessionId) {
        const timeParkedElement = document.querySelector(`.time-parked[data-session-id="${sessionId}"]`);
        if (!timeParkedElement) return;

        fetch(`/get_time_parked/${sessionId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.time_parked) {
                    timeParkedElement.textContent = data.time_parked;
                }
            })
            .catch(error => console.error('Error updating time parked:', error));
    }

    // Update the socket event handlers
    function setupSocketHandlers(socket) {
        socket.on('session_update', function(data) {
            console.log('Received session update:', data);
            
            switch(data.update_type) {
                case 'car_requested':
                    showNotification(`Car requested for ticket ${data.session_id}`, 'info');
                    updateTicketStatus(data.session_id, 'retrieving');
                    updateTimeParked(data.session_id);
                    flashReceiveButton();
                    playNotificationSound();
                    break;
                    
                case 'status_change':
                    updateTicketStatus(data.session_id, data.status);
                    updateTimeParked(data.session_id);
                    break;
                    
                case 'space_assigned':
                    updateTicketStatus(data.session_id, data.status, data.parking_space);
                    updateTimeParked(data.session_id);
                    break;
                    
                case 'completed':
                    const ticketCard = document.querySelector(`.ticket-card[data-session-id="${data.session_id}"]`);
                    if (ticketCard) {
                        ticketCard.remove();
                    }
                    break;
            }
        });

        socket.on('car_request', function(data) {
            playNotificationSound();
            showNotification(`Customer requested car for Ticket #${data.ticket_number} in Space ${data.parking_space}`, 'info');
            
            const ticketCard = document.querySelector(`.ticket-card[data-session-id="${data.session_id}"]`);
            if (ticketCard) {
                ticketCard.classList.add('highlight-card');
                const retrieveButton = ticketCard.querySelector('.retrieve-car');
                if (retrieveButton) {
                    retrieveButton.classList.add('pulsing-red');
                }
            }
            updateTimeParked(data.session_id);
        });
    }

    // Update the socket connection setup
    function setupSocketConnection() {
        const socket = io('/valet');
        
        socket.on('connect', () => {
            console.log('Connected to valet namespace');
            socket.emit('join', { room: `valet_${currentUserId}` });
        });

        setupSocketHandlers(socket);
        return socket;
    }
});
