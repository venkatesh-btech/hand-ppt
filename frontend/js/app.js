// =============================================
// Hand Gesture PPT Controller — Dashboard JS
// 100vh Single-Page — OpenCV/MediaPipe Theme
// =============================================

(() => {
    "use strict";

    // ── DOM References ───────────────────────
    const cameraCanvas = document.getElementById("cameraCanvas");
    const cameraPlaceholder = document.getElementById("cameraPlaceholder");
    const ctx = cameraCanvas.getContext("2d");
    const connectionBadge = document.getElementById("connectionBadge");
    const connectionText = document.getElementById("connectionText");
    const fpsBadge = document.getElementById("fpsBadge");

    // Stats
    const statTotal = document.getElementById("statTotal");
    const statFingers = document.getElementById("statFingers");
    const statFps = document.getElementById("statFps");

    // Gesture
    const gestureEmoji = document.getElementById("gestureEmoji");
    const gestureName = document.getElementById("gestureName");
    const gestureDetail = document.getElementById("gestureDetail");
    const gestureRing = document.getElementById("gestureRing");

    // Log
    const actionLog = document.getElementById("actionLog");
    const logCount = document.getElementById("logCount");

    // Toast
    const toastContainer = document.getElementById("toastContainer");



    // ── State ────────────────────────────────
    let ws = null;
    let frameCount = 0;
    let lastFpsTime = performance.now();
    let actionCount = 0;
    let isFirstLog = true;
    let switching = false;  // true while camera switch is in progress
    const gestureStats = {};

    // Reusable Image for performance
    const frameImage = new Image();
    let pendingFrame = false;

    frameImage.onload = () => {
        cameraCanvas.width = frameImage.width;
        cameraCanvas.height = frameImage.height;
        ctx.drawImage(frameImage, 0, 0);
        pendingFrame = false;
    };

    // Gesture metadata
    const GESTURE_META = {
        next_slide:      { emoji: "➡️", name: "Next Slide",      type: "next" },
        prev_slide:      { emoji: "⬅️", name: "Prev Slide",      type: "prev" },
        first_slide:     { emoji: "🏠", name: "First Slide",     type: "home" },

    };

    // ── WebSocket ────────────────────────────
    function connect() {
        const protocol = location.protocol === "https:" ? "wss:" : "ws:";
        ws = new WebSocket(`${protocol}//${location.host}/ws`);
        ws.binaryType = "arraybuffer";

        ws.onopen = () => {
            connectionBadge.classList.add("connected");
            connectionText.textContent = "Online";
            cameraPlaceholder.style.display = "none";
            restoreStats();
        };

        ws.onclose = () => {
            connectionBadge.classList.remove("connected");
            connectionText.textContent = "Offline";
            cameraPlaceholder.style.display = "flex";
            if (!switching) {
                setTimeout(connect, 2000);
            }
        };

        ws.onerror = () => ws.close();

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.error) {
                    cameraPlaceholder.querySelector("p").textContent = data.error;
                    return;
                }
                handleFrame(data);
            } catch (e) {
                console.error("Parse error:", e);
            }
        };
    }

    // ── Restore Stats ────────────────────────
    async function restoreStats() {
        try {
            const res = await fetch("/api/history");
            const data = await res.json();
            if (data.stats && data.stats.total_gestures > 0) {
                actionCount = data.stats.total_gestures;
                statTotal.textContent = actionCount;

                if (data.stats.breakdown) {
                    for (const [g, count] of Object.entries(data.stats.breakdown)) {
                        gestureStats[g] = count;
                    }
                }

                if (data.stats.most_used && data.stats.most_used !== "none") {
                    // stats restored
                }

                if (data.history && data.history.length > 0) {
                    isFirstLog = false;
                    actionLog.innerHTML = "";
                    for (const entry of data.history.slice(0, 15)) {
                        const info = GESTURE_META[entry.gesture] || { emoji: "❓", name: entry.gesture, type: "next" };
                        addLogEntry(entry.time, info.emoji, info.name, info.type, false);
                    }
                    logCount.textContent = actionCount;
                }
            }
        } catch (e) {
            console.log("Could not restore stats:", e);
        }
    }

    // ── Handle Frame ─────────────────────────
    function handleFrame(data) {
        if (data.frame && !pendingFrame) {
            pendingFrame = true;
            frameImage.src = "data:image/jpeg;base64," + data.frame;
        }

        frameCount++;
        const now = performance.now();
        if (now - lastFpsTime >= 1000) {
            const fps = frameCount;
            fpsBadge.textContent = fps + " FPS";
            statFps.textContent = fps;
            frameCount = 0;
            lastFpsTime = now;
        }

        handleGestureData(data);

    }

    // ── Handle Gestures ──────────────────────
    function handleGestureData(data) {
        if (data.detections && data.detections.length > 0) {
            statFingers.textContent = data.detections[0].fingers;
        }

        if (data.action) {
            const act = data.action;
            const info = GESTURE_META[act.gesture] || { emoji: "❓", name: act.gesture, type: "next" };

            gestureEmoji.textContent = info.emoji;
            gestureEmoji.classList.remove("active");
            void gestureEmoji.offsetWidth;
            gestureEmoji.classList.add("active");
            gestureName.textContent = info.name;
            gestureDetail.textContent = `${act.hand} • ${act.fingers}F • ${act.time}`;

            gestureRing.classList.add("active");
            setTimeout(() => gestureRing.classList.remove("active"), 1000);

            actionCount++;
            statTotal.textContent = actionCount;
            gestureStats[act.gesture] = (gestureStats[act.gesture] || 0) + 1;

            addLogEntry(act.time, info.emoji, info.name, info.type, true);
            showToast(info.emoji, info.name, `${act.hand} • ${act.fingers} fingers`, info.type);
        }
    }

    // ── Log Entry ────────────────────────────
    function addLogEntry(time, icon, action, type, animate) {
        if (isFirstLog) {
            actionLog.innerHTML = "";
            isFirstLog = false;
        }

        const entry = document.createElement("div");
        entry.className = "log-entry";
        if (!animate) entry.style.animation = "none";
        entry.innerHTML = `
            <span class="log-time">${time}</span>
            <span class="log-icon">${icon}</span>
            <span class="log-action">${action}</span>
            <span class="log-badge ${type}">${type.toUpperCase()}</span>
        `;
        actionLog.prepend(entry);

        while (actionLog.children.length > 30) {
            actionLog.removeChild(actionLog.lastChild);
        }

        logCount.textContent = actionCount;
    }

    // ── Toast ────────────────────────────────
    function showToast(icon, title, subtitle, type) {
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-accent"></div>
            <span class="toast-icon">${icon}</span>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-subtitle">${subtitle}</div>
            </div>
        `;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.classList.add("removing");
            setTimeout(() => { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 250);
        }, 2000);

        while (toastContainer.children.length > 3) {
            toastContainer.removeChild(toastContainer.firstChild);
        }
    }

    // ── Camera Switch ────────────────────────
    const btnLaptop = document.getElementById("btnLaptop");
    const btnMobile = document.getElementById("btnMobile");
    const mobileUrlInput = document.getElementById("mobileUrlInput");
    const cameraUrlField = document.getElementById("cameraUrlField");
    const btnConnectCamera = document.getElementById("btnConnectCamera");

    btnLaptop.addEventListener("click", () => {
        btnLaptop.classList.add("active");
        btnMobile.classList.remove("active");
        mobileUrlInput.style.display = "none";
        switchCamera("laptop", null);
    });

    btnMobile.addEventListener("click", () => {
        btnMobile.classList.add("active");
        btnLaptop.classList.remove("active");
        mobileUrlInput.style.display = "flex";
    });

    btnConnectCamera.addEventListener("click", () => {
        const url = cameraUrlField.value.trim();
        if (!url) { alert("Enter IP Webcam URL"); return; }
        switchCamera("mobile", url);
    });

    async function switchCamera(source, url) {
        try {
            switching = true;
            if (ws) ws.close();
            cameraPlaceholder.style.display = "flex";
            cameraPlaceholder.querySelector("p").textContent = "Switching camera...";

            const res = await fetch("/api/camera", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ source, url }),
            });
            const data = await res.json();
            if (data.status === "ok") {
                // Wait for backend to open the new camera, then reconnect
                setTimeout(() => {
                    switching = false;
                    connect();
                }, 2000);
            } else {
                cameraPlaceholder.querySelector("p").textContent = data.error || "Switch failed";
                switching = false;
            }
        } catch (e) {
            console.error("Camera switch error:", e);
            cameraPlaceholder.querySelector("p").textContent = "Connection error";
            switching = false;
            setTimeout(connect, 3000);
        }
    }

    async function loadCameraState() {
        try {
            const res = await fetch("/api/camera");
            const cam = await res.json();
            if (cam.source === "mobile") {
                btnMobile.classList.add("active");
                btnLaptop.classList.remove("active");
                mobileUrlInput.style.display = "flex";
                cameraUrlField.value = cam.url;
            }
        } catch (e) { /* ignore */ }
    }

    // ── Init ─────────────────────────────────
    loadCameraState();
    connect();

})();
