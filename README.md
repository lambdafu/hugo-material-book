# Material Book

This is a boilerplate project for multivolume documentation using Hugo
and the hugo-material-docs theme.

```
$ git clone --recursive https://github.com/lambdafu/hugo-material-book
$ cd hugo-material-book
$ hugo server
```

## PDFs

For PDF generation to work, you need Pandoc and a reasonably complete
Texlive environment.

```
$ make
```

You also need to limit yourself to the common subset of Hugo's
blackfire markdown and Pandoc markdown.  A couple of extensions are
available and converted appropriately in the Python script.
