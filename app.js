const BACKEND_URL = 'http://localhost:5000'; // Default local backend
const SUPABASE_URL = 'https://oxtzjfuevsmparfzriwe.supabase.co';
const SITE_URL = window.location.origin; // Automatically sets the correct site URL
const SUPABASE_ANON_KEY = 'sb_publishable_XBptvECOL0hhP5UCI4yqFw_KI5l_VC7';
let supabaseClient = null;
if (window.supabase) {
    supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
} else {
    console.error("Supabase failed to load! Auth won't work.");
}
// State Management
const state = {
    user: null, // { name, email, college, batch, phone }
    mode: null, // 'study', 'exam'
    currentSubject: 'all',
    currentYear: 'all',
    currentExamYear: '',
    currentExamPaper: '',
    currentUnit: '',
    currentLimit: 'all',
    isCustomQBank: false,
    customSubjects: [],
    superRevisionSubjects: [],

    questions: [], // The filtered set of questions to show
    currentIndex: 0,
    answers: {}, // index -> string ('a', 'b', 'c', 'd')
    showExplanation: false,
    bookmarks: JSON.parse(localStorage.getItem('upsccms_bookmarks')) || [],
    wrongCounts: JSON.parse(localStorage.getItem('upsccms_wrongCounts')) || {},
    isDarkMode: JSON.parse(localStorage.getItem('upsccms_darkMode')) || false,
    soundEnabled: JSON.parse(localStorage.getItem('upsccms_soundEnabled')) !== false,
    timerInterval: null,
    timerSeconds: 0,
    isPremium: false,
    questionsAttempted: parseInt(localStorage.getItem('upsccms_attempts')) || 0
};

// Audio Assets
const audioElements = {
    correct: new Audio('correct.mp3'),
    wrong: new Audio('wrong.mp3')
};

function playSound(type) {
    if (!state.soundEnabled) return;
    if (state.mode === 'exam') return; // Silence for suspense in test mode!
    try {
        const sound = audioElements[type];
        if (sound) {
            sound.currentTime = 0;
            sound.play();

            // Crop the cheer sound to be short and punchy
            if (type === 'correct') {
                setTimeout(() => {
                    sound.pause();
                    sound.currentTime = 0;
                }, 2500);
            }
        }
    } catch (e) {
        console.warn("Sound playback prevented by browser.");
    }
}

// Elements
const el = {
    screens: {},
    auth: {},
    start: {},
    quiz: {},
    flashcard: {}, // Kept empty for safety
    score: {},
    paywall: {
        modal: document.getElementById('paywallModal'),
        btnUpgradeUPSC2026: document.getElementById('btnUpgradeUPSC2026'),
        btnDashboardUpgrade: document.getElementById('btnDashboardUpgrade'),
        btnCancel: document.getElementById('btnCancelPaywall')
    },
    customQBank: {
        modal: document.getElementById('customQBankModal'),
        subjectChips: document.getElementById('customSubjectChips'),
        limitInput: document.getElementById('customLimitInput'),
        timerInput: document.getElementById('customTimerInput'),
        btnCancel: document.getElementById('btnCancelCustomQBank'),
        btnStart: document.getElementById('btnStartCustomQBank')
    },
    examMode: {
        modal: document.getElementById('examModeModal'),
        yearSelect: document.getElementById('examYearSelect'),
        paperSelect: document.getElementById('examPaperSelect'),
        btnCancel: document.getElementById('btnCancelExamMode'),
        btnStart: document.getElementById('btnStartExamNow')
    },
    superRevision: {
        modal: document.getElementById('superRevisionModal'),
        subjectChips: document.getElementById('superSubjectChips'),
        btnCancel: document.getElementById('btnCancelSuperRevision'),
        btnStart: document.getElementById('btnStartSuperRevision')
    },
    toast: document.getElementById('toast')
};

// Utils
function showToast(msg) {
    if (!el.toast) {
        console.warn("Toast missing, showing alert:", msg);
        // alert(msg); // Optional: add alert as fallback
        return;
    }
    el.toast.textContent = msg;
    el.toast.classList.remove('hidden');
    setTimeout(() => {
        el.toast.classList.add('hidden');
    }, 3000);
}

function updatePremiumUI() {
    if (state.isPremium) {
        document.body.classList.add('premium-user');
    } else {
        document.body.classList.remove('premium-user');
    }
}

function switchScreen(screenName) {
    console.log(`Switching to screen: ${screenName}`); // Debug log
    Object.values(el.screens).forEach(s => {
        if (s && s.classList) s.classList.add('hidden');
    });

    const target = el.screens[screenName];
    if (target && target.classList) {
        target.classList.remove('hidden');
        window.scrollTo(0, 0);
    } else {
        console.error(`Screen "${screenName}" not found or has no classList!`, target);
    }

    // Refresh AdSense ads on screen change if not premium
    if (!state.isPremium && window.adsbygoogle) {
        try {
            (adsbygoogle = window.adsbygoogle || []).push({});
        } catch (e) {
            console.error("AdSense error:", e);
        }
    }

    // Re-bind critical listeners when screens are activated to ensure responsiveness
    if (screenName === 'quiz') {
        el.quiz.btnEnd = document.getElementById('btnEndQuiz');
        setupQuizListeners();
    } else if (screenName === 'score') {
        el.score.btnDashboard = document.getElementById('btnBackToDashboard');
        setupScoreListeners();
    }
}

// Bookmark Handlers
function toggleBookmark(qText, silent = false) {
    const index = state.bookmarks.indexOf(qText);
    if (index === -1) {
        state.bookmarks.push(qText);
        if (!silent) showToast("Added to Bookmarks ⭐");
    } else {
        state.bookmarks.splice(index, 1);
        if (!silent) showToast("Removed from Bookmarks ☆");
    }
    localStorage.setItem('upsccms_bookmarks', JSON.stringify(state.bookmarks));
    syncUserData();
    updateBookmarkUI();
}

async function syncUserData() {
    if (!state.user) return;
    try {
        await supabaseClient.from('profiles').update({
            bookmarks: state.bookmarks,
            wrong_counts: state.wrongCounts,
            questions_attempted: state.questionsAttempted
        }).eq('id', state.user.id);
    } catch (e) {
        console.error("Error syncing user data:", e);
    }
}

