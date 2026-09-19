/* =========================================================
Single-Source Retrieval -- frontend controller
========================================================= */
const API = ""; // same origin; set to "http://localhost:8000" if split
const state = {
    documentId: null,
    filename: null,
    busy: false,
    ttsEnabled: false,
};
/* ---------------- element refs ---------------- */
const $ = (id) => document.getElementById(id);
const el = {
    dropzone: $("dropzone"),
    fileInput: $("file-input"),
    progress: $("upload-progress"),
    progressFill: $("progress-fill"),
    progressLabel: $("progress-label"),
    docMeta: $("doc-meta"),
    docName: $("doc-name"),
    docStats: $("doc-stats"),
    clearDoc: $("clear-doc"),
    topicsPanel: $("topics-panel"),
    topicsList: $("topics-list"),
    messages: $("messages"),
    emptyState: $("empty-state"),
    suggestions: $("suggestions"),
    composer: $("composer"),
    question: $("question"),
    sendBtn: $("send-btn"),
    micBtn: $("mic-btn"),
    ttsToggle: $("tts-toggle"),
    statusLine: $("status-line"),
    toast: $("toast"),
};
/* ---------------- small helpers ---------------- */
function toast(message, ms = 4000) {
    el.toast.textContent = message;
    el.toast.classList.remove("hidden");
    clearTimeout(toast._t);
    toast._t = setTimeout(() => el.toast.classList.add("hidden"), ms);
}

function status(text = "") {
    el.statusLine.textContent = text;
}

function setBusy(busy) {
    state.busy = busy;
    const ready = Boolean(state.documentId) && !busy;
    el.question.disabled = !ready;
    el.sendBtn.disabled = !ready;
    el.micBtn.disabled = !ready || !speech.supported;
}

function scrollToBottom() {
    el.messages.scrollTop = el.messages.scrollHeight;
}
/* Always build DOM with textContent, never innerHTML with server data.
Chunk text comes from an arbitrary PDF -- treating it as HTML is an
injection hole with no upside. */
function node(tag, className, text) {
    const n = document.createElement(tag);
    if (className) n.className = className;
    if (text !== undefined) n.textContent = text;
    return n;
}
/* =========================================================
Upload
========================================================= */
el.dropzone.addEventListener("click", () => el.fileInput.click());
el.dropzone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        el.fileInput.click();
    }
});
el.fileInput.addEventListener("change", (e) => {
    if (e.target.files[0]) uploadFile(e.target.files[0]);
});
["dragenter", "dragover"].forEach((evt) =>
    el.dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        el.dropzone.classList.add("dragover");
    })
);
["dragleave", "drop"].forEach((evt) =>
    el.dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        el.dropzone.classList.remove("dragover");
    })
);
el.dropzone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
});

