# Quality and release notes

Version 1.101. Font geometry, spacing, kerning and shaping tables are unchanged from the reviewed candidate; only naming/version/copyright metadata were updated. The master build reproduces both binaries byte for byte with the recorded toolchain.

Latest local checks: universal 82 PASS, 0 FAIL, 2 WARN; catalog Google Fonts 154 PASS, 0 FAIL, 8 WARN. No ERROR or FATAL results. Network-dependent checks were skipped in that final metadata run. Public-network Google Fonts catalog check: 158 PASS, 10 WARN, 60 SKIP, 0 FAIL, 0 ERROR. The metadata copyright/repository link passed. The description-link check skipped because its description/article condition was not met; article links and local image paths were separately inspected. Existing warnings and platform limitations still apply.

All 319 required Latin Core codepoints are present. Functional checks cover 145 composed/decomposed accent comparisons, standard ligatures, soft-dot substitutions, mark positioning and tabular figures. OpenType Sanitizer passes. All 423 UFO glyphs parse; 1,516 FreeType rendering checks complete without load/render errors. The Word specimen was rendered and visually checked across eight pages.

Retained warnings concern decorative contour counts, soft hyphen, subset-unreachable extra symbols, optional orthography beyond Latin Core, near-collinear segments, sharp joins, near-vertical stems, an unregistered vendor ID and tall vertical metrics. These were retained to preserve the ornamental lettering and avoid clipping accents. Google Fonts reviewers may request further changes. Extra desktop symbols may not all be served through Google's Latin web subsets.

The earlier spacing audit sampled 106,793 new-character pairs at two font units per pixel with minimum scanline clearance of 28 units; 16,900 original pair positions were preserved. This does not guarantee every long sequence of overlapping swashes. macOS and Adobe applications were not available for testing.

This independent free release does not promise ongoing support or updates. It is not a Google Fonts approval or a claim of exhaustive legal/name clearance.
