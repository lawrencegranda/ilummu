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

  $('#offer-taken-class').click(function () {
    console.log(this.checked)
    if (this.checked) {
      $('.btn-offer').removeClass('disabled');
    } else {
      $('.btn-offer').removeClass('disabled').addClass('disabled');
    }
  });

});