function updateBookmarkUI() {
    if (!state.questions[state.currentIndex]) return;
    const currentQText = state.questions[state.currentIndex].question;
    const isBookmarked = state.bookmarks.includes(currentQText);

    if (state.mode === 'flashcards') {
        // Flashcard UI elements are no longer directly managed here
        // This block might need to be removed or adapted if flashcards are completely gone
        // For now, keeping it as is, assuming 'flashcards' mode might still exist conceptually
        // but without direct element assignments in `el.flashcard`.
        // If flashcards are fully removed, this 'if' block should be removed.
    } else {
        el.quiz.btnBookmark.textContent = isBookmarked ? '⭐' : '☆';
        el.quiz.btnBookmark.classList.toggle('active', isBookmarked);
    }
}

// Wrong Count Handlers
function incrementWrongCount(qText) {
    if (!state.wrongCounts[qText]) {
        state.wrongCounts[qText] = 0;
    }
    state.wrongCounts[qText]++;
    localStorage.setItem('upsccms_wrongCounts', JSON.stringify(state.wrongCounts));
    syncUserData();
}

// Refresh/Load DOM Elements
function refreshElements() {
    el.screens.auth = document.getElementById('authScreen');
    el.screens.start = document.getElementById('startScreen');
    el.screens.quiz = document.getElementById('quizScreen');
    el.screens.score = document.getElementById('scoreScreen');

    el.auth.tabs = document.querySelectorAll('.tab-btn');
    el.auth.loginForm = document.getElementById('loginForm');
    el.auth.regForm = document.getElementById('registerForm');
    el.auth.forgotForm = document.getElementById('forgotPasswordForm');
    el.auth.resetForm = document.getElementById('resetPasswordForm');
    el.auth.forgotLink = document.getElementById('forgotPasswordLink');
    el.auth.backToLoginBtn = document.getElementById('backToLoginBtn');
    el.auth.headerUser = document.getElementById('headerUser');
    el.auth.userNameDisplay = document.getElementById('userNameDisplay');
    el.auth.logoutBtn = document.getElementById('logoutBtn');

    el.start.moduleTabs = document.querySelectorAll('.module-tab');
    el.start.pyqConfig = document.getElementById('pyqConfig');
    el.start.subjectChips = document.getElementById('subjectChips');
    el.start.chapterSelect = document.getElementById('chapterSelect');
    el.start.yearSelect = document.getElementById('yearSelect');
    el.start.unitInput = document.getElementById('unitInput');
    el.start.limitSelect = document.getElementById('limitSelect');
    el.start.timerInput = document.getElementById('timerInput');
    el.start.toggleDarkMode = document.getElementById('toggleDarkMode');
    el.start.toggleSound = document.getElementById('toggleSound');
    el.start.btnStudy = document.getElementById('btnStudyMode');
    el.start.btnExam = document.getElementById('btnExamMode');
    el.start.btnBookmarks = document.getElementById('btnReviewBookmarks');
    el.start.btnSuperRevision = document.getElementById('btnSuperRevision');
    el.start.btnCustomQBank = document.getElementById('btnCustomQBank');

    el.quiz.progress = document.getElementById('quizProgress');
    el.quiz.btnBookmark = document.getElementById('btnBookmarkQuiz');
    el.quiz.timerDisplay = document.getElementById('quizTimerDisplay');
    el.quiz.timerText = document.getElementById('quizTimerText');
    el.quiz.qCurrent = document.getElementById('qCurrent');
    el.quiz.qTotal = document.getElementById('qTotal');
    el.quiz.qSubject = document.getElementById('qSubject');
    el.quiz.qText = document.getElementById('qText');
    el.quiz.qImage = document.getElementById('qImage');
    el.quiz.qOptions = document.getElementById('qOptions');
    el.quiz.qExplanation = document.getElementById('qExplanation');
    el.quiz.expText = document.getElementById('expText');
    el.quiz.expImage = document.getElementById('expImage');
    el.quiz.btnPrev = document.getElementById('btnPrev');
    el.quiz.btnNext = document.getElementById('btnNext');
    el.quiz.btnEnd = document.getElementById('btnEndQuiz');

    el.score.percentage = document.getElementById('scorePercentage');
    el.score.circle = document.getElementById('scoreCircle');
    el.score.correct = document.getElementById('scoreCorrect');
    el.score.wrong = document.getElementById('scoreWrong');
    el.score.unanswered = document.getElementById('scoreUnanswered');
    el.score.btnReview = document.getElementById('btnReviewAnswers');
    el.score.btnDashboard = document.getElementById('btnBackToDashboard');

    // Paywall elements
    el.paywall.modal = document.getElementById('paywallModal');
    el.paywall.btnUpgradeUPSC2026 = document.getElementById('btnUpgradeUPSC2026');
    el.paywall.btnCancel = document.getElementById('btnCancelPaywall');

    el.examMode.modal = document.getElementById('examModeModal');
    el.examMode.yearSelect = document.getElementById('examYearSelect');
    el.examMode.paperSelect = document.getElementById('examPaperSelect');
    el.examMode.btnCancel = document.getElementById('btnCancelExamMode');
    el.examMode.btnStart = document.getElementById('btnStartExamNow');
}

