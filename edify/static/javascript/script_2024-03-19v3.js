$("#bid-bar").ready(function () {
  let elem = $("#bid-bar");
  let changed = -1;
  let option = false;
  let width = 1;
  let id = setInterval(frame, 100);

  function frame() {
    if (width >= 100) {
      clearInterval(id);
    } else if (width <= 20) {
      width += 0.1;
    } else if (width <= 50) {
      width += 0.03;
    } else if (width <= 80) {
      width += 0.015;
    } else if (width <= 90) {
      width += 0.005;
    } else if (width <= 100) {
      width += 0.002;
    }
    elem.css("width", width + "%");

    if (width - changed > 15) {
      if (option) {
        $("#question-wait-header").text("Looking For Tutors...");
        option = false;
      } else {
        $("#question-wait-header").text("Waiting For Replies...");
        option = true;
      }
      changed = width;
    }
  }
});

$(document).ready(function () {
  $(window).keydown(function (event) {
    if (event.keyCode == 13) {
      event.preventDefault();
      return false;
    }
  });

  $("#notification").on("click", function () {
    if ($("#notification-wrapper:visible").length)
      $("#notification-wrapper").hide();
    else $("#notification-wrapper").show();
  });

  $("#add-button, #button-nav-question").on("click", function () {
    let element = $(".create-question-wrapper-dimensions");

    if (element.is(":visible")) element.hide();
    else element.show();
  });

  $(".create-question-wrapper-background").on("click", function () {
    let element = $(".create-question-wrapper-dimensions");

    element.hide();
  });

  $("#offer-fare").on("input", function () {
    $("#button-make-offer").text(
      "Counter $" + parseFloat($(this).val()).toFixed(2)
    );
  });
});

function getErrorResponse(error) {
  try {
    if ("msg" in error["responseJSON"]) {
      return error["responseJSON"]["msg"];
    }

    if ("errors" in error["responseJSON"]) {
      return error["responseJSON"]["errors"];
    }
  } catch (e) {}

  return undefined;
}
