CREATE TABLE IF NOT EXISTS corpus_words (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   testament TEXT NOT NULL,          -- 'OT', 'NT', or 'LXX'
   book TEXT NOT NULL,               -- Normalized book code (e.g., 'Gen', 'Matt', 'Rom')
   chapter INTEGER NOT NULL,
   verse INTEGER NOT NULL,
   word_index INTEGER NOT NULL,      -- Word order within the verse
   surface_text TEXT NOT NULL,       -- Original script with punctuation/cantillation
   normalized_text TEXT,             -- Stripped/normalized form
   transliteration TEXT,             -- Phonetic transliteration
   root_lemma TEXT NOT NULL,         -- Strong's ID (e.g. 'H430', 'G3056') or Greek root lemma
   strongs_id TEXT,                  -- Explicit Strong's ID ('H...' or 'G...') when available
   pos TEXT,                         -- Part of Speech code
   morph_code TEXT NOT NULL,         -- Full morphological parsing string
   morph_decoded TEXT,               -- Human-readable expanded morphology
   english_gloss TEXT                -- Direct mechanical word-level gloss
);

CREATE TABLE IF NOT EXISTS lexicon_entries (
   lemma_id TEXT PRIMARY KEY,        -- Matches corpus_words.root_lemma or strongs_id
   strongs_id TEXT,                  -- Canonical Strong's ID (e.g., 'H430', 'G3056')
   language TEXT NOT NULL,           -- 'Hebrew', 'Aramaic', 'Greek'
   original_word TEXT NOT NULL,      -- Original script lemma
   transliteration TEXT,             -- Phonetic transliteration
   primary_glosses TEXT NOT NULL,    -- Stripped of theological commentary
   idiomatic_notes TEXT              -- Lexical/syntactic/cultural notes
);

CREATE INDEX IF NOT EXISTS idx_lemma ON corpus_words(root_lemma);
CREATE INDEX IF NOT EXISTS idx_strongs ON corpus_words(strongs_id);
CREATE INDEX IF NOT EXISTS idx_reference ON corpus_words(book, chapter, verse);
CREATE INDEX IF NOT EXISTS idx_testament_ref ON corpus_words(testament, book, chapter, verse);
CREATE INDEX IF NOT EXISTS idx_morph ON corpus_words(root_lemma, morph_code);
CREATE INDEX IF NOT EXISTS idx_lex_word ON lexicon_entries(original_word);
CREATE INDEX IF NOT EXISTS idx_lex_strongs ON lexicon_entries(strongs_id);