// Initial Setup
async function initApp() {
    try {
        console.log("Initializing App...");
        refreshElements();

        // Normalize mcqData subjects to Title Case to prevent filtering inconsistencies
        const toTitleCase = (str) => {
            if (!str) return str;
            return str.toLowerCase().split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
                .replace('&', '&') // Keep ampersands if needed, or normalize to "and"
                .replace('And', 'and'); // Common normalization
        };

        // No longer mutating q.subject in-place to avoid filtering issues for combined subjects

        // DATA QUALITY GUARDRAIL: Filter out bad questions before they reach the dashboard
        const originalCount = (typeof mcqData !== 'undefined') ? mcqData.length : 0;
        window.allQuestions = ((typeof mcqData !== 'undefined') ? mcqData : []).filter(q => {
            const hasOptions = q.options && Object.keys(q.options).length === 4;
            const hasAnswer = q.answer && q.answer.trim().length > 0;
            const hasValidQuestion = q.question && q.question.trim().length > 10;
            const isCancelled = (q.question || '').toLowerCase().includes('cancelled');
            
            return hasOptions && hasAnswer && hasValidQuestion && !isCancelled;
        });
        console.log(`Guardrail active: Kept ${window.allQuestions.length}/${originalCount} high-quality questions.`);

        applyDarkMode(state.isDarkMode);

        setupAuthListeners();
        setupDashboardListeners();
        setupQuizListeners();
        setupScoreListeners();
        // setupReadingListeners(); // Reading logic removed

        console.log("All listeners setup successfully.");
    } catch (err) {
        console.error("Critical Error during listener setup:", err);
    }

    // Global Auth State Change for Password Recovery
    supabaseClient.auth.onAuthStateChange((event, session) => {
        if (event === 'PASSWORD_RECOVERY') {
            switchScreen('auth');
            el.auth.loginForm.classList.add('hidden');
            el.auth.regForm.classList.add('hidden');
            el.auth.forgotForm.classList.add('hidden');
            el.auth.resetForm.classList.remove('hidden');
            el.auth.tabs.forEach(b => b.classList.add('hidden')); // hide tabs during reset
            showToast("Please enter your new password.", 5000);
        }
    });

    // Check Supabase session
    if (supabaseClient) {
        try {
            const { data: { session } } = await supabaseClient.auth.getSession();
            if (session) {
                state.user = session.user;
                await fetchProfile();
                updateHeaderAuth();
                initDashboard();
                switchScreen('start');
                
            }
        } catch (e) {
            console.error("Supabase session check error:", e);
        }
    } else {
        showToast("Warning: Supabase not found. You are in offline mode.", 5000);
    }
}

async function fetchProfile() {
    if (!state.user) return;
    try {
        const { data, error } = await supabaseClient
            .from('profiles')
            .select('is_premium, questions_attempted, full_name, college, batch_year, phone, bookmarks, wrong_counts')
            .eq('id', state.user.id)
            .single();

        if (error) throw error;

        if (data) {
            state.isPremium = data.is_premium || false;
            updatePremiumUI();
            state.questionsAttempted = data.questions_attempted || 0;

            // Populate state with retrieved profile data
            state.user.full_name = data.full_name;
            state.user.college = data.college;
            state.user.batch_year = data.batch_year;
            state.user.phone = data.phone;

            // Sync bookmarks and wrong counts if available and newer than local
            if (data.bookmarks) {
                state.bookmarks = data.bookmarks;
                localStorage.setItem('upsccms_bookmarks', JSON.stringify(state.bookmarks));
            }
            if (data.wrong_counts) {
                state.wrongCounts = data.wrong_counts;
                localStorage.setItem('upsccms_wrongCounts', JSON.stringify(state.wrongCounts));
            }

            // Set name for display
            state.user.name = data.full_name || state.user.email;

            // Toggle body class for ad hiding
            if (state.isPremium) {
                document.body.classList.add('premium-user');
            } else {
                document.body.classList.remove('premium-user');
            }
        }
    } catch (e) {
        console.error('Error fetching profile:', e);
    }
}

// Auth Handlers
function setupAuthListeners() {
    if (el.auth.tabs) {
        el.auth.tabs.forEach((btn) => {
            btn.addEventListener('click', (e) => {
                const tabBtn = e.currentTarget;
                el.auth.tabs.forEach(b => b.classList.remove('active'));
                tabBtn.classList.add('active');

                if (tabBtn.dataset.tab === 'login') {
                    el.auth.loginForm.classList.remove('hidden');
                    el.auth.regForm.classList.add('hidden');
                } else {
                    el.auth.loginForm.classList.add('hidden');
                    el.auth.regForm.classList.remove('hidden');
                }
                el.auth.forgotForm.classList.add('hidden');
                el.auth.resetForm.classList.add('hidden');
            });
        });
    }

    if (el.auth.forgotLink) {
        el.auth.forgotLink.addEventListener('click', (e) => {
            e.preventDefault();
            el.auth.loginForm.classList.add('hidden');
            el.auth.regForm.classList.add('hidden');
            el.auth.forgotForm.classList.remove('hidden');
        });
    }

    if (el.auth.backToLoginBtn) {
        el.auth.backToLoginBtn.addEventListener('click', () => {
            el.auth.forgotForm.classList.add('hidden');
            el.auth.loginForm.classList.remove('hidden');
            if (el.auth.tabs[0]) el.auth.tabs[0].click(); // Activate login tab
        });
    }

    if (el.auth.loginForm) {
        el.auth.loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            const submitBtn = document.getElementById('loginSubmitBtn');

            if (submitBtn) {
                submitBtn.textContent = 'Logging in...';
                submitBtn.disabled = true;
            }

            const { data, error } = await supabaseClient.auth.signInWithPassword({
                email: email,
                password: password,
            });

            if (submitBtn) {
                submitBtn.textContent = 'Login';
                submitBtn.disabled = false;
            }

            if (error) {
                showToast(error.message);
            } else {
                state.user = data.user;
                await fetchProfile();
                updateHeaderAuth();
                initDashboard();
                switchScreen('start');
                showToast('Welcome back!');
            }
        });
    }

    if (el.auth.regForm) {
        el.auth.regForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('regName').value;
            const email = document.getElementById('regEmail').value;
            const password = document.getElementById('regPassword').value;
            const college = document.getElementById('regCollege').value;
            const batch = document.getElementById('regBatch').value;
            const phone = document.getElementById('regPhone').value;
            const submitBtn = document.getElementById('regSubmitBtn');

            if (submitBtn) {
                submitBtn.textContent = 'Registering...';
                submitBtn.disabled = true;
            }

            const { data, error } = await supabaseClient.auth.signUp({
                email: email,
                password: password,
                options: {
                    emailRedirectTo: SITE_URL,
                    data: {
                        full_name: name,
                        college: college,
                        batch_year: batch,
                        phone: phone
                    }
                }
            });

            if (submitBtn) {
                submitBtn.textContent = 'Register';
                submitBtn.disabled = false;
            }

            if (error) {
                if (error.message.toLowerCase().includes('confirmation email')) {
                    showToast("Account created, but there was an error sending the confirmation email. Please try logging in or check your dashboard settings.", 7000);
                    console.error("Supabase Email Error: Ensure 'Confirm email' is OFF in your Supabase Auth settings if you don't have an SMTP provider configured.");
                } else {
                    showToast(error.message);
                }
            } else if (data.user) {
                state.user = data.user;

                // Explicitly sync profile data to the profiles table
                try {
                    await supabaseClient.from('profiles').update({
                        full_name: name,
                        college: college,
                        batch_year: batch,
                        phone: phone
                    }).eq('id', data.user.id);
                } catch (err) {
                    console.error("Error explicitly syncing profile:", err);
                }

                await fetchProfile();
                updateHeaderAuth();
                initDashboard();
                switchScreen('start');
                showToast('Registration successful!');
            } else {
                showToast("Registration pending. Please check your email for a confirmation link.");
            }
        });
    }

    if (el.auth.forgotForm) {
        el.auth.forgotForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('forgotEmail').value;
            const submitBtn = document.getElementById('forgotSubmitBtn');

            if (submitBtn) {
                submitBtn.textContent = 'Sending...';
                submitBtn.disabled = true;
            }

            const { data, error } = await supabaseClient.auth.resetPasswordForEmail(email, {
                redirectTo: SITE_URL,
            });

            if (submitBtn) {
                submitBtn.textContent = 'Send Reset Link';
                submitBtn.disabled = false;
            }

            if (error) {
                showToast(error.message);
            } else {
                showToast("Password reset link sent to your email!");
                if (el.auth.backToLoginBtn) el.auth.backToLoginBtn.click();
            }
        });
    }

    if (el.auth.resetForm) {
        el.auth.resetForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const newPassword = document.getElementById('newPassword').value;
            const submitBtn = document.getElementById('resetSubmitBtn');

            if (submitBtn) {
                submitBtn.textContent = 'Updating...';
                submitBtn.disabled = true;
            }

            const { data, error } = await supabaseClient.auth.updateUser({
                password: newPassword
            });

            if (submitBtn) {
                submitBtn.textContent = 'Update Password';
                submitBtn.disabled = false;
            }

            if (error) {
                showToast(error.message);
            } else {
                showToast("Password updated successfully! Please login.");
                el.auth.resetForm.classList.add('hidden');
                el.auth.loginForm.classList.remove('hidden');
                el.auth.tabs.forEach(b => b.classList.remove('hidden')); // restore tabs
            }
        });
    }

    if (el.auth.logoutBtn) {
        el.auth.logoutBtn.addEventListener('click', async () => {
            await supabaseClient.auth.signOut();
            
            // Clear local user data on logout
            localStorage.removeItem('upsccms_bookmarks');
            localStorage.removeItem('upsccms_wrongCounts');
            localStorage.removeItem('upsccms_attempts');
            
            state.user = null;
            state.isPremium = false;
            state.questionsAttempted = 0;
            state.bookmarks = [];
            state.wrongCounts = {};
            
            updateHeaderAuth();
            switchScreen('auth');
        });
    }
}

