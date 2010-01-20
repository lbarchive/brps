google.load("jquery", "1");


// Global error indicator
function init_error_indicator() {
  $("#messages").ajaxError(function(event, request, settings){
    var err_msg;
    switch(request.status) {
      case 404:
        err_msg = "Oops! Got 404 NOT FOUND!";
        break;
      case 500:
        err_msg = "It is 500! Server does not want to serve you! :-)";
        break;
      default:
        err_msg = "Unknown problem!";
      }
    $(this).html('<div class="error">' + err_msg + '</div>');
    });
  }


// Reviewed
function reviewed(blog_id) {
  var query_url = 'http://brps.appspot.com/admin/';
  if (window.location.href.indexOf('localhost') >= 0)
    query_url = 'http://localhost:8080/admin/';
  if (blog_id == '#')
    return;
  $.getJSON(query_url + 'reviewed.json?blog_id=' + blog_id + '&callback=?', function(json) {
    if (json.code == 0) {
      $("a.reviewed").each(function(){
        var $ele = $(this)
        if ($ele.attr('href').indexOf("('" + json.blog_id + "')") >= 0) {
          $ele.replaceWith("<span>Reviewed</span>");
          $('#messages').html();
          return false;
          }
        });
      }
    else
      $('#messages').html(json.error);
    });
  }


// accept
function accept(blog_id) {
  var query_url = 'http://brps.appspot.com/admin/';
  if (window.location.href.indexOf('localhost') >= 0)
    query_url = 'http://localhost:8080/admin/';
  if (blog_id == '#')
    return;
  $.getJSON(query_url + 'accept.json?blog_id=' + blog_id + '&callback=?', function(json) {
    if (json.code == 0) {
      $("a.accept").each(function(){
        var $ele = $(this)
        if ($ele.attr('href').indexOf("('" + json.blog_id + "')") >= 0) {
          $ele.replaceWith("<span>Accepted</span>");
          $('#messages').html();
          return false;
          }
        });
      }
    else
      $('#messages').html(json.error);
    });
  }


// block
function block(blog_id) {
  var query_url = 'http://brps.appspot.com/admin/';
  if (window.location.href.indexOf('localhost') >= 0)
    query_url = 'http://localhost:8080/admin/';
  if (blog_id == '#')
    return;
  $.getJSON(query_url + 'block.json?blog_id=' + blog_id + '&callback=?', function(json) {
    if (json.code == 0) {
      $("a.block").each(function(){
        var $ele = $(this)
        if ($ele.attr('href').indexOf("('" + json.blog_id + "')") >= 0) {
          $ele.replaceWith("<span>Blocked</span>");
          $('#messages').html();
          return false;
          }
        });
      }
    else
      $('#messages').html(json.error);
    });
  }


google.setOnLoadCallback(function () {
  init_error_indicator();
  });
