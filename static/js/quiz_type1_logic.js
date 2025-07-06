document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded");
    console.log("Question element:", document.getElementById("question"));
    console.log("Options container:", document.getElementById("options"));
});

console.log("読み込まれたquestions:", questions);

// もしquestionsが存在しないか、形式がおかしかったら停止
if (!Array.isArray(questions)) {
    console.error("questionsが正しくロードされていません。");
    throw new Error("questionsが正しくロードされていません。");
}

// 初期変数
let currentQuestionIndex = 0;
let score = 0;
let wrongAnswersCount = 0;
let selected = false;
let shuffledQuestions = [];

// クイズ初期化
function initQuiz() {
    shuffleQuestions();
    currentQuestionIndex = 0;
    score = 0;
    loadQuestion();
}

// クイズ・選択肢をシャッフル
function shuffleQuestions() {
    shuffledQuestions = [...questions];
    for (let i = shuffledQuestions.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffledQuestions[i], shuffledQuestions[j]] = [shuffledQuestions[j], shuffledQuestions[i]];
    }
    shuffledQuestions.forEach(q => {
        for (let i = q.options.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [q.options[i], q.options[j]] = [q.options[j], q.options[i]];
        }
    });
}

// 問題を読み込み
function loadQuestion() {
    selected = false;
    const questionData = shuffledQuestions[currentQuestionIndex];

    document.getElementById("question").innerText = questionData.question || "";
    document.getElementById("question-counter").innerText = 
        `Question ${currentQuestionIndex + 1} of ${shuffledQuestions.length}`;

    const imgElement = document.getElementById("question-img");
    if (questionData.image) {
        imgElement.src = questionData.image;
        imgElement.style.display = "block";
    } else {
        imgElement.style.display = "none";
    }

    document.getElementById("hintBox").innerHTML = questionData.hint || "";
    document.getElementById("hintBox").style.display = "none";
    document.getElementById("hintBtn").innerHTML = "<span>💡</span> Show Hint";

    document.getElementById("explanationBox").style.display = "none";

    let optionsHtml = "";
    if (Array.isArray(questionData.options)) {
        questionData.options.forEach(option => {
            optionsHtml += `<button class='option' onclick='checkAnswer(this, "${option.replace(/"/g, '\\"')}")'>${option}</button>`;
        });
    }
    document.getElementById("options").innerHTML = optionsHtml;

    document.querySelector('.next-btn').style.display = 'none';
    document.getElementById("results-container").style.display = "none";
}

// 答えをチェック
function checkAnswer(btn, selectedOption) {
    selected = true;
    const correctAnswer = shuffledQuestions[currentQuestionIndex].answer;
    const explanationBox = document.getElementById("explanationBox");

    document.querySelectorAll(".option").forEach(button => button.disabled = true);

    if (selectedOption === correctAnswer) {
        btn.classList.add("correct");
        score++;
        showCracker();
        triggerConfetti();
        explanationBox.innerHTML = shuffledQuestions[currentQuestionIndex].explanation?.correct || "";
        explanationBox.style.display = "block";

        const nextBtn = document.querySelector('.next-btn');
        nextBtn.style.display = 'block';
        nextBtn.style.animation = 'popIn 0.5s forwards';
    } else {
        btn.classList.add("incorrect");
        wrongAnswersCount++;
        showBooingHands();

        document.querySelectorAll(".option").forEach(button => {
            if (button.textContent === correctAnswer) {
                button.classList.add("correct");
            }
        });

        explanationBox.innerHTML = shuffledQuestions[currentQuestionIndex].explanation?.incorrect || "";
        explanationBox.style.display = "block";

        const nextBtn = document.querySelector('.next-btn');
        nextBtn.style.display = 'block';
        nextBtn.style.animation = 'popIn 0.5s forwards';
    }
}

// ヒントボタン
document.getElementById("hintBtn").addEventListener("click", function() {
    const hintBox = document.getElementById("hintBox");
    if (hintBox.style.display === "block") {
        hintBox.style.display = "none";
        this.innerHTML = "<span>💡</span> Show Hint";
    } else {
        hintBox.style.display = "block";
        this.innerHTML = "<span>🔍</span> Hide Hint";
    }
});