function updateHeaderAuth() {
    if (state.user) {
        el.auth.userNameDisplay.textContent = state.user.name || state.user.email || 'User';
        el.auth.headerUser.classList.remove('hidden');

        // Remove auth mock notice if it exists
        const mockNotice = document.querySelector('.auth-mock-notice');
        if (mockNotice) mockNotice.remove();
    } else {
        el.auth.headerUser.classList.add('hidden');
    }
}

function initDashboard() {
    console.log("initDashboard starting...");
    const MEDICAL_SUBJECTS = ['Medicine', 'Surgery', 'PSM', 'OBGYN', 'Pediatrics', 'Orthopaedics', 'Psychiatry'];
    const subjectsSet = new Set();
    const years = new Set();
    
    if (typeof allQuestions === 'undefined' || !Array.isArray(allQuestions)) {
        console.error("CRITICAL: questions data NOT FOUND during dashboard init!");
        showToast("Error: Questions data failed to load. Please refresh.", 10000);
        return;
    }

    allQuestions.forEach(q => {
        const rawSubject = q.subject || (q.tags && q.tags[0]) || '';
        const cleaned = cleanSubject(rawSubject);
        if (MEDICAL_SUBJECTS.includes(cleaned)) subjectsSet.add(cleaned);
        if (q.year) years.add(q.year.toString());
    });

    const subjectsList = MEDICAL_SUBJECTS.filter(s => subjectsSet.has(s));
    console.log("Subjects found in data:", subjectsList);

    // Populate Chips
    if (el.start.subjectChips) {
        el.start.subjectChips.innerHTML = '';
        
        // Add "All Subjects" chip
        const allChip = document.createElement('div');
        allChip.className = 'chip active';
        allChip.textContent = 'All Subjects';
        allChip.addEventListener('click', () => {
            el.start.subjectChips.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
            allChip.classList.add('active');
            state.currentSubject = 'all';
            console.log("Selected All Subjects");
        });
        el.start.subjectChips.appendChild(allChip);

        subjectsList.forEach(sub => {
            const chip = document.createElement('div');
            chip.className = 'chip';
            chip.textContent = sub;
            chip.addEventListener('click', () => {
                el.start.subjectChips.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                state.currentSubject = sub;
                console.log("Selected Subject:", sub);
            });
            el.start.subjectChips.appendChild(chip);
        });
    }

    el.start.yearSelect.innerHTML = '<option value="all">All Years</option>';
    Array.from(years).sort().reverse().forEach(y => {
        const opt = document.createElement('option');
        opt.value = y;
        opt.textContent = y;
        el.start.yearSelect.appendChild(opt);

        // Also for Exam Mode
        const examOpt = opt.cloneNode(true);
        el.examMode.yearSelect.appendChild(examOpt);
    });

    initCustomQBankDashboard(subjectsList);
    initSuperRevisionDashboard(subjectsList);
}

function initSuperRevisionDashboard(subjects) {
    el.superRevision.subjectChips.innerHTML = '';
    subjects.forEach(sub => {
        const chip = document.createElement('div');
        chip.className = 'chip';
        chip.textContent = sub;
        chip.addEventListener('click', () => {
            const index = state.superRevisionSubjects.indexOf(sub);
            if (index === -1) {
                state.superRevisionSubjects.push(sub);
                chip.classList.add('multi-selected');
            } else {
                state.superRevisionSubjects.splice(index, 1);
                chip.classList.remove('multi-selected');
            }
        });
        el.superRevision.subjectChips.appendChild(chip);
    });
}

