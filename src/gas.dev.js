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

  var MAX_RESULTS = 20;
  var MAX_TAGS = 20;
  var RESULTS_PER_PAGE = 8;

  if ($('#gas-results').length != 1)
    return;

  var brps_gas = $.extend({
      limit: 5,
      tag_selector: 'a[rel=tag]',
      html_loading: '<span>Loading...</span>',
      html_no_results: '<span>Found no results.</span>'
      }, window.brps_gas);

  if (brps_gas.limit > MAX_RESULTS)
    brps_gas.limit = MAX_RESULTS;
  window.brps_gas = brps_gas;

  var websearch = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&rsz=8' + '&callback=?';

  // Count tags
  var tag_count = {};
  var tags = $(brps_gas.tag_selector);
  if (tags.length == 0) {
    $('#gas-results').append($(brps_gas.html_no_results));
    return;
    }

  $.each(tags, function(idx, tag) {
    var tag = $(tag).text().toLowerCase();
    // Quote tag if it contains spaces
    if (tag.indexOf(' ') > -1)
      tag = '"' + tag + '"';
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
  var q = tags.join(' | ') + ' ' + sites.join(' | ');

  $('#gas-results').empty().append($(brps_gas.html_loading));

  var base_url = websearch + '&q=' + encodeURIComponent(q);
  $.getJSON(base_url, function(data) {brps_gas_callback(data, base_url)});
  });

function brps_gas_callback(data, base_url) {

  var MAX_PAGES = 5;
  var RESULTS_PER_PAGE = 8;
  
  var results = data.responseData.results;
  var cursor = data.responseData.cursor;
  var $results;
  
  if (!cursor.currentPageIndex || cursor.currentPageIndex == 0) {
    $('#gas-results').empty();
    $results = $('<ul/>').appendTo('#gas-results');
    }
  else
    $results = $('#gas-results ul');

  if (results.length > 0) {
    $.each(results, function(idx, result) {
      // Do not list same page
      if (result.unescapedUrl == document.location.href)
        return;
      // Check if the result link is exclude
      if (brps_gas.exclude_url_regexp && brps_gas.exclude_url_regexp.test(result.unescapedUrl))
        return;
      var $a = $('<a/>')
          .attr('href', result.unescapedUrl)
          .text($('<span>' + result.titleNoFormatting.replace(brps_gas.remove_string_regexp, '') + '</span>').text())
          ;
      var $result = $('<li/>').append($a);
      $result.appendTo($results).hide().animate({height: 'toggle', opacity: 'toggle'}, 'slow');
      // Check if reach limit
      if ($results.find('li').length >= brps_gas.limit)
        return false;
      });
    }

  function track() {
    function _track() {
      try {
        var pageTracker = _gat._getTracker("UA-8340561-4");
        pageTracker._setDomainName("none");
        pageTracker._setAllowLinker(true);
        pageTracker._trackPageview();
        }
      catch(err) {
        }
      }
    if (window._gat) {
      _track();
      }
    else {
      $.getScript(('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js', function(){
          _track();
          });
      }
    }

  if ($results.find('li').length < brps_gas.limit) {
    // Get more results
    if (cursor.currentPageIndex < MAX_PAGES - 1 && (cursor.currentPageIndex + 1) * RESULTS_PER_PAGE < cursor.estimatedResultCount) {
      $.getJSON(base_url + '&start=' + ((cursor.currentPageIndex + 1) * RESULTS_PER_PAGE).toString(), function(data){brps_gas_callback(data, base_url)});
      }
    else {
      if ($results.find('li').length == 0) {
        $('#gas-results').append($(brps_gas.html_no_results));
        }
      // Finish getting related posts, track it.
      track();
      }
    }
  else {
    track();
    }
  }
// vim: set sw=2 ts=2 et:
