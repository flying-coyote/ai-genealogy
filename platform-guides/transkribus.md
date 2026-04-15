# Transkribus

AI-powered transcription for historical handwriting. Primary genealogy use cases: German Kurrent script, 17th-19th century English secretary hand, pre-modern European scripts.

## What It Is

Transkribus (`https://www.transkribus.org/`) is an AI transcription platform trained on historical handwriting. It is not a records database — you bring the document image, it produces a text transcription.

**Two access modes**
| Mode | URL | Best For | Cost |
|---|---|---|---|
| Transkribus Lite | `https://lite.transkribus.org/` | One-off documents, quick transcription | Free tier with monthly credit limit |
| Transkribus Expert Client | Desktop app | Batch processing, multi-page documents | Paid subscription |

## When to Use

- German Kurrent script: pre-1940 German handwriting is almost universally Kurrent, which is unreadable to most modern eyes. Transkribus has specialized Kurrent models.
- 17th-century English secretary hand: pre-printed church registers, wills, deeds.
- Any historical document where OCR fails. Standard OCR is designed for printed text — it cannot handle handwriting.
- Latin church records with individual handwritten entries.

## German Kurrent — What You're Dealing With

Kurrent (Kurrentschrift) was the standard German cursive script from the 16th to mid-20th century. It is unrelated to modern Latin cursive — letters look completely different. It was replaced by Sütterlin (a simplified Kurrent) in schools and then by standard Latin script after World War II. Most German-language parish registers, civil records, and correspondence before 1940 are in Kurrent.

**Key recognition challenges**
- `n`, `u`, and `m` are visually identical without context. Transkribus uses surrounding context to distinguish them.
- Long `s` (ſ) looks like `f`. Frequent OCR error.
- Abbreviations are common:
  - `geb.` = geboren (born)
  - `gest.` = gestorben (died)
  - `get.` = getauft (baptized)
  - `∞` or `copul.` = married
  - `leg.` / `elig.` = legitimate / illegitimate
- Dates written in German order: day month year, e.g. `14 März 1842`
- Umlauts written with superscript `e`: `ae` = `ä`, `oe` = `ö`, `ue` = `ü`

## Workflow

1. Obtain the document image: download from FS Catalog, Archion.de, Matricula, PRONI, IrishGenealogy.ie, or a locally scanned document.

2. Upload to Transkribus Lite at `https://lite.transkribus.org/`

3. Select the appropriate model:
   - **Transkribus German Kurrent M1** — for German Kurrent (most German records)
   - **Print M1** — for early printed records (incunabula, early books)
   - **Historical Documents** — general model for pre-1900 European handwriting

4. Review output: Transkribus is ~85-95% accurate on clean Kurrent. Always read through and correct against the original image. Never trust the transcript alone.

5. Document the transcript: save as `research/evidence/{case}_{record_date}_transcript.md` with:
   - Path to original image file
   - Source URL or archive reference
   - Date transcribed
   - Model used
   - Notes on uncertain readings (mark with `[?]`)

## Accuracy Expectations

| Document Condition | Expected Word Accuracy |
|---|---|
| Clean Kurrent on high-quality microfilm | 90-95% |
| Faded, damaged, or unusual hand | 70-85% |
| Mixed hands (multiple scribes in same register) | 75-90% |

Names are the hardest part. Common names are recognized more reliably; unusual surnames require careful verification against the image. Context helps: if you know the village and approximate date, you can sanity-check names against what's plausible for that location.

## Alternatives

**Script Source (FamilySearch)**
`https://www.familysearch.org/en/help/helpcenter/article/how-do-i-read-old-handwriting`
Not automated — good reference images organized by script type and era. Useful for learning to read a script yourself.

**BYU German Genealogy Script Reading**
Free online course teaching Kurrent fundamentals. Useful if you expect to work regularly with German records.

**Human transcription services**
Some genealogy societies offer Kurrent transcription for a fee per page. Worthwhile for critical documents where accuracy matters more than cost.

## Evidence Note

Transkribus output is a working transcript, not a primary source. Cite the original document — the parish register or civil record is the evidence. The transcript is a research tool that makes the evidence legible.

In citations, format as: "[Original source citation]. Transcribed using Transkribus [model name], [date]."
