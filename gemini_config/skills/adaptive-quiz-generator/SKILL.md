---
name: adaptive-quiz-generator
description: Generates an interactive, adaptive HTML quiz artifact with progress tracking, scoring, hints, performance analytics, and dynamic weak-area regeneration.
---

# Adaptive Quiz Generator Skill

When the user requests an interactive quiz, testing, or adaptive learning experience, generate an HTML artifact (`quiz.html`) using the boilerplate below. 

## Instructions
1. Use `write_to_file` to create a `.html` file in the artifact directory. **You MUST include `ArtifactMetadata` since you are creating an artifact.** Set `UserFacing: true`.
2. Do NOT embed this inline with `<agent-embed>` unless explicitly requested.
3. Replace the `questionBank` array with a massive set of questions (at least 20-30 questions if possible) spanning multiple categories and difficulty levels (1-3).
4. The built-in JS engine will automatically handle drawing an initial set of questions, computing performance per category, and providing the user with a UI to generate targeted follow-up questions based on their weak areas from the remaining local bank.

## Quiz HTML Boilerplate (Tailwind + Vanilla JS)

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-thumb { background-color: var(--border); border-radius: 4px; }
  </style>
  <title>Adaptive Mastery Quiz</title>
</head>
<body class="bg-[var(--background)] text-[var(--foreground)] antialiased h-screen m-0 p-4 flex justify-center items-center font-sans">

  <div class="bg-[var(--card)] w-full max-w-3xl rounded-2xl border border-[var(--border)] shadow-lg flex flex-col h-full max-h-[850px] overflow-hidden">
    
    <!-- Header -->
    <div class="p-6 border-b border-[var(--border)] flex flex-col gap-4">
      <div class="flex justify-between items-center">
        <h1 id="quiz-title" class="text-xl font-semibold">Adaptive Mastery Quiz</h1>
        <div id="header-stats" class="flex gap-2 text-sm font-medium">
          <span class="flex items-center text-[var(--muted-foreground)] mr-4">
            <span id="progress-text">1 / 10</span>
          </span>
          <span class="flex items-center gap-1 bg-red-500/20 text-red-400 px-3 py-1 rounded-full">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            <span id="score-incorrect">0</span>
          </span>
          <span class="flex items-center gap-1 bg-green-500/20 text-green-400 px-3 py-1 rounded-full">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
            <span id="score-correct">0</span>
          </span>
        </div>
      </div>
      <!-- Progress Bar -->
      <div class="w-full bg-[var(--border)] h-1.5 rounded-full overflow-hidden">
        <div id="progress-bar" class="bg-[var(--primary)] h-full transition-all duration-300" style="width: 10%"></div>
      </div>
    </div>

    <!-- Active Quiz Area -->
    <div id="quiz-area" class="flex-1 overflow-y-auto p-6 flex flex-col">
      <div class="flex justify-between items-center mb-2">
        <h2 class="text-lg font-medium text-[var(--muted-foreground)]">Question <span id="question-number">1</span></h2>
        <span id="question-tags" class="text-xs font-semibold px-2 py-1 bg-[var(--border)] rounded text-[var(--muted-foreground)]"></span>
      </div>
      <p id="question-text" class="text-base mb-6 leading-relaxed">Loading question...</p>

      <div id="options-container" class="flex flex-col gap-3 mb-6"></div>

      <div class="mt-auto pt-4">
        <button id="hint-toggle" class="text-[var(--muted-foreground)] hover:text-[var(--foreground)] text-sm flex items-center gap-2 transition-colors">
          Hint & Explanation
          <svg id="hint-icon" class="w-4 h-4 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
        </button>
        <div id="hint-content" class="hidden mt-3 p-4 bg-[var(--background)] rounded-lg text-sm text-[var(--muted-foreground)] border border-[var(--border)]"></div>
      </div>
    </div>

    <!-- Performance & Adaptive Dashboard (Hidden by default) -->
    <div id="finish-area" class="hidden flex-1 overflow-y-auto p-6 flex flex-col">
      <h2 class="text-2xl font-bold mb-2">Session Complete!</h2>
      <p class="text-[var(--muted-foreground)] mb-6">Here is your performance breakdown. Generate more targeted questions to strengthen your weak areas.</p>
      
      <div class="grid grid-cols-2 gap-4 mb-8" id="category-stats-container">
        <!-- Injected via JS -->
      </div>

      <div class="bg-[var(--background)] border border-[var(--border)] p-5 rounded-xl">
        <h3 class="text-lg font-semibold mb-4">Adaptive Drill Generator</h3>
        <div class="flex flex-col gap-4">
          <div>
            <label class="block text-sm text-[var(--muted-foreground)] mb-1">Target Weak Area</label>
            <select id="adapt-category" class="w-full bg-[var(--card)] border border-[var(--border)] text-[var(--foreground)] p-2 rounded-lg"></select>
          </div>
          <div class="flex gap-4">
            <div class="flex-1">
              <label class="block text-sm text-[var(--muted-foreground)] mb-1">Difficulty</label>
              <select id="adapt-difficulty" class="w-full bg-[var(--card)] border border-[var(--border)] text-[var(--foreground)] p-2 rounded-lg">
                <option value="All">Mixed</option>
                <option value="1">Level 1 (Core Concepts)</option>
                <option value="2">Level 2 (Application)</option>
                <option value="3">Level 3 (Exam Traps)</option>
              </select>
            </div>
            <div class="flex-1">
              <label class="block text-sm text-[var(--muted-foreground)] mb-1"># of Questions</label>
              <input type="number" id="adapt-count" value="5" min="1" max="20" class="w-full bg-[var(--card)] border border-[var(--border)] text-[var(--foreground)] p-2 rounded-lg">
            </div>
          </div>
          <button id="btn-generate-adaptive" class="mt-2 w-full py-3 rounded-xl font-bold text-[var(--primary-foreground)] bg-[var(--primary)] hover:opacity-90 transition-opacity">
            Generate Drill Set
          </button>
          <p id="adapt-warning" class="text-red-400 text-sm hidden mt-2"></p>
        </div>
      </div>
    </div>

    <!-- Footer Controls -->
    <div id="footer-controls" class="p-4 border-t border-[var(--border)] flex justify-between items-center bg-[var(--background)]/50">
      <button id="btn-back" class="px-5 py-2 rounded-full font-medium text-[var(--foreground)] bg-[var(--background)] border border-[var(--border)] hover:bg-[var(--border)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed">Back</button>
      <button id="btn-next" class="px-5 py-2 rounded-full font-medium text-[var(--primary-foreground)] bg-[var(--primary)] hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed">Next</button>
    </div>
  </div>

  <script>
    // --- AI GENERATES MASSIVE QUESTION BANK HERE ---
    const questionBank = [
      {
        id: "q1",
        category: "Sample Category",
        difficulty: 1,
        question: "Sample Question?",
        options: ["A", "B", "C", "D"],
        correctAnswer: 0,
        hint: "Explanation."
      }
    ];
    // -----------------------------------------------

    let activeQueue = [];
    let currentQuestionIndex = 0;
    let score = { correct: 0, incorrect: 0 };
    let userAnswers = {}; // { questionId: { selectedOption, isCorrect } }
    let usedIds = new Set();

    // DOM
    const elTitle = document.getElementById('quiz-title');
    const elProgText = document.getElementById('progress-text');
    const elProgBar = document.getElementById('progress-bar');
    const elScoreCorrect = document.getElementById('score-correct');
    const elScoreIncorrect = document.getElementById('score-incorrect');
    const elQNum = document.getElementById('question-number');
    const elQTags = document.getElementById('question-tags');
    const elQText = document.getElementById('question-text');
    const elOptions = document.getElementById('options-container');
    const elHintToggle = document.getElementById('hint-toggle');
    const elHintContent = document.getElementById('hint-content');
    const elHintIcon = document.getElementById('hint-icon');
    const elBtnBack = document.getElementById('btn-back');
    const elBtnNext = document.getElementById('btn-next');
    
    const elQuizArea = document.getElementById('quiz-area');
    const elFinishArea = document.getElementById('finish-area');
    const elFooterControls = document.getElementById('footer-controls');
    
    const elCatStats = document.getElementById('category-stats-container');
    const elAdaptCat = document.getElementById('adapt-category');
    const elAdaptDiff = document.getElementById('adapt-difficulty');
    const elAdaptCount = document.getElementById('adapt-count');
    const elBtnGenerate = document.getElementById('btn-generate-adaptive');
    const elAdaptWarning = document.getElementById('adapt-warning');

    function initQuiz() {
      elTitle.textContent = document.title || "Adaptive Mastery Quiz";
      elBtnNext.addEventListener('click', goNext);
      elBtnBack.addEventListener('click', goBack);
      elHintToggle.addEventListener('click', toggleHint);
      elBtnGenerate.addEventListener('click', handleGenerateAdaptive);

      // Start with a mix of up to 5 initial questions
      buildInitialSet(5);
      renderQuestion();
    }

    function buildInitialSet(count) {
      let pool = [...questionBank].sort(() => Math.random() - 0.5);
      let selected = pool.slice(0, Math.min(count, pool.length));
      activeQueue = selected;
      selected.forEach(q => usedIds.add(q.id));
    }

    function renderQuestion() {
      const q = activeQueue[currentQuestionIndex];
      const total = activeQueue.length;
      
      elQuizArea.classList.remove('hidden');
      elFinishArea.classList.add('hidden');
      elFooterControls.classList.remove('hidden');

      elProgText.textContent = `${currentQuestionIndex + 1} / ${total}`;
      elProgBar.style.width = `${((currentQuestionIndex + 1) / total) * 100}%`;
      elQNum.textContent = currentQuestionIndex + 1;
      elQTags.textContent = `${q.category} | Lvl ${q.difficulty}`;
      elQText.textContent = q.question;
      elScoreCorrect.textContent = score.correct;
      elScoreIncorrect.textContent = score.incorrect;
      elOptions.innerHTML = '';
      
      const letters = ['A', 'B', 'C', 'D', 'E', 'F'];
      const hasAnswered = userAnswers[q.id] !== undefined;
      const ansData = userAnswers[q.id];

      q.options.forEach((opt, idx) => {
        const btn = document.createElement('button');
        btn.className = `w-full text-left p-4 rounded-xl border transition-all flex items-center gap-4 ${hasAnswered ? 'cursor-default' : 'hover:bg-[var(--border)] cursor-pointer'}`;
        
        let borderClass = 'border-[var(--border)] bg-transparent text-[var(--foreground)]';
        let iconHtml = `<div class="w-6 h-6 rounded border border-[var(--muted-foreground)] flex shrink-0 items-center justify-center text-xs font-bold text-[var(--muted-foreground)]">${letters[idx]}</div>`;

        if (hasAnswered) {
          if (idx === q.correctAnswer) {
            borderClass = 'border-green-500/50 bg-green-500/10 text-green-400';
            iconHtml = `<div class="w-6 h-6 rounded bg-green-500/20 text-green-400 flex shrink-0 items-center justify-center"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg></div>`;
          } else if (idx === ansData.selectedOption && idx !== q.correctAnswer) {
            borderClass = 'border-red-500/50 bg-red-500/10 text-red-400';
            iconHtml = `<div class="w-6 h-6 rounded bg-red-500/20 text-red-400 flex shrink-0 items-center justify-center"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></div>`;
          } else {
             borderClass = 'border-[var(--border)] bg-transparent opacity-50';
          }
        }

        btn.className += ` ${borderClass}`;
        btn.innerHTML = `${iconHtml} <span>${opt}</span>`;
        if (!hasAnswered) btn.addEventListener('click', () => handleSelect(idx, q));
        elOptions.appendChild(btn);
      });

      elHintContent.innerHTML = q.hint;
      if (hasAnswered) {
        elHintContent.classList.remove('hidden');
        elHintIcon.classList.add('rotate-180');
      } else {
        elHintContent.classList.add('hidden');
        elHintIcon.classList.remove('rotate-180');
      }

      elBtnBack.disabled = currentQuestionIndex === 0;
      elBtnNext.disabled = !hasAnswered;
      elBtnNext.textContent = (currentQuestionIndex === total - 1 && hasAnswered) ? 'View Analysis' : 'Next';
    }

    function handleSelect(selectedIndex, q) {
      if (userAnswers[q.id] !== undefined) return;
      
      const isCorrect = selectedIndex === q.correctAnswer;
      userAnswers[q.id] = { selectedOption: selectedIndex, isCorrect: isCorrect };

      if (isCorrect) score.correct++;
      else score.incorrect++;

      renderQuestion();
    }

    function toggleHint() {
      elHintContent.classList.toggle('hidden');
      elHintIcon.classList.toggle('rotate-180');
    }

    function goNext() {
      if (currentQuestionIndex < activeQueue.length - 1) {
        currentQuestionIndex++;
        renderQuestion();
      } else {
        showFinishScreen();
      }
    }

    function goBack() {
      if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        renderQuestion();
      }
    }

    function showFinishScreen() {
      elQuizArea.classList.add('hidden');
      elFinishArea.classList.remove('hidden');
      elFooterControls.classList.add('hidden');
      elAdaptWarning.classList.add('hidden');

      // Calculate stats
      const stats = {};
      const categories = new Set(questionBank.map(q => q.category));
      categories.forEach(c => stats[c] = { total: 0, correct: 0 });

      activeQueue.forEach(q => {
        const ans = userAnswers[q.id];
        if (ans) {
          stats[q.category].total++;
          if (ans.isCorrect) stats[q.category].correct++;
        }
      });

      elCatStats.innerHTML = '';
      let weakestCat = null;
      let weakestPct = 101;

      Object.keys(stats).forEach(cat => {
        if (stats[cat].total > 0) {
          const pct = Math.round((stats[cat].correct / stats[cat].total) * 100);
          if (pct < weakestPct) { weakestPct = pct; weakestCat = cat; }
          
          let color = pct >= 80 ? 'text-green-400 bg-green-500/10 border-green-500/20' : 
                      pct >= 50 ? 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20' : 
                      'text-red-400 bg-red-500/10 border-red-500/20';
          
          elCatStats.innerHTML += `
            <div class="p-4 border rounded-xl flex flex-col ${color}">
              <span class="text-sm font-semibold truncate" title="${cat}">${cat}</span>
              <span class="text-2xl font-bold">${pct}%</span>
              <span class="text-xs opacity-80">${stats[cat].correct} / ${stats[cat].total} correct</span>
            </div>
          `;
        }
      });

      // Populate dropdowns
      elAdaptCat.innerHTML = `<option value="All">All Categories</option>`;
      categories.forEach(c => {
        elAdaptCat.innerHTML += `<option value="${c}">${c}</option>`;
      });
      if (weakestCat) elAdaptCat.value = weakestCat;
    }

    function handleGenerateAdaptive() {
      const cat = elAdaptCat.value;
      const diff = elAdaptDiff.value;
      const count = parseInt(elAdaptCount.value) || 5;

      let pool = questionBank.filter(q => !usedIds.has(q.id));
      if (cat !== 'All') pool = pool.filter(q => q.category === cat);
      if (diff !== 'All') pool = pool.filter(q => q.difficulty === parseInt(diff));

      if (pool.length === 0) {
        let totalExist = questionBank.filter(q => {
           let match = true;
           if (cat !== 'All' && q.category !== cat) match = false;
           if (diff !== 'All' && q.difficulty !== parseInt(diff)) match = false;
           return match;
        }).length;
        
        if (totalExist === 0) {
           elAdaptWarning.textContent = "No questions exist in the bank with these exact criteria.";
        } else {
           elAdaptWarning.textContent = `Recycling pool: you answered all ${totalExist} questions for these criteria!`;
           questionBank.forEach(q => {
               if ((cat === 'All' || q.category === cat) && (diff === 'All' || q.difficulty === parseInt(diff))) {
                   usedIds.delete(q.id);
                   delete userAnswers[q.id]; // CRITICAL: Allows re-answering
               }
           });
           pool = questionBank.filter(q => !usedIds.has(q.id));
           if (cat !== 'All') pool = pool.filter(q => q.category === cat);
           if (diff !== 'All') pool = pool.filter(q => q.difficulty === parseInt(diff));
        }
        
        if (pool.length === 0) {
            elAdaptWarning.classList.remove('hidden');
            return;
        }
      }

      elAdaptWarning.classList.add('hidden');
      pool.sort(() => Math.random() - 0.5);
      const selected = pool.slice(0, count);
      
      activeQueue = selected;
      currentQuestionIndex = 0;
      selected.forEach(q => usedIds.add(q.id));
      
      renderQuestion();
    }

    initQuiz();
  </script>
</body>
</html>
```
