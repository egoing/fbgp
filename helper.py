def autolink(html):
    import re
    # match all the urls
    # this returns a tuple with two groups
    # if the url is part of an existing link, the second element
    # in the tuple will be "> or </a>
    # if not, the second element will be an empty string
    urlre = re.compile("(\(?https?://[-A-Za-z0-9+&@#/%?=~_()|!:,.;]*[-A-Za-z0-9+&@#/%=~_()|])(\">|</a>)?")
    urls = urlre.findall(html)
    clean_urls = []

    # remove the duplicate matches
    # and replace urls with a link
    for url in urls:
        # ignore urls that are part of a link already
        if url[1]: continue
        c_url = url[0]
        # ignore parens if they enclose the entire url
        if c_url[0] == '(' and c_url[-1] == ')':
            c_url = c_url[1:-1]

        if c_url in clean_urls: continue # We've already linked this url

        clean_urls.append(c_url)
        # substitute only where the url is not already part of a
        # link element.
        html = re.sub("(?<!(=\"|\">))" + re.escape(c_url), 
                      "<a rel=\"nofollow\" href=\"" + c_url + "\" target=\"_blank\">" + c_url + "</a>",
                      html)
    return html

def escape_html(string):
    import cgi
    return cgi.escape(string)

def nl2br(string):
    return string.replace('\n', '<br/>');

def space2nbsp(string):
    return string.replace(' ', '&nbsp;'); 

def message(string):
    import logging
    string = escape_html(string)
    string = nl2br(string)
    string = space2nbsp(string)
    return string