function initCustomQBankDashboard(subjects) {
    el.customQBank.subjectChips.innerHTML = '';
    subjects.forEach(sub => {
        const chip = document.createElement('div');
        chip.className = 'chip';
        chip.textContent = sub;
        chip.addEventListener('click', () => {
            const index = state.customSubjects.indexOf(sub);
            if (index === -1) {
                state.customSubjects.push(sub);
                chip.classList.add('multi-selected');
            } else {
                state.customSubjects.splice(index, 1);
                chip.classList.remove('multi-selected');
            }
        });
        el.customQBank.subjectChips.appendChild(chip);
    });
}

// Module setup removed

// updateRRChapters removed



function setupDashboardListeners() {
    if (el.start.btnStudy) el.start.btnStudy.addEventListener('click', () => startMode('study'));
    if (el.start.btnExam) {
        el.start.btnExam.addEventListener('click', () => {
            el.examMode.modal.classList.remove('hidden');
        });
    }
    if (el.start.btnBookmarks) el.start.btnBookmarks.addEventListener('click', () => startMode('bookmarks_review'));

    // Exam Mode Modal Listeners
    if (el.examMode.btnCancel) {
        el.examMode.btnCancel.addEventListener('click', () => {
            el.examMode.modal.classList.add('hidden');
        });
    }

    if (el.examMode.btnStart) {
        el.examMode.btnStart.addEventListener('click', () => {
            state.currentExamYear = el.examMode.yearSelect.value;
            state.currentExamPaper = el.examMode.paperSelect.value;
            el.examMode.modal.classList.add('hidden');
            startMode('exam');
        });
    }
    if (el.start.btnSuperRevision) {
        el.start.btnSuperRevision.addEventListener('click', () => {
            el.superRevision.modal.classList.remove('hidden');
        });
    }

    // Super Revision Modal Listeners
    if (el.superRevision.btnCancel) {
        el.superRevision.btnCancel.addEventListener('click', () => {
            el.superRevision.modal.classList.add('hidden');
        });
    }

    if (el.superRevision.btnStart) {
        el.superRevision.btnStart.addEventListener('click', () => {
            if (state.superRevisionSubjects.length === 0) {
                showToast("Please select at least one subject!");
                return;
            }
            startMode('super_revision');
        });
    }

    // btnReading removed
    if (el.start.btnCustomQBank) {
        el.start.btnCustomQBank.addEventListener('click', () => {
            el.customQBank.modal.classList.remove('hidden');
        });
    }

    if (el.customQBank.btnCancel) {
        el.customQBank.btnCancel.addEventListener('click', () => {
            el.customQBank.modal.classList.add('hidden');
        });
    }

    if (el.customQBank.btnStart) {
        el.customQBank.btnStart.addEventListener('click', () => {
            if (state.customSubjects.length === 0) {
                showToast("Please select at least one subject!");
                return;
            }
            startMode('custom_qbank');
        });
    }

    // chapterSelect removed

    if (el.start.yearSelect) {
        el.start.yearSelect.addEventListener('change', (e) => {
            state.currentYear = e.target.value;
        });
    }

    if (el.start.unitInput) {
        el.start.unitInput.addEventListener('input', (e) => {
            state.currentUnit = e.target.value.toLowerCase().trim();
        });
    }

    if (el.start.limitSelect) {
        el.start.limitSelect.addEventListener('change', (e) => {
            state.currentLimit = e.target.value;
        });
    }

    if (el.start.toggleDarkMode) {
        el.start.toggleDarkMode.checked = state.isDarkMode;
        el.start.toggleDarkMode.addEventListener('change', (e) => {
            state.isDarkMode = e.target.checked;
            localStorage.setItem('upsccms_darkMode', JSON.stringify(state.isDarkMode));
            applyDarkMode(state.isDarkMode);
        });
    }

    if (el.start.toggleSound) {
        el.start.toggleSound.checked = state.soundEnabled;
        el.start.toggleSound.addEventListener('change', (e) => {
            state.soundEnabled = e.target.checked;
            localStorage.setItem('upsccms_soundEnabled', JSON.stringify(state.soundEnabled));
        });
    }
}

function applyDarkMode(isDark) {
    if (isDark) {
        document.body.classList.add('dark-mode');
    }
}
// Marrow specific helpers removed

function filterQuestions() {
    let source = (typeof allQuestions !== 'undefined') ? allQuestions : [];
    const mode = state.mode || 'study';

    // 1. Mode Pre-filtering
    if (mode === 'exam') {
        // Strict year and paper filtering for Exam Mode
        const selYear = (state.currentExamYear || '').toString().toLowerCase().trim();
        const selPaper = (state.currentExamPaper || '').toString().toLowerCase().trim();
        
        if (selYear && selYear !== 'all') {
            source = source.filter(q => (q.year || '').toString().toLowerCase().trim() === selYear);
        }
        if (selPaper) {
            source = source.filter(q => (q.paper || '').toString().toLowerCase().trim() === selPaper);
        }
    } else if (mode === 'bookmarks_review') {
        source = source.filter(q => state.bookmarks.includes(q.question));
    } else if (mode === 'super_revision') {
        source = source.filter(q => (state.wrongCounts[q.question] || 0) >= 1);
    }

    // 2. Select Subjects to match
    let selSubs = [];
    if (mode === 'custom_qbank') {
        selSubs = state.customSubjects || [];
    } else if (mode === 'super_revision') {
        selSubs = state.superRevisionSubjects || [];
    } else if (mode !== 'exam' && state.currentSubject && state.currentSubject !== 'all') {
        selSubs = [state.currentSubject];
    }

    if (selSubs.length > 0) {
        const targetSubs = selSubs.map(s => s.toLowerCase().trim());
        source = source.filter(q => {
            // Split by common separators and clean each part
            const raw = q.subject || (q.tags && q.tags[0]) || '';
            const qParts = raw.split(/[&/]/).map(p => cleanSubject(p).toLowerCase().trim());
            const qTopic = (q.topic || '').toLowerCase().trim();
            
            // CONSOLIDATION: Medicine selection includes Pediatrics
            const effectiveTargetSubs = [...targetSubs];
            if (targetSubs.includes('medicine')) {
                effectiveTargetSubs.push('pediatrics');
            }

            // Match if any cleaned part of the question's subject matches any target subject
            return effectiveTargetSubs.some(s => qParts.includes(s) || qTopic.includes(s));
        });
    }

    // 3. Year Filter (Only if not in custom modes generally, but let's allow it for standard)
    if (mode !== 'exam' && mode !== 'custom_qbank' && mode !== 'super_revision' && mode !== 'bookmarks_review') {
        if (state.currentYear && state.currentYear !== 'all') {
            const selYear = state.currentYear.toString().toLowerCase().trim();
            source = source.filter(q => (q.year || '').toString().toLowerCase().trim() === selYear);
        }
    }

    // 4. Keyword/Unit Filter
    if (state.currentUnit) {
        const unit = state.currentUnit.toLowerCase().trim();
        source = source.filter(q => 
            (q.question || '').toLowerCase().includes(unit) || 
            (q.topic || '').toLowerCase().includes(unit) ||
            (q.subject || (q.tags && q.tags[0]) || '').toLowerCase().includes(unit)
        );
    }

    return source;
}

