// Copyright 2026 Shachain
// License OPL-1 (Odoo Proprietary License v1.0)

(function () {
    "use strict";

    // =========================================================================
    // Theme Configurations
    // =========================================================================

    var THEMES = {
        playful: {
            characters: [
                {
                    id: "purple",
                    cls: "sc_char--purple",
                    hasEyeballs: true,
                    eyeballSmall: false,
                    pupilSmall: false,
                    hasMouth: false,
                    eyeGap: 32,
                    eyeDefaultLeft: 45,
                    eyeDefaultTop: 40,
                    maxPupilDist: 5,
                    defaultHeight: 400,
                },
                {
                    id: "black",
                    cls: "sc_char--black",
                    hasEyeballs: true,
                    eyeballSmall: true,
                    pupilSmall: true,
                    hasMouth: false,
                    eyeGap: 24,
                    eyeDefaultLeft: 26,
                    eyeDefaultTop: 32,
                    maxPupilDist: 4,
                    defaultHeight: 310,
                },
                {
                    id: "orange",
                    cls: "sc_char--orange",
                    hasEyeballs: false,
                    hasMouth: false,
                    eyeGap: 32,
                    eyeDefaultLeft: 82,
                    eyeDefaultTop: 90,
                    maxPupilDist: 5,
                    defaultHeight: 200,
                },
                {
                    id: "yellow",
                    cls: "sc_char--yellow",
                    hasEyeballs: false,
                    hasMouth: true,
                    eyeGap: 24,
                    eyeDefaultLeft: 52,
                    eyeDefaultTop: 40,
                    maxPupilDist: 5,
                    mouthDefaultLeft: 40,
                    mouthDefaultTop: 88,
                    defaultHeight: 230,
                },
            ],
        },
        professional: {
            // 2 characters: purple + black (subdued, no exaggerated animations)
            characters: [
                {
                    id: "purple",
                    cls: "sc_char--purple",
                    hasEyeballs: true,
                    eyeballSmall: false,
                    pupilSmall: false,
                    hasMouth: false,
                    eyeGap: 32,
                    eyeDefaultLeft: 45,
                    eyeDefaultTop: 40,
                    maxPupilDist: 4,
                    defaultHeight: 400,
                },
                {
                    id: "black",
                    cls: "sc_char--black",
                    hasEyeballs: true,
                    eyeballSmall: true,
                    pupilSmall: true,
                    hasMouth: false,
                    eyeGap: 24,
                    eyeDefaultLeft: 26,
                    eyeDefaultTop: 32,
                    maxPupilDist: 3,
                    defaultHeight: 310,
                },
            ],
        },
        minimal: {
            // 1 character: orange semi-circle (just eyes, most subtle)
            characters: [
                {
                    id: "orange",
                    cls: "sc_char--orange",
                    hasEyeballs: false,
                    hasMouth: false,
                    eyeGap: 32,
                    eyeDefaultLeft: 82,
                    eyeDefaultTop: 90,
                    maxPupilDist: 3,
                    defaultHeight: 200,
                },
            ],
        },
    };

    // =========================================================================
    // Math Helpers
    // =========================================================================

    /**
     * Track a pupil element within a circular area, following the mouse
     * or snapping to a forced position.
     *
     * @param {HTMLElement} pupilEl - The pupil DOM element
     * @param {number} maxDist - Maximum translation distance in px
     * @param {number} mouseX - Current mouse X
     * @param {number} mouseY - Current mouse Y
     * @param {number|undefined} forceLookX - Force X offset (skip mouse calc)
     * @param {number|undefined} forceLookY - Force Y offset (skip mouse calc)
     */
    function trackPupil(pupilEl, maxDist, mouseX, mouseY, forceLookX, forceLookY) {
        if (!pupilEl) return;
        if (forceLookX !== undefined && forceLookY !== undefined) {
            pupilEl.style.transform = "translate(" + forceLookX + "px, " + forceLookY + "px)";
            return;
        }
        var rect = pupilEl.getBoundingClientRect();
        var cx = rect.left + rect.width / 2;
        var cy = rect.top + rect.height / 2;
        var dx = mouseX - cx;
        var dy = mouseY - cy;
        var dist = Math.min(Math.sqrt(dx * dx + dy * dy), maxDist);
        var angle = Math.atan2(dy, dx);
        pupilEl.style.transform =
            "translate(" + (Math.cos(angle) * dist) + "px, " + (Math.sin(angle) * dist) + "px)";
    }

    /**
     * Calculate body skew angle based on mouse X relative to element center.
     * Returns a value clamped to [-6, 6] degrees.
     */
    function calcBodySkew(el, mouseX) {
        if (!el) return 0;
        var rect = el.getBoundingClientRect();
        var cx = rect.left + rect.width / 2;
        return Math.max(-6, Math.min(6, -(mouseX - cx) / 120));
    }

    /**
     * Calculate face (eyes container) offset from mouse position.
     * Returns { fx, fy } clamped within maxX/maxY bounds.
     */
    function calcFaceOffset(el, mouseX, mouseY, scaleX, scaleY, maxX, maxY) {
        if (!el) return { fx: 0, fy: 0 };
        scaleX = scaleX || 20;
        scaleY = scaleY || 30;
        maxX = maxX || 15;
        maxY = maxY || 10;
        var rect = el.getBoundingClientRect();
        var cx = rect.left + rect.width / 2;
        var cy = rect.top + rect.height / 3;
        return {
            fx: Math.max(-maxX, Math.min(maxX, (mouseX - cx) / scaleX)),
            fy: Math.max(-maxY, Math.min(maxY, (mouseY - cy) / scaleY)),
        };
    }

    // =========================================================================
    // LoginAnimationManager
    // =========================================================================

    /**
     * Main animation engine. Reads theme from container, builds character DOM,
     * runs the rAF loop, and reacts to form events.
     *
     * @param {HTMLElement} container - The .sc_login_characters element
     */
    function LoginAnimationManager(container) {
        this.container = container;
        this.mouseX = 0;
        this.mouseY = 0;
        this.isTypingEmail = false;
        this.passwordValue = "";
        this.showPassword = false;
        this.animFrameId = null;
        this.destroyed = false;

        // Resolve theme
        var rootContainer = container.closest(".sc_login_animated");
        var themeName = rootContainer
            ? rootContainer.getAttribute("data-sc-theme") || "playful"
            : "playful";
        this.themeConfig = THEMES[themeName] || THEMES.playful;

        // DOM element references per character (populated in _buildDOM)
        // Each entry: { el, eyes, pupils: [l, r], eyeballs: [l, r]|null, mouth: null|el, config }
        this.chars = [];

        // Blink timers (to clear on destroy)
        this._blinkTimers = [];

        // Bound handlers (for removeEventListener)
        this._onMouseMove = this._handleMouseMove.bind(this);
        this._onEmailFocus = this._handleEmailFocus.bind(this);
        this._onEmailBlur = this._handleEmailBlur.bind(this);
        this._onPasswordInput = this._handlePasswordInput.bind(this);
        this._onPasswordToggle = this._handlePasswordToggle.bind(this);
        this._animateFrame = this._animate.bind(this);

        this._buildDOM();
        this._applyCustomColors(rootContainer);
        this._bindEvents();
        this._startBlinking();
        this._startAnimation();
        this._observeErrors();
    }

    // -------------------------------------------------------------------------
    // DOM Construction
    // -------------------------------------------------------------------------

    LoginAnimationManager.prototype._buildDOM = function () {
        // Create scene wrapper
        var scene = document.createElement("div");
        scene.className = "sc_characters_scene";
        var inner = document.createElement("div");
        inner.className = "sc_characters_inner";
        scene.appendChild(inner);

        var chars = this.themeConfig.characters;
        for (var i = 0; i < chars.length; i++) {
            var cfg = chars[i];
            var charEl = document.createElement("div");
            charEl.className = "sc_char " + cfg.cls;
            charEl.id = "sc_char_" + cfg.id;

            var eyesEl = document.createElement("div");
            eyesEl.className = "sc_eyes";
            eyesEl.id = "sc_eyes_" + cfg.id;
            eyesEl.style.gap = cfg.eyeGap + "px";
            eyesEl.style.left = cfg.eyeDefaultLeft + "px";
            eyesEl.style.top = cfg.eyeDefaultTop + "px";

            var pupilL, pupilR;
            var eyeballL = null, eyeballR = null;

            if (cfg.hasEyeballs) {
                // Eyeball-wrapped pupils (purple, black)
                eyeballL = document.createElement("div");
                eyeballL.className = "sc_eyeball" + (cfg.eyeballSmall ? " sc_eyeball--small" : "");
                eyeballL.id = "sc_eye_" + cfg.id + "_l";
                pupilL = document.createElement("div");
                pupilL.className = "sc_pupil" + (cfg.pupilSmall ? " sc_pupil--small" : "");
                pupilL.id = "sc_pupil_" + cfg.id + "_l";
                eyeballL.appendChild(pupilL);

                eyeballR = document.createElement("div");
                eyeballR.className = "sc_eyeball" + (cfg.eyeballSmall ? " sc_eyeball--small" : "");
                eyeballR.id = "sc_eye_" + cfg.id + "_r";
                pupilR = document.createElement("div");
                pupilR.className = "sc_pupil" + (cfg.pupilSmall ? " sc_pupil--small" : "");
                pupilR.id = "sc_pupil_" + cfg.id + "_r";
                eyeballR.appendChild(pupilR);

                eyesEl.appendChild(eyeballL);
                eyesEl.appendChild(eyeballR);
            } else {
                // Naked pupils (orange, yellow)
                pupilL = document.createElement("div");
                pupilL.className = "sc_naked_pupil";
                pupilL.id = "sc_pupil_" + cfg.id + "_l";
                pupilR = document.createElement("div");
                pupilR.className = "sc_naked_pupil";
                pupilR.id = "sc_pupil_" + cfg.id + "_r";

                eyesEl.appendChild(pupilL);
                eyesEl.appendChild(pupilR);
            }

            charEl.appendChild(eyesEl);

            var mouthEl = null;
            if (cfg.hasMouth) {
                mouthEl = document.createElement("div");
                mouthEl.className = "sc_mouth";
                mouthEl.id = "sc_mouth_" + cfg.id;
                charEl.appendChild(mouthEl);
            }

            inner.appendChild(charEl);

            this.chars.push({
                el: charEl,
                eyes: eyesEl,
                pupils: [pupilL, pupilR],
                eyeballs: cfg.hasEyeballs ? [eyeballL, eyeballR] : null,
                mouth: mouthEl,
                config: cfg,
            });
        }

        this.container.appendChild(scene);
    };

    // -------------------------------------------------------------------------
    // Custom Color Application
    // -------------------------------------------------------------------------

    LoginAnimationManager.prototype._applyCustomColors = function (rootContainer) {
        if (!rootContainer) return;
        var primary = rootContainer.getAttribute("data-sc-primary");
        var bg = rootContainer.getAttribute("data-sc-bg");

        // Only apply custom colors if they are valid hex values.
        // "False" comes from Odoo when the field is empty; default values
        // should be left to CSS (which has per-theme defaults via data-sc-theme).
        var isValidColor = function (v) {
            return v && v !== "False" && v.charAt(0) === "#";
        };

        if (isValidColor(primary)) {
            rootContainer.style.setProperty("--sc-char-purple", primary);
            rootContainer.style.setProperty("--sc-bg-mid", primary);
        }
        if (isValidColor(bg)) {
            rootContainer.style.setProperty("--sc-bg-start", bg);
            rootContainer.style.setProperty("--sc-bg-end", bg);
        }
    };

    // -------------------------------------------------------------------------
    // Event Binding
    // -------------------------------------------------------------------------

    LoginAnimationManager.prototype._bindEvents = function () {
        document.addEventListener("mousemove", this._onMouseMove, { passive: true });

        // Email input
        var emailInput = document.getElementById("login");
        if (emailInput) {
            emailInput.addEventListener("focus", this._onEmailFocus, { passive: true });
            emailInput.addEventListener("blur", this._onEmailBlur, { passive: true });
        }

        // Password input
        var passwordInput = document.getElementById("password");
        if (passwordInput) {
            passwordInput.addEventListener("input", this._onPasswordInput, { passive: true });
        }

        // Password visibility toggle
        var toggleBtn = document.querySelector(".o_show_password");
        if (toggleBtn) {
            toggleBtn.addEventListener("click", this._onPasswordToggle, { passive: true });
        }
    };

    LoginAnimationManager.prototype._handleMouseMove = function (e) {
        this.mouseX = e.clientX;
        this.mouseY = e.clientY;
    };

    LoginAnimationManager.prototype._handleEmailFocus = function () {
        this.isTypingEmail = true;
    };

    LoginAnimationManager.prototype._handleEmailBlur = function () {
        this.isTypingEmail = false;
    };

    LoginAnimationManager.prototype._handlePasswordInput = function (e) {
        this.passwordValue = e.target.value;
    };

    LoginAnimationManager.prototype._handlePasswordToggle = function () {
        // Detect actual state after Odoo toggles it
        var passwordInput = document.getElementById("password");
        if (passwordInput) {
            // Use a microtask so we read the state *after* Odoo's own handler runs
            var self = this;
            Promise.resolve().then(function () {
                self.showPassword = passwordInput.type === "text";
            });
        }
    };

    // -------------------------------------------------------------------------
    // Blinking
    // -------------------------------------------------------------------------

    LoginAnimationManager.prototype._startBlinking = function () {
        var self = this;
        for (var i = 0; i < this.chars.length; i++) {
            var charData = this.chars[i];
            if (charData.eyeballs) {
                this._scheduleBlink(charData);
            }
        }
    };

    LoginAnimationManager.prototype._scheduleBlink = function (charData) {
        var self = this;
        var delay = Math.random() * 4000 + 3000; // 3-7 seconds
        var timer = setTimeout(function () {
            if (self.destroyed) return;
            // Blink on
            charData.eyeballs[0].classList.add("sc_eyeball--blink");
            charData.eyeballs[1].classList.add("sc_eyeball--blink");
            var closeTimer = setTimeout(function () {
                if (self.destroyed) return;
                // Blink off
                charData.eyeballs[0].classList.remove("sc_eyeball--blink");
                charData.eyeballs[1].classList.remove("sc_eyeball--blink");
                self._scheduleBlink(charData);
            }, 150);
            self._blinkTimers.push(closeTimer);
        }, delay);
        this._blinkTimers.push(timer);
    };

    // -------------------------------------------------------------------------
    // Error Observation (MutationObserver)
    // -------------------------------------------------------------------------

    LoginAnimationManager.prototype._observeErrors = function () {
        var self = this;

        // Watch for .alert-danger appearing in the login form
        var form = document.querySelector(".oe_login_form");
        if (!form) return;

        this._errorObserver = new MutationObserver(function (mutations) {
            for (var i = 0; i < mutations.length; i++) {
                var mutation = mutations[i];
                // Check added nodes for alert-danger
                for (var j = 0; j < mutation.addedNodes.length; j++) {
                    var node = mutation.addedNodes[j];
                    if (
                        node.nodeType === 1 &&
                        (node.classList.contains("alert-danger") ||
                            node.querySelector && node.querySelector(".alert-danger"))
                    ) {
                        self._triggerShake();
                        return;
                    }
                }
            }
        });
        this._errorObserver.observe(form, { childList: true, subtree: true });

        // Also check if error already exists on page load
        var existingError = form.querySelector(".alert-danger");
        if (existingError) {
            // Delay slightly so the animation is visible after page renders
            setTimeout(function () {
                self._triggerShake();
            }, 300);
        }
    };

    LoginAnimationManager.prototype._triggerShake = function () {
        var self = this;
        for (var i = 0; i < this.chars.length; i++) {
            var charEl = this.chars[i].el;
            charEl.classList.add("sc_char--shake");
        }
        setTimeout(function () {
            for (var i = 0; i < self.chars.length; i++) {
                self.chars[i].el.classList.remove("sc_char--shake");
            }
        }, 800);
    };

    // -------------------------------------------------------------------------
    // Animation Loop
    // -------------------------------------------------------------------------

    LoginAnimationManager.prototype._startAnimation = function () {
        this.animFrameId = requestAnimationFrame(this._animateFrame);
    };

    LoginAnimationManager.prototype._animate = function () {
        if (this.destroyed) return;

        var mx = this.mouseX;
        var my = this.mouseY;
        var hiding = this.passwordValue.length > 0 && this.showPassword;
        var coveringEyes = this.passwordValue.length > 0 && !this.showPassword;

        for (var i = 0; i < this.chars.length; i++) {
            var c = this.chars[i];
            var cfg = c.config;
            var skew = calcBodySkew(c.el, mx);
            var face = calcFaceOffset(c.el, mx, my);

            if (cfg.id === "purple") {
                this._animatePurple(c, cfg, skew, face, mx, my, hiding, coveringEyes);
            } else if (cfg.id === "black") {
                this._animateBlack(c, cfg, skew, face, mx, my, hiding);
            } else if (cfg.id === "orange") {
                this._animateOrange(c, cfg, skew, face, mx, my, hiding);
            } else if (cfg.id === "yellow") {
                this._animateYellow(c, cfg, skew, face, mx, my, hiding);
            }
        }

        this.animFrameId = requestAnimationFrame(this._animateFrame);
    };

    // --- Per-character animation ---

    LoginAnimationManager.prototype._animatePurple = function (
        c, cfg, skew, face, mx, my, hiding, coveringEyes
    ) {
        if (hiding) {
            // Password visible → look away
            c.el.style.transform = "skewX(0deg)";
            c.el.style.height = cfg.defaultHeight + "px";
            c.eyes.style.left = "20px";
            c.eyes.style.top = "35px";
            trackPupil(c.pupils[0], cfg.maxPupilDist, mx, my, -4, -4);
            trackPupil(c.pupils[1], cfg.maxPupilDist, mx, my, -4, -4);
        } else if (this.isTypingEmail || coveringEyes) {
            // Email focus or password hidden → stretch up and lean
            c.el.style.height = (cfg.defaultHeight + 40) + "px";
            c.el.style.transform = "skewX(" + (skew - 12) + "deg) translateX(40px)";
            if (this.isTypingEmail) {
                c.eyes.style.left = "55px";
                c.eyes.style.top = "65px";
                trackPupil(c.pupils[0], cfg.maxPupilDist, mx, my, 3, 4);
                trackPupil(c.pupils[1], cfg.maxPupilDist, mx, my, 3, 4);
            } else {
                c.eyes.style.left = (cfg.eyeDefaultLeft + face.fx) + "px";
                c.eyes.style.top = (cfg.eyeDefaultTop + face.fy) + "px";
                trackPupil(c.pupils[0], cfg.maxPupilDist, mx, my);
                trackPupil(c.pupils[1], cfg.maxPupilDist, mx, my);
            }
        } else {
            // Default → track mouse
            c.el.style.height = cfg.defaultHeight + "px";
            c.el.style.transform = "skewX(" + skew + "deg)";
            c.eyes.style.left = (cfg.eyeDefaultLeft + face.fx) + "px";
            c.eyes.style.top = (cfg.eyeDefaultTop + face.fy) + "px";
            trackPupil(c.pupils[0], cfg.maxPupilDist, mx, my);
            trackPupil(c.pupils[1], cfg.maxPupilDist, mx, my);
        }
    };

    LoginAnimationManager.prototype._animateBlack = function (
        c, cfg, skew, face, mx, my, hiding
    ) {
        if (hiding) {
            // Password visible → look away
            c.el.style.transform = "skewX(0deg)";
            c.eyes.style.left = "10px";
            c.eyes.style.top = "28px";
            trackPupil(c.pupils[0], cfg.maxPupilDist, mx, my, -4, -4);
            trackPupil(c.pupils[1], cfg.maxPupilDist, mx, my, -4, -4);
        } else if (this.isTypingEmail) {
            // Email focus → lean toward purple
            c.el.style.transform = "skewX(" + (skew * 1.5 + 10) + "deg) translateX(20px)";
            c.eyes.style.left = "32px";
            c.eyes.style.top = "12px";
            trackPupil(c.pupils[0], cfg.maxPupilDist, mx, my, 0, -4);
            trackPupil(c.pupils[1], cfg.maxPupilDist, mx, my, 0, -4);
        } else {
            // Default → track mouse
            c.el.style.transform = "skewX(" + skew + "deg)";
            c.eyes.style.left = (cfg.eyeDefaultLeft + face.fx) + "px";
            c.eyes.style.top = (cfg.eyeDefaultTop + face.fy) + "px";
            trackPupil(c.pupils[0], cfg.maxPupilDist, mx, my);
            trackPupil(c.pupils[1], cfg.maxPupilDist, mx, my);
        }
    };

    LoginAnimationManager.prototype._animateOrange = function (
        c, cfg, skew, face, mx, my, hiding
    ) {
        if (hiding) {
            // Password visible → look away
            c.el.style.transform = "skewX(0deg)";
            c.eyes.style.left = "50px";
            c.eyes.style.top = "85px";
            trackPupil(c.pupils[0], cfg.maxPupilDist, mx, my, -5, -4);
            trackPupil(c.pupils[1], cfg.maxPupilDist, mx, my, -5, -4);
        } else {
            // Default → track mouse
            c.el.style.transform = "skewX(" + skew + "deg)";
            c.eyes.style.left = (cfg.eyeDefaultLeft + face.fx) + "px";
            c.eyes.style.top = (cfg.eyeDefaultTop + face.fy) + "px";
            trackPupil(c.pupils[0], cfg.maxPupilDist, mx, my);
            trackPupil(c.pupils[1], cfg.maxPupilDist, mx, my);
        }
    };

    LoginAnimationManager.prototype._animateYellow = function (
        c, cfg, skew, face, mx, my, hiding
    ) {
        if (hiding) {
            // Password visible → look away
            c.el.style.transform = "skewX(0deg)";
            c.eyes.style.left = "20px";
            c.eyes.style.top = "35px";
            if (c.mouth) {
                c.mouth.style.left = "10px";
                c.mouth.style.top = (cfg.mouthDefaultTop || 88) + "px";
            }
            trackPupil(c.pupils[0], cfg.maxPupilDist, mx, my, -5, -4);
            trackPupil(c.pupils[1], cfg.maxPupilDist, mx, my, -5, -4);
        } else {
            // Default → track mouse
            c.el.style.transform = "skewX(" + skew + "deg)";
            c.eyes.style.left = (cfg.eyeDefaultLeft + face.fx) + "px";
            c.eyes.style.top = (cfg.eyeDefaultTop + face.fy) + "px";
            if (c.mouth) {
                c.mouth.style.left = ((cfg.mouthDefaultLeft || 40) + face.fx) + "px";
                c.mouth.style.top = ((cfg.mouthDefaultTop || 88) + face.fy) + "px";
            }
            trackPupil(c.pupils[0], cfg.maxPupilDist, mx, my);
            trackPupil(c.pupils[1], cfg.maxPupilDist, mx, my);
        }
    };

    // -------------------------------------------------------------------------
    // Destroy (cleanup)
    // -------------------------------------------------------------------------

    LoginAnimationManager.prototype.destroy = function () {
        this.destroyed = true;

        if (this.animFrameId) {
            cancelAnimationFrame(this.animFrameId);
        }

        for (var i = 0; i < this._blinkTimers.length; i++) {
            clearTimeout(this._blinkTimers[i]);
        }
        this._blinkTimers = [];

        document.removeEventListener("mousemove", this._onMouseMove);

        var emailInput = document.getElementById("login");
        if (emailInput) {
            emailInput.removeEventListener("focus", this._onEmailFocus);
            emailInput.removeEventListener("blur", this._onEmailBlur);
        }

        var passwordInput = document.getElementById("password");
        if (passwordInput) {
            passwordInput.removeEventListener("input", this._onPasswordInput);
        }

        var toggleBtn = document.querySelector(".o_show_password");
        if (toggleBtn) {
            toggleBtn.removeEventListener("click", this._onPasswordToggle);
        }

        if (this._errorObserver) {
            this._errorObserver.disconnect();
            this._errorObserver = null;
        }
    };

    // =========================================================================
    // Bootstrap
    // =========================================================================

    function initAnimation() {
        // Prevent double init
        if (window.__sc_login_animation) return;

        // Find the animation container
        var rootContainer = document.querySelector(".sc_login_animated");
        if (!rootContainer) return;

        // Check disabled state
        if (rootContainer.getAttribute("data-sc-enabled") === "False") return;

        // Find or create the characters panel
        var container = rootContainer.querySelector(".sc_login_characters");
        if (!container) return;

        // Initialize the animation manager
        window.__sc_login_animation = new LoginAnimationManager(container);
    }

    // Support both normal and lazy-loaded scenarios:
    // - If DOM is already ready (lazy JS loaded after DOMContentLoaded), run immediately
    // - If DOM is not ready yet, wait for DOMContentLoaded
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initAnimation);
    } else {
        initAnimation();
    }
})();
