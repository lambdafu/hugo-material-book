---
title: Advanced
url: user/advanced
weight: 20
menu:
  main:
    parent: User's Manual
    identifier: Advanced
    weight: 20
---

## Advanced Editing

### Lists and such

There are bullet-style lists:

* **bold**
* _italic_
* ~~strike-through~~
* `code`

There are also numbered lists.  In case of fire:

1. `git commit -a -m .`
2. `git push --all`
3. Run away.

And definition lists:

Debian

:    We got'em all!

Ubuntu

:    Our window buttons are like Apple's!

Gentoo

:    What was that USE-flag again?

### Block elements

Code blocks come with syntax highlighting:

``` ini
[segmentorize]

phunk = 7.3
hype = true
```

You can disable it, too, with the special language `nohighlight`:

``` nohighlight
[segmentorize]

phunk = 7.3
hype = true
```

### Admonitions

These admonitions are shortcodes for hugo-material-docs which are
implemented for PDFs in our special preprocessor.

{{< note title="Why does this not work?" >}}
Because it never did and never will.
{{< /note >}}

{{< warning title="It's a trap." >}}
Bazinga!
{{< /warning >}}