function startMode(mode) {
    console.log("startMode triggered:", mode);
    // FREEMIUM CHECK 
    if (!state.isPremium && state.questionsAttempted >= 50) {
        console.warn("Entry blocked: User hit 50 question limit.");
        el.paywall.modal.classList.remove('hidden');
        return; 
    }

    state.mode = mode;
    state.isCustomQBank = (mode === 'custom_qbank');

    // Run unified filter
    let matching = filterQuestions();

    // Pad with random questions if fewer than 120 (for Exam Mode)
    if (mode === 'exam' && matching.length < 120) {
        const needed = 120 - matching.length;
        // Avoid duplicates
        const existingIds = new Set(matching.map(q => q.id));
        const pool = mcqData.filter(q => !existingIds.has(q.id));
        
        // Randomly pick the extras
        const shuffledPool = [...pool].sort(() => 0.5 - Math.random());
        const extras = shuffledPool.slice(0, needed);
        
        matching = [...matching, ...extras];
    }

    // Support sorting for Super Revision (hardest first)
    if (mode === 'super_revision') {
        matching.sort((a, b) => (state.wrongCounts[b.question] || 0) - (state.wrongCounts[a.question] || 0));
    } else if (mode === 'exam') {
        // Sort by question number for a realistic experience
        matching.sort((a, b) => {
            const numA = parseInt(a.num) || 0;
            const numB = parseInt(b.num) || 0;
            return numA - numB;
        });
    } else {
        // Randomize for other modes? Usually better for practice
        matching.sort(() => Math.random() - 0.5);
    }

    // Apply limits
    let limit = 0;
    if (mode === 'exam') {
        limit = 120; // UPSC CMS papers have 120 questions
    } else if (mode === 'custom_qbank') {
        limit = parseInt(el.customQBank.limitInput.value) || 50;
    } else if (state.currentLimit && state.currentLimit !== 'all') {
        limit = parseInt(state.currentLimit);
    }

    if (limit > 0) {
        matching = matching.slice(0, limit);
    }

    state.questions = matching;
    console.log("Questions loaded for mode:", state.questions.length);

    state.currentIndex = 0;
    state.answers = {};
    state.showExplanation = false;

    if (state.timerInterval) clearInterval(state.timerInterval);

    if (state.questions.length === 0) {
        showToast("No practice questions available for this filter.");
        console.warn("Returning early: No questions found after filtering.");
        return;
    }

    // Timer Logic
    if (mode === 'exam') {
        startTimer(120 * 60); // 120 Minutes for Exam Mode
    } else if (mode === 'custom_qbank') {
        const mins = parseInt(el.customQBank.timerInput.value);
        if (mins > 0) startTimer(mins * 60);
        else el.quiz.timerDisplay.classList.add('hidden');
        el.customQBank.modal.classList.add('hidden');
    } else if (mode === 'super_revision') {
        el.superRevision.modal.classList.add('hidden');
        if (el.quiz.timerDisplay) el.quiz.timerDisplay.classList.add('hidden');
    } else {
        if (el.quiz.timerDisplay) el.quiz.timerDisplay.classList.add('hidden');
    }

    renderQuestion();
    switchScreen('quiz');
}

// Reading, Recall, and Annotation logic removed

// Quiz Handlers
function setupQuizListeners() {
    if (el.quiz.btnBookmark) {
        el.quiz.btnBookmark.onclick = () => {
            if (state.questions[state.currentIndex]) {
                toggleBookmark(state.questions[state.currentIndex].question);
            }
        };
    }

    if (el.quiz.btnNext) {
        el.quiz.btnNext.addEventListener('click', () => {
            if (state.currentIndex < state.questions.length - 1) {
                state.currentIndex++;
                state.showExplanation = false;
                renderQuestion();
            } else {
                finishQuiz(); // Still finish quiz if it's the last question
            }
        });
    }

    if (el.quiz.btnPrev) {
        el.quiz.btnPrev.onclick = () => {
            if (state.currentIndex > 0) {
                state.currentIndex--;
                state.showExplanation = state.mode === 'study' && !!state.answers[state.currentIndex];
                renderQuestion();
            }
        };
    }

    if (el.quiz.btnEnd) {
        console.log("Binding btnEndQuiz listener with addEventListener...");
        // Use a named function so we can remove it if needed, or stick to onclick for simplicity if re-binding
        el.quiz.btnEnd.onclick = (e) => {
            e.preventDefault();
            console.log("btnEndQuiz clicked! Direct finishQuiz call.");
            finishQuiz();
        };
    } else {
        console.error("btnEndQuiz element NOT FOUND during setupQuizListeners!");
    }
}

function startTimer(seconds) {
    state.timerSeconds = seconds;
    el.quiz.timerDisplay.classList.remove('hidden');
    updateTimerUI();

    state.timerInterval = setInterval(() => {
        state.timerSeconds--;
        updateTimerUI();
        if (state.timerSeconds <= 0) {
            clearInterval(state.timerInterval);
            finishQuiz();
            showToast("Time's up! Showing your results.");
        }
    }, 1000);
}

