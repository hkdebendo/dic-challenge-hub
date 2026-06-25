(function () {
  function pad(value) {
    return String(value).padStart(2, "0");
  }

  function formatRemaining(milliseconds) {
    var totalSeconds = Math.max(0, Math.floor(milliseconds / 1000));
    var hours = Math.floor(totalSeconds / 3600);
    var minutes = Math.floor((totalSeconds % 3600) / 60);
    var seconds = totalSeconds % 60;
    return pad(hours) + ":" + pad(minutes) + ":" + pad(seconds);
  }

  function updateCountdown(panel) {
    var end = new Date(panel.dataset.countdownEnd);
    var value = panel.querySelector("[data-countdown-value]");
    if (!value || Number.isNaN(end.getTime())) {
      return;
    }

    var remaining = end.getTime() - Date.now();
    value.textContent = formatRemaining(remaining);

    if (remaining <= 0) {
      panel.classList.add("ended");
      var caption = panel.querySelector(".countdown-caption");
      if (caption) {
        caption.textContent = "Evenement termine";
      }
    }
  }

  function bootCountdowns() {
    document.querySelectorAll("[data-countdown]").forEach(function (panel) {
      updateCountdown(panel);
      setInterval(function () {
        updateCountdown(panel);
      }, 1000);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootCountdowns);
  } else {
    bootCountdowns();
  }
})();
