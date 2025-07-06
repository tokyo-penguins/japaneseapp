// --- quiz_type2_logic.js ---
console.log("受け取ったquestions:", questions);
console.log("クイズID:", quiz_id);
document.addEventListener("DOMContentLoaded", () => {
  const sentenceDiv = document.getElementById("sentence-container");
  const optionsDiv = document.getElementById("options-container");
  const questionNumber = document.getElementById("question-number");
  const feedbackDiv = document.getElementById("feedback");
  const explanationDiv = document.getElementById("explanations");
  const translationDiv = document.getElementById("translation");
  const finalBtn = document.getElementById("final-btn");
  const nextBtn = document.getElementById("next-btn");
  const tryAgainBtn = document.getElementById("try-again-btn");
  const backMenuBtn = document.getElementById("back-menu-btn");
  const menuBtn = document.getElementById("menu-btn");
  const incorrectPopup = document.getElementById("incorrect-popup");

  let current = 0;
  let selected = [];

    showQuestion(); 

  function showQuestion() {
    const q = questions[current];
    questionNumber.textContent = `Question ${current + 1} of ${questions.length}`;
    sentenceDiv.innerHTML = '';
    optionsDiv.innerHTML = '';
    feedbackDiv.style.display = 'none';
    explanationDiv.innerHTML = '';
    translationDiv.innerHTML = '';
    nextBtn.style.display = 'none';
    finalBtn.disabled = true;

    const fixedPosition = q.possiblePositions?.[0] - 1;

    for (let i = 0; i < q.answer.length; i++) {
      if (i === fixedPosition) {
        const fixed = document.createElement("div");
        fixed.className = "fixed-part";
        fixed.textContent = q.fixedPart || "";
        sentenceDiv.appendChild(fixed);
      }

      const w = selected[i];
      const span = document.createElement("div");
      span.className = w ? "word" : "blank";
      span.innerHTML = w ? toRuby(w, q.options.find(o => o.word === w)?.furigana) : "";
      if (w) {
        span.onclick = () => {
          selected.splice(i, 1);
          showQuestion();
        };
      }
      sentenceDiv.appendChild(span);
    }

    if (fixedPosition >= q.answer.length) {
      const fixed = document.createElement("div");
      fixed.className = "fixed-part";
      fixed.textContent = q.fixedPart || "";
      sentenceDiv.appendChild(fixed);
    }

    q.options.forEach(opt => {
      if (!selected.includes(opt.word)) {
        const div = document.createElement("div");
        div.className = "option";
        div.innerHTML = toRuby(opt.word, opt.furigana);
        div.onclick = () => {
          if (selected.length < q.answer.length) {
            selected.push(opt.word);
            showQuestion();
          }
        };
        optionsDiv.appendChild(div);
      }
    });

    finalBtn.disabled = selected.length !== q.answer.length;
  }

  function toRuby(word, furigana = "") {
    return furigana ? `<ruby>${word}<rt>${furigana}</rt></ruby>` : word;
  }

  finalBtn.onclick = () => {
    const q = questions[current];
    const isCorrect = JSON.stringify(selected) === JSON.stringify(q.answer);
    feedbackDiv.style.display = 'block';
    feedbackDiv.className = isCorrect ? "feedback correct" : "feedback incorrect";
    feedbackDiv.textContent = isCorrect ? "Correct!" : "Incorrect";

    explanationDiv.innerHTML = "<strong>Words:</strong><br>" +
      (q.options || []).map(o => `${o.word}: ${o.meaning || ""}`).join("<br>");
    translationDiv.textContent = "Full Translation: " + (q.translation || "");
    finalBtn.disabled = true;

    if (isCorrect) {
      confetti();
      if (current < questions.length - 1) {
        nextBtn.style.display = "inline-block";
        nextBtn.onclick = () => {
          current++;
          selected = [];
          showQuestion();
        };
      } else {
        nextBtn.style.display = "inline-block";
        nextBtn.textContent = "Next";
        nextBtn.onclick = () => {
          if (quiz_id) {
            fetch(`/complete_quiz/${quiz_id}`, { method: 'POST' });
            const parts = quiz_id.split('-');
            const nextQuizId = `${parts[0]}-${parseInt(parts[1]) + 1}`;
            window.location.href = `/${nextQuizId}`;
          } else {
            console.error("quiz_idが存在しません！");
          }
        };
      }
    } else {
      setTimeout(() => {
        incorrectPopup.style.display = "block";
      }, 300);
    }
  };

  tryAgainBtn.onclick = () => {
    incorrectPopup.style.display = "none";
    selected = [];
    showQuestion();
  };

  backMenuBtn.onclick = menuBtn.onclick = () => {
    if (quiz_id) {
      const level = quiz_id.split('-')[0];
      window.location.href = `/${level}`;
    } else {
      window.location.href = "/";
    }
  };
});
