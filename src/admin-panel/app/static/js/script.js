(function() {
    'use strict';

    $('#sidebar').toggleClass('active');
    $('#body').toggleClass('active');

    // Toggle sidebar on Menu button click
    $('#sidebarCollapse').on('click', function() {
        $('#sidebar').toggleClass('active');
        $('#body').toggleClass('active');
    });
})();