function uploadFile(file) {
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
        return toast("Only PDF files are supported.");
    }
    if (file.size > 50 * 1024 * 1024) {
        return toast("That file is larger than 50 MB.");
    }
    const body = new FormData();
    body.append("file", file);
    el.dropzone.classList.add("hidden");
    el.progress.classList.remove("hidden");
    el.progressFill.style.width = "0%";
    el.progressLabel.textContent = "Uploading…";
    /* XMLHttpRequest rather than fetch, purely for upload progress events --
    fetch has no equivalent for request-body progress. */
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API}/api/upload`);
    xhr.upload.addEventListener("progress", (e) => {
        if (!e.lengthComputable) return;
        const pct = Math.round((e.loaded / e.total) * 100);
        el.progressFill.style.width = `${pct}%`;
        if (pct >= 100) el.progressLabel.textContent = "Indexing document…";
    });
    xhr.addEventListener("load", () => {
        el.progress.classList.add("hidden");
        let data;
        try {
            data = JSON.parse(xhr.responseText);
        } catch {
            data = {};
        }
        if (xhr.status >= 200 && xhr.status < 300) {
            onDocumentReady(data);
        } else {
            el.dropzone.classList.remove("hidden");
            toast(data.detail || `Upload failed (${xhr.status}).`);
        }
    });
    xhr.addEventListener("error", () => {
        el.progress.classList.add("hidden");
        el.dropzone.classList.remove("hidden");
        toast("Network error. Is the backend running?");
    });
    xhr.send(body);
}

function onDocumentReady(data) {
    state.documentId = data.document_id;
    state.filename = data.filename;
    el.docName.textContent = data.filename;
    el.docStats.textContent = `${data.pages} pages · ${data.chunks} chunks indexed`;
    el.docMeta.classList.remove("hidden");
    el.emptyState.classList.add("hidden");
    setBusy(false);
    el.question.focus();
    status("Document ready. Ask anything about it.");
    loadSuggestions();
    loadTopics();
}
el.clearDoc.addEventListener("click", () => {
    s
    t
    a
    t
    e.d
    o
    c
    u
    m
    e
    n
    t
    I
    d
        =
        n
    u
    l
    l;
    el.docMeta.classList.add(
        "
        h i d d e n "
    );
    el.dropzone.classList.remove("hidde
        n "
    );
    el.topicsPanel.classList.add("hidden");
    el.suggestions.classList.add("hidden");
    el.messages.replaceChildren(el.emptySta t e);
    el.emptyState.classList.remove("hidden");
    el.fileInput.value = "";
    setBusy(false);
    status("");
});
/* ==========================================
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
S
u
g
g
e
s
t
i
o
n
s
&
t
o
p
i
c
s
(
n
o
n
-
c
r
i
t
i
c
a
l
-
-
f
a
i
l
s
i
l
e
n
t
l
y
)
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
=
*
/
a
s
y
n
c
f
u
n
c
t
i
o
n
l
o
a
d
S
u
g
g
e
s
t
i
o
n
s
(
)
{
t
r
y
{
c
o
n
s
t
r
e
s
=
a
w
a
i
t
f
e
t
c
h
(
`
$
{
A
P
I
}
/
a
p
i
/
s
u
g
g
e
s
t
i
o
n
s
`, {
m
e
t
h
o
d: "
P
O
S
T
", headers: { "Con
t
e
n
t
-
T
y
p
e
": "
a
p
p
l
i
c
a
t
i
o
n
/
j
s
o
n
"
}, body: JSON.stringify({ document_id: state.docume
n
t
I
d
}
), }); const { suggestions } = await res.json(); if (!suggestions?.length) return; el.suggestions.replaceChildren(); suggestions.forEach((text) => { const chip = node("button", "chip", text); chip.type = "button"; chip.addEventListener("click", () => { el.question.value = text; el.composer.requestSubmit(); }); el.suggestions.appendChild(chip); }); el.suggestions.classList.remove("hidden"); } catch { /* decorative feature; ignore */
}
}
a
s
y
n
c
f
u
n
c
t
i
o
n
l
o
a
d
T
o
p
i
c
s
    () {
        t
        r
        y {
            c
            o
            n
            s
            t
            r
            e
            s
                =
                a
            w
            a
            i
            t
            f
            e
            t
            c
            h
                (
                    `
$
{
A
P
I
}
/
a
p
i
/
t
o
p
i
c
s
`, {
                        m
                        e
                        t
                        h
                        o
                        d: "
                        P
                        O
                        S
                        T ", headers: { "
                        Con
                        t
                        e
                        n
                        t -
                        T
                        y
                        p
                        e ": "
                        a
                        p
                        p
                        l
                        i
                        c
                        a
                        t
                        i
                        o
                        n /
                        j
                        s
                        o
                        n "
                    }, body: JSON.stringify({
                        document_id: state.docume
                        n
                        t
                        I
                        d
                    }),
                });
        const {
            topics
        } = await res.json();
        if (!topics?.length) return;
        el.topicsList.replaceChildren();
        topics.forEach((t) => {
            const li = node("li");
            li.appendChild(node("strong", null, t.title));
            if (t.summary) li.appendChild(node("span", null, t.summa r y));
            li.addEventListener("click", () => {
                el.question.value = `Tell me about ${t.title} in this docum
