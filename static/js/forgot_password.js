document.getElementById('forgotPasswordForm').addEventListener('submit', async function(event) {
    event.preventDefault(); // Stop the default form submission

    const email = document.getElementById('email').value;
    const messageElement = document.getElementById('message');
    
    try {
        const response = await fetch('/forgot_password/', {   // <-- changed here
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({ email: email })
        });

        if (response.ok) {
            messageElement.textContent = 'If the email is registered, a password reset link has been sent.';
            messageElement.style.color = 'green';
        } else {
            messageElement.textContent = 'Error processing request. Please try again.';
            messageElement.style.color = 'red';
        }

    } catch (error) {
        console.error('Network error:', error);
        messageElement.textContent = 'A network error occurred.';
        messageElement.style.color = 'red';
    }
});
