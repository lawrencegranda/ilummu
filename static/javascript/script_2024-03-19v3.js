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
    console.log("ok");
    let element = $(this).closest('.comment-container').children('.comment-area').first();

    if (element.is(':visible'))
      setTimeout(function () {
        element.hide();
      }, 200);
    else {
      element.show();
    }
  });



});