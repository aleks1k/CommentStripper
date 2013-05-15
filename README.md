See file parse_comments.py

<pre><code>
    parser = ParseComments()
    dirs = ['/repo/github/diaspora/diaspora', '/repo/github/django/django']
    for d in dirs:
        comments = parser.parse_dir(d)
        pprint(comments)

    print 'Statictics\n'
    parser.print_statistics()
</code></pre>

Set var <code>ParseComments.collect_statistic = True</code> for collect statistic for file types and parse time

[Wikipedia](http://en.wikipedia.org/wiki/Comparison_of_programming_languages_%28syntax%29#Inline_comments "Comments") has a good reference on comments
