(function () {
  function getCookie(name) {
    var cookies = document.cookie ? document.cookie.split(";") : [];
    for (var i = 0; i < cookies.length; i += 1) {
      var cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        return decodeURIComponent(cookie.substring(name.length + 1));
      }
    }
    return "";
  }

  function syncCsrfFields() {
    var token = getCookie("csrftoken");
    if (!token) {
      return;
    }
    document.querySelectorAll('input[name="csrfmiddlewaretoken"]').forEach(function (input) {
      input.value = token;
    });
  }

  document.addEventListener("submit", function () {
    syncCsrfFields();
  }, true);

  document.addEventListener("DOMContentLoaded", syncCsrfFields);

  document.body.addEventListener("htmx:configRequest", function (event) {
    var token = getCookie("csrftoken");
    if (token) {
      event.detail.headers["X-CSRFToken"] = token;
    }
  });
})();
