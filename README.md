# Aurethalen

An ornamental Latin display typeface by **The Gilded Threshold**, with pointed serifs, strong stroke contrast and sweeping flourishes. Designed for book covers, headings, invitations and imaginative storytelling.

![Aurethalen specimen](documentation/article/aurethalen.png)

## Download and use

[Complete package — Aurethalen-v1.101.zip](Aurethalen-v1.101.zip).

The desktop font is [Aurethalen-Regular.ttf](fonts/ttf/Aurethalen-Regular.ttf). Open that file on Windows or macOS and choose Install. The webfont is [Aurethalen-Regular.woff2](fonts/webfonts/Aurethalen-Regular.woff2).

Version 1.101 includes all 319 required Google Fonts Latin Core codepoints, 379 Unicode mappings and 423 glyphs. Features include standard ff/fi/fl/ffi/ffl ligatures, kerning, combining-accent attachment, stacked accents, tabular figures, superscripts, subscripts and fractions. Enable kerning and standard ligatures where supported, and leave space for the flourishes.

This is an independent release. Aurethalen has not been accepted into or published by Google Fonts.

## License

The font software and its design sources are licensed under the **SIL Open Font License 1.1**; see [OFL.txt](OFL.txt). No Reserved Font Name is declared. The font may be used in personal and commercial projects under those terms.

The three specimen images are licensed under **CC BY-SA 4.0**; see [image-license.txt](documentation/image-license.txt). The lantern-and-arch studio profile PNG has its own [CC BY-SA notice](documentation/designer-profile/image-license.txt). Those image licenses do not cover the full tarot cover or other studio artwork.

## Build

Use Python 3.12 and an isolated environment:

```text
python -m venv .venv
```

Activate it (`.venv\Scripts\Activate.ps1` on Windows, or `source .venv/bin/activate` on macOS/Linux), then run:

```text
python -m pip install -r requirements.txt
python sources/build.py
```

The authoritative editable source is `sources/Aurethalen.ufo`. Builds produce the desktop TTF and WOFF2 files without overwriting that master. Historical derivation inputs are retained in `sources/derivation`; their earlier font names describe project history.

## Creation history and checks

The initial lettering image was generated using Microsoft Edge's AI theme generator from the owner's description. AI assistance was also used for tracing, added-character construction, engineering and documentation. See [source provenance](documentation/SOURCE-PROVENANCE.md). The studio emblem was generated with ChatGPT from the owner's descriptions without supplied references, then extracted from the approved print cover for the profile PNG; see its [provenance](documentation/designer-profile/PROVENANCE.md).

The latest local universal and Google Fonts checks report no failures or errors. Retained warnings, online-check limits and platform limitations are described in [QUALITY.md](documentation/QUALITY.md). Checks are diagnostics, not Google Fonts acceptance.

## Support and onboarding

The font is offered as-is without ongoing user support. The owner has clarified the following Google Fonts participation scope:

> I am available to actively maintain and update the repository throughout the onboarding and review process to address any QA or FontBakery issues. Once the typeface is published as a completed release, I do not plan to provide ongoing feature development or active long-term maintenance, though the repository includes full editable source files under the SIL Open Font License so the community or Google Fonts team can apply future fixes if needed.

The availability of editable sources permits future fixes by others; it does not mean another maintainer has agreed to provide them. Google Fonts review is pending. Replies can be made on the [onboarding issue](https://github.com/google/fonts/issues/11304). No public contact email is provided.

## Studio

<p>The Gilded Threshold is an independent creative studio and type foundry focused on expressive display typography and illustrated print projects. Drawing on classical serif traditions, celestial imagery, and storybook influences, the studio pairs ornate flourishes with carefully considered structure. Its debut typeface, Aurethalen, brings that approach to book covers, titles, packaging, and imaginative storytelling. The studio develops open-source typography to give authors, designers, and makers distinctive tools for their work. Beyond type design, its practice includes original tarot decks, artistic print editions, and mythic visual art.</p>