function updateTimerUI() {
    const mins = Math.floor(state.timerSeconds / 60).toString().padStart(2, '0');
    const secs = (state.timerSeconds % 60).toString().padStart(2, '0');
    el.quiz.timerText.textContent = `${mins}:${secs}`;

    if (state.timerSeconds < 60) {
        el.quiz.timerDisplay.style.color = '#ef4444'; // Red for last minute
        el.quiz.timerDisplay.style.borderColor = '#ef4444';
    } else {
        el.quiz.timerDisplay.style.color = 'var(--accent)';
        el.quiz.timerDisplay.style.borderColor = 'var(--accent)';
    }
}

function renderQuestion() {
    // FREEMIUM CHECK 
    if (!state.isPremium && state.questionsAttempted >= 50) {
        el.paywall.modal.classList.remove('hidden');
        switchScreen('start');
        return; 
    }

    const q = state.questions[state.currentIndex];

    // Header updates
    el.quiz.qCurrent.textContent = state.currentIndex + 1;
    el.quiz.qTotal.textContent = state.questions.length;
    el.quiz.progress.style.width = `${((state.currentIndex + 1) / state.questions.length) * 100}%`;
    el.quiz.qSubject.textContent = q.subject || (q.tags && q.tags[0]) || 'General';

    updateBookmarkUI();

    // Content updates
    el.quiz.qText.innerHTML = q.question || q.topic || '';
    if (q.isRepeated) {
        el.quiz.qText.innerHTML += ' <span class="repeated-star" title="This question has appeared multiple times across years!">⭐</span>';
    }

    if (q.image) {
        el.quiz.qImage.src = 'images/' + q.image;
        el.quiz.qImage.classList.remove('hidden');
    } else {
        el.quiz.qImage.classList.add('hidden');
    }

    el.quiz.qOptions.innerHTML = '';

    const hasAnswered = !!state.answers[state.currentIndex];

    // Build options
    ['a', 'b', 'c', 'd'].forEach(opt => {
        if (!q.options[opt]) return;

        const optionDiv = document.createElement('div');
        optionDiv.className = 'option';

        // CSS states based on study/exam mode
        if (hasAnswered) {
            if (state.mode === 'study') {
                if (opt.toLowerCase() === q.answer.toLowerCase()) optionDiv.classList.add('correct');
                else if (state.answers[state.currentIndex] === opt) optionDiv.classList.add('wrong');
                optionDiv.classList.add('disabled');
            } else {
                if (state.answers[state.currentIndex] === opt) optionDiv.classList.add('selected');
            }
        }

        const letterDiv = document.createElement('div');
        letterDiv.className = 'option-letter';
        letterDiv.textContent = opt.toUpperCase();

        const textDiv = document.createElement('div');
        textDiv.className = 'option-text';
        textDiv.textContent = q.options[opt];

        optionDiv.appendChild(letterDiv);
        optionDiv.appendChild(textDiv);

        if (!hasAnswered || state.mode === 'exam' || state.mode === 'custom_qbank') {
            optionDiv.addEventListener('click', () => selectOption(opt));
        }

        el.quiz.qOptions.appendChild(optionDiv);
    });

    // Explanation visibility
    if (state.mode === 'study' && hasAnswered) {
        el.quiz.qExplanation.classList.remove('hidden');
        el.quiz.expText.innerHTML = `<strong>Correct Answer: ${q.answer.toUpperCase()}</strong><br><br>${q.explanation}`;
        if (q.explanation_image) {
            el.quiz.expImage.src = 'images/' + q.explanation_image;
            el.quiz.expImage.classList.remove('hidden');
        } else {
            el.quiz.expImage.classList.add('hidden');
        }
    } else {
        el.quiz.qExplanation.classList.add('hidden');
    }

    // Buttons
    el.quiz.btnPrev.disabled = state.currentIndex === 0;
    if (state.currentIndex === state.questions.length - 1) {
        el.quiz.btnNext.textContent = 'Finish';
    } else {
        el.quiz.btnNext.textContent = 'Next';
    }
}

function selectOption(opt) {
    if (state.mode === 'study' && state.answers[state.currentIndex]) return; // locked in study mode

    state.answers[state.currentIndex] = opt;
    state.showExplanation = true;

    renderQuestion();

    // Auto prompt bookmark on wrong answer in Study/Exam mode AFTER render
    const q = state.questions[state.currentIndex];
    const isCorrect = opt.toLowerCase() === q.answer.toLowerCase();

    if (!isCorrect) {
        incrementWrongCount(q.question);
        playSound('wrong');
    } else {
        playSound('correct');
    }

    // Update global attempt count and sync
    state.questionsAttempted++;
    localStorage.setItem('upsccms_attempts', state.questionsAttempted);
    
    if (state.user) {
        // Sync every 5 questions or when limit is reached
        if (state.questionsAttempted % 5 === 0 || state.questionsAttempted >= 50) {
            syncQuestionsAttempted();
        }
    }

    if ((state.mode === 'study' || state.mode === 'custom_qbank') && !isCorrect) {
        if (!state.bookmarks.includes(q.question)) {
            // Auto add to bookmarks for Review
            toggleBookmark(q.question);
        }
    }
}

// Score Handlers
function finishQuiz() {
    console.log("finishQuiz() called. State:", {
        mode: state.mode,
        questionsCount: state.questions.length,
        currentIndex: state.currentIndex
    });
    if (state.timerInterval) clearInterval(state.timerInterval);

    let correct = 0;
    let wrong = 0;
    let unanswered = 0;

    let newlyBookmarked = 0;
    const total = state.questions.length;

    state.questions.forEach((q, i) => {
        const userAns = state.answers[i];
        if (!userAns) {
            unanswered++;
        } else if (userAns.toLowerCase() === q.answer.toLowerCase()) {
            correct++;
        } else {
            wrong++;

            // Exam Mode auto-add to Review (bookmarks) and Super Revision (wrongCount)
            if (state.mode === 'exam') {
                incrementWrongCount(q.question);
                if (!state.bookmarks.includes(q.question)) {
                    state.bookmarks.push(q.question);
                    newlyBookmarked++;
                }
            }
        }
    });

    // Save bookmarks if any new ones were added in exam mode
    if (newlyBookmarked > 0) {
        localStorage.setItem('upsccms_bookmarks', JSON.stringify(state.bookmarks));
        showToast(`${newlyBookmarked} wrong answers added to Review ⭐`);
    }

    // Update Supabase Questions Attempted (Freemium logic)
    const questionsJustAttempted = total - unanswered;
    if (questionsJustAttempted > 0) {
        state.questionsAttempted += questionsJustAttempted;
        localStorage.setItem('upsccms_attempts', state.questionsAttempted);

        if (state.user) {
            // Fire and forget update to Supabase
            supabaseClient.from('profiles').update({
                questions_attempted: state.questionsAttempted
            }).eq('id', state.user.id).then(({ error }) => {
                if (error) console.error("Error updating attempted count:", error);
            });
        }
    }

    const percentage = total > 0 ? Math.round((correct / total) * 100) : 0;

    el.score.percentage.textContent = `${percentage}%`;
    el.score.circle.setAttribute('stroke-dasharray', `${percentage}, 100`);

    el.score.correct.textContent = correct;
    el.score.wrong.textContent = wrong;
    el.score.unanswered.textContent = unanswered;

    switchScreen('score');
}

