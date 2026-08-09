// SAIR Target AI Site DOM Injector Script (target_injector.js)
console.log("⚡ SAIR Universal Compatibility Target Injector Active on: " + window.location.href);

if (window === window.top) {
    let injectionLock = false;

    // Zero-CSP Pure In-Memory Base64 Data URI to Blob Conversion
    const dataURItoBlob = (dataURI) => {
        try {
            const parts = dataURI.split(',');
            const byteString = atob(parts[1] || parts[0]);
            const mimeMatch = parts[0].match(/:(.*?);/);
            const mimeString = mimeMatch ? mimeMatch[1] : 'image/png';

            const ab = new ArrayBuffer(byteString.length);
            const ia = new Uint8Array(ab);
            for (let i = 0; i < byteString.length; i++) {
                ia[i] = byteString.charCodeAt(i);
            }
            return new Blob([ab], { type: mimeString });
        } catch(e) {
            console.error("[SAIR Injector] dataURItoBlob conversion error:", e);
            return null;
        }
    };

    // Deep Shadow DOM Query Selector for Web Components & Shadow Roots
    const findDeepElement = (selector, root = document, requireVisible = true) => {
        try {
            let el = root.querySelector(selector);
            if (el && (!requireVisible || (el.offsetWidth || el.offsetHeight || el.getClientRects().length))) {
                return el;
            }

            const allNodes = root.querySelectorAll('*');
            for (const node of allNodes) {
                if (node.shadowRoot) {
                    const found = findDeepElement(selector, node.shadowRoot, requireVisible);
                    if (found) return found;
                }
            }
        } catch(e) {}
        return null;
    };

    // Find ALL Deep Matching Elements
    const findAllDeepElements = (selector, root = document, requireVisible = true) => {
        let results = [];
        try {
            const nodes = Array.from(root.querySelectorAll(selector)).filter(el => 
                !requireVisible || (el.offsetWidth || el.offsetHeight || el.getClientRects().length)
            );
            results.push(...nodes);

            const allNodes = root.querySelectorAll('*');
            for (const node of allNodes) {
                if (node.shadowRoot) {
                    const sub = findAllDeepElements(selector, node.shadowRoot, requireVisible);
                    results.push(...sub);
                }
            }
        } catch(e) {}
        return results;
    };

    // Safe Slate.js Selection & Blinking Caret Activator
    const activateSlateCursor = (el) => {
        try {
            if (!el || !document.contains(el)) return;
            if (window.focus) window.focus();
            el.focus();

            let targetNode = el.querySelector('[data-slate-string="true"]') || 
                             el.querySelector('[data-slate-leaf="true"]') || 
                             el.querySelector('p[data-slate-node="element"]') || 
                             el;

            if (!targetNode || !document.contains(targetNode)) return;

            let textNode = null;
            const findText = (node) => {
                if (node.nodeType === Node.TEXT_NODE) return node;
                for (let child of node.childNodes) {
                    if (child.nodeType === Node.TEXT_NODE) return child;
                    const f = findText(child);
                    if (f) return f;
                }
                return null;
            };
            textNode = findText(targetNode);

            if (!textNode && document.contains(targetNode)) {
                try {
                    textNode = document.createTextNode('');
                    targetNode.appendChild(textNode);
                } catch(e) {}
            }

            if (textNode && document.contains(textNode)) {
                try {
                    const r = document.createRange();
                    r.setStart(textNode, textNode.length);
                    r.setEnd(textNode, textNode.length);

                    const s = window.getSelection();
                    s.removeAllRanges();
                    s.addRange(r);
                } catch(e) {}
            }

            try {
                document.dispatchEvent(new Event('selectionchange', { bubbles: true }));
                el.dispatchEvent(new Event('focus', { bubbles: true }));
            } catch(e) {}
        } catch(e) {}
    };

    // Slate.js React AST Synchronizer & Button Activator
    const injectIntoSlate = (el, text) => {
        try {
            // 1. Force Slate Caret Activation
            activateSlateCursor(el);

            // 2. Hide placeholder span if present
            const placeholder = el.querySelector('[data-slate-placeholder="true"]');
            if (placeholder) {
                try { placeholder.style.display = 'none'; } catch(e) {}
            }

            // 3. Locate text paragraph and leaf node
            let textParagraph = el.querySelector('p[data-slate-node="element"]') || 
                                el.querySelector('[data-slate-node="element"]:last-child') || 
                                el;

            let leafSpan = textParagraph.querySelector('[data-slate-leaf="true"]') || 
                           textParagraph.querySelector('[data-slate-string="true"]') || 
                           textParagraph;

            // 4. Find or create inner TextNode
            let textNode = null;
            const findText = (node) => {
                if (node.nodeType === Node.TEXT_NODE) return node;
                for (let child of node.childNodes) {
                    if (child.nodeType === Node.TEXT_NODE) return child;
                    const f = findText(child);
                    if (f) return f;
                }
                return null;
            };
            textNode = findText(leafSpan);

            if (!textNode) {
                textNode = document.createTextNode('');
                leafSpan.appendChild(textNode);
            }

            // 5. Ensure textNode is empty first so browser treats execCommand as a real DOM change
            textNode.nodeValue = '';

            // 6. Position Selection Range on empty textNode
            if (document.contains(textNode)) {
                try {
                    const r = document.createRange();
                    r.setStart(textNode, 0);
                    r.setEnd(textNode, 0);
                    const s = window.getSelection();
                    s.removeAllRanges();
                    s.addRange(r);
                } catch(e) {}
            }

            // 7. Native execCommand('paste') or execCommand('insertText') to trigger Slate's React onChange
            let inserted = false;
            try {
                inserted = document.execCommand('paste');
            } catch(e) {}

            if (!inserted) {
                try {
                    inserted = document.execCommand('insertText', false, text);
                } catch(e) {}
            }

            // 8. Fallback: If browser didn't insert, mutate nodeValue and fire beforeinput carrying data: text
            if (!inserted || textNode.nodeValue !== text) {
                textNode.nodeValue = text;
                try {
                    el.dispatchEvent(new InputEvent('beforeinput', { bubbles: true, cancelable: true, inputType: 'insertText', data: text }));
                    el.dispatchEvent(new InputEvent('input', { bubbles: true, cancelable: true, inputType: 'insertText', data: text }));
                } catch(e) {}
            }

            // 9. Dispatch change & input events to notify submit button validator
            try {
                el.dispatchEvent(new Event('input', { bubbles: true, cancelable: true }));
                el.dispatchEvent(new Event('change', { bubbles: true, cancelable: true }));
            } catch(e) {}

            // 10. OS Clipboard backup write
            if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
                try {
                    navigator.clipboard.writeText(text).then(() => {}).catch(() => {});
                } catch(e) {}
            }

            return true;
        } catch(e) {
            console.warn("[SAIR Injector] Slate injection error:", e);
            return false;
        }
    };

    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.action === 'EXECUTE_AUTO_INJECT') {
            if (injectionLock) {
                sendResponse({ success: true, warning: 'Injection in progress...' });
                return true;
            }
            injectionLock = true;

            const { specText, imageBase64 } = request;

            // Send instant 0.001s response to SAIR Cockpit for maximum speed feedback
            sendResponse({ success: true, textInjected: true, imageInjected: true });

            const executeInjection = () => {
                const textSelectors = [
                    'div[data-slate-editor="true"]',
                    '[data-slate-editor="true"]',
                    'textarea[placeholder*="무엇을"]',
                    'div[placeholder*="무엇을"]',
                    'textarea[placeholder*="만들고"]',
                    'div[placeholder*="만들고"]',
                    '#prompt-textarea',
                    'rich-textarea div[contenteditable="true"]',
                    'gmp-prompt-input textarea',
                    'gmp-prompt-input',
                    'div[aria-label*="Prompt"]',
                    'div[aria-label*="프롬프트"]',
                    'div[aria-label*="Jules"]',
                    'textarea[aria-label*="Jules"]'
                ];

                let targetElements = [];
                for (const sel of textSelectors) {
                    const found = findAllDeepElements(sel, document, true);
                    if (found.length > 0) {
                        targetElements.push(...found);
                    }
                }

                targetElements = Array.from(new Set(targetElements));
                // Target ONLY the primary active single editor element
                const primaryTargetEl = targetElements.length > 0 ? targetElements[targetElements.length - 1] : null;

                // Smart DOM Character Limit Detection
                let domMaxLength = 99999;
                if (primaryTargetEl) {
                    const attrMax = primaryTargetEl.getAttribute('maxlength') || primaryTargetEl.dataset?.maxlength;
                    if (attrMax) domMaxLength = parseInt(attrMax, 10);
                }

                const isManus = window.location.hostname.includes('manus');
                const isLimitExceeded = specText && specText.length > domMaxLength;
                const requiresTextFilePack = isManus || isLimitExceeded;

                const boxText = (isLimitExceeded && domMaxLength < 99999) ? 
                    specText.substring(0, Math.max(50, domMaxLength - 30)) + "..." : 
                    specText;

                const isGoogleFlow = window.location.hostname.includes('google');
                const hasImage = (imageBase64 && imageBase64.startsWith('data:image')) || requiresTextFilePack;

                // STEP 1: Immediate Text Injection FIRST
                if (primaryTargetEl && boxText) {
                    try {
                        const isSlate = primaryTargetEl.hasAttribute('data-slate-editor') || 
                                        primaryTargetEl.querySelector('[data-slate-node]') || 
                                        primaryTargetEl.closest('[data-slate-editor="true"]');

                        if (isSlate) {
                            const slateEditor = primaryTargetEl.closest('[data-slate-editor="true"]') || primaryTargetEl;
                            injectIntoSlate(slateEditor, boxText);
                        } else {
                            if (primaryTargetEl._valueTracker) {
                                try { primaryTargetEl._valueTracker.setValue(''); } catch(e) {}
                            }

                            if (primaryTargetEl.tagName === 'TEXTAREA') {
                                const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')?.set;
                                if (nativeSetter) nativeSetter.call(primaryTargetEl, boxText);
                                else primaryTargetEl.value = boxText;
                            } else if (primaryTargetEl.tagName === 'INPUT') {
                                const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
                                if (nativeSetter) nativeSetter.call(primaryTargetEl, boxText);
                                else primaryTargetEl.value = boxText;
                            } else {
                                let inserted = false;
                                try {
                                    inserted = document.execCommand('insertText', false, boxText);
                                } catch(e) {}

                                if (!inserted || !primaryTargetEl.innerText || primaryTargetEl.innerText.trim() === '') {
                                    const safeHtml = boxText.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, '<br>');
                                    primaryTargetEl.innerHTML = '<p>' + safeHtml + '</p>';
                                }
                            }

                            primaryTargetEl.dispatchEvent(new InputEvent('beforeinput', { bubbles: true, cancelable: true, inputType: 'insertText', data: boxText }));
                            primaryTargetEl.dispatchEvent(new InputEvent('input', { bubbles: true, cancelable: true, inputType: 'insertText', data: boxText }));
                            primaryTargetEl.dispatchEvent(new Event('input', { bubbles: true, cancelable: true }));
                            primaryTargetEl.dispatchEvent(new Event('change', { bubbles: true, cancelable: true }));
                        }
                    } catch(e) {
                        console.warn("[SAIR Injector] Text injection exception:", e);
                    }
                }

                // STEP 2: Image Injection SECOND (100ms)
                setTimeout(() => {
                    if (hasImage) {
                        try {
                            const dt = new DataTransfer();
                            let imgFile = null;

                            if (requiresTextFilePack && specText) {
                                const txtBlob = new Blob([specText], { type: "text/plain;charset=utf-8" });
                                const txtFile = new File([txtBlob], "sair_master_specification.txt", { type: "text/plain;charset=utf-8" });
                                dt.items.add(txtFile);
                            }

                            if (imageBase64 && imageBase64.startsWith('data:image')) {
                                const imgBlob = dataURItoBlob(imageBase64);
                                if (imgBlob) {
                                    imgFile = new File([imgBlob], "sair_render_matrix.png", { type: "image/png" });
                                    dt.items.add(imgFile);
                                }
                            }

                            // For non-Google Flow sites, upload via generic file inputs
                            if (!isGoogleFlow && dt.files.length > 0) {
                                const fileInputElements = findAllDeepElements('input[type="file"], input[accept*="image"]', document, false);
                                if (fileInputElements.length > 0) {
                                    fileInputElements.forEach(primaryFileInput => {
                                        try {
                                            primaryFileInput.files = dt.files;
                                            primaryFileInput.dispatchEvent(new Event('change', { bubbles: true, cancelable: true }));
                                            primaryFileInput.dispatchEvent(new Event('input', { bubbles: true, cancelable: true }));
                                        } catch(e) {}
                                    });
                                }
                            }

                            // Direct Paste Attachment on Prompt Box for Gemini & Google Flow
                            if (primaryTargetEl && imgFile && (window.location.hostname.includes('gemini') || isGoogleFlow)) {
                                try {
                                    const dtImg = new DataTransfer();
                                    dtImg.items.add(imgFile);
                                    const imgPasteEvt = new ClipboardEvent('paste', { bubbles: true, cancelable: true, clipboardData: dtImg });
                                    primaryTargetEl.dispatchEvent(imgPasteEvt);
                                } catch(e) {}
                            }
                        } catch(e) {
                            console.warn("[SAIR Injector] File injection exception:", e);
                        }
                    }

                    setTimeout(() => { injectionLock = false; }, 300);
                }, 100);
            };

            executeInjection();
            return true;
        }
    });
}
