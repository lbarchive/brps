# Introduction #

This is a new experimental method to get a list of related content, it is still based on _labels_. You can read how I [installed](http://blog.yjl.im/2010/08/using-brps-new-method-to-get-related.html) it on my blog.

# Facts #

Now, a quick comparison with `brps.js`.

## Pros ##

  * It's faster. Because it do not use BRPS database, therefore BRPS do not need to search for labels via Blogger API. It directly uses Google Search with labels as search keyword.
  * It supports multi-blog, even multi-site, because it uses Google search operator `site:example.com | site:someblog.blogspot.com | ...`
  * It can now work on any page of your Blogger blog, _but_ it will use all labels from that page to do the search. In other words, the search keywords can come from labels of different posts on that page which user is visiting. It will only use top 20 frequent label to query.
  * No Key required! No blocking!

## Cons ##

  * Since the result are Google Search results, therefore, un-indexed page will never show up in related list until it's archived by Google. If you just publish new post, then it may not show up in other post's related list right away.
  * ~~Only up to 8 results. Though Google AJAX Search API provides paging, but it will not try to grab results from second page.~~

## Others ##

  * Up to 20 results by specifying `limit` parameter.

# Known Issues #

  * ~~Blogs (or sites) home pages or archive pages may be listed.~~

# Installation #

The steps are simple as `brps.js`:

```
<script src="http://ajax.googleapis.com/ajax/libs/jquery/1/jquery.min.js"></script>
<script src="http://brps.appspot.com/gas.js"></script>
<h2>Related Posts</h2>
<div id="gas-results"></div>
```

If your website already have jQuery installed, then you can omit the first line of code, just to make sure you include `gas.js` after jQuery is loaded.

# Customization #

You can customize it with the options as follow:

```
<script>
window.brps_gas = {
  remove_tags: ['unwanted_tag1', 'unwanted_tag2'],
  tag_selector: 'a[rel=tag]',
  limit: 5,
  add_sites: ['secondblog.blogspot.com', 'thirdblog.blogspot.com'],
  remove_string_regexp: /^.*?: /,
  exclude_url_regexp: /(\/search\/label\/|\/view\/|(archive\.html|blog\.example\.com\/|\.blogspot\.com\/)$)/,
  html_loading: '<span>Loading...</span>',
  html_no_results: '<span>Found no results.</span>'
  };
</script>
```

`tag_selector` is added because some blog template might not be standard or it's possible to use `tag_selector` for a normal website.

`remove_string_regexp` is added because normal Blogger blog will have titles like 'Blog Name: Post Title'. It will be strange to read it, you can use this option in regular expression to remove "Blog Name: " from result string.

If you need to match these characters in `remove_string_regexp`: `\/+*?(){}|`, you may need to prefix with `\`, e.g. `\\`, `\(`. If you still don't know how to enter, please ask in discussions group.

Note: for matching single quote (apostrophe) `'` or double quote `"` in the title, since they are HTML escaped, you will need to use `&#39;` or `&#34;` to match them, respectively. There might be [more characters](http://www.w3.org/MarkUp/html-spec/html-spec_13.html) are escaped. Basically, you don't have to match them, standard Blogger blog's title can be matched by the regular expression as shown in the code block above, i.e. `/^.*?: /`.

`exclude_url_regexp` can remove archive pages (`archive\.html$`), label pages (`\/search\/label\/`), and homepage of blogs by matching the link urls.

# Questions/Inputs? #

Please ask your questions at [Discussions Group](http://groups.google.com/group/blogger-related-posts-service).