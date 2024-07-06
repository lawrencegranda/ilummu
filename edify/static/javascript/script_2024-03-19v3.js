$('#bid-bar').ready(function () {
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
    elem.css('width', width + '%')

    if ((width - changed) > 15) {
      if (option) {
        $('#question-wait-header').text('Looking For Tutors...');
        option = false;
      } else {
        $('#question-wait-header').text('Waiting For Replies...')
        option = true;
      }
      changed = width
    }
  }
})

$(document).ready(function () {
  $(window).keydown(function (event) {
    if (event.keyCode == 13) {
      event.preventDefault();
      return false;
    }
  });

  $("#notification").on("click", function () {
    if ($('#notification-wrapper:visible').length)
      $('#notification-wrapper').hide();
    else
      $('#notification-wrapper').show();
  });;

  $(".category").not(".all-subjects").on("click", function () {
    $(".all-subjects").removeClass("selected");
    $(this).toggleClass("selected");
  });

  $(".all-subjects").on("click", function () {
    $(".category").removeClass("selected");
    $(this).toggleClass("selected");
  });

  // $(".btn-reply").on("click", function () {
  //   let element = $(this).closest('.comment-container').children('.comment-area').first();

  //   if (element.is(':visible'))
  //     element.hide();
  //   else {
  //     element.show();
  //   }
  // });

  // $(".btn-submit-comment, .btn-cancel-comment").on("click", function () {
  //   let element = $(this).closest('.comment-container').children('.comment-area').first();

  //   if (element.is(':visible'))
  //     setTimeout(function () {
  //       element.hide();
  //     }, 200);
  //   else {
  //     element.show();
  //   }
  // });

  $("#add-button, #button-nav-question").on("click", function () {
    let element = $(".create-question-wrapper-dimensions");

    if (element.is(':visible'))
      element.hide();
    else
      element.show();
  });

  $(".create-question-wrapper-background").on("click", function () {
    console.log('kkk')
    let element = $(".create-question-wrapper-dimensions");

    element.hide();
  });

  $("#create-question-form").on("submit", function (event) {
    var correct = true

    var school = $("#create-question-category").val();
    if (!school) {
      event.preventDefault();
      correct = false
    }

    var method = $("#create-question-method").val();
    if (!method) {
      event.preventDefault();
      correct = false
    }

    if (correct) {
      let element = $(".create-question-wrapper-dimensions");

      if (element.is(':visible'))
        setTimeout(function () {
          element.hide();
        }, 300);
      else
        element.show();
    }
  });

  // $('#offer-taken-class').on("click", function () {
  //   console.log(this.checked)
  //   if (this.checked) {
  //     $('.btn-offer').removeClass('disabled');
  //   } else {
  //     $('.btn-offer').removeClass('disabled').addClass('disabled');
  //   }
  // });

  $('#create-question-price').on("change", function () {
    let value = parseFloat($(this).val()).toFixed(2);
    if (isNaN(value)) {
      console.log()
      value = "";
      $(this).attr("placeholder", "Invalid. Try again.");
    }
    $(this).val(value);
  });

  $('#btn-bid-raise').on("click", function () {
    console.log(($('#bid-value').val()))
    // $('#bid-value').val('$' + (parseFloat($('#bid-value').val()) + 2).toFixed(2));
  });

  $('#offer-fare').on("input", function () {
    console.log($('#button-make-offer').val())
    $('#button-make-offer').text('Offer $' + parseFloat($(this).val()).toFixed(2));
  });

  $('#create-question-file').on("change", function () {
    let file = $(this).prop('files')[0]['name'];

    if (file.length > 33) {
      file = file.substring(0, 15) + "..." + file.substring(file.length - 15, file.length)
    }

    $('#file-selected').text(file)

  });

  $('#button-log-out').on("click", function () {
    $.ajax({
      url: '/user/logout',
      type: 'POST',
      contentType: 'application/json',
      data: null,
      success: function (response) {
        // Handle success (e.g., redirect to main page)
        console.log(response)
        window.location.href = "/";
      },
      error: function (error) {
        // Handle error (e.g., display error message)
        console.log(error);
        window.location.href = "/";
      }
    });
  });


});