// 次の問題へ
function nextQuestion() {
    if (!selected) {
        alert("Please select an answer before continuing!");
        return;
    }

    currentQuestionIndex++;

    if (currentQuestionIndex < shuffledQuestions.length) {
        loadQuestion();
    } else {
        showResults();
    }
}

// リザルト表示
function showResults() {
    const resultsContainer = document.getElementById("results-container");
    const resultMessage = document.getElementById("result-message");
    const resultLink = document.getElementById("result-link");

    document.querySelector('.next-btn').style.display = 'none';

    if (score === shuffledQuestions.length) {
        resultMessage.innerHTML = '<div class="trophy">🏆</div>Perfect score! You\'re talented!';
        resultLink.textContent = 'Continue to Next Quiz';
        resultLink.href = `/${quizLevel}-${quizNum + 1}`;

        fetch(`/complete_quiz/${quizLevel}-${quizNum}`, { method: 'POST' });

        triggerConfetti();
        setTimeout(triggerConfetti, 500);
        setTimeout(triggerConfetti, 1000);
        setTimeout(triggerConfetti, 1500);
    } else if (score >= shuffledQuestions.length * 0.7) {
        resultMessage.textContent = 'Great job! You\'re almost there!';
        resultLink.textContent = 'Review Mistakes';
        resultLink.href = '#review';

        document.getElementById("retryNotification").style.display = "block";
        triggerConfetti();
    } else {
        resultMessage.textContent = 'Keep practicing!';
        resultLink.textContent = 'Try Again';
        resultLink.onclick = function() { retryQuiz(); return false; };

        document.getElementById("retryNotification").style.display = "block";
    }

    resultsContainer.style.display = 'block';
    resultsContainer.style.animation = 'popIn 0.5s forwards';
}

// リトライ
function retryQuiz() {
    document.getElementById("retryNotification").style.display = "none";
    currentQuestionIndex = 0;
    score = 0;
    wrongAnswersCount = 0;
    selected = false;
    document.querySelector('.next-btn').style.display = 'none';
    shuffleQuestions();
    loadQuestion();
}

// 紙吹雪
function showCracker() {
    confetti({
        particleCount: 150,
        spread: 100,
        origin: { x: 0.5, y: 0.5 },
        colors: ['#ff0', '#f00', '#0f0', '#00f', '#ff69b4'],
        scalar: 1.2,
        ticks: 200
    });
}

// ブーイング手
function showBooingHands() {
    const container = document.createElement('div');
    container.className = 'booing-container';
    document.body.appendChild(container);

    for (let i = 0; i < Math.min(wrongAnswersCount, 10); i++) {
        setTimeout(() => {
            const hands = document.createElement('div');
            hands.className = 'booing-hands';
            hands.innerHTML = '👎';
            hands.style.left = `calc(50% + ${(Math.random() * 200 - 100)}px)`;
            container.appendChild(hands);

            setTimeout(() => {
                hands.remove();
            }, 2000);
        }, i * 150);
    }

    setTimeout(() => {
        container.remove();
    }, Math.min(wrongAnswersCount, 10) * 150 + 2000);
}

// 紙吹雪（花火風）
function triggerConfetti() {
    confetti({
        particleCount: 100,
        angle: 60,
        spread: 80,
        origin: { x: 0 },
        colors: ['#ff0000', '#ff7700', '#ffff00']
    });

    confetti({
        particleCount: 100,
        angle: 120,
        spread: 80,
        origin: { x: 1 },
        colors: ['#00ff00', '#00ffff', '#0000ff']
    });

    confetti({
        particleCount: 200,
        spread: 120,
        origin: { y: 0.4 },
        colors: ['#ff0000', '#ffff00', '#00ff00', '#00ffff', '#0000ff', '#ff00ff'],
        shapes: ['circle', 'square'],
        scalar: 1.5
    });
}

// リトライボタンイベント
document.querySelector('.retry-home').addEventListener('click', function() {
    window.location.href = `/${quizLevel}`;
});

document.querySelector('.retry-again').addEventListener('click', retryQuiz);

// スタート！
initQuiz();