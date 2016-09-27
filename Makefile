mdbooks = user system extensions infrastructure
author = "Marcus Brinkmann"

all: all_mds

clean:
	-rm -rf public pdfs

.PHONY: all hugo clean


define CHAPTER_template

allparts-html: $(1)-html

allparts-pdf: $(1)-pdf

$(1): $(1)-html $(1)-pdf

$(1)-html:
	# Maybe singlehtml?
	$(SPHINXBUILD) -t $(1) -b html $(SPHINXOPTS) . $(BUILDDIR)/$(1)-html

$(1)-pdf:
	$(SPHINXBUILD) -t $(1) -b latex $(SPHINXOPTS) . $(BUILDDIR)/$(1)-pdf
	$(MAKE) -C $(BUILDDIR)/$(1)-pdf LATEXOPTS=$(LATEXOPTS)

.PHONY : $(1) $(1)-html $(1)-pdf

endef

chapter_dirs = $(shell find . -maxdepth 1 -type d -name ch_\*)
chapters = full $(chapter_dirs:./ch_%=%)

# Insert template for each chapter (and "full")
$(foreach chapter, $(chapters), $(eval $(call CHAPTER_template,$(chapter))))


# $(1): book, $(2): chapter
define MDBOOK_chapter

MDBOOK_$(1)_$(2)_src = $$(patsubst %.pdf,%.md,$(2))

pdfs/$(1)/$(2): content/$(1)/$$(MDBOOK_$(1)_$(2)_src)
	mkdir -p pdfs/$(1)
	python pandoc-book.py --author ${author} --article $$< | pandoc -f json -s -o $$@

all_mdarticles_$(1): pdfs/$(1)/$(2)
endef


define MDBOOK_template
MDBOOK_$(1)_chapters = $$(shell (cd content/$(1); ls *.md | grep -v 00-index.md | sort -n))
MDBOOK_$(1)_chapter_files = $$(addprefix content/$(1)/, $$(MDBOOK_$(1)_chapters))

pdfs/full.pdf: content/$(1)/00-index.md $$(MDBOOK_$(1)_chapter_files)

pdfs/$(1).pdf: content/$(1)/00-index.md $$(MDBOOK_$(1)_chapter_files)
	mkdir -p pdfs
	python pandoc-book.py --book content/$(1)/00-index.md --chapters $$(MDBOOK_$(1)_chapter_files) | pandoc -f json -s -o $$@

all_mdbooks: pdfs/$(1).pdf


MDBOOK_$(1)_articles = $$(MDBOOK_$(1)_chapters:%.md=%.pdf)
all_mdarticles: all_mdarticles_$(1)

.PHONY: all_mdarticles_$(1)

$$(foreach mdarticle, $$(MDBOOK_$(1)_articles), $$(eval $$(call MDBOOK_chapter,$(1),$$(mdarticle))))

endef


$(foreach mdbook, $(mdbooks), $(eval $(call MDBOOK_template,$(mdbook))))

pdfs/full.pdf: content/index.md
	mkdir -p pdfs
	python pandoc-book.py --book content/index.md $(foreach mdbook, $(mdbooks), --part content/$(mdbook)/00-index.md --chapters $(MDBOOK_$(mdbook)_chapter_files)) | pandoc -f json -s -o $@

all_mds: all_mdarticles all_mdbooks pdfs/full.pdf

.PHONY: all_mds all_mdbooks all_mdarticles
