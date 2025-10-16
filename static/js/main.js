document.addEventListener("DOMContentLoaded", () => {
    const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

    fetch("/set_timezone", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({timezone: userTimezone})
    });
});