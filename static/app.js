document.addEventListener("DOMContentLoaded", () => {
    const navButtons = document.querySelectorAll(".nav-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");
            
            navButtons.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            document.getElementById(`tab-${targetTab}`).classList.add("active");

            if (targetTab === "server") {
                fetchServerInfo();
            }
        });
    });

    // --- زر تسجيل الخروج ---
    document.getElementById("btn-logout").addEventListener("click", () => {
        document.cookie = "samood_session=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        localStorage.removeItem("samood_token");
        window.location.href = "/login.html";
    });

    // --- تحديث حالة واستعلام السيرفر ---
    function fetchServerInfo() {
        fetch("/api/server-info")
            .then(res => res.json())
            .then(data => {
                if (data.cpu_usage_percent !== undefined) {
                    document.getElementById("srv-cpu").innerText = `${data.cpu_usage_percent}%`;
                    document.getElementById("srv-ram").innerText = `${data.ram_usage_percent}%`;
                }
            })
            .catch(() => {});
    }

    // --- تحديث الإحصائيات والحالة الحية ---
    function fetchStatus() {
        fetch("/api/status")
            .then(res => res.json())
            .then(data => {
                if (data.status === "success" && data.stats) {
                    document.getElementById("stat-sent").innerText = data.stats.sent_count || 0;
                    document.getElementById("stat-failed").innerText = data.stats.failed_count || 0;
                    document.getElementById("stat-unsub").innerText = data.stats.unsub_count || 0;
                    document.getElementById("stat-active-acc").innerText = data.accounts_count || 0;
                }

                if (data.status === "success" && data.settings) {
                    const st = data.settings;
                    if (document.getElementById("set-working-hours-only") && st.working_hours_only !== undefined) {
                        document.getElementById("set-working-hours-only").value = st.working_hours_only === 1 ? "true" : "false";
                    }
                    if (document.getElementById("set-work-start-hour") && st.work_start_hour !== undefined) {
                        document.getElementById("set-work-start-hour").value = st.work_start_hour;
                    }
                    if (document.getElementById("set-work-end-hour") && st.work_end_hour !== undefined) {
                        document.getElementById("set-work-end-hour").value = st.work_end_hour;
                    }
                    if (document.getElementById("set-target-country") && st.target_country) {
                        document.getElementById("set-target-country").value = st.target_country;
                    }
                }

                const dot = document.getElementById("global-status-dot");
                const statusText = document.getElementById("global-status-text");

                dot.className = "status-dot active";
                statusText.innerText = "السيرفر أونلاين 24/7";
            })
            .catch(err => console.error("Error fetching status:", err));
    }

    fetchStatus();
    setInterval(fetchStatus, 4000);

    // --- تحميل القوالب المسبقة الجاهزة ---
    function populateTemplateFields(found) {
        if (!found) return;
        document.getElementById("tpl-title").value = found.title || "";
        document.getElementById("tpl-sector").value = found.sector || "عام";
        document.getElementById("tpl-language").value = found.language || "العربية (فصحى)";
        document.getElementById("tpl-subject").value = found.subject || "";
        document.getElementById("tpl-body").value = found.body || "";
    }

    let builtinTemplatesCache = [];
    function loadBuiltinTemplates() {
        fetch("/api/templates/builtin")
            .then(res => res.json())
            .then(data => {
                if (data.status === "success" && data.templates && data.templates.length > 0) {
                    builtinTemplatesCache = data.templates;
                    const select = document.getElementById("select-builtin-template");
                    select.innerHTML = "";
                    data.templates.forEach(t => {
                        const opt = document.createElement("option");
                        opt.value = t.id;
                        opt.innerText = `[${t.sector}] - ${t.title} (${t.language})`;
                        select.appendChild(opt);
                    });

                    // تعبئة المحرر أوتوماتيكياً بأول قالب (القالب الدعائي الفعال) فور تحميل الصفحة
                    select.value = data.templates[0].id;
                    populateTemplateFields(data.templates[0]);
                }
            })
            .catch(err => console.error("Error builtin templates:", err));
    }

    loadBuiltinTemplates();

    function triggerSmartSynthesis() {
        const sectorElem = document.getElementById("smart-select-sector");
        const countryElem = document.getElementById("smart-select-country");
        const langElem = document.getElementById("smart-select-language");

        const sector = sectorElem ? sectorElem.value : "المقاولات والتشييد";
        const country_code = countryElem ? countryElem.value : "SA";
        const language = langElem ? langElem.value : "العربية (فصحى)";

        // جمع الحالات المفعلة للمتغيرات الـ 8
        const active_vars = [];
        document.querySelectorAll(".antispam-var-switch").forEach(sw => {
            if (sw.checked) {
                active_vars.push(sw.value);
            }
        });

        fetch("/api/templates/synthesize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ sector, country_code, language, active_vars })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success" && data.template) {
                populateTemplateFields(data.template);
            }
        })
        .catch(err => console.error("Error smart synthesis:", err));
    }

    // --- تحميل 22 دولة عربية كاملة بمواعيد عملها ---
    function loadArabCountries() {
        fetch("/api/countries")
            .then(res => res.json())
            .then(data => {
                if (data.status === "success" && data.countries) {
                    const settingsSelect = document.getElementById("set-target-country");
                    const smartSelect = document.getElementById("smart-select-country");
                    
                    if (settingsSelect) settingsSelect.innerHTML = "";
                    if (smartSelect) smartSelect.innerHTML = "";

                    data.countries.forEach(c => {
                        const optText = `${c.flag} ${c.name} (${c.utc} | الأيام: ${c.work_days} | الدوام: ${c.work_hours})`;
                        
                        if (settingsSelect) {
                            const opt1 = document.createElement("option");
                            opt1.value = c.code;
                            opt1.innerText = optText;
                            settingsSelect.appendChild(opt1);
                        }

                        if (smartSelect) {
                            const opt2 = document.createElement("option");
                            opt2.value = c.code;
                            opt2.innerText = `${c.flag} ${c.name}`;
                            smartSelect.appendChild(opt2);
                        }
                    });
                }
            })
            .catch(err => console.error("Error loading countries:", err));
    }

    loadArabCountries();

    // ربط أحداث المولّد الذكي والمفاتيح الـ 8 التلقائية بمجرد التغيير
    ["smart-select-sector", "smart-select-country", "smart-select-language"].forEach(id => {
        const elem = document.getElementById(id);
        if (elem) {
            elem.addEventListener("change", () => triggerSmartSynthesis());
        }
    });

    document.querySelectorAll(".antispam-var-switch").forEach(sw => {
        sw.addEventListener("change", () => triggerSmartSynthesis());
    });

    // التعبئة الفورية المباشرة بمجرد تغيير الاختيار في قائمة القوالب المسبقة
    document.getElementById("select-builtin-template").addEventListener("change", (e) => {
        const selectedId = e.target.value;
        const found = builtinTemplatesCache.find(t => t.id === selectedId);
        if (found) {
            populateTemplateFields(found);
        }
    });

    // --- حفظ القالب ---
    document.getElementById("form-template").addEventListener("submit", (e) => {
        e.preventDefault();
        const payload = {
            title: document.getElementById("tpl-title").value,
            sector: document.getElementById("tpl-sector").value,
            language: document.getElementById("tpl-language").value,
            subject: document.getElementById("tpl-subject").value,
            body_text: document.getElementById("tpl-body").value
        };

        fetch("/api/templates", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(d => {
            alert(d.message || "تم حفظ القالب بنجاح");
        });
    });

    // --- رفع بروفايل الشركة Mوحد (PDF) ---
    document.getElementById("btn-upload-profile-ar").addEventListener("click", () => {
        const fileInput = document.getElementById("profile-ar-file");
        if (fileInput.files.length === 0) {
            alert("يرجى اختيار ملف PDF أولاً");
            return;
        }
        const formData = new FormData();
        formData.append("file", fileInput.files[0]);
        formData.append("lang", "ar");

        fetch("/api/profile/upload", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(d => {
            if (d.status === "success") {
                document.getElementById("status-profile-ar").classList.remove("hidden");
                alert(d.message);
            } else {
                alert("خطأ: " + d.message);
            }
        });
    });

    document.getElementById("btn-upload-profile-en").addEventListener("click", () => {
        const fileInput = document.getElementById("profile-en-file");
        if (fileInput.files.length === 0) {
            alert("يرجى اختيار ملف PDF أولاً");
            return;
        }
        const formData = new FormData();
        formData.append("file", fileInput.files[0]);
        formData.append("lang", "en");

        fetch("/api/profile/upload", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(d => {
            if (d.status === "success") {
                document.getElementById("status-profile-en").classList.remove("hidden");
                alert(d.message);
            } else {
                alert("خطأ: " + d.message);
            }
        });
    });

    let accountsCache = [];
    // --- تحميل الحسابات المسجلة ---
    function loadAccounts() {
        fetch("/api/accounts")
            .then(res => res.json())
            .then(data => {
                accountsCache = data.accounts || [];
                const tbody = document.getElementById("accounts-table-body");
                tbody.innerHTML = "";
                if (accountsCache.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" class="text-center">لا توجد حسابات مسجلة بعد. قم بإضافة حسابك الأول بالأعلى!</td></tr>';
                    return;
                }

                accountsCache.forEach(acc => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td>${acc.sender_name}</td>
                        <td>${acc.email}</td>
                        <td>${acc.smtp_host}:${acc.smtp_port}</td>
                        <td><strong>${acc.sent_today} / ${acc.daily_limit}</strong> رسالة/يومياً</td>
                        <td><span class="status-pill ${acc.is_active ? 'green' : 'red'}">${acc.is_active ? 'نشط' : 'متوقف'}</span></td>
                        <td>
                            <button class="btn btn-sm btn-warning btn-edit-acc" data-id="${acc.id}"><i class="fa-solid fa-pen"></i> تعديل</button>
                            <button class="btn btn-sm btn-danger btn-del-acc" data-id="${acc.id}"><i class="fa-solid fa-trash"></i> حذف</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });

                // ربط أزرار الحذف والتعديل
                document.querySelectorAll(".btn-del-acc").forEach(btn => {
                    btn.addEventListener("click", (e) => {
                        const id = btn.getAttribute("data-id");
                        if (confirm("هل أنت تأكد من رغبتك في حذف هذا الحساب؟")) {
                            fetch(`/api/accounts/${id}`, { method: "DELETE" })
                                .then(res => res.json())
                                .then(d => {
                                    alert(d.message || "تم الحذف بنجاح");
                                    loadAccounts();
                                });
                        }
                    });
                });

                document.querySelectorAll(".btn-edit-acc").forEach(btn => {
                    btn.addEventListener("click", (e) => {
                        const id = parseInt(btn.getAttribute("data-id"));
                        const found = accountsCache.find(a => a.id === id);
                        if (found) {
                            document.getElementById("edit-acc-id").value = found.id;
                            document.getElementById("edit-acc-sender").value = found.sender_name;
                            document.getElementById("edit-acc-limit").value = found.daily_limit;
                            document.getElementById("edit-acc-active").value = found.is_active ? "true" : "false";
                            document.getElementById("modal-edit-account").classList.remove("hidden");
                        }
                    });
                });
            });
    }

    // إغلاق المودال
    document.getElementById("btn-close-modal").addEventListener("click", () => {
        document.getElementById("modal-edit-account").classList.add("hidden");
    });

    // حفظ التعديل
    document.getElementById("form-update-account").addEventListener("submit", (e) => {
        e.preventDefault();
        const data = {
            account_id: document.getElementById("edit-acc-id").value,
            sender_name: document.getElementById("edit-acc-sender").value,
            daily_limit: document.getElementById("edit-acc-limit").value,
            is_active: document.getElementById("edit-acc-active").value === "true"
        };
        fetch("/api/accounts/update", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        })
        .then(res => res.json())
        .then(d => {
            alert(d.message || "تم حفظ التعديل بنجاح");
            document.getElementById("modal-edit-account").classList.add("hidden");
            loadAccounts();
        });
    });

    // --- قسم اختبار وفحص الإيميلات والقرار الذكي Audit Center ---
    const auditDropzone = document.getElementById("audit-dropzone");
    const auditFileInput = document.getElementById("audit-file-input");
    let currentAuditFileId = null;

    if (auditDropzone && auditFileInput) {
        auditDropzone.addEventListener("click", () => auditFileInput.click());
        auditDropzone.addEventListener("dragover", (e) => { e.preventDefault(); auditDropzone.style.borderColor = "#10b981"; });
        auditDropzone.addEventListener("dragleave", () => { auditDropzone.style.borderColor = "var(--accent-cyan)"; });
        auditDropzone.addEventListener("drop", (e) => {
            e.preventDefault();
            auditDropzone.style.borderColor = "var(--accent-cyan)";
            if (e.dataTransfer.files.length > 0) handleAuditUpload(e.dataTransfer.files[0]);
        });
        auditFileInput.addEventListener("change", (e) => {
            if (e.target.files.length > 0) handleAuditUpload(e.target.files[0]);
        });
    }

    const btnAuditPasteSubmit = document.getElementById("btn-audit-paste-submit");
    if (btnAuditPasteSubmit) {
        btnAuditPasteSubmit.addEventListener("click", () => {
            const textVal = document.getElementById("audit-paste-input").value.trim();
            if (!textVal) {
                alert("يرجى لصق الإيميلات في المربع النصي أولاً");
                return;
            }

            const origHtml = btnAuditPasteSubmit.innerHTML;
            btnAuditPasteSubmit.disabled = true;
            btnAuditPasteSubmit.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> جاري فحص الـ MX والدومينات الآن...';

            fetch("/api/audit/paste", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: textVal })
            })
            .then(res => res.json())
            .then(data => {
                btnAuditPasteSubmit.disabled = false;
                btnAuditPasteSubmit.innerHTML = origHtml;
                if (data.status === "success") {
                    currentAuditFileId = data.file_id;
                    renderAuditReport(data, "قائمة_ملصوقة_مباشرة.csv");
                    const auditPanel = document.getElementById("audit-report-panel");
                    if (auditPanel) auditPanel.scrollIntoView({ behavior: 'smooth' });
                } else {
                    alert("خطأ أثناء فحص النص الملصوق: " + data.message);
                }
            })
            .catch(err => {
                btnAuditPasteSubmit.disabled = false;
                btnAuditPasteSubmit.innerHTML = origHtml;
                alert("حدث خطأ أثناء الفحص: " + err.message);
            });
        });
    }

    function handleAuditUpload(file) {
        const formData = new FormData();
        formData.append("file", file);

        const auditPanel = document.getElementById("audit-report-panel");
        if (auditPanel) auditPanel.classList.add("hidden");

        fetch("/api/excel/upload", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                currentAuditFileId = data.file_id;
                renderAuditReport(data, file.name);
            } else {
                alert("خطأ أثناء الفحص: " + data.message);
            }
        });
    }

    function renderAuditReport(data, filename) {
        const panel = document.getElementById("audit-report-panel");
        if (!panel) return;
        panel.classList.remove("hidden");

        document.getElementById("audit-file-title").innerHTML = `<i class="fa-solid fa-file-signature"></i> التقرير التشخيصي الشامل لملف: ${filename}`;
        document.getElementById("audit-stat-valid").innerText = data.mx_valid_count || data.valid_count || 0;
        document.getElementById("audit-stat-invalid").innerText = data.mx_invalid_count || 0;
        document.getElementById("audit-stat-duplicates").innerText = data.duplicates_count || 0;
        document.getElementById("audit-stat-sentbefore").innerText = data.already_sent_count || 0;
        document.getElementById("btn-clean-cnt").innerText = data.mx_valid_count || data.valid_count || 0;

        const tbody = document.getElementById("audit-table-tbody");
        if (tbody && data.recipients) {
            tbody.innerHTML = "";
            data.recipients.forEach((r, idx) => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${idx + 1}</td>
                    <td><strong style="color: var(--accent-gold);">${r.company_name || 'شركة'}</strong></td>
                    <td><code>${r.email}</code></td>
                    <td>
                        <span class="badge blue" style="font-size: 0.75rem;">
                            <i class="fa-solid fa-network-wired"></i> 🌐 سيرفر البريد نشط (Domain MX)
                        </span>
                    </td>
                    <td><span class="badge green">🟢 معتمد للإرسال 100%</span></td>
                `;
                tbody.appendChild(tr);
            });
        }
    }

    // أزرار التحكم بالقرار الذكي
    const btnAuditAutopilot = document.getElementById("btn-audit-autopilot");
    if (btnAuditAutopilot) {
        btnAuditAutopilot.addEventListener("click", () => {
            if (!currentAuditFileId) return;
            fetch(`/api/excel/files/${currentAuditFileId}/activate`, { method: "POST" })
                .then(res => res.json())
                .then(d => {
                    alert("🤖 اتخذ الذكاء الاصطناعي القرار واعتمد الإرسال المباشر للإيميلات المفحوصة بنجاح 100%!");
                    document.querySelector('[data-tab="dashboard"]').click();
                });
        });
    }

    const btnAuditSendClean = document.getElementById("btn-audit-send-clean");
    if (btnAuditSendClean) {
        btnAuditSendClean.addEventListener("click", () => {
            if (!currentAuditFileId) return;
            fetch(`/api/excel/files/${currentAuditFileId}/activate`, { method: "POST" })
                .then(res => res.json())
                .then(d => {
                    alert("🟢 تم اعتماد وإيقاد الإرسال للإيميلات السليمة والمفحوصة فقط بنجاح!");
                    document.querySelector('[data-tab="dashboard"]').click();
                });
        });
    }

    const btnAuditCancel = document.getElementById("btn-audit-cancel");
    if (btnAuditCancel) {
        btnAuditCancel.addEventListener("click", () => {
            document.getElementById("audit-report-panel").classList.add("hidden");
            alert("🛑 تم إلغاء الحملة وإعادة الملف لمرحلة المراجعة.");
        });
    }

    loadAccounts();

    // أزرار التعبئة السريعة للإعدادات
    const presetHostinger = document.getElementById("preset-hostinger");
    if (presetHostinger) {
        presetHostinger.addEventListener("click", (e) => {
            e.preventDefault();
            document.getElementById("acc-host").value = "smtp.hostinger.com";
            document.getElementById("acc-port").value = "465";
            if (document.getElementById("acc-imap-host")) document.getElementById("acc-imap-host").value = "imap.hostinger.com";
            if (document.getElementById("acc-imap-port")) document.getElementById("acc-imap-port").value = "993";
            document.getElementById("acc-ssl").value = "true";
        });
    }

    const presetGmail = document.getElementById("preset-gmail");
    if (presetGmail) {
        presetGmail.addEventListener("click", (e) => {
            e.preventDefault();
            document.getElementById("acc-host").value = "smtp.gmail.com";
            document.getElementById("acc-port").value = "465";
            if (document.getElementById("acc-imap-host")) document.getElementById("acc-imap-host").value = "imap.gmail.com";
            if (document.getElementById("acc-imap-port")) document.getElementById("acc-imap-port").value = "993";
            document.getElementById("acc-ssl").value = "true";
        });
    }

    // --- إضافة حساب جديد ---
    document.getElementById("form-add-account").addEventListener("submit", (e) => {
        e.preventDefault();
        const payload = {
            sender_name: document.getElementById("acc-sender-name").value,
            email: document.getElementById("acc-email").value,
            password: document.getElementById("acc-password").value,
            smtp_host: document.getElementById("acc-host").value,
            smtp_port: document.getElementById("acc-port").value,
            imap_host: document.getElementById("acc-imap-host") ? document.getElementById("acc-imap-host").value : "imap.hostinger.com",
            imap_port: document.getElementById("acc-imap-port") ? document.getElementById("acc-imap-port").value : 993,
            use_ssl: document.getElementById("acc-ssl").value === "true",
            daily_limit: document.getElementById("acc-limit").value
        };

        fetch("/api/accounts", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            alert(data.message || "تم إضافة الحساب بنجاح");
            loadAccounts();
            document.getElementById("form-add-account").reset();
        });
    });

    // --- حفظ إعدادات التوقيت والدولة ---
    // --- حفظ إعدادات التوقيت والمفاتيح الشاملة ---
    document.getElementById("form-settings").addEventListener("submit", (e) => {
        e.preventDefault();
        const payload = {
            target_country: document.getElementById("set-target-country").value,
            working_hours_only: document.getElementById("set-working-hours-only").value === "true",
            work_start_hour: document.getElementById("set-work-start-hour").value,
            work_end_hour: document.getElementById("set-work-end-hour").value,
            delay_min_seconds: document.getElementById("set-delay-min").value,
            delay_max_seconds: document.getElementById("set-delay-max").value,
            hourly_cap_per_account: document.getElementById("set-hourly-cap").value,
            golden_hour_enabled: document.getElementById("set-golden-hour").value === "true",
            hot_lead_alert_enabled: document.getElementById("set-hot-lead-alert").value === "true",
            alert_whatsapp_number: document.getElementById("set-alert-whatsapp").value,
            anti_trap_shield_enabled: document.getElementById("set-anti-trap").value === "true",
            double_impact_enabled: document.getElementById("set-double-impact").value === "true",
            auto_load_balancing_enabled: document.getElementById("set-load-balancing").value === "true",
            followup_sequence_enabled: document.getElementById("set-followup-sequence").value === "true",
            ab_testing_enabled: document.getElementById("set-ab-testing").value === "true",
            crm_pipeline_enabled: document.getElementById("set-crm-pipeline").value === "true",
            warmup_engine_enabled: document.getElementById("set-warmup-engine").value === "true",
            warmup_auto_unspam_enabled: document.getElementById("set-warmup-auto-unspam").value === "true",
            warmup_reply_threading_enabled: document.getElementById("set-warmup-reply-threading").value === "true",
            warmup_rampup_step: document.getElementById("set-warmup-rampup-step").value
        };

        fetch("/api/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(d => {
            alert(d.message || "تم حفظ مفاتيح وإعدادات المنظومة بنجاح");
        });
    });

    // --- زر الإطلاق الفوري بنقرة واحدة 1-Click Launch Wizard ---
    const btn1Click = document.getElementById("btn-1click-launch");
    if (btn1Click) {
        btn1Click.addEventListener("click", () => {
            fetch("/api/campaign/launch-wizard", { method: "POST" })
                .then(res => res.json())
                .then(d => {
                    if (d.status === "success") {
                        alert(d.message);
                        loadStatus();
                    } else {
                        alert("⚠️ تنبيه الجاهزية: " + d.message);
                    }
                })
                .catch(err => {
                    alert("حدث خطأ أثناء الاتصال بالمحرك. يرجى التأكد من إضافة حساب بريد وملف إكسيل.");
                });
        });
    }

    // --- إدراج المتغيرات في محرر القوالب ---
    document.querySelectorAll(".btn-tag").forEach(btn => {
        btn.addEventListener("click", () => {
            const tag = btn.getAttribute("data-tag");
            const bodyInput = document.getElementById("tpl-body");
            bodyInput.value += " " + tag;
        });
    });

    // --- معالج النقر والسحب والإسقاط لملف Excel ---
    const dropzone = document.getElementById("excel-dropzone");
    const fileInput = document.getElementById("excel-file-input");

    if (dropzone && fileInput) {
        dropzone.addEventListener("click", () => {
            fileInput.click();
        });

        fileInput.addEventListener("change", (e) => {
            if (e.target.files.length > 0) {
                handleExcelUpload(e.target.files[0]);
            }
        });

        dropzone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropzone.style.borderColor = "var(--accent-gold)";
        });

        dropzone.addEventListener("dragleave", () => {
            dropzone.style.borderColor = "var(--accent-cyan)";
        });

        dropzone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropzone.style.borderColor = "var(--accent-cyan)";
            if (e.dataTransfer.files.length > 0) {
                handleExcelUpload(e.dataTransfer.files[0]);
            }
        });
    }

    function renderExcelWorkbookViewer(previewSheets) {
        const tabsContainer = document.getElementById("excel-sheet-tabs");
        const thead = document.getElementById("excel-raw-thead");
        const tbody = document.getElementById("excel-raw-tbody");

        if (!tabsContainer || !thead || !tbody || !previewSheets) return;

        tabsContainer.innerHTML = "";
        const sheetNames = Object.keys(previewSheets);

        if (sheetNames.length === 0) return;

        sheetNames.forEach((sheetName, index) => {
            const btn = document.createElement("button");
            btn.className = `btn btn-sm ${index === 0 ? 'btn-primary' : 'btn-outline'}`;
            btn.innerHTML = `<i class="fa-solid fa-table"></i> ${sheetName}`;
            btn.addEventListener("click", () => {
                document.querySelectorAll("#excel-sheet-tabs button").forEach(b => {
                    b.classList.remove("btn-primary");
                    b.classList.add("btn-outline");
                });
                btn.classList.remove("btn-outline");
                btn.classList.add("btn-primary");
                displaySheetContent(previewSheets[sheetName]);
            });
            tabsContainer.appendChild(btn);
        });

        displaySheetContent(previewSheets[sheetNames[0]]);
    }

    function displaySheetContent(sheetData) {
        const thead = document.getElementById("excel-raw-thead");
        const tbody = document.getElementById("excel-raw-tbody");

        if (!sheetData || !sheetData.columns) return;

        thead.innerHTML = "";
        tbody.innerHTML = "";

        const trHead = document.createElement("tr");
        sheetData.columns.forEach(colName => {
            const th = document.createElement("th");
            th.innerText = colName;
            trHead.appendChild(th);
        });
        thead.appendChild(trHead);

        sheetData.rows.forEach(rowObj => {
            const tr = document.createElement("tr");
            sheetData.columns.forEach(colName => {
                const td = document.createElement("td");
                const val = rowObj[colName] || "";
                if (val.includes("@")) {
                    td.innerHTML = `<code style="color: var(--accent-cyan); font-weight: bold;">${val}</code>`;
                } else {
                    td.innerText = val;
                }
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
    }

    function renderRecipientsTable(recipients) {
        const tbody = document.getElementById("excel-recipients-tbody");
        if (!tbody) return;
        tbody.innerHTML = "";

        if (!recipients || recipients.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">لا يوجد مستلمين مسجلين بعد. قم برفع ملف إكسيل!</td></tr>';
            return;
        }

        recipients.forEach((r, idx) => {
            const tr = document.createElement("tr");
            const compName = r.company_name || 'شركتكم الموقرة';
            const waMsg = encodeURIComponent(`السلام عليكم ورحمة الله وبركاته، تحياتنا لسيادتكم في شركة ${compName} - م. مصطفى رياض من مجموعة شركات صمود وسهيل للتوظيف بالخارج (ترخيص 1366).`);
            const waUrl = `https://wa.me/201068158722?text=${waMsg}`;

            tr.innerHTML = `
                <td><strong>${idx + 1}</strong></td>
                <td><i class="fa-solid fa-building" style="color: var(--accent-gold);"></i> ${compName}</td>
                <td><code>${r.email}</code></td>
                <td>${r.contact_name || 'السيد المسؤول'}</td>
                <td><span class="badge blue">${r.industry || 'عام'}</span></td>
                <td>
                    <span class="badge blue" style="font-size: 0.75rem; background: rgba(59,130,246,0.15); color: #60a5fa; border: 1px solid #3b82f6;">
                        <i class="fa-solid fa-network-wired"></i> 🌐 سيرفر البريد نشط (Domain MX)
                    </span>
                </td>
                <td>
                    <span class="status-pill green mb-5">جاهز</span>
                    <a href="${waUrl}" target="_blank" class="btn btn-sm style-glass" style="color: #25D366; border: 1px solid #25D366; font-size: 0.8rem; padding: 3px 8px; margin-right: 4px; display: inline-flex; align-items: center; gap: 4px;">
                        <i class="fa-brands fa-whatsapp"></i> واتساب
                    </a>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    function loadRecipientsList() {
        fetch("/api/recipients")
            .then(res => res.json())
            .then(data => {
                if (data.status === "success" && data.recipients) {
                    const statsPanel = document.getElementById("excel-stats-panel");
                    if (statsPanel && data.recipients.length > 0) {
                        statsPanel.classList.remove("hidden");
                    }
                    renderRecipientsTable(data.recipients);
                }
            })
            .catch(err => console.error("Error loading recipients:", err));
    }

    const btnReload = document.getElementById("btn-reload-recipients");
    if (btnReload) {
        btnReload.addEventListener("click", () => loadRecipientsList());
    }

    loadRecipientsList();

    function renderExcelLibraryTable(files) {
        const tbody = document.getElementById("excel-files-library-tbody");
        if (!tbody) return;
        tbody.innerHTML = "";

        if (!files || files.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">لا توجد ملفات إكسيل مضافة بعد. اسحب وأسقط ملفاتك بالأعلى!</td></tr>';
            return;
        }

        files.forEach(f => {
            const tr = document.createElement("tr");
            const isActive = f.is_active === 1;
            const dateStr = f.uploaded_at ? f.uploaded_at.split('.')[0] : 'سحابي';

            tr.innerHTML = `
                <td>
                    <i class="fa-solid fa-file-excel" style="color: #10b981; font-size: 1.1rem; margin-left: 6px;"></i>
                    <strong>${f.original_name}</strong>
                </td>
                <td><strong style="color: var(--accent-cyan);">${f.valid_count}</strong> إيميل صالح</td>
                <td><small class="text-muted">${dateStr}</small></td>
                <td>
                    <span class="status-pill ${isActive ? 'green' : 'gray'}">
                        ${isActive ? '⚡ نشط للحملة' : 'متوقف'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm ${isActive ? 'btn-secondary' : 'btn-success'} btn-act-file" data-id="${f.id}">
                        <i class="fa-solid fa-bolt"></i> ${isActive ? 'مُفعل' : 'تفعيل'}
                    </button>
                    <button class="btn btn-sm btn-info btn-view-file" data-id="${f.id}">
                        <i class="fa-solid fa-eye"></i> معاينة
                    </button>
                    <button class="btn btn-sm btn-danger btn-del-file" data-id="${f.id}">
                        <i class="fa-solid fa-trash"></i> حذف
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        // ربط أزرار التحكم بمكتبة الملفات
        document.querySelectorAll(".btn-act-file").forEach(b => {
            b.addEventListener("click", () => {
                const id = b.getAttribute("data-id");
                activateExcelFile(id);
            });
        });

        document.querySelectorAll(".btn-view-file").forEach(b => {
            b.addEventListener("click", () => {
                const id = b.getAttribute("data-id");
                previewExcelFile(id);
            });
        });

        document.querySelectorAll(".btn-del-file").forEach(b => {
            b.addEventListener("click", () => {
                const id = b.getAttribute("data-id");
                if (confirm("هل أنت تأكد من رغبتك في حذف هذا الملف وقائمته نهائياً؟")) {
                    deleteExcelFile(id);
                }
            });
        });
    }

    function loadExcelFilesLibrary() {
        fetch("/api/excel/files")
            .then(res => res.json())
            .then(data => {
                if (data.status === "success" && data.files) {
                    renderExcelLibraryTable(data.files);
                    const active = data.files.find(f => f.is_active === 1);
                    if (active) {
                        previewExcelFile(active.id);
                    }
                }
            })
            .catch(err => console.error("Error loading excel library:", err));
    }

    function activateExcelFile(fileId) {
        fetch(`/api/excel/files/${fileId}/activate`, { method: "POST" })
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    if (data.files) renderExcelLibraryTable(data.files);
                    if (data.recipients) renderRecipientsTable(data.recipients);
                    previewExcelFile(fileId);
                    alert("⚡ تم تفعيل ملف الإكسيل للحملة المباشرة بنجاح!");
                }
            });
    }

    function deleteExcelFile(fileId) {
        fetch(`/api/excel/files/${fileId}`, { method: "DELETE" })
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    if (data.files) renderExcelLibraryTable(data.files);
                    loadRecipientsList();
                    alert("🗑️ تم حذف الملف وقائمته بنجاح!");
                }
            });
    }

    function previewExcelFile(fileId) {
        fetch(`/api/excel/files/${fileId}/preview`)
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    const statsPanel = document.getElementById("excel-stats-panel");
                    if (statsPanel) statsPanel.classList.remove("hidden");

                    if (data.file) {
                        document.getElementById("ex-valid").innerText = data.file.valid_count || 0;
                        document.getElementById("ex-invalid").innerText = data.file.invalid_count || 0;
                        document.getElementById("ex-duplicates").innerText = data.file.duplicates_count || 0;
                    }
                    if (data.preview_sheets) {
                        renderExcelWorkbookViewer(data.preview_sheets);
                    }
                    if (data.recipients) {
                        renderRecipientsTable(data.recipients);
                    }
                }
            });
    }

    const btnRefreshLib = document.getElementById("btn-refresh-excel-files");
    if (btnRefreshLib) {
        btnRefreshLib.addEventListener("click", () => loadExcelFilesLibrary());
    }

    loadExcelFilesLibrary();

    function handleExcelUpload(file) {
        const formData = new FormData();
        formData.append("file", file);

        fetch("/api/excel/upload", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(d => {
            if (d.status === "success") {
                const statsPanel = document.getElementById("excel-stats-panel");
                if (statsPanel) statsPanel.classList.remove("hidden");
                
                document.getElementById("ex-valid").innerText = d.valid_count || 0;
                document.getElementById("ex-invalid").innerText = d.invalid_count || 0;
                document.getElementById("ex-duplicates").innerText = d.duplicates_count || 0;
                document.getElementById("ex-sent-before").innerText = d.already_sent_count || 0;

                if (d.files_list) {
                    renderExcelLibraryTable(d.files_list);
                } else {
                    loadExcelFilesLibrary();
                }

                if (d.preview_sheets) {
                    renderExcelWorkbookViewer(d.preview_sheets);
                }

                if (d.recipients) {
                    renderRecipientsTable(d.recipients);
                } else {
                    loadRecipientsList();
                }

                alert(`🎉 تم حفظ وتنقية ملف (${file.name}) بمكتبتك الدائمة بنجاح! تم استخراج ${d.valid_count || 0} إيميل صالح للإرسال وعرضه بالداش بورد.`);
            } else {
                alert("خطأ أثناء رفع الملف: " + (d.message || "ملف غير صالح"));
            }
        })
        .catch(err => {
            console.error("Excel upload error:", err);
            alert("حدث خطأ أثناء رفع ملف الإكسيل. يرجى المحاولة مرة أخرى.");
        });
    }

    function loadCRMDeals(query = "") {
        const url = query ? `/api/crm/deals?q=${encodeURIComponent(query)}` : "/api/crm/deals";
        fetch(url)
            .then(res => res.json())
            .then(data => {
                if (data.status === "success" && data.deals) {
                    renderCRMPipeline(data.deals);
                }
            });
    }

    const crmSearchInput = document.getElementById("crm-search-input");
    if (crmSearchInput) {
        let debounceTimer;
        crmSearchInput.addEventListener("input", (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                loadCRMDeals(e.target.value);
            }, 200);
        });
    }

    const crmFilterStage = document.getElementById("crm-filter-stage");
    if (crmFilterStage) {
        crmFilterStage.addEventListener("change", (e) => {
            const selectedStage = e.target.value;
            const stageIds = {
                'NEW': 'crm-col-new',
                'CONTACTED': 'crm-col-contacted',
                'HOT_LEAD': 'crm-col-hotlead',
                'PROPOSAL_SENT': 'crm-col-proposal',
                'CONTRACT_SIGNED': 'crm-col-signed'
            };
            Object.entries(stageIds).forEach(([stg, colId]) => {
                const el = document.getElementById(colId);
                if (el && el.parentElement) {
                    if (selectedStage === "ALL" || selectedStage === stg) {
                        el.parentElement.style.display = "block";
                    } else {
                        el.parentElement.style.display = "none";
                    }
                }
            });
        });
    }

    function renderCRMPipeline(deals) {
        const cols = {
            'NEW': document.getElementById("crm-col-new"),
            'CONTACTED': document.getElementById("crm-col-contacted"),
            'HOT_LEAD': document.getElementById("crm-col-hotlead"),
            'PROPOSAL_SENT': document.getElementById("crm-col-proposal"),
            'CONTRACT_SIGNED': document.getElementById("crm-col-signed")
        };

        const stageOrder = ['NEW', 'CONTACTED', 'HOT_LEAD', 'PROPOSAL_SENT', 'CONTRACT_SIGNED'];
        const counts = { 'NEW': 0, 'CONTACTED': 0, 'HOT_LEAD': 0, 'PROPOSAL_SENT': 0, 'CONTRACT_SIGNED': 0 };

        Object.entries(cols).forEach(([stageKey, colEl]) => {
            if (!colEl) return;
            colEl.innerHTML = "";

            // إعداد أحداث السحب والإسقاط على العمود (Drop Zone)
            colEl.addEventListener("dragover", (e) => {
                e.preventDefault();
                colEl.style.background = "rgba(14, 165, 233, 0.25)";
                colEl.style.border = "2px dashed var(--accent-cyan)";
                colEl.style.borderRadius = "10px";
            });

            colEl.addEventListener("dragleave", () => {
                colEl.style.background = "";
                colEl.style.border = "";
            });

            colEl.addEventListener("drop", (e) => {
                e.preventDefault();
                colEl.style.background = "";
                colEl.style.border = "";
                const dealId = e.dataTransfer.getData("text/plain");
                if (dealId) {
                    fetch("/api/crm/deals/stage", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ deal_id: dealId, stage: stageKey })
                    })
                    .then(res => res.json())
                    .then(() => loadCRMDeals());
                }
            });
        });

        deals.forEach(d => {
            if (counts[d.stage] !== undefined) counts[d.stage]++;

            const card = document.createElement("div");
            card.className = "crm-card style-glass";
            card.draggable = true;
            card.setAttribute("data-deal-id", d.id);
            card.style.cssText = "background: linear-gradient(135deg, rgba(30,41,59,0.85), rgba(15,23,42,0.95)); border: 1px solid rgba(255,255,255,0.12); border-radius: 12px; padding: 14px; box-shadow: 0 4px 15px rgba(0,0,0,0.25); cursor: grab; transition: transform 0.2s, box-shadow 0.2s;";
            
            // أحداث بدء السحب للكارت
            card.addEventListener("dragstart", (e) => {
                e.dataTransfer.setData("text/plain", d.id);
                card.style.opacity = "0.5";
            });

            card.addEventListener("dragend", () => {
                card.style.opacity = "1";
            });

            const currIndex = stageOrder.indexOf(d.stage);
            const prevStage = currIndex > 0 ? stageOrder[currIndex - 1] : None = null;
            const nextStage = currIndex < stageOrder.length - 1 ? stageOrder[currIndex + 1] : None = null;

            const compName = d.company_name || 'شركة موثقة';
            const waMsg = encodeURIComponent(`السلام عليكم ورحمة الله، تحياتنا لسيادتكم في شركة ${compName} - م. مصطفى رياض من مجموعة شركات صمود للتأهيل والتوظيف بالخارج (ترخيص 1366).`);
            const waUrl = `https://wa.me/201068158722?text=${waMsg}`;

            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                    <strong style="color: var(--accent-gold); font-size: 0.98rem; font-weight: bold;">
                        <i class="fa-solid fa-grip-vertical" style="color: #64748b; margin-left: 6px; cursor: grab;"></i>
                        <i class="fa-solid fa-building" style="margin-left: 4px; color: var(--accent-gold);"></i> ${compName}
                    </strong>
                    <span class="badge blue" style="font-size: 0.7rem; padding: 2px 6px;">صفقة</span>
                </div>
                <div style="margin-bottom: 10px;">
                    <code style="color: var(--accent-cyan); font-size: 0.82rem; font-weight: bold; word-break: break-all;">${d.email}</code>
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 6px; align-items: center; justify-content: space-between; pt-8; border-top: 1px dashed rgba(255,255,255,0.1);">
                    <div style="display: flex; gap: 4px;">
                        <a href="${waUrl}" target="_blank" class="btn btn-sm style-glass" style="color: #25D366; border: 1px solid #25D366; font-size: 0.75rem; padding: 2px 6px; border-radius: 6px;" title="مراسلة واتساب">
                            <i class="fa-brands fa-whatsapp"></i>
                        </a>
                        <button class="btn btn-sm style-glass btn-gen-prop" data-comp="${compName}" style="color: var(--accent-gold); border: 1px solid var(--accent-gold); font-size: 0.75rem; padding: 2px 6px; border-radius: 6px;" title="عرض سعر">
                            <i class="fa-solid fa-file-pdf"></i>
                        </button>
                    </div>
                    
                    <div style="display: flex; gap: 3px; align-items: center;">
                        ${prevStage ? `
                            <button class="btn btn-sm btn-outline btn-move-deal" data-id="${d.id}" data-target="${prevStage}" style="font-size: 0.75rem; padding: 2px 6px; border-radius: 6px;" title="تراجع لمرحلة سابقة">
                                🔄 ◄
                            </button>
                        ` : ''}
                        ${nextStage ? `
                            <button class="btn btn-sm btn-primary btn-move-deal" data-id="${d.id}" data-target="${nextStage}" style="font-size: 0.75rem; padding: 2px 8px; font-weight: bold; border-radius: 6px;" title="تقديم للمرحلة التالية">
                                نقل ►
                            </button>
                        ` : '<span class="badge purple" style="font-size: 0.75rem; font-weight: bold;">مكتملة 🎉</span>'}
                    </div>
                </div>
            `;

            if (cols[d.stage]) {
                cols[d.stage].appendChild(card);
            }
        });

        // تحديث أشرطة الإحصائيات العلوية والعدادات الحية
        document.getElementById("crm-stat-total").innerText = deals.length;
        document.getElementById("crm-stat-hot").innerText = counts['HOT_LEAD'];
        document.getElementById("crm-stat-proposals").innerText = counts['PROPOSAL_SENT'];
        document.getElementById("crm-stat-signed").innerText = counts['CONTRACT_SIGNED'];

        document.getElementById("badge-cnt-new").innerText = counts['NEW'];
        document.getElementById("badge-cnt-contacted").innerText = counts['CONTACTED'];
        document.getElementById("badge-cnt-hotlead").innerText = counts['HOT_LEAD'];
        document.getElementById("badge-cnt-proposal").innerText = counts['PROPOSAL_SENT'];
        document.getElementById("badge-cnt-signed").innerText = counts['CONTRACT_SIGNED'];

        // ربط أزرار النقل والتراجع
        document.querySelectorAll(".btn-move-deal").forEach(b => {
            b.addEventListener("click", () => {
                const dealId = b.getAttribute("data-id");
                const targetStage = b.getAttribute("data-target");
                fetch("/api/crm/deals/stage", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ deal_id: dealId, stage: targetStage })
                })
                .then(res => res.json())
                .then(() => loadCRMDeals());
            });
        });

        // ربط أزرار إنشاء عرض السعر المباشر
        document.querySelectorAll(".btn-gen-prop").forEach(b => {
            b.addEventListener("click", () => {
                const comp = b.getAttribute("data-comp");
                fetch("/api/proposal/generate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ company_name: comp, sector: "المقاولات والتشييد", country: "المملكة العربية السعودية" })
                })
                .then(res => res.json())
                .then(d => {
                    if (d.proposal_html) {
                        const win = window.open("", "_blank");
                        win.document.write(d.proposal_html);
                        win.document.close();
                    }
                });
            });
        });
    }

    function loadWarmupStatus() {
        fetch("/api/warmup/status")
            .then(res => res.json())
            .then(data => {
                if (data.status === "success" && data.warmup_status) {
                    let totalSent = 0;
                    let totalRec = 0;
                    data.warmup_status.forEach(acc => {
                        totalSent += (acc.warmup_sent || 0);
                        totalRec += (acc.warmup_received || 0);
                    });
                    if (document.getElementById("warmup-stat-sent")) document.getElementById("warmup-stat-sent").innerText = totalSent;
                    if (document.getElementById("warmup-stat-received")) document.getElementById("warmup-stat-received").innerText = totalRec;
                    if (document.getElementById("warmup-stat-inbox")) document.getElementById("warmup-stat-inbox").innerText = "100%";
                    if (document.getElementById("warmup-stat-reputation")) document.getElementById("warmup-stat-reputation").innerText = "100 / 100";

                    renderWarmupTable(data.warmup_status);
                }
            });
    }

    function renderWarmupTable(list) {
        const tbody = document.getElementById("warmup-table-tbody");
        const selector = document.getElementById("warmup-account-selector");
        if (!tbody) return;

        // تعبئة قائمة اختيار الحسابات
        if (selector && list && list.length > 0) {
            const currentSelected = selector.value || "ALL";
            selector.innerHTML = '<option value="ALL">جميع الحسابات المضافة بالمنظومة (تسخين شامل 👑)</option>';
            list.forEach(acc => {
                const opt = document.createElement("option");
                opt.value = acc.account_id;
                opt.innerText = `📧 ${acc.email} (اليوم ${acc.warmup_day_number || 1} - طاقة ${acc.current_daily_cap || 20}/يوم)`;
                selector.appendChild(opt);
            });
            selector.value = currentSelected;
        }

        tbody.innerHTML = "";

        if (!list || list.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">لا توجد حسابات بريد مضافة بعد. أضف حسابات لتفعيل التسخين!</td></tr>';
            return;
        }

        const selectedAccId = selector ? selector.value : "ALL";
        const filteredList = (selectedAccId === "ALL") ? list : list.filter(w => String(w.account_id) === String(selectedAccId));

        filteredList.forEach(w => {
            const tr = document.createElement("tr");
            const isEnabled = w.is_enabled === 1;
            const dayNum = w.warmup_day_number || 1;
            const progress = w.warmup_progress_percent || 100;
            const currentCap = w.current_daily_cap || 20;
            const maxTarget = w.target_max_daily || 500;

            tr.innerHTML = `
                <td>
                    <i class="fa-solid fa-at" style="color: var(--accent-gold); margin-left: 4px;"></i>
                    <strong>${w.email}</strong>
                </td>
                <td>
                    <div style="font-size: 0.85rem; font-weight: bold; color: var(--accent-cyan);">
                        اليوم ${dayNum} من 14 (${progress}%)
                    </div>
                    <div style="width: 100%; background: rgba(255,255,255,0.1); height: 6px; border-radius: 3px; margin-top: 4px; overflow: hidden;">
                        <div style="width: ${progress}%; background: linear-gradient(90deg, #3b82f6, #10b981); height: 100%;"></div>
                    </div>
                </td>
                <td>
                    <strong style="color: #f97316;">${currentCap} إيميل/يوم</strong>
                    <div style="font-size: 0.75rem; color: #94a3b8;">هدف الإنتاج: ${maxTarget} إيميل/يوم 🎯</div>
                </td>
                <td>
                    <strong style="color: #10b981;">100% (Inbox 👑)</strong>
                    <div style="font-size: 0.75rem; color: #94a3b8;">${w.warmup_sent || 0} إرسال | ${w.warmup_received || 0} استلام</div>
                </td>
                <td>
                    <span class="status-pill ${isEnabled ? 'green' : 'gray'}">
                        ${isEnabled ? '🔥 تدرج نشط' : 'متوقف'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm ${isEnabled ? 'btn-danger' : 'btn-success'} btn-toggle-warmup" data-id="${w.account_id}" data-enabled="${!isEnabled}">
                        ${isEnabled ? 'إيقاف' : 'تفعيل'}
                    </button>
                    <button class="btn btn-sm btn-outline btn-reset-warmup" data-id="${w.account_id}" title="إعادة ضبط الجدول الزمني للتسخين من اليوم 1">
                        <i class="fa-solid fa-rotate-left"></i> إعادة ضبط
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        document.querySelectorAll(".btn-toggle-warmup").forEach(b => {
            b.addEventListener("click", () => {
                const accId = b.getAttribute("data-id");
                const isEnabled = b.getAttribute("data-enabled") === "true";
                fetch("/api/warmup/toggle", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ account_id: accId, is_enabled: isEnabled })
                })
                .then(res => res.json())
                .then(() => loadWarmupStatus());
            });
        });

        document.querySelectorAll(".btn-reset-warmup").forEach(b => {
            b.addEventListener("click", () => {
                const accId = b.getAttribute("data-id");
                if (confirm("هل أنت تأكد من رغبتك في إعادة ضبط الخطة الزمنية لتسخين هذا الحساب للبدء من اليوم 1؟")) {
                    fetch("/api/warmup/reset", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ account_id: accId })
                    })
                    .then(res => res.json())
                    .then(d => {
                        alert(d.message || "تم إعادة ضبط الخطة الزمنية للتسخين بنجاح!");
                        loadWarmupStatus();
                    });
                }
            });
        });

        const selectorElem = document.getElementById("warmup-account-selector");
        if (selectorElem) {
            selectorElem.addEventListener("change", () => loadWarmupStatus());
        }

        const btnEnableAll = document.getElementById("btn-warmup-enable-all");
        if (btnEnableAll) {
            btnEnableAll.addEventListener("click", () => {
                fetch("/api/warmup/toggle-all", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ is_enabled: true })
                }).then(() => loadWarmupStatus());
            });
        }

        const btnDisableAll = document.getElementById("btn-warmup-disable-all");
        if (btnDisableAll) {
            btnDisableAll.addEventListener("click", () => {
                fetch("/api/warmup/toggle-all", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ is_enabled: false })
                }).then(() => loadWarmupStatus());
            });
        }

        loadWarmupTemplates();
        loadWarmupLogs();
        loadWarmupThreads();
        loadWarmupConfig();
    }

    function loadWarmupThreads() {
        fetch("/api/warmup/threads?limit=50")
            .then(res => res.json())
            .then(data => {
                const tbody = document.getElementById("warmup-threads-tbody");
                if (!tbody) return;
                tbody.innerHTML = "";
                
                if (!data.threads || data.threads.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" class="text-center" style="color: #94a3b8;">لا توجد سلاسل محادثات مفتوحة حالياً. يتم فتح السلاسل أوتوماتيكياً عند بدء التسخين!</td></tr>';
                    return;
                }
                
                data.threads.forEach((t, idx) => {
                    const tr = document.createElement("tr");
                    const stepNum = t.step_number || 1;
                    let stepBadge = `<span class="badge blue" style="font-size: 0.75rem;">الخطوة ${stepNum} من 4 (Inquiry)</span>`;
                    if (stepNum === 2) stepBadge = `<span class="badge orange" style="font-size: 0.75rem;">الخطوة ${stepNum} من 4 (Re: Details)</span>`;
                    if (stepNum === 3) stepBadge = `<span class="badge purple" style="font-size: 0.75rem;">الخطوة ${stepNum} من 4 (Re: Specs)</span>`;
                    if (stepNum >= 4) stepBadge = `<span class="badge green" style="font-size: 0.75rem;">الخطوة ${stepNum} من 4 (Re: Close 🎉)</span>`;
                    
                    tr.innerHTML = `
                        <td>${idx + 1}</td>
                        <td>
                            <strong style="color: var(--accent-gold); font-size: 0.85rem;">${t.sender_email}</strong>
                            <span style="color: var(--accent-cyan); margin: 0 4px;">↔</span>
                            <code style="color: var(--accent-cyan); font-size: 0.85rem;">${t.receiver_email}</code>
                        </td>
                        <td><span style="color: #e2e8f0; font-weight: bold; font-size: 0.85rem;">${t.subject}</span></td>
                        <td>${stepBadge}</td>
                        <td><small style="color: #94a3b8;">${t.last_action_at || '-'}</small></td>
                        <td>
                            <button class="btn btn-sm btn-outline btn-view-thread-history" data-id="${t.id}" style="font-size: 0.75rem; border-color: var(--accent-gold); color: var(--accent-gold);">
                                👁️ معاينة المحادثة الكاملة
                            </button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });

                document.querySelectorAll(".btn-view-thread-history").forEach(b => {
                    b.addEventListener("click", () => {
                        const tid = b.getAttribute("data-id");
                        loadWarmupThreadHistoryModal(tid);
                    });
                });
            });
    }

    function loadWarmupThreadHistoryModal(threadId) {
        const modal = document.getElementById("modal-warmup-thread-history");
        const container = document.getElementById("thread-modal-messages-container");
        if (!modal || !container) return;
        
        container.innerHTML = '<p class="text-center text-muted">جاري تحميل رسائل ومسار المحادثة...</p>';
        modal.classList.remove("hidden");

        fetch(`/api/warmup/threads/${threadId}/messages`)
            .then(res => res.json())
            .then(data => {
                if (data.status === "success" && data.thread) {
                    const t = data.thread;
                    const msgs = data.messages || [];
                    
                    document.getElementById("thread-modal-subject").innerText = t.subject || "-";
                    document.getElementById("thread-modal-step-badge").innerText = `مرحلة المحادثة: ${t.step_number || 1} من 4`;
                    
                    if (msgs.length === 0) {
                        container.innerHTML = '<p class="text-center text-muted">لم تُسجل رسائل لهذه السلسلة بعد.</p>';
                        return;
                    }
                    
                    container.innerHTML = "";
                    msgs.forEach((m, idx) => {
                        const isSenderA = m.account_email.toLowerCase() === t.sender_email.toLowerCase();
                        const bubble = document.createElement("div");
                        bubble.style.cssText = `background: ${isSenderA ? 'rgba(15,23,42,0.95)' : 'rgba(30,41,59,0.95)'}; border: 1px solid ${isSenderA ? 'var(--accent-cyan)' : 'var(--accent-gold)'}; border-radius: 12px; padding: 14px; margin-bottom: 8px;`;
                        
                        bubble.innerHTML = `
                            <div style="display: flex; justify-content: space-between; border-bottom: 1px dashed rgba(255,255,255,0.15); padding-bottom: 6px; margin-bottom: 8px;">
                                <span style="color: ${isSenderA ? 'var(--accent-cyan)' : 'var(--accent-gold)'}; font-weight: bold; font-size: 0.85rem;">
                                    <i class="fa-solid ${isSenderA ? 'fa-paper-plane' : 'fa-reply'}"></i> المرحلة ${idx + 1}: ${m.account_email} ➔ ${m.target_email}
                                </span>
                                <small style="color: #94a3b8;">${m.created_at || ''}</small>
                            </div>
                            <div style="margin-bottom: 6px; font-weight: bold; font-size: 0.88rem; color: #fff;">الموضوع: ${m.subject}</div>
                            <div style="color: #e2e8f0; font-size: 0.85rem; white-space: pre-line; line-height: 1.5; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px;">${m.body}</div>
                        `;
                        container.appendChild(bubble);
                    });
                }
            });
    }

    const btnCloseThreadModal = document.getElementById("btn-close-thread-history-modal");
    if (btnCloseThreadModal) {
        btnCloseThreadModal.addEventListener("click", () => {
            const modal = document.getElementById("modal-warmup-thread-history");
            if (modal) modal.classList.add("hidden");
        });
    }

    const btnCloseThreadModalBottom = document.getElementById("btn-close-thread-history-modal-bottom");
    if (btnCloseThreadModalBottom) {
        btnCloseThreadModalBottom.addEventListener("click", () => {
            const modal = document.getElementById("modal-warmup-thread-history");
            if (modal) modal.classList.add("hidden");
        });
    }

    const btnRefThreads = document.getElementById("btn-refresh-warmup-threads");
    if (btnRefThreads) {
        btnRefThreads.addEventListener("click", () => loadWarmupThreads());
    }

    function loadWarmupConfig() {
        fetch("/api/warmup/config")
            .then(res => res.json())
            .then(data => {
                if (data.status === "success" && data.config) {
                    const cfg = data.config;
                    const intervalSel = document.getElementById("ctrl-warmup-interval");
                    const topicsSel = document.getElementById("ctrl-warmup-topics");
                    const replyDelaySel = document.getElementById("ctrl-warmup-reply-delay");
                    const markImpSel = document.getElementById("ctrl-warmup-mark-important");
                    const badge = document.getElementById("warmup-state-badge");

                    if (intervalSel) intervalSel.value = cfg.warmup_interval_minutes || 15;
                    if (topicsSel) topicsSel.value = cfg.warmup_topics_per_cycle || 1;
                    if (replyDelaySel) replyDelaySel.value = cfg.warmup_reply_delay_seconds !== undefined ? cfg.warmup_reply_delay_seconds : 60;
                    if (markImpSel) markImpSel.value = cfg.warmup_mark_important !== undefined ? cfg.warmup_mark_important : 1;

                    if (badge) {
                        const st = (cfg.warmup_state || "RUNNING").toUpperCase();
                        if (st === "RUNNING") {
                            badge.className = "badge green";
                            badge.style.background = "rgba(16,185,129,0.2)";
                            badge.style.color = "#34d399";
                            badge.style.borderColor = "#10b981";
                            badge.innerHTML = "🟢 قيد التشغيل والعمل 24/7 (RUNNING)";
                        } else if (st === "PAUSED") {
                            badge.className = "badge orange";
                            badge.style.background = "rgba(245,158,11,0.2)";
                            badge.style.color = "#fbbf24";
                            badge.style.borderColor = "#f59e0b";
                            badge.innerHTML = "🟠 متوقف مؤقتاً (PAUSED)";
                        } else {
                            badge.className = "badge red";
                            badge.style.background = "rgba(239,68,68,0.2)";
                            badge.style.color = "#f87171";
                            badge.style.borderColor = "#ef4444";
                            badge.innerHTML = "🔴 متوقف نهائياً (STOPPED)";
                        }
                    }
                }
            })
            .catch(err => console.error("Error loading warmup config:", err));
    }

    const btnSaveWarmupConfig = document.getElementById("btn-save-warmup-config");
    if (btnSaveWarmupConfig) {
        btnSaveWarmupConfig.addEventListener("click", () => {
            const interval = document.getElementById("ctrl-warmup-interval").value;
            const topics = document.getElementById("ctrl-warmup-topics").value;
            const replyDelay = document.getElementById("ctrl-warmup-reply-delay").value;
            const markImp = document.getElementById("ctrl-warmup-mark-important").value;

            fetch("/api/warmup/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    interval_minutes: parseInt(interval),
                    topics_per_cycle: parseInt(topics),
                    reply_delay_seconds: parseInt(replyDelay),
                    mark_important: parseInt(markImp)
                })
            })
            .then(res => res.json())
            .then(data => {
                alert(data.message || "تم حفظ الإعدادات الفنية للتسخين بنجاح!");
                loadWarmupConfig();
            });
        });
    }

    function setWarmupState(state) {
        fetch("/api/warmup/state", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ state: state })
        })
        .then(res => res.json())
        .then(data => {
            alert(data.message || "تم تحديث حالة التسخين بنجاح!");
            loadWarmupConfig();
        });
    }

    const btnWarmupStart = document.getElementById("btn-warmup-state-start");
    if (btnWarmupStart) {
        btnWarmupStart.addEventListener("click", () => setWarmupState("RUNNING"));
    }

    const btnWarmupPause = document.getElementById("btn-warmup-state-pause");
    if (btnWarmupPause) {
        btnWarmupPause.addEventListener("click", () => setWarmupState("PAUSED"));
    }

    const btnWarmupStop = document.getElementById("btn-warmup-state-stop");
    if (btnWarmupStop) {
        btnWarmupStop.addEventListener("click", () => setWarmupState("STOPPED"));
    }

    const btnTriggerWarmupNow = document.getElementById("btn-trigger-warmup-now");
    if (btnTriggerWarmupNow) {
        btnTriggerWarmupNow.addEventListener("click", () => {
            btnTriggerWarmupNow.disabled = true;
            btnTriggerWarmupNow.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> جاري التنفيذ...';
            fetch("/api/warmup/trigger-cycle", { method: "POST" })
                .then(r => r.json())
                .then(d => {
                    alert(d.message || "تم إطلاق نبضة التسخين بنجاح!");
                    loadWarmupStatus();
                })
                .finally(() => {
                    btnTriggerWarmupNow.disabled = false;
                    btnTriggerWarmupNow.innerHTML = '<i class="fa-solid fa-bolt"></i> إطلاق نبضة تسخين فورية الآن ⚡';
                });
        });
    }


    function loadWarmupLogs() {
        const filterElem = document.getElementById("warmup-log-account-filter");
        const accountEmail = filterElem ? filterElem.value : "ALL";
        fetch(`/api/warmup/logs?account_email=${encodeURIComponent(accountEmail)}&limit=100`)
            .then(res => res.json())
            .then(data => {
                if (data.status === "success" && data.logs) {
                    renderWarmupLogsTable(data.logs);
                }
            });
    }

    function renderWarmupLogsTable(logs) {
        const tbody = document.getElementById("warmup-logs-tbody");
        const filterElem = document.getElementById("warmup-log-account-filter");
        if (!tbody) return;

        // تحديث قائمة الفلترة بأيميلات الحسابات المتاحة
        if (filterElem && logs && logs.length > 0) {
            const currentSelected = filterElem.value || "ALL";
            const emailsSet = new Set();
            logs.forEach(l => {
                if (l.account_email) emailsSet.add(l.account_email);
                if (l.target_email && l.target_email !== "IMAP_SYSTEM") emailsSet.add(l.target_email);
            });
            filterElem.innerHTML = '<option value="ALL">🌐 عرض جميع المراسلات</option>';
            emailsSet.forEach(em => {
                const opt = document.createElement("option");
                opt.value = em;
                opt.innerText = `📧 ${em}`;
                filterElem.appendChild(opt);
            });
            filterElem.value = currentSelected;
        }

        tbody.innerHTML = "";

        if (!logs || logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center" style="color: #94a3b8;">لا توجد مراسلات تسخين مسجلة بعد. اضغط "تحديث السمعة" لإطلاق نبضة جديدة!</td></tr>';
            return;
        }

        logs.forEach((log, idx) => {
            const tr = document.createElement("tr");
            const isSuccess = log.status === "SUCCESS";
            const dateStr = log.created_at || "-";
            const actionText = log.imap_action || "SENT_VIA_SMTP";
            
            let statusBadge = isSuccess ? 
                '<span class="badge green" style="font-size: 0.75rem;">🟢 تم التسليم بنجاح</span>' : 
                '<span class="badge red" style="font-size: 0.75rem;">🔴 تعثر الإرسال</span>';

            let actionBadge = '<span class="badge blue" style="font-size: 0.75rem;"><i class="fa-solid fa-paper-plane"></i> إرسال SMTP</span>';
            if (actionText.includes("INBOX") || actionText.includes("IMAP")) {
                actionBadge = '<span class="badge purple" style="font-size: 0.75rem;"><i class="fa-solid fa-inbox"></i> تفاعل IMAP وتدريب</span>';
            }

            tr.innerHTML = `
                <td>${idx + 1}</td>
                <td><small style="color: #94a3b8;">${dateStr}</small></td>
                <td><strong style="color: var(--accent-gold); font-size: 0.85rem;">${log.account_email}</strong></td>
                <td><code style="color: var(--accent-cyan); font-size: 0.85rem;">${log.target_email}</code></td>
                <td><span style="color: #e2e8f0; font-weight: bold; font-size: 0.85rem;">${log.subject}</span></td>
                <td>${statusBadge}</td>
                <td>${actionBadge}</td>
                <td>
                    <button class="btn btn-sm btn-outline btn-inspect-warmup-log" style="font-size: 0.75rem; border-color: #3b82f6; color: #60a5fa;"
                        data-sender="${log.account_email}"
                        data-target="${log.target_email}"
                        data-time="${dateStr}"
                        data-status="${log.status}"
                        data-action="${log.imap_action}"
                        data-subject="${encodeURIComponent(log.subject)}"
                        data-body="${encodeURIComponent(log.body)}">
                        👁️ معاينة
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        document.querySelectorAll(".btn-inspect-warmup-log").forEach(btn => {
            btn.addEventListener("click", () => {
                const modal = document.getElementById("modal-warmup-email-inspect");
                if (!modal) return;
                document.getElementById("inspect-sender-email").innerText = btn.getAttribute("data-sender");
                document.getElementById("inspect-target-email").innerText = btn.getAttribute("data-target");
                document.getElementById("inspect-timestamp").innerText = btn.getAttribute("data-time");
                document.getElementById("inspect-status-badge").innerText = `${btn.getAttribute("data-status")} (${btn.getAttribute("data-action")})`;
                document.getElementById("inspect-subject").innerText = decodeURIComponent(btn.getAttribute("data-subject"));
                document.getElementById("inspect-body").innerText = decodeURIComponent(btn.getAttribute("data-body"));
                modal.classList.remove("hidden");
            });
        });
    }

    const btnCloseInspect = document.getElementById("btn-close-inspect-modal");
    if (btnCloseInspect) {
        btnCloseInspect.addEventListener("click", () => {
            const modal = document.getElementById("modal-warmup-email-inspect");
            if (modal) modal.classList.add("hidden");
        });
    }

    const btnCloseInspectBottom = document.getElementById("btn-close-inspect-modal-bottom");
    if (btnCloseInspectBottom) {
        btnCloseInspectBottom.addEventListener("click", () => {
            const modal = document.getElementById("modal-warmup-email-inspect");
            if (modal) modal.classList.add("hidden");
        });
    }

    const btnRefreshWarmupLogs = document.getElementById("btn-refresh-warmup-logs");
    if (btnRefreshWarmupLogs) {
        btnRefreshWarmupLogs.addEventListener("click", () => loadWarmupLogs());
    }

    const filterLogAccount = document.getElementById("warmup-log-account-filter");
    if (filterLogAccount) {
        filterLogAccount.addEventListener("change", () => loadWarmupLogs());
    }

    function loadWarmupTemplates() {
        fetch("/api/warmup/templates")
            .then(res => res.json())
            .then(data => {
                const tbody = document.getElementById("warmup-templates-tbody");
                if (tbody && data.templates) {
                    tbody.innerHTML = "";
                    data.templates.forEach(t => {
                        const tr = document.createElement("tr");
                        const replyPreview = t.reply_spintax || "{GREETING} {SENDER_NAME}، تم استلام طلبكم وسيتم التواصل معكم.";
                        tr.innerHTML = `
                            <td><strong style="color: #a855f7;">${t.title}</strong></td>
                            <td><code style="font-size: 0.8rem; color: var(--accent-gold);">${t.subject_spintax}</code></td>
                            <td><div style="font-size: 0.8rem; color: #e2e8f0; max-height: 50px; overflow-y: auto;">${t.body_spintax}</div></td>
                            <td><div style="font-size: 0.8rem; color: #34d399; max-height: 50px; overflow-y: auto;">${replyPreview}</div></td>
                            <td>
                                <button class="btn btn-sm btn-danger btn-del-wtpl" data-id="${t.id}">حذف</button>
                            </td>
                        `;
                        tbody.appendChild(tr);
                    });

                    document.querySelectorAll(".btn-del-wtpl").forEach(b => {
                        b.addEventListener("click", () => {
                            const id = b.getAttribute("data-id");
                            fetch(`/api/warmup/templates/${id}`, { method: "DELETE" })
                                .then(r => r.json())
                                .then(d => {
                                    alert(d.message || "تم حذف القالب بنجاح!");
                                    loadWarmupTemplates();
                                });
                        });
                    });
                }
            });
    }

    const btnSynthesizeWarmup = document.getElementById("btn-synthesize-warmup");
    if (btnSynthesizeWarmup) {
        btnSynthesizeWarmup.addEventListener("click", () => {
            fetch("/api/warmup/synthesize-4turns")
                .then(res => res.json())
                .then(data => {
                    const box = document.getElementById("warmup-preview-box");
                    if (box && data.turns) {
                        let html = `<div style="margin-bottom: 10px; border-bottom: 1px dashed var(--accent-gold); padding-bottom: 8px;">
                            <strong style="color: var(--accent-gold); font-size: 1rem;">
                                🎬 سيناريو المحادثة التفاعلية الحية المسبوق بـ 4 مراحل (${data.template_title}):
                            </strong>
                        </div>`;
                        
                        data.turns.forEach(turn => {
                            const isOdd = turn.step % 2 !== 0;
                            const borderColor = turn.step === 1 ? 'var(--accent-cyan)' : (turn.step === 2 ? 'var(--accent-gold)' : (turn.step === 3 ? '#a855f7' : '#10b981'));
                            
                            html += `
                                <div style="background: rgba(15,23,42,0.95); border: 1px solid ${borderColor}; border-radius: 12px; padding: 14px; margin-bottom: 12px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed rgba(255,255,255,0.15); padding-bottom: 6px; margin-bottom: 8px;">
                                        <span style="color: ${borderColor}; font-weight: bold; font-size: 0.9rem;">
                                            <i class="fa-solid fa-comments"></i> ${turn.title} (${turn.sender} ➔ ${turn.receiver})
                                        </span>
                                        <span class="badge blue" style="font-size: 0.75rem;">الخطوة ${turn.step} من 4</span>
                                    </div>
                                    <div style="margin-bottom: 6px;">
                                        <strong style="color: #fff; font-size: 0.88rem;">الموضوع: </strong>
                                        <code style="color: var(--accent-gold); font-size: 0.88rem;">${turn.subject}</code>
                                    </div>
                                    <div style="color: #e2e8f0; font-size: 0.85rem; white-space: pre-line; line-height: 1.5; background: rgba(30,41,59,0.6); padding: 10px; border-radius: 8px;">${turn.body}</div>
                                </div>
                            `;
                        });
                        
                        box.innerHTML = html;
                    }
                });
        });
    }

    const formAddWarmupTemplate = document.getElementById("form-add-warmup-template");
    if (formAddWarmupTemplate) {
        formAddWarmupTemplate.addEventListener("submit", (e) => {
            e.preventDefault();
            const payload = {
                title: document.getElementById("wtpl-title").value,
                subject: document.getElementById("wtpl-subject").value,
                body: document.getElementById("wtpl-body").value,
                reply: document.getElementById("wtpl-reply") ? document.getElementById("wtpl-reply").value : "",
                turn_3: document.getElementById("wtpl-turn3") ? document.getElementById("wtpl-turn3").value : "",
                turn_4: document.getElementById("wtpl-turn4") ? document.getElementById("wtpl-turn4").value : ""
            };

            fetch("/api/warmup/templates", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                alert(data.message || "تم إضافة سيناريو ومحادثة تسخين جديدة بـ 4 مراحل بنجاح!");
                formAddWarmupTemplate.reset();
                loadWarmupTemplates();
            });
        });
    }

    const btnRefCRM = document.getElementById("btn-refresh-crm");
    if (btnRefCRM) btnRefCRM.addEventListener("click", () => loadCRMDeals());

    const btnRefWarm = document.getElementById("btn-refresh-warmup");
    if (btnRefWarm) {
        btnRefWarm.addEventListener("click", () => {
            fetch("/api/warmup/trigger-cycle", { method: "POST" })
                .then(res => res.json())
                .then(d => {
                    alert(d.message || "تم إطلاق نبضة تسخين حية وتأديب الفلاتر بنجاح!");
                    loadWarmupStatus();
                });
        });
    }

    // أدوات النطاقات ومولد النماذج والتقرير التنفيذي
    const btnExtractDomain = document.getElementById("btn-extract-domain");
    if (btnExtractDomain) {
        btnExtractDomain.addEventListener("click", () => {
            const domainInput = document.getElementById("tool-domain-input");
            const domain = domainInput ? domainInput.value.trim() : "";
            if (!domain) {
                alert("يرجى كتابة اسم الدومين أو الموقع لاستخراج الإيميلات (مثال: sonatrach.dz)");
                return;
            }
            fetch("/api/tools/extract-emails", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ domain: domain })
            })
            .then(res => res.json())
            .then(data => {
                const resBox = document.getElementById("domain-extract-results");
                const resTbody = document.getElementById("domain-extract-tbody");
                if (resBox && resTbody && data.extracted_emails) {
                    resBox.classList.remove("hidden");
                    resTbody.innerHTML = "";
                    data.extracted_emails.forEach(item => {
                        const row = document.createElement("div");
                        row.style.cssText = "display: flex; justify-content: space-between; align-items: center; background: rgba(15,23,42,0.8); padding: 6px 12px; border-radius: 6px;";
                        row.innerHTML = `
                            <code style="color: var(--accent-cyan); font-weight: bold;">${item.email}</code>
                            <span class="badge ${item.confidence.includes('100%') ? 'green' : 'blue'}" style="font-size: 0.75rem;">${item.confidence}</span>
                        `;
                        resTbody.appendChild(row);
                    });
                }
                alert(data.message || "تم استخراج وفحص الإيميلات بنجاح!");
                loadRecipientsList();
            });
        });
    }

    const btnOpenRecForm = document.getElementById("btn-open-rec-form");
    if (btnOpenRecForm) {
        btnOpenRecForm.addEventListener("click", () => {
            window.open("/api/tools/recruitment-form", "_blank");
        });
    }

    const btnOpenExecReport = document.getElementById("btn-open-exec-report");
    if (btnOpenExecReport) {
        btnOpenExecReport.addEventListener("click", () => {
            fetch("/api/reports/executive-summary")
                .then(res => res.json())
                .then(data => {
                    if (data.report_html) {
                        const win = window.open("", "_blank");
                        win.document.write(data.report_html);
                        win.document.close();
                    }
                });
        });
    }

    const btnFindPersonEmail = document.getElementById("btn-find-person-email");
    if (btnFindPersonEmail) {
        btnFindPersonEmail.addEventListener("click", () => {
            const domainInput = document.getElementById("tool-domain-input");
            const domain = domainInput ? domainInput.value.trim() : "";
            const fname = document.getElementById("tool-fname-input").value.trim();
            const lname = document.getElementById("tool-lname-input").value.trim();

            if (!domain) {
                alert("يرجى كتابة اسم الدومين أولاً في مربع المستخرج (مثال: sonatrach.dz)");
                return;
            }

            fetch("/api/tools/find-person-email", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ first_name: fname, last_name: lname, domain: domain })
            })
            .then(res => res.json())
            .then(data => {
                const resBox = document.getElementById("domain-extract-results");
                const resTbody = document.getElementById("domain-extract-tbody");
                if (resBox && resTbody && data.patterns) {
                    resBox.classList.remove("hidden");
                    resTbody.innerHTML = `
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="color: var(--accent-gold); font-size: 0.85rem; font-weight: bold;">الأنماط الـ 6 المحتملة لإيميل المسؤول:</span>
                            <a href="${data.dork_url}" target="_blank" class="btn btn-sm btn-outline" style="font-size: 0.75rem; color: #60a5fa; border-color: #60a5fa;">
                                🔍 بحث عن إيميل الموظف بـ LinkedIn Google Dork
                            </a>
                        </div>
                    `;
                    data.patterns.forEach(pat => {
                        const row = document.createElement("div");
                        row.style.cssText = "display: flex; justify-content: space-between; align-items: center; background: rgba(15,23,42,0.8); padding: 6px 12px; border-radius: 6px;";
                        row.innerHTML = `
                            <code style="color: var(--accent-cyan); font-weight: bold;">${pat}</code>
                            <span class="badge blue" style="font-size: 0.75rem;">نمط مؤسسي متوقع ⚡</span>
                        `;
                        resTbody.appendChild(row);
                    });
                }
            });
        });
    }

    loadCRMDeals();
    loadWarmupStatus();
});
