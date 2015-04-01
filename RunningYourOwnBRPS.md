_**This is a work in progress, please help improve it by leaving comment with issues.**_

# Introduction #

The reason of running your own BRPS is because currently BRPS doesn't accept new users for brps.js (the old script), which uses Blogger API.

# Instructions #

## Step 1: Creating a new Google App Engine application ##

Go to [Google App Engine](https://appengine.google.com/) to create a new application with your desired `[APPID]`, which will be used in later steps.

The client script URL will be:

```
http://[APPID].appspot.com/brps.js?key=12345678
```

## Step 2: Modifying `app.yaml` ##

Change `brps` in first line

```
application: brps
```

to

```
application: [APPID]
```

## Step 3: Modifying `brps.js` ##

Find the following string in `brps.js`:

```
brps.appspot.com
```

There should be two matches, replace them with:

```
[APPID].appspot.com
```

## Step 4: Modifying `brps/blog.py` ##

Find

```
def get_blog_key(blog_id):
  blog_id = int(blog_id)
  key = memcache.get('k%d' % blog_id)
  if key:
    return key
  key = md5.md5('%d%s' % (blog_id, config.KEY_SALT)).hexdigest()[:8]
  memcache.set('k%d' % blog_id, key, 3600)
  return key
```

Replace with

```
ACCEPTED_BLOG_IDS = [123, 456];

def get_blog_key(blog_id):
  blog_id = int(blog_id)
  if blog_id in ACCEPTED_BLOG_IDS:
    return '12345678'
  return None
```

Where `123` and `456` is your Blogger blog IDs, you can put in as many as you like.

### Step 5: Deploying ###

Please follow [Google App Engine's instruction](https://developers.google.com/appengine/docs/python/tools/uploadinganapp#Uploading_the_App).

### Step 6: Installing client script ###

Put the following to where you want to see the related list:

```
<script src='http://www.google.com/jsapi'></script>
<script src='http://[APPID].appspot.com/brps.js?key=12345678'></script>
<div id='related_posts'></div>
```

You may also want to read about customization of [brps.js](http://code.google.com/p/brps/wiki/ClientBrpsJs).