e
n
t.`;
                el.question.focus();
            });
            el.topicsList.appendChild(li);
        });
        el.topicsPanel.classList.remove("hidden");
    } catch {
        /* ignore */ }
}
/ *
= = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
Q
u
e
ry
    = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = *
    /
e
l.c
o
m
p
o
s
e
r.a
d
d
E
v
e
n
t
L
i
s
t
e
n
e
r
    (
        "
        s u b m i t ", (
        e
    ) = >
    {
        e.p
        r
        e
        v
        e
        n
        t
        D
        e
        f
        a
        u
        l
        t();askQuestion();
    });
/* Enter sends, Shift
+
E
n
t
e
r
m
a
k
e
s
a
n
e
w
l
i
n
e. *
/
e
l.q
u
e
s
t
i
o
n.a
d
d
E
v
e
n
t
L
i
s
t
e
n
e
r
(
"
k
e
y
d
o
w
n
", (
e
)
=
>
{
i
f
(
e.k
e
y
=
=
=
"
E
n
t
e
r
"
&
& !e.s
h
i
f
t
K
e
y
)
{
e.p
r
e
v
e
n
t
D
e
f
a
u
l
t
(
); el.composer.request
S
u
b
m
i
t
(
); }
}
); /*
A
u
t
o
-
g
r
o
w
t
h
e
t
e
x
t
a
r
e
a. *
/
e
l.q
u
e
s
t
i
o
n.a
d
d
E
v
e
n
t
L
i
s
t
e
n
e
r
(
"
i
n
p
u
t
", (
)
=
>
{
e
l.q
u
e
s
t
i
o
n.s
t
y
l
e.h
e
i
g
h
t
=
"
a
u
t
o
"; el.question.style.height = `${Math.m
i
n
(
e
l.q
u
e
s
t
i
o
n.s
c
r
o
l
l
H
e
i
g
h
t, 1
6
0
)
}
p
x
`; });
async function askQuestion() {
const question = el.question.value.trim();
if (!question || !state.documentId || state.busy) return;
el.suggestions.classList.add("hidden");
renderUserMessage(question);
el.question.value = "";
el.question.style.height = "auto";
setBusy(true);
const thinking = renderThinking();
status("Retrieving, re-ranking, generating…");
try {
const res = await fetch(`${API}/api/query`, {
method: "POST",
headers: { "Content-Type": "application/json" },
body: JSON.stringify({
document_id: state.documentId,
question,
evaluate: true,
}),
});
const data = await res.json();
thinking.remove();
if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);
renderBotMessage(data);
if (state.ttsEnabled) speak(data.answer);
status(`Answered in ${data.latency_ms} ms · ${data.sources.length} sources`);
} catch (err) {
thinking.remove();
toast(err.message);
status("");
} finally {
setBusy(false);
el.question.focus();
}
}
/* =========================================================
Rendering
========================================================= */
function renderUserMessage(text) {
    el.messages.appendChild(node("div", "msg user", text));
    scrollToBottom();
}

function renderThinking() {
    const wrap = node("div", "msg bot");
    const dots = node("div", "thinking");
    dots.append(node("i"), node("i"), node("i"));
    wrap.appendChild(dots);
    el.messages.appendChild(wrap);
    scrollToBottom();
    return wrap;
}

function renderBotMessage(data) {
    const wrap = node("div", "msg bot");
    const answer = node("div", "bot-answer", data.answer);
    if (!data.grounded) answer.classList.add("ungrounded");
    wrap.appendChild(answer);
    if (data.sources?.length) {
        const details = node("details", "sources");
        details.appendChild(
            node("summary", null, `${data.sources.length} source passages`)
        );
        data.sources.forEach((src, i) => {
            const box = node("div", "source");
            const head = node("div", "source-head");
            head.appendChild(
                node("span", null,
                    `[${i + 1}]` + (src.page ? ` · page ${src.page}` : "") +
                    ` · was #${src.vector_rank + 1} before re-ranking`)
            );
            const pill = node("span", "score-pill", src.rerank_score.toFixed(2));
            if (src.rerank_score > 0) pill.classList.add("high");
            head.appendChild(pill);
            box.appendChild(head);
            box.appendChild(node("div", "source-text", src.text));
            details.appendChild(box);
        });
        wrap.appendChild(details);
    }
    const meta = node("div", "msg-meta");
    meta.appendChild(node("span", null, `${data.latency_ms} ms`));
    const replay = node("button", "link-btn", "Read aloud");
    replay.type = "button";
    replay.addEventListener("click", () => speak(data.answer));
    meta.appendChild(replay);
    wrap.appendChild(meta);
    el.messages.appendChild(wrap);
    scrollToBottom();
}
/* =========================================================
Speech recognition (input)
========================================================= */
const speech = {
    supported: false,
    recognition: null,
    listening: false,
};
(function initSpeech() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
        el.micBtn.title = "Voice input needs Chrome, Edge, or Safari";
        return;
    }
    const recognition = new SR();
    recognition.lang = "en-US";
    recognition.continuous = false; // stop after one utterance
    recognition.interimResults = true; // show words as they are recognised
    recognition.addEventListener("result", (event) => {
        let transcript = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
        }
        el.question.value = transcript;
        el.question.dispatchEvent(new Event("input")); // trigger auto-grow
    });
    recognition.addEventListener("end", () => {
        speech.listening = false;
        el.micBtn.classList.remove("recording");
        status("");
        // Auto-send if we actually captured something.
        if (el.question.value.trim()) el.composer.requestSubmit();
    });
    recognition.addEventListener("error", (event) => {
        speech.listening = false;
        el.micBtn.classList.remove("recording");
        const messages = {
            "not-allowed": "Microphone permission was denied.",
            "no-speech": "I didn't hear anything. Try again.",
            "audio-capture": "No microphone found.",
            "network": "Speech recognition needs a network connection.",
        };
        toast(messages[event.error] || `Voice input failed: ${event.error}`);
    });
    speech.recognition = recognition;
    speech.supported = true;
})();
el.micBtn.addEventListener("click", () => {
    if (!speech.supported) return;
    if (speech.listening) {
        speech.recognition.stop();
        return;
    }
    try {
        stopSpeaking(); // do not transcribe our own TTS
        speech.recognition.start();
        speech.listening = true;
        el.micBtn.classList.add("recording");
        status("Listening… speak now.");
    } catch {
        toast("Could not start the microphone.");
    }
});
/* =========================================================
Speech synthesis (output)
========================================================= */
el.ttsToggle.addEventListener("change", (e) => {
    state.ttsEnabled = e.target.checked;
    if (!state.ttsEnabled) stopSpeaking();
});

