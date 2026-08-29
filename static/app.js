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
        fetch("/api/logout", { method: "POST" })
            .then(() => {
                document.cookie = "samood_session=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                localStorage.removeItem("samood_token");
                window.location.href = "/login.html";
            });
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
                document.getElementById("stat-sent").innerText = data.sent_count;
                document.getElementById("stat-failed").innerText = data.failed_count;
                document.getElementById("stat-unsub").innerText = data.unsub_count;
                document.getElementById("stat-active-acc").innerText = data.active_accounts_count;

                const dot = document.getElementById("global-status-dot");
                const statusText = document.getElementById("global-status-text");

                if (data.status === "RUNNING") {
                    dot.className = "status-dot active";
                    statusText.innerText = "الحملة شغالة حالياً...";
                } else if (data.status === "PAUSED") {
                    dot.className = "status-dot";
                    statusText.innerText = "الحملة متوقفة مؤقتاً";
                } else {
                    dot.className = "status-dot";
                    statusText.innerText = "جاهز وبانتظار البدء";
                }

                if (data.total_records > 0) {
                    const pct = Math.round((data.current_index / data.total_records) * 100);
                    document.getElementById("progress-bar").style.width = `${pct}%`;
                    document.getElementById("progress-text").innerText = `التقدم: ${data.current_index} من ${data.total_records} (${pct}%)`;
                }
            })
            .catch(err => console.error("Error fetching status:", err));
    }

    fetchStatus();
    setInterval(fetchStatus, 3000);

    // --- الاتصال ببث الأحداث الحي SSE ---
    function initSSE() {
        const evtSource = new EventSource("/api/events");
        const terminal = document.getElementById("terminal-logs");

        evtSource.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                const line = document.createElement("div");
                line.className = "log-line";

                if (data.type === "SENDING") {
                    line.className = "log-line system";
                    line.innerText = `[${new Date().toLocaleTimeString()}] ${data.log}`;
                } else if (data.type === "PROGRESS") {
                    line.className = "log-line success";
                    line.innerText = `[${new Date().toLocaleTimeString()}] ${data.log} - (التالي بعد ${data.next_delay_seconds} ثانية)`;
                    document.getElementById("countdown-text").innerText = `الإيميل التالي بعد ${data.next_delay_seconds} ثانية...`;
                } else if (data.type === "PAUSED" || data.type === "CIRCUIT_BREAKER_TRIPPED") {
                    line.className = "log-line error";
                    line.innerText = `[${new Date().toLocaleTimeString()}] ${data.message}`;
                } else {
                    line.innerText = `[${new Date().toLocaleTimeString()}] ${data.message || data.log}`;
                }

                terminal.appendChild(line);
                terminal.scrollTop = terminal.scrollHeight;
                fetchStatus();
            } catch (e) {
                console.error("SSE parse error:", e);
            }
        };
    }

    initSSE();

    // --- أزرار التحكم بالحملة ---
    document.getElementById("btn-start").addEventListener("click", () => {
        fetch("/api/campaign/start", { method: "POST" })
            .then(res => res.json())
            .then(d => {
                alert(d.message);
                fetchStatus();
            })
            .catch(err => alert("خطأ: " + err));
    });

    document.getElementById("btn-pause").addEventListener("click", () => {
        fetch("/api/campaign/pause", { method: "POST" })
            .then(res => res.json())
            .then(d => fetchStatus());
    });

    document.getElementById("btn-stop").addEventListener("click", () => {
        fetch("/api/campaign/stop", { method: "POST" })
            .then(res => res.json())
            .then(d => fetchStatus());
    });

    document.getElementById("btn-clear-logs").addEventListener("click", () => {
        document.getElementById("terminal-logs").innerHTML = "";
    });

    // --- رفع ملفات Excel ---
    const dropzone = document.getElementById("excel-dropzone");
    const fileInput = document.getElementById("excel-file-input");

    dropzone.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            uploadFile(e.target.files[0]);
        }
    });

    function uploadFile(file) {
        const formData = new FormData();
        formData.append("file", file);

        fetch("/api/upload-excel", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                document.getElementById("excel-stats-panel").classList.remove("hidden");
                document.getElementById("ex-valid").innerText = data.stats.valid_count;
                document.getElementById("ex-invalid").innerText = data.stats.invalid_count;
                document.getElementById("ex-duplicates").innerText = data.stats.duplicate_in_file;
                document.getElementById("ex-sent-before").innerText = data.stats.already_sent_count;
                fetchStatus();
            } else {
                alert("خطأ: " + data.detail);
            }
        })
        .catch(err => alert("فشل رفع الملف: " + err));
    }

    // --- تحميل الحسابات المسجلة ---
    function loadAccounts() {
        fetch("/api/accounts")
            .then(res => res.json())
            .then(accounts => {
                const tbody = document.getElementById("accounts-table-body");
                tbody.innerHTML = "";
                if (accounts.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" class="text-center">لا توجد حسابات مسجلة بعد. قم بإضافة حسابك الأول بالأعلى!</td></tr>';
                    return;
                }

                accounts.forEach(acc => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td>${acc.sender_name}</td>
                        <td>${acc.email}</td>
                        <td>${acc.smtp_host}:${acc.smtp_port}</td>
                        <td>${acc.sent_today} / ${acc.daily_limit}</td>
                        <td><span class="badge ${acc.is_active ? 'green' : 'red'}">${acc.is_active ? 'نشط' : 'متوقف'}</span></td>
                        <td><button class="btn btn-sm btn-danger btn-del-acc" data-id="${acc.id}">حذف</button></td>
                    `;
                    tbody.appendChild(tr);
                });

                document.querySelectorAll(".btn-del-acc").forEach(btn => {
                    btn.addEventListener("click", (e) => {
                        const id = e.target.getAttribute("data-id");
                        fetch(`/api/accounts/${id}`, { method: "DELETE" })
                            .then(res => res.json())
                            .then(d => loadAccounts());
                    });
                });
            });
    }

    loadAccounts();

    // --- تجهيز Presets الحسابات ---
    document.getElementById("preset-hostinger").addEventListener("click", () => {
        document.getElementById("acc-host").value = "smtp.hostinger.com";
        document.getElementById("acc-port").value = 465;
        document.getElementById("acc-ssl").value = "true";
    });

    document.getElementById("preset-gmail").addEventListener("click", () => {
        document.getElementById("acc-host").value = "smtp.gmail.com";
        document.getElementById("acc-port").value = 587;
        document.getElementById("acc-ssl").value = "false";
    });

    // --- إضافة حساب جديد ---
    document.getElementById("form-add-account").addEventListener("submit", (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append("sender_name", document.getElementById("acc-sender-name").value);
        formData.append("email", document.getElementById("acc-email").value);
        formData.append("password", document.getElementById("acc-password").value);
        formData.append("smtp_host", document.getElementById("acc-host").value);
        formData.append("smtp_port", document.getElementById("acc-port").value);
        formData.append("use_ssl", document.getElementById("acc-ssl").value);
        formData.append("daily_limit", document.getElementById("acc-limit").value);

        fetch("/api/accounts", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                loadAccounts();
                document.getElementById("form-add-account").reset();
            } else {
                alert("خطأ: " + data.detail);
            }
        })
        .catch(err => alert("فشل الفحص والإضافة: " + err));
    });

    // --- تغيير كلمة المرور ---
    document.getElementById("form-change-pwd").addEventListener("submit", (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append("old_password", document.getElementById("pwd-old").value);
        formData.append("new_password", document.getElementById("pwd-new").value);

        fetch("/api/change-password", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(d => {
            alert(d.message || d.detail);
            document.getElementById("form-change-pwd").reset();
        })
        .catch(err => alert("خطأ: " + err));
    });

    // --- إدراج المتغيرات في محرر القوالب ---
    document.querySelectorAll(".btn-tag").forEach(btn => {
        btn.addEventListener("click", () => {
            const tag = btn.getAttribute("data-tag");
            const bodyInput = document.getElementById("tpl-body");
            bodyInput.value += " " + tag;
        });
    });
});
