// Base client-side JS for the FOUNDER-0 vanilla MVP template.
// Generated feature behavior gets appended below the FOUNDER0:FEATURE_JS marker.

document.getElementById('waitlist-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const emailInput = document.getElementById('email-input');
  const statusEl = document.getElementById('signup-status');
  statusEl.textContent = 'Submitting...';

  try {
    const res = await fetch('/api/waitlist', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: emailInput.value }),
    });
    const data = await res.json();
    if (res.ok) {
      statusEl.textContent = `You're on the list! (${data.total_signups} signups so far)`;
      emailInput.value = '';
    } else {
      statusEl.textContent = data.error || 'Something went wrong.';
    }
  } catch (err) {
    statusEl.textContent = 'Network error — please try again.';
  }
});

// FOUNDER0:FEATURE_JS
// /FOUNDER0:FEATURE_JS