function stopSpeaking() {
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
}

function speak(text) {
    if (!("speechSynthesis" in window) || !text) return;
    stopSpeaking();
    // Strip the inline [1][2] citation markers -- they read terribly aloud.
    const spoken = text.replace(/\[\d+\]/g, "").replace(/\s{2,}/g, " ").trim();
    const utterance = new SpeechSynthesisUtterance(spoken);
    utterance.rate = 1.02;
    utterance.pitch = 1;
    utterance.lang = "en-US";
    const voice = pickVoice();
    if (voice) utterance.voice = voice;
    window.speechSynthesis.speak(utterance);
}

function pickVoice() {
    const voices = window.speechSynthesis.getVoices();
    if (!voices.length) return null;
    return (
        voices.find((v) => /Google US English|Samantha|Microsoft Aria/i.test(v.name)) ||
        voices.find((v) => v.lang === "en-US") ||
        voices[0]
    );
}
/* Chrome populates the voice list asynchronously. */
if ("speechSynthesis" in window) {
    window.speechSynthesis.addEventListener("voiceschanged", pickVoice);
}
/* =========================================================
Boot
========================================================= */
(async function boot() {
    setBusy(false);
    try {
        const res = await fetch(`${API}/health`);
        if (!res.ok) throw new Error();
        const health = await res.json();
        status(`Connected · ${health.llm_model}`);
    } catch {
        status("");
        toast("Cannot reach the backend. Start it with: uvicorn app.main:app --port 8000", 8000);
    }
})();