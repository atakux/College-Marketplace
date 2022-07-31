$(document).ready(function () {

  /* Every time the window is scrolled ... */
  $(window).scroll(function () {

      /* Check the location of each desired element */
      $('.item').each(function (i) {

          var bottom_of_object = $(this).position().top + $(this).outerHeight();
          var bottom_of_window = $(window).scrollTop() + $(window).height()*1.1;

          /* If the object is completely visible in the window, fade it it */
          if (bottom_of_window > bottom_of_object) {
              $(this).addClass("reveal");
              // $(this).animate({ 'opacity': '1' }, 1500);

          }

      });

  });

});