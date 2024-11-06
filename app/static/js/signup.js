let stripe;
let elements;
let currentStep = 1;
let selectedPlan = null;
let accountData = null;



document.addEventListener('DOMContentLoaded', function() {
    // Get Stripe key from data attribute
    const stripeKey = document.querySelector('.signup-container').dataset.stripeKey;
    // Initialize Stripe
    stripe = Stripe(stripeKey);
    elements = stripe.elements();
    
    const accountForm = document.getElementById('account-form');
    const paymentForm = document.getElementById('payment-form');
    const planButtons = document.querySelectorAll('.btn-select-plan');

    // Setup card element
    const card = elements.create('card');
    card.mount('#card-element');

    accountForm.addEventListener('submit', handleAccountSubmit);
    paymentForm.addEventListener('submit', handlePaymentSubmit);
    planButtons.forEach(button => {
        button.addEventListener('click', () => selectPlan(button.dataset.plan));
    });
});

async function handleAccountSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    accountData = Object.fromEntries(formData);
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    try {
        const response = await fetch('/api/auth/validate-account', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(accountData)
        });

        const data = await response.json();
        
        if (response.ok) {
            showStep(2);
        } else {
            showNotification(data.error || 'Error creating account', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error creating account', 'error');
    }
}

function selectPlan(plan) {
    selectedPlan = plan;
    showStep(3);
}

async function handlePaymentSubmit(e) {
    e.preventDefault();
    const button = e.target.querySelector('button');
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    
    try {
        const { paymentMethod } = await stripe.createPaymentMethod({
            type: 'card',
            card: elements.getElement('card')
        });

        const response = await fetch('/api/auth/complete-signup', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            body: JSON.stringify({
                account: accountData,
                plan: selectedPlan,
                paymentMethodId: paymentMethod.id
            })
        });

        const data = await response.json();
        
        if (data.success) {
            showNotification('Signup successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = data.redirect_url;
            }, 1500);
        } else {
            throw new Error(data.error || 'Signup failed');
        }
    } catch (error) {
        showNotification(error.message || 'Payment failed', 'error');
        button.disabled = false;
        button.textContent = 'Complete Signup';
    }
}

function showStep(step) {
    console.log('Attempting to show step:', step);
    
    // Hide all steps first
    document.querySelectorAll('.step').forEach(el => {
        console.log('Hiding step:', el.dataset.step);
        el.style.display = 'none';
    });
    
    // Show the target step
    const nextStep = document.querySelector(`.step[data-step="${step}"]`);
    if (nextStep) {
        console.log('Found and showing step:', step);
        nextStep.style.display = 'block';
    } else {
        console.error('Step element not found:', step);
    }
    
    // Update progress indicators
    document.querySelectorAll('.progress-step').forEach(el => {
        el.classList.remove('active');
        if (parseInt(el.dataset.step) <= step) {
            el.classList.add('active');
        }
    });
    
    currentStep = step;
}

function showNotification(message, type) {
    // You can implement this however you want to show notifications
    // For example:
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 15000);
} 