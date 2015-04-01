_**As of 2011-09-21, the list is not loaded automatically when page loads.**_

_**As of 2010-09-22, this client is deprecated and no longer accepts new users. Please use ClientGasJs, instead**_



# Introduction #
Blogger Related Posts Service, **brps** for short, simplifies the process of installation and reduces the burden of complexity of Related Posts installation. It's not like other methods that you can find on the Internet, which you must go deep into the Blogger.com template and may be drowned by template code still can not get it work.

Please aware:
  * This service only serves for public blogs.
  * The author of BRPS may be blocking your blogs from using this service due to
    * Copyright infringement _(If your blogs have links to any illegal downloads, directly or indirectly, upload by youself or not, please **DO NOT** use BRPS. Otherwise, your blogs will be **BLOCKED** for sure)_,
    * Hate against a protected group,
    * Adult or pornographic images,
    * Promotion of dangerous and illegal activity,
    * Content facilitating phishing or account hijacking,
    * Impersonated user identity, or
    * Abuse this service.
The reasons may not be only limited to above and it is solely judged by the author of BRPS.

_Please must also read: **[Blocking Policy](http://thebrps.blogspot.com/2009/10/blocking-policy.html)**_

_Blogger Related Posts Service is not affiliated with [Blogger](http://www.blogger.com/)_.

# Features/Facts #
  * Lists up to 10 related posts
  * Relating is based on labels of queried post
  * Customization of widget title
  * 3 Lines only for manual installation
  * Data cache for 24 hours

# Installation #
The standard installation steps please follow them in [service homepage](http://brps.appspot.com/).

# Customization #
The following code shows all options that you can customize:
```
<script type="text/javascript">
window.brps_options = {
  "title": "<h2>Hey! Check out my other related posts!</h2>",
  "load_button_text": "Click to load related posts list",
  "autoload": false,
  "max_results": 5
  }
</script>
```
Please read the following subsection for explanations.

## Widget Title ##
By default, if your blogs are written in English, you should be more likely having no need to customize the widget title. However, if your blog is not a normal blog or not in English. For example, it's a food/cuisine/etc or written in Japanese. You could set the title to **Related Recipes** or **関連記事** (translated by Google Translate).

Here is how you can do that:
Change the original code:
```
<script src='http://www.google.com/jsapi'></script>
<script src='http://brps.appspot.com/brps.js?key=[KEY]' type='text/javascript'/>
```
into
```
<script src='http://www.google.com/jsapi'></script>
<script type="text/javascript">
window.brps_options = {
  "title": "<h2>Hey! Check out my other related posts!</h2>"
  }
</script>
<script src='http://brps.appspot.com/brps.js?key=[KEY]' type='text/javascript'/>
```
Notice that we have a new `<script>` block. You can also use HTML in it, you may need to as shown above since normal Blogger widgets use `<h2>` as title. If you don't use, the widget may look different.

## Limit number of related posts ##
By default, BRPS lists 10 related posts at most, which is all from database. You can down it to any number that you like

Here is how you can do that:
Change the original code:
```
<script src='http://www.google.com/jsapi'></script>
<script src='http://brps.appspot.com/brps.js?key=[KEY]' type='text/javascript'/>
}}}' type='text/javascript'/>
```
into
```
<script src='http://www.google.com/jsapi'></script>
<script type="text/javascript">
window.brps_options = {
  "max_results": 5
  }
</script>
<script src='http://brps.appspot.com/brps.js?key=[KEY]' type='text/javascript'/>
}}}' type='text/javascript'/>
```

## CSS ##
The DOM looks like:
```
div#related_posts
 h2 /* By default. If you customize brps_options["title"], it will be whatever you set */
 ul
  li
```

If you want to set CSS of every related post item of list:
```
#related_posts ul li {
  /* CSS here */
  font-family: Arial;
  font-size: 1.2em;
  font-weight: bold;
  color: #888;
  }
```

If you want to set CSS of default title of list:
```
#related_posts h2 {
  /* CSS here */
  }
```

## Tracking Helper ##
BRPS doesn't provide click-through tracking, but you can ask the client-side script to append `?src=brps` to end of post links, that may looks like `http://example.blogspot.com/2009/03/post-title.html?src=brps`.

Please using the following setting:
```
<script type="text/javascript">
window.brps_options = {
  "append_src": true
  }
</script>
```

# How this Works? #
  1. When a visitor reads a post, the web browser will contact BRPS server and ask for related posts for that.
  1. BRPS checks if there is a cached data (cache time is 24 hours currently). If yes, then send the cached data to web browser; if not:
    1. BRPS will use _Blogger Data API_ to retrieve **labels** of the post.
    1. Once gets the labels of requested post, it continues to use all labels to query which posts have labelled with one or more same labels.
    1. In the returned post list, for post matches more label, they get higher score. Higher score will list first.
    1. After scoring all post, currently, BRPS will cache first 10 posts.
  1. BRPS sends cached data to browser.
  1. Web browser renders the list.

# Known Issues #
  * Your template must include `<b:include data='blog' name='all-head-content'/>`, if yours not, please include right after `<head>`. A first discussion can be found [here](http://groups.google.com/group/blogger-related-posts-service/browse_thread/thread/e035597d6191c200).
  * `*`May not work with 1.3, untested`*` BRPS is not compatible with others scripts using jQuery 1.1.x or earlier. But here is a workaround, please replace the conflict script's jQuery inclusion with
```
<script src="http://ajax.googleapis.com/ajax/libs/jquery/1.3/jquery.min.js" type="text/JavaScript"></script>
<script src="http://dev.jquery.com/export/6078/trunk/plugins/compat-1.1/jquery.compat-1.1.js" type="text/JavaScript"></script>
```

# FAQ #
  * [No related posts found](http://thebrps.blogspot.com/2009/07/explanation-of-no-related-posts-found.html)
  * [Why do we need key?](http://thebrps.blogspot.com/2009/11/why-enforce-using-key.html)
  * [Only see Loading...](http://thebrps.blogspot.com/2009/11/about-loading.html)