$('#bid-bar').ready(function () {
  let elem = $("#bid-bar")
  let width = 1;
  let id = setInterval(frame, 1000);
  console.log('going')
  function frame() {
    console.log('going...')
    if (width >= 100) {
      clearInterval(id);
    } else if (width <= 20) {
      width += 1;
    } else if (width <= 50) {
      width += 0.3;
    } else if (width <= 80) {
      width += 0.15;
    } else if (width <= 90) {
      width += 0.05;
    } else if (width <= 100) {
      width += 0.02;
    }
    elem.css('width', width + '%')
  }
})

$(document).ready(function () {

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

  $(".btn-reply").on("click", function () {
    let element = $(this).closest('.comment-container').children('.comment-area').first();

    if (element.is(':visible'))
      element.hide();
    else {
      element.show();
    }
  });

  $(".btn-submit-comment, .btn-cancel-comment").on("click", function () {
    let element = $(this).closest('.comment-container').children('.comment-area').first();

    if (element.is(':visible'))
      setTimeout(function () {
        element.hide();
      }, 200);
    else {
      element.show();
    }
  });

  $("#add-button").on("click", function () {
    let element = $(".create-question-wrapper-dimensions");

    if (element.is(':visible'))
      element.hide();
    else
      element.show();
  });

  $("#create-question-button").on("click", function () {
    let element = $(".create-question-wrapper-dimensions");

    if (element.is(':visible'))
      setTimeout(function () {
        element.hide();
      }, 300);
    else
      element.show();
  });

  $('#offer-taken-class').on("click", function () {
    console.log(this.checked)
    if (this.checked) {
      $('.btn-offer').removeClass('disabled');
    } else {
      $('.btn-offer').removeClass('disabled').addClass('disabled');
    }
  });

  $('#create-question-price').on("change", function () {
    $(this).val(parseFloat($(this).val()).toFixed(2));
  });

});

