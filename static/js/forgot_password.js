document.getElementById('forgotPasswordForm').addEventListener('submit', async function(event) {
    event.preventDefault(); // Stop the default form submission

    const email = document.getElementById('email').value;
    const messageElement = document.getElementById('message');
    
    // 1. Send the email to your backend endpoint (e.g., /api/forgot-password)
    try {
        const response = await fetch('/api/forgot-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email: email })
        });

        // 2. Handle the response (since you don't have a DB, assume success)
        if (response.ok) {
            messageElement.textContent = 'If the email is registered, a password reset link has been sent.';
        } else {
            // Handle specific backend errors if you implement them later
            messageElement.textContent = 'Error processing request. Please try again.';
            messageElement.style.color = 'red';
        }

    } catch (error) {
        console.error('Network error:', error);
        messageElement.textContent = 'A network error occurred.';
        messageElement.style.color = 'red';
    }
});