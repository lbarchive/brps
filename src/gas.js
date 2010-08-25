// BRPS client using Google AJAX Search API (http://brps.appspot.com/)
//
// Copyright (C) 2010  Yu-Jie Lin
//  
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//  
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.


$(function() {

  var MAX_TAGS = 20;

  if ($('#gas-results').length != 1)
    return;

  var brps_gas = $.extend({
      limit: 5,
      tag_selector: 'a[rel=tag]',
      html_loading: '<span>Loading...</span>',
      html_no_results: '<span>Found no results.</span>'
      }, window.brps_gas);

  if (brps_gas.limit > 8)
    brps_gas.limit = 8;

  var websearch = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&rsz=' + brps_gas.limit.toString() + '&callback=?';

  // Count tags
  var tag_count = {};
  var tags = $(brps_gas.tag_selector);
  if (tags.length == 0) {
    $('#gas-results').append($(brps_gas.html_no_results));
    return;
    }

  $.each(tags, function(idx, tag) {
    var tag = $(tag).text().toLowerCase();
    tag_count[tag] = ((tag in tag_count) ? tag_count[tag] : 0 ) + 1;
    });
  tags = [];
  $.each(tag_count, function(tag, count) {
    tags.push([tag, count]);
    });

  // Sort tags from biggest to smallest
  tags.sort(function(a,b){return b[1] - a[1];});
  tags = $.map(tags, function(tag) {return tag[0]});
  
  // Remove unwanted tags
  if (brps_gas.remove_tags) {
    var remove_tags = $.map(brps_gas.remove_tags, function(tag, idx) {
        return tag.toLowerCase();
        });
    var new_tags = [];
    $.map(tags, function(tag, idx) {
        if ($.inArray(tag.toLowerCase(), remove_tags) > -1)
          return;
        new_tags.push(tag);
        });
    tags = new_tags;
    }

  // Limit tags
  tags.splice(MAX_TAGS);

  // Prepare sites list
  var sites = $.map([document.location.hostname].concat(brps_gas.add_sites), function(site, idx) {
    if (site)
      return 'site:' + site;
    });

  // Composing the query string
  var q = '(' + tags.join(' | ') + ') ' + sites.join(' | ');

  $('#gas-results').empty().append($(brps_gas.html_loading));

  $.getJSON(websearch + '&q=' + encodeURIComponent(q), function(data) {
    var results = data.responseData.results;
    $('#gas-results').empty();
    if (results.length > 0) {
      var $results = $('<ul/>');
      $.each(results, function(idx, result) {
        // Do not list same page
        if (result.unescapedUrl == document.location.href)
          return;
        var $a = $('<a/>')
            .attr('href', result.unescapedUrl)
            .text($('<span>' + result.titleNoFormatting.replace(brps_gas.remove_string_regexp, '') + '</span>').text())
            ;
        var $result = $('<li/>').append($a);
        $result.appendTo($results);
        });
      $results.appendTo('#gas-results').hide().animate({height: 'toggle', opacity: 'toggle'}, 'slow');
      }
    else
      $('#gas-results').append($(brps_gas.html_no_results));
    });
  });  
// vim: set sw=2 ts=2 et: