<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>GAMMA 雲端智慧照護平台</title>
  
  <!-- 載入 Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  
  <!-- 載入 FontAwesome 圖示庫 -->
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
  
  <!-- 載入 React 與 Babel (讓瀏覽器直接看懂 React 語法) -->
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>

  <!-- 載入 Firebase (Compat 版本，最適合單一 HTML 使用) -->
  <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js"></script>
  <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-auth-compat.js"></script>
  <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore-compat.js"></script>

  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background-color: #f8fafc; color: #1e293b; -webkit-tap-highlight-color: transparent; padding-bottom: env(safe-area-inset-bottom); }
    .no-scrollbar::-webkit-scrollbar { display: none; }
    .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
    input[type=range] { -webkit-appearance: none; background: transparent; height: 30px; }
    input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; height: 24px; width: 24px; border-radius: 50%; background: #fff; border: 2px solid currentColor; margin-top: -10px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); transition: transform 0.1s; }
    input[type=range]::-webkit-slider-thumb:active { transform: scale(1.2); }
    input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 4px; background: #e2e8f0; border-radius: 2px; }
    .pb-safe { padding-bottom: max(12px, env(safe-area-inset-bottom)); }
  </style>
</head>
<body>
  <div id="root"></div>

  <script type="text/babel">
    const { useState, useEffect, useMemo } = React;

    // ==========================================
    // 1. 圖示對應系統 (替換原有的 Lucide Icons)
    // ==========================================
    const iconMapping = {
      Activity: "fa-chart-line", Heart: "fa-heart", User: "fa-user",
      ClipboardList: "fa-clipboard-list", Database: "fa-database",
      MessageSquare: "fa-comment-dots", ChevronRight: "fa-chevron-right",
      Copy: "fa-copy", CheckCircle: "fa-circle-check", Plus: "fa-plus",
      Save: "fa-floppy-disk", HeartPulse: "fa-heart-pulse", Droplet: "fa-droplet",
      Box: "fa-cube", AlertTriangle: "fa-triangle-exclamation",
      ShieldCheck: "fa-shield-halved", Stethoscope: "fa-stethoscope",
      Wind: "fa-wind", Users: "fa-users", Bell: "fa-bell",
      BookOpen: "fa-book-open", RefreshCw: "fa-arrows-rotate",
      Dumbbell: "fa-dumbbell", Share2: "fa-share-nodes", Brain: "fa-brain",
      Pill: "fa-pills", Search: "fa-magnifying-glass", Trash2: "fa-trash-can",
      LogIn: "fa-right-to-bracket", LogOut: "fa-right-from-bracket",
      Download: "fa-download", MonitorSmartphone: "fa-mobile-screen"
    };

    const IconComponents = {};
    Object.keys(iconMapping).forEach(name => {
      IconComponents[name] = ({ className, size }) => (
        <i className={`fa-solid ${iconMapping[name]} ${className || ''}`} style={{ fontSize: size ? `${size}px` : 'inherit' }}></i>
      );
    });
    
    const { 
      Activity, Heart, User, ClipboardList, Database, MessageSquare, 
      ChevronRight, Copy, CheckCircle, Plus, Save, HeartPulse, Droplet, 
      Box, AlertTriangle, ShieldCheck, Stethoscope, Wind, Users, Bell, 
      BookOpen, RefreshCw, Dumbbell, Share2, Brain, Pill, Search, Trash2,
      LogIn, LogOut, Download, MonitorSmartphone
    } = IconComponents;

    // ==========================================
    // 2. Firebase 雲端引擎適配器
    // ==========================================
    let app, auth, db;
    
    // 【請在這裡填入您的 Firebase Config】 
    // 若未填寫，系統將自動以「本地展示模式」運行
    let firebaseConfig = {};
    if (typeof __firebase_config !== 'undefined') {
        try { firebaseConfig = JSON.parse(__firebase_config); } catch(e){}
    }

    try {
      if (Object.keys(firebaseConfig).length > 0 && !firebase.apps.length) {
        app = firebase.initializeApp(firebaseConfig);
        auth = firebase.auth();
        db = firebase.firestore();
      }
    } catch (e) {
      console.error("Cloud Engine Init Error", e);
    }

    const appId = typeof __app_id !== 'undefined' ? __app_id : 'gamma-health-cloud-v1';

    // Firebase Modular API 模擬器 (為了相容既有代碼)
    const signInAnonymously = (a) => a.signInAnonymously();
    const signInWithCustomToken = (a, t) => a.signInWithCustomToken(t);
    const onAuthStateChanged = (a, cb) => a.onAuthStateChanged(cb);
    const GoogleAuthProvider = firebase.auth ? firebase.auth.GoogleAuthProvider : null;
    const signInWithPopup = (a, p) => a.signInWithPopup(p);
    const signOut = (a) => a.signOut();
    const collection = (d, ...paths) => d.collection(paths.join('/'));
    const addDoc = (ref, data) => ref.add(data);
    const onSnapshot = (ref, onNext, onError) => {
      return ref.onSnapshot((snap) => {
        onNext({ docs: snap.docs.map(doc => ({ id: doc.id, data: () => doc.data() })) });
      }, onError);
    };

    // ==========================================
    // 3. 醫學知識庫與 Prompt
    // ==========================================
    const PROMPTS = [
      { id: '01', title: '01-體檢報告提取', desc: '拍照 -> 結構化數據', content: '# Role: 醫療數據提取專家\n\n**Task:** 請將我提供的體檢報告圖片，轉換為結構化的 JSON 或 CSV 格式，提取出異常指標。' },
      { id: '02', title: '02-藥盒識別', desc: '拍藥盒 -> 用藥清單', content: '# Role: 藥師 AI\n\n**Task:** 根據上傳的藥盒照片，列出：藥品名稱、主要功效、用法用量、禁忌症與交互作用。' },
      { id: '03', title: '03-趨勢分析', desc: '歷史對比 + 異常標註', content: '# Role: 健康數據分析師\n\n**Task:** 對比我提供的歷次體檢數據，畫出重點異常指標的變化趨勢，並標註風險等級。' },
      { id: '04', title: '04-最新血脂評估', desc: '代入 2026 PREVENT', content: '# Role: 心臟科臨床 AI\n\n**Task:** 根據我提供的血脂數據與病史，使用 2026 AHA/ACC 最新指引與 PREVENT 方程式，評估我的十年心血管風險，並給予 LDL-C 目標值建議。' },
      { id: '05', title: '05-KDIGO 腎病評估', desc: '糖腎共病用藥建議', content: '# Role: 腎臟科臨床 AI\n\n**Task:** 根據我的 eGFR、UACR (尿液白蛋白/肌酸酐比值) 與糖尿病史，依據 KDIGO 2026 糖尿病與 CKD 指引，提供 SGLT2i、GLP-1 RA 或 nsMRA (如 Finerenone) 的用藥評估與血壓控制建議。' },
      { id: '06', title: '06-AWGS 肌少症篩查', desc: '肌肉流失風險評估', content: '# Role: 高齡醫學 AI\n\n**Task:** 根據我提供的年齡、性別、握力 (kg) 與小腿圍 (cm)，依據 AWGS 2025 最新亞洲肌少症共識，評估是否達到肌少症標準，並給予蛋白質攝取與阻力訓練建議。' },
      { id: '07', title: '07-ACB 抗膽鹼減藥', desc: '高齡藥物負擔評估', content: '# Role: 高齡醫學與臨床藥師 AI\n\n**Task:** 根據我提供的長輩用藥清單與 ACB (抗膽鹼) 總分，評估哪些藥物可能導致其跌倒、譫妄或認知退化，並列出建議與醫師討論的「減藥/換藥清單」。' }
    ];

    const ACB_DATABASE = [
      { name: 'Amitriptyline (阿米替林)', score: 3, category: '抗憂鬱藥' },
      { name: 'Chlorpheniramine (氯苯那敏/感冒藥)', score: 3, category: '抗組織胺(一代)' },
      { name: 'Diphenhydramine (苯海拉明/助眠)', score: 3, category: '抗組織胺(一代)' },
      { name: 'Oxybutynin (奧昔布寧)', score: 3, category: '泌尿道解痙藥 (頻尿)' },
      { name: 'Quetiapine (思覺思/喹硫平)', score: 3, category: '抗精神病藥' },
      { name: 'Paroxetine (克憂果/帕羅西汀)', score: 3, category: '抗憂鬱藥' },
      { name: 'Tolterodine (得舒妥)', score: 3, category: '泌尿道解痙藥 (頻尿)' },
      { name: 'Atropine (阿托品)', score: 3, category: '解痙/散瞳' },
      { name: 'Carbamazepine (卡馬西平/癲通)', score: 2, category: '抗癲癇/神經痛' },
      { name: 'Cetirizine (驅黑敏/西替利嗪)', score: 2, category: '抗組織胺(二代)' },
      { name: 'Loperamide (洛哌丁胺/止瀉藥)', score: 2, category: '腸胃藥' },
      { name: 'Tramadol (曲馬多)', score: 2, category: '止痛藥' },
      { name: 'Amantadine (金剛胺)', score: 2, category: '巴金森氏症藥' },
      { name: 'Alprazolam (讚安諾/阿普唑侖)', score: 1, category: '抗焦慮/安眠' },
      { name: 'Diazepam (得靜/地西泮)', score: 1, category: '抗焦慮/肌肉鬆弛' },
      { name: 'Digoxin (毛地黃)', score: 1, category: '心臟/心衰竭藥' },
      { name: 'Furosemide (弗西米/利尿劑)', score: 1, category: '降血壓/消水腫' },
      { name: 'Metoprolol (美托洛爾)', score: 1, category: '降血壓/心律' },
      { name: 'Warfarin (華法林)', score: 1, category: '抗凝血劑' },
      { name: 'Haloperidol (好度)', score: 1, category: '抗精神病藥' }
    ];

    // ==========================================
    // 4. 主應用程式 App Component
    // ==========================================
    const App = () => {
      const [activeTab, setActiveTab] = useState('hub');
      const [copiedId, setCopiedId] = useState(null);
      const [disclaimerAccepted, setDisclaimerAccepted] = useState(false);
      
      const [user, setUser] = useState(null);
      const [trackingData, setTrackingData] = useState([]);
      const [isSyncing, setIsSyncing] = useState(true);
      
      const [showAddForm, setShowAddForm] = useState(false);
      const [newMetric, setNewMetric] = useState({ date: new Date().toISOString().split('T')[0], metric: '', value: '', unit: '', status: '正常' });

      const [risks, setRisks] = useState({ isMale: true, cvd: false, dm: false, ckd: false, age: false, smoke: false, family: false });
      const [vitals, setVitals] = useState({ sbp: 120, dbp: 80, ldl: 100, a1c: 5.5, grip: 30, calf: 35 });

      const [acbSearch, setAcbSearch] = useState('');
      const [acbSelectedDrugs, setAcbSelectedDrugs] = useState([]);

      // Auth Effect
      useEffect(() => {
        if (!auth) {
          setIsSyncing(false);
          return;
        }
        const initAuth = async () => {
          try {
            if (typeof __initial_auth_token !== 'undefined' && __initial_auth_token) {
              await signInWithCustomToken(auth, __initial_auth_token);
            } else {
              await signInAnonymously(auth);
            }
          } catch (error) {
            console.error("Auth Engine Failed", error);
            setIsSyncing(false);
          }
        };
        const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
          if (currentUser) setUser(currentUser);
          else initAuth();
        });
        return () => unsubscribe();
      }, []);

      const handleGoogleLogin = async () => {
        if (!auth || !GoogleAuthProvider) return alert("雲端服務未初始化！請檢查 Config。");
        try {
          await signInWithPopup(auth, new GoogleAuthProvider());
          alert("✅ 成功連結 Google 帳號！您的資料將跨裝置同步。");
        } catch (error) {
          console.error("Google Login Failed", error);
          alert("Google 登入失敗，請確認彈出視窗設定。");
        }
      };

      const handleLogout = async () => {
        if (!auth) return;
        try {
          await signOut(auth);
          alert("已登出 Google 帳號，切換回本地/匿名模式。");
        } catch (error) { console.error("Logout Failed", error); }
      };

      // DB Effect
      useEffect(() => {
        if (!user || !db) return;
        setIsSyncing(true);
        const metricsRef = collection(db, 'artifacts', appId, 'users', user.uid, 'health_metrics');
        const unsubscribe = onSnapshot(metricsRef, (snapshot) => {
          const data = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
          data.sort((a, b) => b.timestamp - a.timestamp);
          setTrackingData(data);
          setIsSyncing(false);
        }, (error) => {
          console.error("Data Sync Error", error);
          setIsSyncing(false);
        });
        return () => unsubscribe();
      }, [user]);

      const handleSaveMetric = async (metricData = newMetric) => {
        if (!metricData.metric || !metricData.value) return;
        if (!db || !user) {
          setTrackingData([{ id: Date.now().toString(), ...metricData, timestamp: Date.now() }, ...trackingData]);
          if(metricData === newMetric) setShowAddForm(false);
          return;
        }
        try {
          await addDoc(collection(db, 'artifacts', appId, 'users', user.uid, 'health_metrics'), {
            ...metricData, timestamp: Date.now()
          });
          if(metricData === newMetric) {
            setShowAddForm(false);
            setNewMetric({ date: new Date().toISOString().split('T')[0], metric: '', value: '', unit: '', status: '正常' });
          }
        } catch (error) { console.error("Save Failed", error); }
      };

      const copyToClipboard = (text, id) => {
        const textArea = document.createElement("textarea");
        textArea.value = text; document.body.appendChild(textArea);
        textArea.focus(); textArea.select();
        try { document.execCommand('copy'); setCopiedId(id); setTimeout(() => setCopiedId(null), 2000); } catch (err) {}
        document.body.removeChild(textArea);
      };

      const exportToCSV = () => {
        if (trackingData.length === 0) return alert("沒有可匯出的數據！");
        const headers = ["日期", "指標名稱", "數值", "單位", "狀態"];
        const csvContent = [headers.join(","), ...trackingData.map(row => `${row.date},"${row.metric}","${row.value}","${row.unit}","${row.status}")`)].join("\n");
        const blob = new Blob(["\ufeff" + csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a"); link.href = url;
        link.setAttribute("download", `gamma_health_records_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link); link.click(); document.body.removeChild(link);
      };

      const exportToFHIR = () => {
        const payload = {
          resourceType: "Bundle", type: "document", timestamp: new Date().toISOString(),
          patientId: user ? user.uid : "anonymous", vitals: vitals, risks: risks, analysis: metabolicAnalysis.report
        };
        const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a"); link.href = url;
        link.setAttribute("download", `gamma_fhir_report_${new Date().toISOString().split('T')[0]}.json`);
        document.body.appendChild(link); link.click(); document.body.removeChild(link);
        alert("✅ 成功產生 HL7 FHIR 格式 JSON，並下載至您的裝置！");
      };

      const metabolicAnalysis = useMemo(() => {
        const { sbp, dbp, ldl, a1c, grip, calf } = vitals;
        const { cvd, dm, ckd, age, smoke, family, isMale } = risks;

        let riskCategory = "Low Risk (低風險)";
        let riskColor = "text-emerald-600";
        let ldlTarget = 116;
        let rfCount = (age ? 1 : 0) + (smoke ? 1 : 0) + (family ? 1 : 0) + (sbp >= 140 ? 1 : 0) + (ldl >= 160 ? 1 : 0);

        if (cvd && (dm || ckd || smoke || family)) { riskCategory = "Extreme Risk (極高危)"; riskColor = "text-rose-600"; ldlTarget = 55; } 
        else if (cvd || (dm && ckd)) { riskCategory = "Very High Risk (心血管/糖腎共病)"; riskColor = "text-rose-600"; ldlTarget = 55; } 
        else if (dm && (age || smoke || family || sbp >= 140)) { riskCategory = "High Risk (高危險群糖尿病)"; riskColor = "text-orange-500"; ldlTarget = 70; } 
        else if (dm) { riskCategory = "Moderate Risk (一般糖尿病)"; riskColor = "text-orange-500"; ldlTarget = 100; } 
        else if (ckd || ldl >= 190) { riskCategory = "High Risk (高危險群)"; riskColor = "text-orange-500"; ldlTarget = 70; } 
        else if (rfCount >= 2) { riskCategory = "Moderate Risk (中度風險)"; riskColor = "text-orange-500"; ldlTarget = 100; }

        if (a1c >= 6.5 && !dm && riskCategory === "Low Risk (低風險)") { riskCategory = "High Risk (新診斷糖尿病)"; riskColor = "text-orange-500"; ldlTarget = 100; }

        let bp = { status: "", class: "", action: "", target: ckd ? "&lt; 120 (KDIGO)" : "&lt; 130/80" };
        if (sbp < 120 && dbp < 80) { bp.status = "正常"; bp.class = "bg-emerald-100 text-emerald-700"; bp.action = "完美！請繼續保持。"; } 
        else if (sbp < 130 && dbp < 80) { bp.status = ckd ? "未達標(KDIGO)" : "偏高"; bp.class = ckd ? "bg-orange-100 text-orange-700" : "bg-yellow-100 text-yellow-700"; bp.action = "非藥物治療：減鹽、運動。" + (ckd ? " (KDIGO 建議 CKD 收縮壓 &lt; 120)" : ""); } 
        else if (sbp < 140 || dbp < 90) { bp.status = "第一期高血壓"; bp.class = (cvd || ckd || dm || riskCategory.includes("High")) ? "bg-orange-100 text-orange-700" : "bg-yellow-100 text-yellow-700"; bp.action = (cvd || ckd || dm || riskCategory.includes("High")) ? "建議藥物治療。" + (ckd ? " 首選 ACEi/ARB。" : "") : "嘗試生活調整 3-6 個月。"; } 
        else { bp.status = "第二期高血壓"; bp.class = "bg-rose-100 text-rose-700"; bp.action = "立即就醫藥物介入。" + (ckd ? " 首選 ACEi/ARB。" : ""); }

        let ldlRes = { status: ldl < ldlTarget ? "達標" : "未達標", class: ldl < ldlTarget ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700", action: ldl < ldlTarget ? "控制良好，請定期追蹤。" : `超出目標 (&lt; ${ldlTarget})，建議強化治療。` };

        let dmRes = { status: "", class: "", action: "", alert: "" };
        if (a1c < 5.7) { dmRes = { status: "正常", class: "bg-emerald-100 text-emerald-700", action: "血糖正常。", alert: "" }; } 
        else if (a1c < 6.5) { dmRes = { status: "前期", class: "bg-yellow-100 text-yellow-700", action: "糖尿病前期：飲食控制逆轉。", alert: (cvd || ckd) ? "需注意心腎風險。" : "" }; } 
        else {
          let alert = "";
          if (dm && ckd) alert = "KDIGO 護腎：強烈建議 SGLT2i + Metformin。";
          else if (ckd) alert = "護腎：評估 SGLT2i。";
          else if (cvd) alert = "護心：優先使用 GLP-1 RA 或 SGLT2i。";
          dmRes = { status: "糖尿病", class: "bg-purple-100 text-purple-700", action: "積極控制，定期檢測 UACR。", alert };
        }

        const lowGrip = isMale ? grip < 28 : grip < 18;
        const lowCalf = isMale ? calf < 34 : calf < 33;
        let muscleRes = { status: "", class: "", action: "", alert: "" };
        if (lowGrip && lowCalf) { muscleRes = { status: "肌少症", class: "bg-rose-100 text-rose-700", action: "確診肌少症！強烈建議介入阻力訓練。", alert: "注意跌倒與衰弱風險！" }; } 
        else if (lowGrip || lowCalf) { muscleRes = { status: "高風險", class: "bg-yellow-100 text-yellow-700", action: "肌肉量或肌力偏低，屬於高危險群。", alert: "" }; } 
        else { muscleRes = { status: "正常", class: "bg-emerald-100 text-emerald-700", action: "肌肉狀態良好。", alert: "" }; }

        let issues = [];
        if (bp.status.includes("高血壓") || bp.status.includes("未達標")) issues.push("血壓");
        if (ldlRes.status === "未達標") issues.push("血脂");
        if (dmRes.status === "糖尿病" || dmRes.status === "前期") issues.push("血糖");
        if (muscleRes.status === "肌少症" || muscleRes.status === "高風險") issues.push("肌肉流失");

        let report = { title: "", color: "", icon: CheckCircle, advice: [] };
        if (issues.length === 0) { report = { title: "控制良好", color: "bg-emerald-500", icon: CheckCircle, advice: ["您的三高與肌肉數值皆在理想範圍。", "請維持目前的健康生活習慣。"] }; } 
        else if (issues.length >= 2 || cvd || ckd) { report = { title: "高度警示", color: "bg-rose-500", icon: Bell, advice: [`您有 ${issues.length} 項指標未達標。`, "具高風險因子，建議與醫師討論器官保護藥物 (SGLT2i/GLP-1)。", ldlRes.status === "未達標" ? `血脂目標極嚴格 (&lt; ${ldlTarget})，請遵循正規用藥。` : ""] }; } 
        else { report = { title: "需注意", color: "bg-yellow-400", icon: AlertTriangle, advice: [`您的 ${issues.join("與")} 數值存在警訊。`, "建議先從飲食與運動著手改善。", "請在 3 個月後回診追蹤。"] }; }

        return { riskCategory, riskColor, ldlTarget, bp, ldlRes, dmRes, muscleRes, report };
      }, [risks, vitals]);

      const loadLatestToMetabolic = () => {
        let latestSbp = vitals.sbp, latestDbp = vitals.dbp, latestLdl = vitals.ldl, latestA1c = vitals.a1c, latestGrip = vitals.grip, latestCalf = vitals.calf;
        trackingData.forEach(item => {
          if (item.metric.includes('收縮壓')) latestSbp = Number(item.value);
          if (item.metric.includes('舒張壓')) latestDbp = Number(item.value);
          if (item.metric.toUpperCase().includes('LDL') || item.metric.includes('低密度')) latestLdl = Number(item.value);
          if (item.metric.toUpperCase().includes('A1C') || item.metric.includes('糖化')) latestA1c = Number(item.value);
          if (item.metric.includes('握力')) latestGrip = Number(item.value);
          if (item.metric.includes('小腿圍')) latestCalf = Number(item.value);
        });
        setVitals({ sbp: latestSbp, dbp: latestDbp, ldl: latestLdl, a1c: latestA1c, grip: latestGrip, calf: latestCalf });
        alert("已從雲端載入最新追蹤數據！");
      };

      const saveMetabolicToTracking = () => {
        const today = new Date().toISOString().split('T')[0];
        handleSaveMetric({ date: today, metric: '收縮壓 (SYS)', value: vitals.sbp, unit: 'mmHg', status: metabolicAnalysis.bp.status.includes('高血壓') || metabolicAnalysis.bp.status.includes('未達標') ? '異常' : '正常' });
        handleSaveMetric({ date: today, metric: '舒張壓 (DIA)', value: vitals.dbp, unit: 'mmHg', status: metabolicAnalysis.bp.status.includes('高血壓') ? '異常' : '正常' });
        handleSaveMetric({ date: today, metric: 'LDL-C (壞膽固醇)', value: vitals.ldl, unit: 'mg/dL', status: metabolicAnalysis.ldlRes.status === '未達標' ? '異常' : '正常' });
        handleSaveMetric({ date: today, metric: 'HbA1c (糖化血色素)', value: vitals.a1c, unit: '%', status: metabolicAnalysis.dmRes.status === '正常' ? '正常' : '異常' });
        handleSaveMetric({ date: today, metric: '握力 (Grip)', value: vitals.grip, unit: 'kg', status: metabolicAnalysis.muscleRes.status === '正常' ? '正常' : '異常' });
        handleSaveMetric({ date: today, metric: '小腿圍 (Calf)', value: vitals.calf, unit: 'cm', status: metabolicAnalysis.muscleRes.status === '正常' ? '正常' : '異常' });
        alert("已將目前的戰情室數值同步存入「指標追蹤庫」！");
      };

      const handleAddDrug = (drug) => { if (!acbSelectedDrugs.find(d => d.name === drug.name)) setAcbSelectedDrugs([...acbSelectedDrugs, drug]); };
      const handleRemoveDrug = (drugName) => setAcbSelectedDrugs(acbSelectedDrugs.filter(d => d.name !== drugName));
      const acbTotalScore = acbSelectedDrugs.reduce((sum, drug) => sum + drug.score, 0);

      // Render Functions
      const renderContent = () => {
        switch (activeTab) {
          case 'hub':
            return (
              <div className="space-y-6 animate-in fade-in duration-300">
                <div className="flex justify-between items-center border-b border-slate-200 pb-2">
                  <h2 className="text-2xl font-bold text-slate-800">🏠 總覽中心 (Hub)</h2>
                  {user && !user.isAnonymous ? (
                    <button onClick={handleLogout} className="text-xs bg-emerald-100 hover:bg-rose-100 text-emerald-700 hover:text-rose-700 px-3 py-1.5 rounded-full font-bold flex items-center transition-colors">
                      <CheckCircle size={14} className="mr-1"/> 已連結 Google 帳戶 <LogOut size={12} className="ml-2 opacity-50"/>
                    </button>
                  ) : (
                    <button onClick={handleGoogleLogin} className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-full font-bold flex items-center shadow-sm transition-colors">
                      <LogIn size={14} className="mr-1"/> 登入 Google 同步
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-5 border border-slate-200 rounded-xl bg-white shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center space-x-3 mb-3">
                      <HeartPulse className="text-rose-500" size={24} />
                      <h3 className="text-lg font-bold text-slate-700">三高戰情室</h3>
                    </div>
                    <p className="text-sm text-slate-500 mb-4">使用 2026 最新醫學指引，評估您的血壓、血脂、血糖綜合風險。</p>
                    <button onClick={() => setActiveTab('metabolic')} className="text-sm font-semibold text-rose-600 flex items-center hover:text-rose-800">
                      開始檢測 <ChevronRight size={16} />
                    </button>
                  </div>
                  <div className="p-5 border border-slate-200 rounded-xl bg-white shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center space-x-3 mb-3">
                      <Brain className="text-purple-500" size={24} />
                      <h3 className="text-lg font-bold text-slate-700">ACB 藥物負擔評估</h3>
                    </div>
                    <p className="text-sm text-slate-500 mb-4">抗膽鹼藥物是高齡者認知退化與跌倒的隱形殺手，計算用藥風險。</p>
                    <button onClick={() => setActiveTab('acb')} className="text-sm font-semibold text-purple-600 flex items-center hover:text-purple-800">
                      風險計算 <ChevronRight size={16} />
                    </button>
                  </div>
                  <div className="p-5 border border-slate-200 rounded-xl bg-white shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center space-x-3 mb-3">
                      <ClipboardList className="text-blue-600" size={24} />
                      <h3 className="text-lg font-bold text-slate-700">指標追蹤庫 (含匯出)</h3>
                    </div>
                    <p className="text-sm text-slate-500 mb-4">手動記錄歷次回診數值，結合 Google 帳號跨裝置同步與 CSV 匯出。</p>
                    <button onClick={() => setActiveTab('tracking')} className="text-sm font-semibold text-blue-600 flex items-center hover:text-blue-800">
                      進入數據庫 <ChevronRight size={16} />
                    </button>
                  </div>
                </div>
                
                <div className="mt-8 bg-slate-50 p-5 rounded-xl border border-slate-200 shadow-inner">
                  <h3 className="font-bold text-slate-700 mb-3 flex items-center"><Activity size={18} className="mr-2 text-slate-500"/> 系統架構狀態 (Status)</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    <div className="flex items-center bg-white p-3 rounded-lg border border-slate-100"><CheckCircle size={16} className="mr-2 text-green-500 shrink-0"/> <span><span className="font-bold text-slate-700">指引引擎:</span> AHA/ADA/KDIGO/AWGS 運行中</span></div>
                    <div className="flex items-center bg-white p-3 rounded-lg border border-slate-100">
                      {user ? (user.isAnonymous ? <><AlertTriangle size={16} className="mr-2 text-yellow-500 shrink-0"/> <span><span className="font-bold text-slate-700">管理模式:</span> 訪客 (建議登入)</span></> : <><CheckCircle size={16} className="mr-2 text-blue-500 shrink-0"/> <span><span className="font-bold text-slate-700">Google 雲端同步:</span> 已連結</span></>) : <><AlertTriangle size={16} className="mr-2 text-amber-500 shrink-0"/> <span><span className="font-bold text-slate-700">雲端儲存:</span> 未啟動 (本地模式)</span></>}
                    </div>
                    <div className="flex items-center bg-white p-3 rounded-lg border border-slate-100"><CheckCircle size={16} className="mr-2 text-green-500 shrink-0"/> <span><span className="font-bold text-slate-700">ACB 藥物:</span> 評估資料庫已掛載</span></div>
                    <div className="flex items-center bg-white p-3 rounded-lg border border-slate-100"><CheckCircle size={16} className="mr-2 text-green-500 shrink-0"/> <span><span className="font-bold text-slate-700">AI 處方:</span> Prompt 架構已載入</span></div>
                  </div>
                </div>
              </div>
            );

          case 'acb':
            return (
              <div className="space-y-6 animate-in fade-in duration-300 pb-10">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end border-b border-slate-200 pb-4 gap-4">
                  <div>
                    <h2 className="text-2xl font-bold text-slate-800 flex items-center"><Brain className="mr-2 text-purple-600" /> 抗膽鹼藥物負擔 (ACB)</h2>
                    <p className="text-xs text-slate-500 mt-1">Anticholinergic Cognitive Burden Scale 計算</p>
                  </div>
                </div>
                <div className="bg-purple-50 rounded-xl p-5 border border-purple-100 shadow-sm flex flex-col md:flex-row gap-4 items-center md:items-start">
                  <div className="bg-white p-3 rounded-full shadow-sm text-purple-500 shrink-0"><Pill size={32} /></div>
                  <div>
                    <h3 className="font-bold text-purple-900 mb-2">什麼是抗膽鹼藥物負擔？</h3>
                    <p className="text-sm text-purple-800/80 leading-relaxed text-justify">
                      許多感冒藥(抗組織胺)、腸胃解痙藥、神經痛與安眠藥具「抗膽鹼」特性。對高齡長輩而言，毒性累積會導致<strong>認知功能退化、譫妄、跌倒與尿液滯留</strong>。若 ACB 總分 <span className="font-bold text-rose-600">≥ 3 分</span>，將大幅增加失智與死亡風險。
                    </p>
                  </div>
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
                    <div className="bg-slate-50 p-4 border-b border-slate-100 flex items-center">
                      <Search size={18} className="text-slate-400 mr-2" />
                      <input type="text" placeholder="搜尋藥物或適應症 (例: 止痛, 組織胺)" value={acbSearch} onChange={(e) => setAcbSearch(e.target.value)} className="bg-transparent border-none outline-none w-full text-sm font-medium text-slate-700 placeholder:text-slate-400" />
                    </div>
                    <div className="p-2 h-80 overflow-y-auto bg-slate-50/50">
                      {ACB_DATABASE.filter(d => d.name.toLowerCase().includes(acbSearch.toLowerCase()) || d.category.includes(acbSearch)).map(drug => (
                        <div key={drug.name} className="flex justify-between items-center p-3 hover:bg-white rounded-lg border border-transparent hover:border-slate-200 hover:shadow-sm transition-all mb-1">
                          <div><div className="font-bold text-sm text-slate-800">{drug.name}</div><div className="text-xs text-slate-500">{drug.category}</div></div>
                          <div className="flex items-center gap-3">
                            <span className={`text-xs font-bold px-2 py-1 rounded ${drug.score === 3 ? 'bg-rose-100 text-rose-700' : drug.score === 2 ? 'bg-orange-100 text-orange-700' : 'bg-yellow-100 text-yellow-700'}`}>{drug.score} 分</span>
                            <button onClick={() => handleAddDrug(drug)} disabled={acbSelectedDrugs.some(d => d.name === drug.name)} className="bg-blue-50 text-blue-600 p-1.5 rounded-md hover:bg-blue-100 disabled:opacity-30 transition"><Plus size={16} /></button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col">
                    <div className="bg-slate-800 text-white p-4 border-b border-slate-700 flex justify-between items-center rounded-t-xl">
                      <h3 className="font-bold text-sm">目前服用清單</h3><span className="text-xs bg-slate-600 px-2 py-1 rounded font-bold">總計: {acbTotalScore} 分</span>
                    </div>
                    <div className="flex-1 p-4 overflow-y-auto max-h-64">
                      {acbSelectedDrugs.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-slate-400"><Pill size={32} className="mb-2 opacity-50" /><p className="text-sm">從左側加入服用的藥物</p></div>
                      ) : (
                        <div className="space-y-2">
                          {acbSelectedDrugs.map(drug => (
                            <div key={drug.name} className="flex justify-between items-center p-3 bg-slate-50 rounded-lg border border-slate-100">
                              <div className="text-sm font-bold text-slate-700">{drug.name}</div>
                              <div className="flex items-center gap-3"><span className="text-sm font-black text-slate-600">+{drug.score}</span><button onClick={() => handleRemoveDrug(drug.name)} className="text-rose-400 hover:text-rose-600"><Trash2 size={16}/></button></div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="p-5 border-t border-slate-100 bg-slate-50 rounded-b-xl">
                      <div className="flex justify-between items-end mb-3"><span className="text-sm font-bold text-slate-500">風險判定：</span><span className={`text-2xl font-black ${acbTotalScore >= 3 ? 'text-rose-600' : acbTotalScore > 0 ? 'text-yellow-600' : 'text-emerald-600'}`}>{acbTotalScore} <span className="text-sm font-bold">分</span></span></div>
                      {acbTotalScore >= 3 ? (<div className="p-3 bg-rose-100 border border-rose-200 text-rose-800 rounded-lg text-sm leading-relaxed"><div className="font-bold flex items-center mb-1"><AlertTriangle size={16} className="mr-1"/> 高度認知與跌倒風險</div>藥物負擔過重！強烈建議將此清單帶至「高齡醫學科」，與醫師討論減藥或更換替代藥物。</div>) : acbTotalScore > 0 ? (<div className="p-3 bg-yellow-100 border border-yellow-200 text-yellow-800 rounded-lg text-sm leading-relaxed"><div className="font-bold flex items-center mb-1"><AlertTriangle size={16} className="mr-1"/> 輕中度風險</div>若長輩近期出現口乾、便祕或頭暈，建議回診反映。</div>) : (<div className="p-3 bg-emerald-100 border border-emerald-200 text-emerald-800 rounded-lg text-sm leading-relaxed"><div className="font-bold flex items-center mb-1"><CheckCircle size={16} className="mr-1"/> 無明顯風險</div>清單中未發現高風險抗膽鹼藥物。</div>)}
                    </div>
                  </div>
                </div>
              </div>
            );

          case 'tracking':
            return (
              <div className="space-y-6 animate-in fade-in duration-300">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-slate-200 pb-2 gap-4">
                  <h2 className="text-2xl font-bold text-slate-800 flex items-center"><ClipboardList className="mr-2 text-blue-600" /> 健康追蹤庫</h2>
                  <div className="flex gap-2">
                    <button onClick={exportToCSV} className="bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1.5 rounded-lg text-sm font-medium flex items-center transition-colors shadow-sm"><Download size={16} className="mr-1"/> 匯出 CSV</button>
                    <button onClick={() => setShowAddForm(!showAddForm)} className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg text-sm font-medium flex items-center transition-colors shadow-sm">{showAddForm ? '取消' : <><Plus size={16} className="mr-1"/> 手動紀錄</>}</button>
                  </div>
                </div>

                {showAddForm && (
                  <div className="bg-white border border-blue-200 p-4 rounded-xl shadow-sm animate-in slide-in-from-top-2">
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
                      <input type="date" value={newMetric.date} onChange={e => setNewMetric({...newMetric, date: e.target.value})} className="p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-100" />
                      <select value={newMetric.metric} onChange={e => {
                          const val = e.target.value; let unit = newMetric.unit;
                          if (val.includes('壓')) unit = 'mmHg'; else if (val.includes('LDL') || val.includes('血糖') || val.includes('三酸甘油酯') || val.includes('膽固醇')) unit = 'mg/dL'; else if (val.includes('HbA1c')) unit = '%'; else if (val.includes('eGFR')) unit = 'mL/min/1.73m²'; else if (val.includes('UACR')) unit = 'mg/g'; else if (val.includes('體重') || val.includes('握力')) unit = 'kg'; else if (val.includes('心率')) unit = 'bpm'; else if (val.includes('小腿圍')) unit = 'cm';
                          setNewMetric({...newMetric, metric: val, unit: unit});
                        }} className="p-2 border border-slate-200 rounded-lg text-sm bg-white outline-none focus:ring-2 focus:ring-blue-100">
                        <option value="" disabled>選擇指標名稱...</option>
                        <optgroup label="血壓管理"><option value="收縮壓 (SYS)">收縮壓 (SYS)</option><option value="舒張壓 (DIA)">舒張壓 (DIA)</option></optgroup>
                        <optgroup label="血脂管理"><option value="LDL-C (壞膽固醇)">LDL-C (壞膽固醇)</option><option value="HDL-C (好膽固醇)">HDL-C (好膽固醇)</option><option value="三酸甘油酯 (TG)">三酸甘油酯 (TG)</option></optgroup>
                        <optgroup label="血糖與腎臟"><option value="HbA1c (糖化血色素)">HbA1c (糖化血色素)</option><option value="空腹血糖 (AC)">空腹血糖 (AC)</option><option value="eGFR (腎絲球過濾率)">eGFR (腎絲球過濾率)</option><option value="UACR (尿蛋白肌酸酐比值)">UACR (尿蛋白肌酸酐比值)</option></optgroup>
                        <optgroup label="肌肉與體態"><option value="握力 (Grip)">握力 (Grip)</option><option value="小腿圍 (Calf)">小腿圍 (Calf)</option><option value="體重 (Weight)">體重 (Weight)</option></optgroup>
                        <optgroup label="穿戴裝置"><option value="心率 (HR)">靜息心率 (HR)</option><option value="血氧 (SpO2)">血氧 (SpO2)</option></optgroup>
                      </select>
                      <input type="number" step="any" placeholder="數值 (例: 120)" value={newMetric.value} onChange={e => setNewMetric({...newMetric, value: e.target.value})} className="p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-100" />
                      <input type="text" placeholder="單位 (例: mmHg)" value={newMetric.unit} onChange={e => setNewMetric({...newMetric, unit: e.target.value})} className="p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-100" />
                      <select value={newMetric.status} onChange={e => setNewMetric({...newMetric, status: e.target.value})} className="p-2 border border-slate-200 rounded-lg text-sm bg-white outline-none focus:ring-2 focus:ring-blue-100">
                        <option value="正常">正常</option><option value="偏高">偏高</option><option value="異常">異常</option>
                      </select>
                    </div>
                    <button onClick={() => handleSaveMetric()} disabled={!newMetric.metric || !newMetric.value} className="mt-4 w-full sm:w-auto bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white px-5 py-2 rounded-lg text-sm font-bold flex items-center justify-center transition-colors"><Save size={16} className="mr-2"/> 保存紀錄</button>
                  </div>
                )}
                
                <div className="overflow-x-auto bg-white rounded-xl border border-slate-200 shadow-sm">
                  <table className="w-full text-left border-collapse min-w-[500px]">
                    <thead><tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider"><th className="p-4 border-b border-slate-200 font-bold">日期</th><th className="p-4 border-b border-slate-200 font-bold">指標名稱</th><th className="p-4 border-b border-slate-200 font-bold">數值</th><th className="p-4 border-b border-slate-200 font-bold">單位</th><th className="p-4 border-b border-slate-200 font-bold">狀態</th></tr></thead>
                    <tbody className="text-sm">
                      {trackingData.length === 0 ? (<tr><td colSpan="5" className="p-10 text-center text-slate-400">{isSyncing ? "雲端同步中..." : "尚無數據，請新增紀錄。"}</td></tr>) : (trackingData.map((row) => (
                        <tr key={row.id} className="hover:bg-slate-50 border-b border-slate-100 last:border-0 transition-colors">
                          <td className="p-4 text-slate-500 font-mono text-xs">{row.date}</td><td className="p-4 font-bold text-slate-700">{row.metric}</td><td className="p-4 font-mono font-bold text-slate-800 text-base">{row.value}</td><td className="p-4 text-slate-400 text-xs">{row.unit}</td>
                          <td className="p-4"><span className={`px-2.5 py-1 rounded-md text-[11px] font-bold ${row.status === '正常' ? 'bg-emerald-50 text-emerald-600 border border-emerald-100' : 'bg-rose-50 text-rose-600 border border-rose-100'}`}>{row.status}</span></td>
                        </tr>
                      )))}
                    </tbody>
                  </table>
                </div>
              </div>
            );

          case 'prompts':
            return (
              <div className="space-y-6 animate-in fade-in duration-300">
                <div className="flex justify-between items-end border-b border-slate-200 pb-2">
                  <h2 className="text-2xl font-bold text-slate-800 flex items-center"><Database className="mr-2 text-indigo-600"/> AI 處方庫</h2>
                </div>
                <p className="text-sm text-slate-600">複製指令至 ChatGPT/Claude，結合雲端數據生成衛教建議。</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {PROMPTS.map((prompt) => (
                    <div key={prompt.id} className="p-5 border border-slate-200 rounded-xl bg-white flex flex-col justify-between items-start hover:border-indigo-300 hover:shadow-md transition-all">
                      <div className="mb-4 w-full">
                        <div className="flex items-center space-x-2 mb-1"><span className="bg-indigo-100 text-indigo-700 text-xs font-bold px-2 py-0.5 rounded font-mono">{prompt.id}</span><h3 className="font-bold text-slate-800 text-lg">{prompt.title.replace(`${prompt.id}-`, '')}</h3></div>
                        <p className="text-xs text-slate-500">{prompt.desc}</p>
                      </div>
                      <button onClick={() => copyToClipboard(prompt.content, prompt.id)} className={`w-full flex justify-center items-center space-x-2 px-4 py-2.5 rounded-lg font-bold text-sm transition-colors ${copiedId === prompt.id ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}`}>
                        {copiedId === prompt.id ? <><CheckCircle size={16}/> <span>已複製</span></> : <><Copy size={16}/> <span>複製指令</span></>}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            );

          case 'metabolic':
            return (
              <div className="space-y-6 animate-in fade-in duration-300 pb-10">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end border-b border-slate-200 pb-4 gap-4">
                  <div>
                    <h2 className="text-2xl font-bold text-slate-800 flex items-center"><HeartPulse className="mr-2 text-rose-500" /> 綜合決策戰情室</h2>
                    <p className="text-xs text-slate-500 mt-1">內嵌醫療指引：AHA/ADA/KDIGO/AWGS</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button onClick={loadLatestToMetabolic} className="bg-white border border-slate-300 text-slate-600 px-3 py-1.5 rounded-lg text-xs font-bold flex items-center hover:bg-slate-50 shadow-sm transition"><RefreshCw size={14} className="mr-1.5 text-blue-500"/> 從追蹤庫載入</button>
                    <button onClick={saveMetabolicToTracking} className="bg-slate-800 text-white px-3 py-1.5 rounded-lg text-xs font-bold flex items-center hover:bg-slate-700 shadow-sm transition"><Save size={14} className="mr-1.5 text-emerald-400"/> 儲存評估快照</button>
                  </div>
                </div>

                <section className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
                  <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
                    <h3 className="font-bold text-slate-800 flex items-center text-sm"><span className="bg-slate-800 text-white w-5 h-5 rounded flex items-center justify-center mr-2 text-[10px]">1</span>病患風險輪廓</h3>
                    <div className="flex bg-slate-100 p-1 rounded-lg">
                      <button onClick={() => setRisks({...risks, isMale: true})} className={`px-3 py-1 text-xs font-bold rounded-md transition ${risks.isMale ? 'bg-white shadow text-blue-600' : 'text-slate-500 hover:text-slate-700'}`}>男性</button>
                      <button onClick={() => setRisks({...risks, isMale: false})} className={`px-3 py-1 text-xs font-bold rounded-md transition ${!risks.isMale ? 'bg-white shadow text-rose-500' : 'text-slate-500 hover:text-slate-700'}`}>女性</button>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                    {[
                      { id: 'cvd', icon: Activity, color: 'rose', label: '心血管病史', sub: '中風/心梗' },
                      { id: 'dm', icon: Droplet, color: 'purple', label: '糖尿病', sub: '血糖異常' },
                      { id: 'ckd', icon: Stethoscope, color: 'amber', label: '慢性腎病', sub: 'eGFR↓或尿蛋白' },
                      { id: 'age', icon: User, color: 'slate', label: '高齡', sub: '男>45 / 女>55' },
                      { id: 'smoke', icon: Wind, color: 'slate', label: '吸菸', sub: '目前有抽菸' },
                      { id: 'family', icon: Users, color: 'teal', label: '家族病史', sub: '早發性心血管' },
                    ].map(r => (
                      <label key={r.id} className="cursor-pointer group select-none">
                        <input type="checkbox" className="hidden" checked={risks[r.id]} onChange={() => setRisks({...risks, [r.id]: !risks[r.id]})} />
                        <div className={`border-2 rounded-xl p-3 h-full flex flex-col items-center justify-center text-center transition-all relative ${risks[r.id] ? `border-${r.color}-400 bg-${r.color}-50` : 'border-slate-100 hover:border-slate-300'}`}>
                          <r.icon className={`w-6 h-6 mb-2 ${risks[r.id] ? `text-${r.color}-600` : 'text-slate-400'}`} size={24} />
                          <span className={`text-[11px] font-bold ${risks[r.id] ? `text-${r.color}-800` : 'text-slate-600'}`}>{r.label}</span>
                          <div className="text-[9px] text-slate-400 mt-0.5">{r.sub}</div>
                          {risks[r.id] && <CheckCircle className={`absolute top-2 right-2 w-3.5 h-3.5 text-${r.color}-500`} size={14}/>}
                        </div>
                      </label>
                    ))}
                  </div>
                  <div className="mt-4 bg-slate-50 border border-slate-100 rounded-lg p-3 flex justify-between items-center text-sm">
                    <span className="text-slate-500 font-bold uppercase tracking-wider text-xs">CVD 風險等級</span>
                    <span className={`font-black ${metabolicAnalysis.riskColor}`}>{metabolicAnalysis.riskCategory}</span>
                  </div>
                </section>

                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-5">
                  <section className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
                    <div className="bg-blue-50/50 p-4 border-b border-slate-100 flex justify-between items-center"><h3 className="font-bold text-blue-900 flex items-center text-sm"><HeartPulse className="mr-2 w-4 h-4 text-blue-500"/> 血壓 BP</h3><span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${metabolicAnalysis.bp.class}`}>{metabolicAnalysis.bp.status}</span></div>
                    <div className="p-5 space-y-5 flex-1">
                      <div><div className="flex justify-between text-xs font-bold text-slate-500 mb-2"><span>收縮壓 (SYS)</span><span className="text-blue-600 text-sm">{vitals.sbp} mmHg</span></div><input type="range" min="90" max="200" value={vitals.sbp} onChange={e => setVitals({...vitals, sbp: Number(e.target.value)})} className="w-full accent-blue-600" /></div>
                      <div><div className="flex justify-between text-xs font-bold text-slate-500 mb-2"><span>舒張壓 (DIA)</span><span className="text-blue-600 text-sm">{vitals.dbp} mmHg</span></div><input type="range" min="50" max="130" value={vitals.dbp} onChange={e => setVitals({...vitals, dbp: Number(e.target.value)})} className="w-full accent-blue-600" /></div>
                      <div className="pt-4 border-t border-dashed border-slate-200"><div className="text-xs text-slate-500 mb-2">臨床目標: <span className="font-bold text-blue-700" dangerouslySetInnerHTML={{__html: metabolicAnalysis.bp.target}}></span></div><div className="text-[11px] p-2 bg-blue-50 text-blue-800 rounded border border-blue-100 leading-relaxed">{metabolicAnalysis.bp.action}</div></div>
                    </div>
                  </section>
                  <section className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
                    <div className="bg-emerald-50/50 p-4 border-b border-slate-100 flex justify-between items-center"><h3 className="font-bold text-emerald-900 flex items-center text-sm"><Activity className="mr-2 w-4 h-4 text-emerald-500"/> 血脂 LDL-C</h3><span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${metabolicAnalysis.ldlRes.class}`}>{metabolicAnalysis.ldlRes.status}</span></div>
                    <div className="p-5 space-y-5 flex-1">
                      <div><div className="flex justify-between text-xs font-bold text-slate-500 mb-2"><span>壞膽固醇</span><span className="text-emerald-600 text-sm">{vitals.ldl} mg/dL</span></div><input type="range" min="30" max="250" value={vitals.ldl} onChange={e => setVitals({...vitals, ldl: Number(e.target.value)})} className="w-full accent-emerald-600" /></div>
                      <div className="pt-4 border-t border-dashed border-slate-200 mt-auto"><div className="text-xs text-slate-500 mb-2">計算目標: <span className="font-bold text-emerald-700" dangerouslySetInnerHTML={{__html: `&lt; ${metabolicAnalysis.ldlTarget}`}}></span></div><div className="text-[11px] p-2 bg-emerald-50 text-emerald-800 rounded border border-emerald-100 leading-relaxed" dangerouslySetInnerHTML={{__html: metabolicAnalysis.ldlRes.action}}></div></div>
                    </div>
                  </section>
                  <section className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
                    <div className="bg-purple-50/50 p-4 border-b border-slate-100 flex justify-between items-center"><h3 className="font-bold text-purple-900 flex items-center text-sm"><Box className="mr-2 w-4 h-4 text-purple-500"/> 血糖 A1C</h3><span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${metabolicAnalysis.dmRes.class}`}>{metabolicAnalysis.dmRes.status}</span></div>
                    <div className="p-5 space-y-5 flex-1 flex flex-col">
                      <div><div className="flex justify-between text-xs font-bold text-slate-500 mb-2"><span>糖化血色素</span><span className="text-purple-600 text-sm">{vitals.a1c} %</span></div><input type="range" min="4.0" max="14.0" step="0.1" value={vitals.a1c} onChange={e => setVitals({...vitals, a1c: Number(e.target.value)})} className="w-full accent-purple-600" /></div>
                      <div className="pt-4 border-t border-dashed border-slate-200 mt-auto">
                        <div className="text-[11px] p-2 bg-purple-50 text-purple-800 rounded border border-purple-100 mb-2 leading-relaxed">{metabolicAnalysis.dmRes.action}</div>
                        {metabolicAnalysis.dmRes.alert && (<div className="text-[10px] p-2 bg-rose-50 text-rose-800 rounded border border-rose-100 flex items-start"><ShieldCheck className="w-3 h-3 mr-1 shrink-0 mt-0.5 text-rose-500" /><span className="leading-relaxed">{metabolicAnalysis.dmRes.alert}</span></div>)}
                      </div>
                    </div>
                  </section>
                  <section className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
                    <div className="bg-amber-50/50 p-4 border-b border-slate-100 flex justify-between items-center"><h3 className="font-bold text-amber-900 flex items-center text-sm"><Dumbbell className="mr-2 w-4 h-4 text-amber-500"/> 肌肉健康</h3><span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${metabolicAnalysis.muscleRes.class}`}>{metabolicAnalysis.muscleRes.status}</span></div>
                    <div className="p-5 space-y-5 flex-1 flex flex-col">
                      <div><div className="flex justify-between text-xs font-bold text-slate-500 mb-2"><span>握力</span><span className="text-amber-600 text-sm">{vitals.grip} kg</span></div><input type="range" min="5" max="60" value={vitals.grip} onChange={e => setVitals({...vitals, grip: Number(e.target.value)})} className="w-full accent-amber-600" /></div>
                      <div><div className="flex justify-between text-xs font-bold text-slate-500 mb-2"><span>小腿圍</span><span className="text-amber-600 text-sm">{vitals.calf} cm</span></div><input type="range" min="20" max="50" value={vitals.calf} onChange={e => setVitals({...vitals, calf: Number(e.target.value)})} className="w-full accent-amber-600" /></div>
                      <div className="pt-4 border-t border-dashed border-slate-200 mt-auto"><div className="text-[11px] p-2 bg-amber-50 text-amber-800 rounded border border-amber-100 mb-2 leading-relaxed">{metabolicAnalysis.muscleRes.action}</div></div>
                    </div>
                  </section>
                </div>

                <section className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                  <div className="bg-slate-800 text-white p-3 px-5 flex justify-between items-center">
                    <h3 className="font-bold text-sm flex items-center"><ClipboardList className="mr-2 w-4 h-4"/> 綜合健康報告</h3>
                    <button onClick={exportToFHIR} className="text-[10px] bg-slate-700 hover:bg-blue-600 px-3 py-1.5 rounded flex items-center transition"><Share2 size={12} className="mr-1.5"/> 匯出 JSON</button>
                  </div>
                  <div className="p-6 flex flex-col md:flex-row gap-6 items-center">
                    <div className="w-full md:w-1/4 text-center shrink-0">
                      <div className={`w-16 h-16 mx-auto rounded-full ${metabolicAnalysis.report.color} flex items-center justify-center text-white shadow-lg mb-3`}><metabolicAnalysis.report.icon size={28} /></div>
                      <h4 className="font-bold text-lg text-slate-800">{metabolicAnalysis.report.title}</h4>
                    </div>
                    <div className="w-full md:w-3/4 text-sm text-slate-600 border-t md:border-t-0 md:border-l border-slate-100 pt-4 md:pt-0 md:pl-6">
                      <ul className="space-y-2 list-disc pl-4 marker:text-slate-400">
                        {metabolicAnalysis.report.advice.map((txt, i) => txt ? <li key={i} dangerouslySetInnerHTML={{__html: txt}}></li> : null)}
                      </ul>
                    </div>
                  </div>
                </section>
              </div>
            );
          default: return null;
        }
      };

      // Main App Layout
      return (
        <React.Fragment>
          {!disclaimerAccepted && (
            <div className="fixed inset-0 z-[100] bg-slate-900/40 backdrop-blur-sm flex flex-col items-center justify-center p-4">
              <div className="w-full max-w-md bg-white rounded-3xl p-8 shadow-2xl flex flex-col items-center animate-in zoom-in-95 duration-300">
                <div className="bg-blue-50 p-5 rounded-full mb-5"><HeartPulse size={48} className="text-blue-600" /></div>
                <h2 className="text-xl font-bold text-slate-800 mb-2">GAMMA 個人健康總署</h2>
                <p className="text-[10px] text-slate-400 font-bold mb-6 tracking-wider uppercase">Health Vault & Guidelines</p>
                <div className="w-full bg-slate-50 p-5 rounded-xl border border-slate-100 mb-6 text-sm text-slate-600 space-y-3">
                  <p className="font-bold flex items-center text-slate-700"><AlertTriangle size={16} className="mr-1.5 text-amber-500"/>使用前聲明：</p>
                  <p>• 本系統為單機版個人健康追蹤庫，結合 2026 最新臨床指引與藥物評估引擎。</p>
                  <p>• 僅供衛教與紀錄參考，<span className="text-rose-600 font-bold">切勿以此自行停藥。</span></p>
                </div>
                <button onClick={() => setDisclaimerAccepted(true)} className="w-full bg-blue-600 text-white font-bold py-3.5 rounded-xl shadow-lg hover:bg-blue-700 active:scale-95 transition-all">進入系統</button>
              </div>
            </div>
          )}

          <div className="flex h-screen bg-slate-50 text-slate-900 font-sans selection:bg-blue-100 selection:text-blue-900">
            {/* Sidebar (Desktop) */}
            <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col border-r border-slate-800 hidden md:flex shrink-0">
              <div className="p-6 border-b border-slate-800">
                <h1 className="text-xl font-bold text-white flex items-center"><HeartPulse size={24} className="mr-2 text-blue-500" /> GAMMA Vault</h1>
                <p className="text-[10px] text-slate-400 mt-1.5 font-mono tracking-wider">v9.0 Standalone HTML</p>
              </div>
              <nav className="flex-1 py-5 space-y-2 px-3">
                {[
                  { id: 'hub', icon: Activity, label: '總覽中心' },
                  { id: 'acb', icon: Brain, label: '藥物風險 (ACB)' },
                  { id: 'metabolic', icon: HeartPulse, label: '綜合戰情室' },
                  { id: 'tracking', icon: ClipboardList, label: '健康追蹤庫' },
                  { id: 'prompts', icon: Database, label: 'AI 處方庫' }
                ].map(tab => (
                  <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`w-full flex items-center space-x-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${activeTab === tab.id ? 'bg-blue-600/10 text-blue-400 font-bold' : 'hover:bg-slate-800 hover:text-slate-200'}`}>
                    <tab.icon size={18} className={activeTab === tab.id ? 'text-blue-500' : ''} /><span>{tab.label}</span>
                  </button>
                ))}
              </nav>
              
              <div className="p-4 border-t border-slate-800">
                {user && !user.isAnonymous ? (
                  <div className="flex flex-col space-y-2">
                    <div className="flex items-center space-x-2 text-xs text-slate-400"><User size={14}/><span className="truncate">{user.email || user.displayName || 'Google 用戶'}</span></div>
                    <button onClick={handleLogout} className="w-full text-xs flex justify-center items-center py-2 rounded bg-slate-800 hover:bg-rose-900/50 hover:text-rose-400 transition-colors"><LogOut size={14} className="mr-1"/> 登出</button>
                  </div>
                ) : (
                  <button onClick={handleGoogleLogin} className="w-full text-xs flex justify-center items-center py-2 rounded bg-blue-600 hover:bg-blue-700 text-white transition-colors"><LogIn size={14} className="mr-1"/> 連結 Google 帳戶</button>
                )}
              </div>
            </aside>

            {/* Main Area */}
            <main className="flex-1 overflow-y-auto relative pb-24 md:pb-0">
              <header className="md:hidden bg-slate-900 text-white p-4 flex justify-between items-center sticky top-0 z-40 shadow-md pb-safe">
                 <h1 className="text-lg font-bold flex items-center"><HeartPulse size={20} className="mr-2 text-blue-500" /> GAMMA Vault</h1>
                 {user && !user.isAnonymous ? (
                    <button onClick={handleLogout} className="text-[10px] bg-slate-800 border border-slate-700 px-2 py-1 rounded">登出</button>
                 ) : (
                    <button onClick={handleGoogleLogin} className="text-[10px] bg-blue-600 border border-blue-500 px-2 py-1 rounded">登入</button>
                 )}
              </header>

              <div className="p-4 sm:p-6 md:p-10 max-w-5xl mx-auto">
                {renderContent()}
              </div>
            </main>

            {/* Bottom Nav (Mobile) */}
            <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur-md border-t border-slate-200 pb-safe z-50 overflow-x-auto no-scrollbar">
              <div className="flex justify-around items-center h-16 min-w-[320px] px-2 gap-1">
                {[
                  { id: 'hub', icon: Activity, label: '總覽' },
                  { id: 'acb', icon: Brain, label: '藥物' },
                  { id: 'metabolic', icon: HeartPulse, label: '戰情室' },
                  { id: 'tracking', icon: ClipboardList, label: '追蹤' },
                  { id: 'prompts', icon: Database, label: '處方' }
                ].map(tab => (
                  <button key={tab.id} onClick={() => { setActiveTab(tab.id); window.scrollTo(0,0); }} className={`flex flex-col items-center justify-center w-full h-full transition-colors ${activeTab === tab.id ? 'text-blue-600' : 'text-slate-400'}`}>
                    <tab.icon size={20} className={`mb-1 ${activeTab === tab.id ? 'stroke-[2.5px]' : ''}`} />
                    <span className="text-[10px] font-bold whitespace-nowrap">{tab.label}</span>
                  </button>
                ))}
              </div>
            </nav>
          </div>
        </React.Fragment>
      );
    };

    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
  </script>
</body>
</html>