function setupScoreListeners() {
    if (el.score.btnDashboard) {
        el.score.btnDashboard.addEventListener('click', () => {
            switchScreen('start');
        });
    }

    if (el.score.btnReview) {
        el.score.btnReview.addEventListener('click', () => {
            state.mode = 'study'; // Force study mode for review
            state.currentIndex = 0;
            renderQuestion();
            switchScreen('quiz');
        });
    }

    // Setup Paywall Buttons
    if (el.paywall.btnCancel) {
        el.paywall.btnCancel.addEventListener('click', () => {
            el.paywall.modal.classList.add('hidden');
        });
    }

    const handleUpgrade = async (btn, planText) => {
        if (!state.user) return;
        const orgHTML = btn.innerHTML;
        btn.innerHTML = `<div style="text-align:center; width: 100%; font-weight: bold;">Processing...</div>`;
        btn.disabled = true;

        try {
            // 1. Create order on the backend
            const amount = 600;
            const res = await fetch(`${BACKEND_URL}/create-order`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount, plan: planText.replace(' ', '_') })
            });
            const orderInfo = await res.json();

            if (!res.ok) throw new Error(orderInfo.error || 'Failed to create order');

            // 2. Open Razorpay Checkout
            const options = {
                key: 'rzp_live_SOuU2TcJf7X8qV', // Public Key
                amount: orderInfo.amount,
                currency: "INR",
                name: "Synopsis UPSC CMS",
                description: `Upgrade to ${planText}`,
                order_id: orderInfo.id,
                handler: async function (response) {
                    // 3. Verify payment on the backend
                    const verifyRes = await fetch(`${BACKEND_URL}/verify-payment`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            razorpay_payment_id: response.razorpay_payment_id,
                            razorpay_order_id: response.razorpay_order_id,
                            razorpay_signature: response.razorpay_signature
                        })
                    });

                    const verifyData = await verifyRes.json();

                    if (verifyData.success) {
                        // 4. Update Supabase Premium Status
                        const { error } = await supabaseClient.from('profiles').update({
                            is_premium: true
                        }).eq('id', state.user.id);

                        if (error) {
                            showToast("Payment captured but DB update failed: " + error.message);
                        } else {
                            state.isPremium = true;
                            updatePremiumUI();
                            el.paywall.modal.classList.add('hidden');
                            showToast(`💎 Upgrade Successful! You are now on the ${planText}.`);
                            startMode(state.mode); // Resume where they left off
                        }
                    } else {
                        showToast("Payment verification failed!");
                    }

                    btn.innerHTML = orgHTML;
                    btn.disabled = false;
                },
                prefill: {
                    name: state.user.user_metadata?.full_name || state.user.email,
                    email: state.user.email,
                },
                theme: {
                    color: "#6366f1" // primary color
                }
            };
            const rzp = new window.Razorpay(options);

            rzp.on('payment.failed', function (response) {
                showToast("Payment Failed: " + response.error.description);
                btn.innerHTML = orgHTML;
                btn.disabled = false;
            });

            rzp.open();

        } catch (error) {
            showToast("Error starting payment: " + error.message);
            btn.innerHTML = orgHTML;
            btn.disabled = false;
        }
    };

    if (el.paywall.btnUpgradeUPSC2026) {
        el.paywall.btnUpgradeUPSC2026.addEventListener('click', () => handleUpgrade(el.paywall.btnUpgradeUPSC2026, 'UPSC CMS 2026 Plan'));
    }
    if (el.paywall.btnDashboardUpgrade) {
        el.paywall.btnDashboardUpgrade.addEventListener('click', () => handleUpgrade(el.paywall.btnDashboardUpgrade, 'UPSC CMS 2026 Plan'));
    }
}


async function syncQuestionsAttempted() {
    if (!state.user) return;
    try {
        const { error } = await supabaseClient
            .from('profiles')
            .update({ questions_attempted: state.questionsAttempted })
            .eq('id', state.user.id);
        if (error) console.error("Error syncing attempted count:", error);
    } catch (e) {
        console.error("Sync error:", e);
    }
}

// Init
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

function cleanSubject(subject) {
    if (!subject) return 'General';
    
    // Normalize case and trim
    let clean = subject.trim();
    
    // Handle combined subjects like "OBGYN/Medicine" -> "OBGYN"
    if (clean.includes('/')) {
        clean = clean.split('/')[0].trim();
    }
    
    // Standardize acronyms and messy headers
    const upper = clean.toUpperCase();
    if (upper.includes('OBSTETRICS') && upper.includes('GYNECOLOGY')) return 'OBGYN';
    if (upper === 'OBG' || upper === 'OBGYN') return 'OBGYN';
    if (upper.includes('PSM') || upper.includes('PREVENTIVE')) return 'PSM';
    if (upper.includes('MEDICINE') && !upper.includes('FORENSIC')) return 'Medicine';
    if (upper.includes('ORTHO')) return 'Orthopaedics';
    if (upper.includes('PAED') || upper.includes('PEDIA')) return 'Pediatrics';
    if (upper.includes('SURGERY')) return 'Surgery';
    if (upper.includes('PSYCH')) return 'Psychiatry';
    
    // General case: Title Case
    return clean.toLowerCase().split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}
