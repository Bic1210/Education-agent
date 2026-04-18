import { useState, useRef, useCallback, useEffect } from "react";

// ─── API 配置 ────────────────────────────────────────────────
const API_BASE = "http://localhost:5000/api";

async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || "请求失败");
  }
  return res.json();
}

// ─── Icons ───────────────────────────────────────────────────
const Icon = ({ type, size = 18 }) => {
  const s = { width: size, height: size, display: "inline-block", verticalAlign: "middle" };
  const icons = {
    book: <svg style={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>,
    graph: <svg style={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="12" cy="5" r="3"/><circle cx="5" cy="19" r="3"/><circle cx="19" cy="19" r="3"/><line x1="12" y1="8" x2="5" y2="16"/><line x1="12" y1="8" x2="19" y2="16"/></svg>,
    db: <svg style={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>,
    upload: <svg style={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>,
    file: <svg style={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>,
    check: <svg style={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><polyline points="20 6 9 17 4 12"/></svg>,
    download: <svg style={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>,
    edit: <svg style={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>,
    trash: <svg style={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>,
    spinner: <svg style={{...s, animation: "spin 1s linear infinite"}} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>,
    alert: <svg style={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>,
    key: <svg style={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>,
  };
  return icons[type] || null;
};

// ─── Main App ────────────────────────────────────────────────
export default function App() {
  const [sidebarPage, setSidebarPage] = useState("database");
  const [books, setBooks] = useState([]);
  const [selectedBook, setSelectedBook] = useState(null);
  const [activeTab, setActiveTab] = useState("original");
  const [processing, setProcessing] = useState(null);
  const [processMsg, setProcessMsg] = useState("");
  const [corpusData, setCorpusData] = useState({});
  const [graphData, setGraphData] = useState({});
  const [editingChunk, setEditingChunk] = useState(null);
  const [editText, setEditText] = useState("");
  const [selectedBooksForGraph, setSelectedBooksForGraph] = useState(new Set());
  const [globalGraph, setGlobalGraph] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [deepseekKey, setDeepseekKey] = useState("");
  const [showKeyInput, setShowKeyInput] = useState(false);
  const fileInputRef = useRef(null);

  const showError = (msg) => { setErrorMsg(msg); setTimeout(() => setErrorMsg(""), 5000); };

  const handleUpload = useCallback(async (e) => {
    const files = e?.target?.files;
    if (!files || files.length === 0) return;
    for (const file of Array.from(files)) {
      try {
        setProcessing("upload"); setProcessMsg(`上传 ${file.name} ...`);
        const form = new FormData(); form.append("file", file);
        const result = await api("/upload", { method: "POST", body: form });
        setBooks(prev => [...prev, result]);
        setProcessing(null);
      } catch (err) { showError(`上传失败: ${err.message}`); setProcessing(null); }
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
  }, []);

  const processCorpus = useCallback(async (book) => {
    try {
      setProcessing("corpus"); setProcessMsg("PDF转TXT + 章节切分 + 打标签 + 清洗中..."); setSelectedBook(book);
      const result = await api(`/process/corpus/${book.id}`, { method: "POST" });
      setBooks(prev => prev.map(b => b.id === book.id ? { ...b, ...result.book, hasCorpus: true } : b));
      setCorpusData(prev => ({ ...prev, [book.id]: result.corpus }));
      setSelectedBook(prev => ({ ...prev, ...result.book, hasCorpus: true }));
      setActiveTab("corpus"); setProcessing(null);
    } catch (err) { showError(`语料库生成失败: ${err.message}`); setProcessing(null); }
  }, []);

  const processGraph = useCallback(async (book) => {
    if (!corpusData[book.id]) { showError("请先生成语料库"); return; }
    try {
      setProcessing("graph"); setProcessMsg(deepseekKey ? "调用 DeepSeek API 抽取实体..." : "关键词提取中...");
      const result = await api(`/process/graph/${book.id}`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: deepseekKey }),
      });
      setGraphData(prev => ({ ...prev, [book.id]: result.graph }));
      setBooks(prev => prev.map(b => b.id === book.id ? { ...b, hasGraph: true } : b));
      setActiveTab("graph"); setProcessing(null);
    } catch (err) { showError(`图谱生成失败: ${err.message}`); setProcessing(null); }
  }, [corpusData, deepseekKey]);

  const generateGlobalGraph = useCallback(async () => {
    if (selectedBooksForGraph.size === 0) return;
    try {
      setProcessing("global_graph"); setProcessMsg("合并图谱，实体去重中...");
      const result = await api("/process/global-graph", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ book_ids: [...selectedBooksForGraph] }),
      });
      setGlobalGraph(result.graph); setProcessing(null); setSidebarPage("knowledge_graph");
    } catch (err) { showError(`全知识图谱生成失败: ${err.message}`); setProcessing(null); }
  }, [selectedBooksForGraph]);

  const removeBook = async (id) => {
    try { await api(`/books/${id}`, { method: "DELETE" }); setBooks(prev => prev.filter(b => b.id !== id)); if (selectedBook?.id === id) setSelectedBook(null); } catch (err) { showError(err.message); }
  };
  const startEditChunk = (chunk) => { setEditingChunk(chunk.chunk_index); setEditText(chunk.text); };
  const saveEditChunk = async (bookId, chunkIndex) => {
    try {
      await api(`/corpus/${bookId}/edit`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chunk_index: chunkIndex, text: editText }) });
      setCorpusData(prev => { const u = { ...prev }; u[bookId] = u[bookId].map(c => c.chunk_index === chunkIndex ? { ...c, text: editText, char_count: editText.length } : c); return u; });
      setEditingChunk(null);
    } catch (err) { showError(err.message); }
  };
  const toggleBookForGraph = (id) => { setSelectedBooksForGraph(prev => { const n = new Set(prev); if (n.has(id)) n.delete(id); else n.add(id); return n; }); };

  return (
    <div style={S.root}>
      <style>{globalCSS}</style>

      {/* ── Sidebar ── */}
      <aside style={S.sidebar}>
        <div style={S.sidebarBrand}>
          <div style={S.brandIcon}>K</div>
          <div style={S.brandLabel}>知识平台</div>
        </div>
        <nav style={S.nav}>
          <SidebarBtn active={sidebarPage === "knowledge_graph"} icon="graph" label="知识图谱" onClick={() => setSidebarPage("knowledge_graph")} />
          <SidebarBtn active={sidebarPage === "database"} icon="db" label="数据库" onClick={() => setSidebarPage("database")} accent />
        </nav>
        <div style={{ marginTop: "auto", width: "100%", padding: "0 8px 20px" }}>
          <button className="sidebar-btn" style={{ ...S.sidebarItem, justifyContent: "center", gap: 6, fontSize: 10, opacity: 0.6 }} onClick={() => setShowKeyInput(!showKeyInput)}>
            <Icon type="key" size={14} /> API
          </button>
          {showKeyInput && (
            <div style={{ padding: "6px 4px 0" }}>
              <input value={deepseekKey} onChange={e => setDeepseekKey(e.target.value)} placeholder="sk-..." style={S.keyInput} />
              <div style={{ fontSize: 9, color: deepseekKey ? "#7EC49D" : "#555", marginTop: 3, textAlign: "center" }}>{deepseekKey ? "✓ 已配置" : "可选 · 不填则用关键词提取"}</div>
            </div>
          )}
        </div>
      </aside>

      {/* ── Main ── */}
      <main style={S.main}>
        {sidebarPage === "database" ? (
          <DatabasePage {...{ books, selectedBook, setSelectedBook, activeTab, setActiveTab, processing, corpusData, graphData, editingChunk, editText, setEditText, fileInputRef, handleUpload, processCorpus, processGraph, removeBook, startEditChunk, saveEditChunk, selectedBooksForGraph, toggleBookForGraph, generateGlobalGraph }} />
        ) : (
          <KnowledgeGraphPage graph={globalGraph} />
        )}
      </main>

      {processing && (
        <div style={S.overlay}><div style={S.overlayCard}>
          <div style={{ color: "#A0522D" }}><Icon type="spinner" size={28} /></div>
          <div style={{ fontSize: 16, fontWeight: 600, marginTop: 20, color: "#2D2A26" }}>{processMsg}</div>
          <div style={S.overlayBar}><div style={S.overlayBarFill} /></div>
        </div></div>
      )}
      {errorMsg && <div style={S.toast}><Icon type="alert" size={15} /> {errorMsg}</div>}
    </div>
  );
}

function SidebarBtn({ active, icon, label, onClick, accent }) {
  return (
    <button className="sidebar-btn" style={{ ...S.sidebarItem, ...(active ? S.sidebarItemActive : {}), ...(active && accent ? { borderLeftColor: "#A0522D" } : {}) }} onClick={onClick}>
      <Icon type={icon} size={18} />
      <span style={{ ...(active && accent ? { color: "#A0522D" } : {}) }}>{label}</span>
    </button>
  );
}

// ─── Database Page ───────────────────────────────────────────
function DatabasePage({ books, selectedBook, setSelectedBook, activeTab, setActiveTab, processing, corpusData, graphData, editingChunk, editText, setEditText, fileInputRef, handleUpload, processCorpus, processGraph, removeBook, startEditChunk, saveEditChunk, selectedBooksForGraph, toggleBookForGraph, generateGlobalGraph }) {
  const hasCorpus = selectedBook && corpusData[selectedBook.id];
  const hasGraph = selectedBook && graphData[selectedBook.id];

  let actionBtn = null;
  if (activeTab === "original" && selectedBook && !hasCorpus) actionBtn = <button style={S.primaryBtn} onClick={() => processCorpus(selectedBook)} disabled={!!processing}>下一步 · 生成语料库</button>;
  else if (activeTab === "original" && hasCorpus) actionBtn = <button style={{ ...S.primaryBtn, opacity: 0.45, cursor: "default" }} disabled>✓ 已生成</button>;
  else if (activeTab === "corpus" && hasCorpus) actionBtn = (<div style={{ display: "flex", gap: 8 }}><button style={S.ghostBtn} onClick={() => window.open(`${API_BASE}/download/${selectedBook.id}/corpus`)}><Icon type="download" size={14} /> 下载</button><button style={S.primaryBtn} onClick={() => processGraph(selectedBook)} disabled={!!processing}>下一步 · 生成图谱</button></div>);
  else if (activeTab === "graph" && hasGraph) actionBtn = (<div style={{ display: "flex", gap: 8 }}><button style={S.ghostBtn} onClick={() => window.open(`${API_BASE}/download/${selectedBook.id}/graph`)}><Icon type="download" size={14} /> 下载</button><button style={S.primaryBtn} onClick={generateGlobalGraph} disabled={selectedBooksForGraph.size === 0 || !!processing}>全知识图谱生成</button></div>);
  else if (activeTab === "graph" && !hasGraph && hasCorpus) actionBtn = <button style={S.primaryBtn} onClick={() => processGraph(selectedBook)} disabled={!!processing}>生成图谱数据</button>;

  return (
    <div style={S.dbPage}><div style={S.dbContent}>
      {/* Left Panel */}
      <div style={S.leftPanel}>
        <div style={S.leftHeader}><Icon type="db" size={16} /><span style={{ fontWeight: 700, fontSize: 14, letterSpacing: 0.3 }}>数据库</span></div>
        <div style={S.uploadZone} onClick={() => fileInputRef.current?.click()} onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); handleUpload({ target: { files: e.dataTransfer.files } }); }}>
          <input ref={fileInputRef} type="file" multiple accept=".pdf,.txt" style={{ display: "none" }} onChange={handleUpload} />
          <div style={S.uploadIcon}><Icon type="upload" size={22} /></div>
          <div style={{ fontSize: 13, fontWeight: 600, marginTop: 8 }}>上传书籍</div>
          <div style={{ fontSize: 11, color: "#A09889", marginTop: 2 }}>支持 TXT / PDF</div>
        </div>
        <div style={S.bookListLabel}><span>书籍列表</span><span style={S.bookCount}>{books.length}</span></div>
        <div style={S.bookList}>
          {books.map(book => (
            <div key={book.id} className="book-item" style={{ ...S.bookItem, ...(selectedBook?.id === book.id ? S.bookItemActive : {}) }} onClick={() => setSelectedBook(book)}>
              <div style={S.bookItemInner}>
                {activeTab === "graph" && <input type="checkbox" checked={selectedBooksForGraph.has(book.id)} onChange={e => { e.stopPropagation(); toggleBookForGraph(book.id); }} style={{ accentColor: "#A0522D", marginRight: 6, cursor: "pointer" }} />}
                <div style={S.bookIcon}><Icon type="file" size={14} /></div>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={S.bookTitle}>{book.name}</div>
                  <div style={S.bookMeta}>{book.size}{book.pages ? ` · ${book.pages}p` : ""}</div>
                </div>
                <div style={{ display: "flex", gap: 4, alignItems: "center", flexShrink: 0 }}>
                  {corpusData[book.id] && <span style={S.dot} title="语料库" />}
                  {graphData[book.id] && <span style={{ ...S.dot, background: "#6A8EAE" }} title="图谱" />}
                </div>
              </div>
              <button className="del-btn" style={S.delBtn} onClick={e => { e.stopPropagation(); removeBook(book.id); }}><Icon type="trash" size={13} /></button>
            </div>
          ))}
          {books.length === 0 && <div style={{ padding: "32px 16px", textAlign: "center", color: "#C4B9AB", fontSize: 13, lineHeight: 1.7 }}>上传 PDF 或 TXT 文件<br />开始构建语料库</div>}
        </div>
      </div>

      {/* Right Panel */}
      <div style={S.rightPanel}>
        <div style={S.rightTopBar}>
          <div style={S.tabRow}>
            {[{ key: "original", label: "原书籍" }, { key: "corpus", label: "标准化语料库" }, { key: "graph", label: "结构化知识图谱数据" }].map(t => (
              <button key={t.key} className="tab-btn" style={{ ...S.tab, ...(activeTab === t.key ? S.tabActive : {}) }} onClick={() => setActiveTab(t.key)}>{t.label}</button>
            ))}
          </div>
          <div style={S.tabActions}>{actionBtn}</div>
        </div>
        <div style={S.rightContent}>
          {!selectedBook ? (
            <div style={S.emptyState}>
              <div style={{ width: 64, height: 64, borderRadius: 20, background: "#F5F0EB", display: "flex", alignItems: "center", justifyContent: "center" }}><Icon type="book" size={28} /></div>
              <div style={{ marginTop: 16, color: "#A09889", fontSize: 14 }}>选择左侧书籍查看内容</div>
            </div>
          ) : activeTab === "original" ? (
            <OriginalTab book={selectedBook} hasCorpus={!!corpusData[selectedBook.id]} />
          ) : activeTab === "corpus" ? (
            <CorpusTab book={selectedBook} data={corpusData[selectedBook.id]} editingChunk={editingChunk} editText={editText} setEditText={setEditText} startEditChunk={startEditChunk} saveEditChunk={saveEditChunk} processCorpus={processCorpus} processing={processing} />
          ) : (
            <GraphTab book={selectedBook} data={graphData[selectedBook.id]} processGraph={processGraph} processing={processing} hasCorpus={!!corpusData[selectedBook.id]} />
          )}
        </div>
      </div>
    </div></div>
  );
}

// ─── Tab Content Components ──────────────────────────────────
function OriginalTab({ book, hasCorpus }) {
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!book?.id) return;
    setLoading(true);
    setPreview(null);
    api(`/preview/${book.id}`).then(data => {
      setPreview(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [book?.id]);

  return (
    <div style={{ padding: "28px 32px" }}>
      <h2 style={{ fontSize: 22, fontWeight: 700, color: "#2D2A26", margin: 0, fontFamily: "'Source Serif 4','Noto Sans SC',serif" }}>{book.name}</h2>
      <div style={{ display: "flex", gap: 10, marginTop: 14, flexWrap: "wrap", alignItems: "center" }}>
        {[book.file, book.size, book.pages ? `${book.pages} 页` : null].filter(Boolean).map((t, i) => <span key={i} style={S.infoTag}>{t}</span>)}
        {preview?.language && <span style={{ ...S.infoTag, background: "#A0522D14", color: "#A0522D" }}>{preview.language === "zh" ? "中文" : "English"}</span>}
        {preview?.total_chars > 0 && <span style={S.infoTag}>{preview.total_chars.toLocaleString()} 字符</span>}
      </div>

      {/* Book info cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginTop: 24 }}>
        <div style={S.statCard}>
          <div style={S.statLabel}>格式</div>
          <div style={S.statValue}>{book.ext === ".pdf" ? "PDF" : "TXT"}</div>
        </div>
        <div style={S.statCard}>
          <div style={S.statLabel}>页数</div>
          <div style={S.statValue}>{book.pages || "—"}</div>
        </div>
        <div style={S.statCard}>
          <div style={S.statLabel}>状态</div>
          <div style={{ ...S.statValue, color: hasCorpus ? "#7EC49D" : "#A09889", fontSize: 13 }}>{hasCorpus ? "✓ 已处理" : "待处理"}</div>
        </div>
      </div>

      {/* Preview */}
      <div style={S.card}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: "#2D2A26" }}>内容预览</div>
          <span style={{ fontSize: 11, color: "#C4B9AB" }}>显示原文前部分内容</span>
        </div>
        {loading ? (
          <div style={{ padding: "32px 0", textAlign: "center", color: "#C4B9AB" }}><Icon type="spinner" size={20} /> 加载中...</div>
        ) : preview?.preview ? (
          <div style={S.previewBox}>{preview.preview}</div>
        ) : (
          <div style={{ padding: "32px 0", textAlign: "center", color: "#C4B9AB", fontSize: 13 }}>暂无预览内容</div>
        )}
      </div>
    </div>
  );
}

function CorpusTab({ book, data, editingChunk, editText, setEditText, startEditChunk, saveEditChunk, processCorpus, processing }) {
  if (!data) return (<div style={S.emptyState}><div style={{ color: "#A09889" }}>尚未生成语料库</div><button style={{ ...S.primaryBtn, marginTop: 12 }} onClick={() => processCorpus(book)} disabled={!!processing}>开始生成</button></div>);
  const totalChars = data.reduce((s, c) => s + c.char_count, 0);
  const lang = data[0]?.language || "unknown";
  return (
    <div style={{ padding: "24px 28px" }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 16, flexWrap: "wrap" }}>
        <h2 style={{ fontSize: 19, fontWeight: 700, color: "#2D2A26", margin: 0 }}>{book.name}</h2>
        <div style={{ display: "flex", gap: 14, fontSize: 12, color: "#A09889" }}><span>{lang === "zh" ? "中文" : "English"}</span><span>{data.length} 段</span><span>{totalChars.toLocaleString()} 字符</span></div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 20 }}>
        {data.map(chunk => (
          <div key={chunk.chunk_index} className="chunk-card" style={S.chunkCard}>
            <div style={S.chunkHead}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, flex: 1, minWidth: 0 }}>
                <span style={S.levelTag}>{chunk.chapter_level}</span>
                <span style={{ fontWeight: 600, fontSize: 14, color: "#2D2A26", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{chunk.chapter_title}</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
                <span style={{ fontSize: 11, color: "#C4B9AB" }}>{chunk.char_count}字</span>
                {editingChunk === chunk.chunk_index ? (
                  <button style={S.tinyBtn} onClick={() => saveEditChunk(book.id, chunk.chunk_index)}><Icon type="check" size={13} /> 保存</button>
                ) : (
                  <button className="edit-btn" style={S.tinyBtnGhost} onClick={() => startEditChunk(chunk)}><Icon type="edit" size={13} /></button>
                )}
              </div>
            </div>
            {editingChunk === chunk.chunk_index ? <textarea style={S.editArea} value={editText} onChange={e => setEditText(e.target.value)} rows={8} /> : <div style={S.chunkBody}>{chunk.text}</div>}
          </div>
        ))}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 16, fontSize: 12, color: "#A0522D" }}><Icon type="edit" size={13} /> 点击段落右侧编辑按钮可直接修改文本</div>
    </div>
  );
}

function GraphTab({ book, data, processGraph, processing, hasCorpus }) {
  if (!data) return (<div style={S.emptyState}><div style={{ color: "#A09889" }}>{hasCorpus ? "尚未生成图谱数据" : "请先生成语料库"}</div>{hasCorpus && <button style={{ ...S.primaryBtn, marginTop: 12 }} onClick={() => processGraph(book)} disabled={!!processing}>生成图谱数据</button>}</div>);
  return (
    <div style={{ padding: "24px 28px" }}>
      <h2 style={{ fontSize: 19, fontWeight: 700, color: "#2D2A26", margin: 0 }}>{book.name}</h2>
      <div style={{ fontSize: 12, color: "#A09889", marginTop: 6 }}>实体 {data.entities?.length || 0} · 关系 {data.relations?.length || 0}</div>
      <div style={{ fontSize: 13, fontWeight: 700, color: "#2D2A26", margin: "24px 0 12px" }}>实体</div>
      <div style={S.entityGrid}>
        {(data.entities || []).map((e, i) => (
          <div key={i} className="entity-card" style={S.entityCard}>
            <span style={{ ...S.entityBadge, background: entColor(e.type) }}>{e.type}</span>
            <div style={{ fontWeight: 600, fontSize: 13, marginTop: 8, color: "#2D2A26" }}>{e.name}</div>
            <div style={{ fontSize: 11, color: "#A09889", marginTop: 4, lineHeight: 1.5 }}>{e.definition}</div>
          </div>
        ))}
      </div>
      {data.relations && data.relations.length > 0 && (<>
        <div style={{ fontSize: 13, fontWeight: 700, color: "#2D2A26", margin: "28px 0 12px" }}>关系</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
          {data.relations.map((r, i) => {
            const src = (data.entities || []).find(e => e.id === r.source);
            const tgt = (data.entities || []).find(e => e.id === r.target);
            return (<div key={i} style={S.relRow}><span style={{ fontWeight: 600, color: "#2D2A26" }}>{src?.name || r.source}</span><span style={{ color: "#A0522D", fontSize: 11, padding: "2px 8px", background: "#A0522D12", borderRadius: 4 }}>{r.relation}</span><span style={{ fontWeight: 600, color: "#2D2A26" }}>{tgt?.name || r.target}</span></div>);
          })}
        </div>
      </>)}
    </div>
  );
}

function entColor(t) { return { concept: "#A0522D18", task: "#6A8EAE20", algorithm: "#7EC49D20", process: "#D4A54120", chapter: "#8B728020" }[t] || "#F0EBE5"; }

function KnowledgeGraphPage({ graph }) {
  if (!graph) return (<div style={{ ...S.emptyState, height: "100%" }}>
    <div style={{ width: 72, height: 72, borderRadius: 24, background: "#F5F0EB", display: "flex", alignItems: "center", justifyContent: "center" }}><Icon type="graph" size={32} /></div>
    <h2 style={{ marginTop: 20, fontSize: 20, fontWeight: 700, color: "#2D2A26" }}>知识图谱</h2>
    <p style={{ color: "#A09889", fontSize: 13, maxWidth: 320, textAlign: "center", lineHeight: 1.7, marginTop: 8 }}>在「数据库」中生成图谱数据后，选择书籍生成全知识图谱</p>
  </div>);
  return (
    <div style={{ padding: 36 }}>
      <h2 style={{ fontSize: 24, fontWeight: 700, color: "#2D2A26" }}>全知识图谱</h2>
      <p style={{ color: "#A09889", fontSize: 13, marginTop: 4, marginBottom: 28 }}>合并 {graph.book_count} 本书 · {graph.entities?.length || 0} 实体 · {graph.relations?.length || 0} 关系</p>
      <div style={{ ...S.entityGrid, gridTemplateColumns: "repeat(auto-fill,minmax(170px,1fr))" }}>
        {(graph.entities || []).map((e, i) => (
          <div key={i} className="entity-card" style={S.entityCard}>
            <span style={{ ...S.entityBadge, background: entColor(e.type) }}>{e.type}</span>
            <div style={{ fontWeight: 600, fontSize: 13, marginTop: 8, color: "#2D2A26" }}>{e.name}</div>
            <div style={{ fontSize: 11, color: "#A09889", marginTop: 4, lineHeight: 1.5 }}>{e.definition}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── CSS ─────────────────────────────────────────────────────
const globalCSS = `
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap');
  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes fadeUp { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
  @keyframes slideDown { from { opacity:0; transform:translateY(-16px); } to { opacity:1; transform:translateY(0); } }
  @keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
  * { box-sizing:border-box; margin:0; padding:0; }
  html, body, #root { height: 100%; overflow: hidden; }
  ::-webkit-scrollbar { width: 5px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #DDD6CD; border-radius: 10px; }
  textarea:focus, button:focus, input:focus { outline: none; }
  button { font-family: inherit; }
  .sidebar-btn:hover { background: rgba(255,255,255,0.05) !important; }
  .book-item:hover { background: #FAF7F4 !important; }
  .book-item:hover .del-btn { opacity: 1 !important; }
  .tab-btn:hover { color: #2D2A26 !important; }
  .chunk-card:hover { border-color: #DDD6CD !important; }
  .chunk-card:hover .edit-btn { opacity: 1 !important; }
  .entity-card:hover { border-color: #C4B9AB !important; transform: translateY(-1px); }
`;

// ─── Styles ──────────────────────────────────────────────────
const S = {
  root: { display: "flex", height: "100vh", width: "100%", fontFamily: "'Noto Sans SC',-apple-system,sans-serif", background: "#FAF7F4", color: "#2D2A26", fontSize: 13, overflow: "hidden" },
  sidebar: { width: 68, background: "#2D2A26", display: "flex", flexDirection: "column", alignItems: "center", paddingTop: 12, flexShrink: 0 },
  sidebarBrand: { display: "flex", flexDirection: "column", alignItems: "center", marginBottom: 28, paddingTop: 4 },
  brandIcon: { width: 32, height: 32, borderRadius: 10, background: "#A0522D", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15, fontWeight: 700, fontFamily: "'Source Serif 4',serif" },
  brandLabel: { fontSize: 9, color: "#8B8078", marginTop: 6, letterSpacing: 1 },
  nav: { display: "flex", flexDirection: "column", gap: 2, width: "100%" },
  sidebarItem: { display: "flex", flexDirection: "column", alignItems: "center", gap: 4, padding: "10px 0", background: "transparent", border: "none", borderLeft: "2.5px solid transparent", color: "#8B8078", fontSize: 10, cursor: "pointer", transition: "all 0.2s", width: "100%" },
  sidebarItemActive: { color: "#E8E0D8", background: "rgba(255,255,255,0.04)", borderLeftColor: "#E8E0D8" },
  keyInput: { width: "100%", padding: "5px 6px", fontSize: 9, background: "#3A3632", border: "1px solid #4A4640", color: "#C4B9AB", borderRadius: 5, fontFamily: "monospace" },
  main: { flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" },
  dbPage: { display: "flex", flexDirection: "column", height: "100%" },
  dbContent: { display: "flex", flex: 1, overflow: "hidden" },
  leftPanel: { width: 264, background: "#FFFFFF", borderRight: "1px solid #EDE8E2", display: "flex", flexDirection: "column", flexShrink: 0, overflow: "hidden" },
  leftHeader: { display: "flex", alignItems: "center", gap: 8, padding: "18px 20px 14px", color: "#2D2A26" },
  uploadZone: { margin: "0 14px", padding: "18px 16px", borderRadius: 10, border: "1.5px dashed #DDD6CD", display: "flex", flexDirection: "column", alignItems: "center", cursor: "pointer", transition: "all 0.2s", background: "#FDFCFA", flexShrink: 0 },
  uploadIcon: { width: 40, height: 40, borderRadius: 12, background: "#F5F0EB", display: "flex", alignItems: "center", justifyContent: "center", color: "#A0522D" },
  bookListLabel: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "14px 20px 8px", fontSize: 11, fontWeight: 600, color: "#A09889", textTransform: "uppercase", letterSpacing: 1 },
  bookCount: { fontSize: 10, background: "#F5F0EB", color: "#A09889", borderRadius: 6, padding: "1px 7px", fontWeight: 500 },
  bookList: { flex: 1, overflowY: "auto", padding: "2px 8px 8px" },
  bookItem: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "9px 12px", cursor: "pointer", transition: "all 0.15s", borderRadius: 8, borderLeft: "2.5px solid transparent", marginBottom: 2, position: "relative" },
  bookItemActive: { background: "#F5F0EB", borderLeftColor: "#A0522D" },
  bookItemInner: { display: "flex", alignItems: "center", gap: 8, flex: 1, minWidth: 0 },
  bookIcon: { width: 28, height: 28, borderRadius: 7, background: "#F5F0EB", display: "flex", alignItems: "center", justifyContent: "center", color: "#A09889", flexShrink: 0 },
  bookTitle: { fontSize: 13, fontWeight: 500, color: "#2D2A26", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },
  bookMeta: { fontSize: 10, color: "#C4B9AB", marginTop: 1 },
  dot: { width: 7, height: 7, borderRadius: "50%", background: "#7EC49D" },
  delBtn: { position: "absolute", right: 8, top: "50%", transform: "translateY(-50%)", background: "transparent", border: "none", color: "#C4B9AB", cursor: "pointer", padding: 4, borderRadius: 4, opacity: 0, transition: "opacity 0.15s" },
  rightPanel: { flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", background: "#FAF7F4" },
  rightTopBar: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 28px", height: 50, borderBottom: "1px solid #EDE8E2", background: "#FFFFFF", flexShrink: 0, gap: 12 },
  tabRow: { display: "flex", gap: 0, height: "100%" },
  tab: { padding: "0 18px", background: "transparent", border: "none", borderBottom: "2px solid transparent", fontSize: 13, fontWeight: 500, color: "#A09889", cursor: "pointer", transition: "all 0.15s", whiteSpace: "nowrap", height: "100%", display: "flex", alignItems: "center" },
  tabActive: { color: "#A0522D", borderBottomColor: "#A0522D", fontWeight: 600 },
  tabActions: { display: "flex", alignItems: "center", flexShrink: 0 },
  rightContent: { flex: 1, overflow: "auto" },
  primaryBtn: { padding: "8px 20px", background: "#A0522D", color: "#fff", border: "none", borderRadius: 7, fontSize: 13, fontWeight: 600, cursor: "pointer", transition: "all 0.15s", whiteSpace: "nowrap" },
  ghostBtn: { padding: "8px 14px", background: "#FFFFFF", color: "#2D2A26", border: "1px solid #DDD6CD", borderRadius: 7, fontSize: 12, fontWeight: 500, cursor: "pointer", display: "flex", alignItems: "center", gap: 5 },
  emptyState: { display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", color: "#C4B9AB" },
  infoTag: { padding: "4px 12px", background: "#F5F0EB", borderRadius: 5, fontSize: 12, color: "#8B7355", fontWeight: 500 },
  card: { background: "#FFFFFF", borderRadius: 12, padding: 28, border: "1px solid #EDE8E2", marginTop: 24, boxShadow: "0 1px 3px rgba(45,42,38,0.04)" },
  statCard: { background: "#FFFFFF", borderRadius: 10, padding: "16px 20px", border: "1px solid #EDE8E2", textAlign: "center" },
  statLabel: { fontSize: 11, color: "#A09889", fontWeight: 500, textTransform: "uppercase", letterSpacing: 0.8 },
  statValue: { fontSize: 20, fontWeight: 700, color: "#2D2A26", marginTop: 6, fontFamily: "'Source Serif 4',serif" },
  previewBox: { fontSize: 13, lineHeight: 2, color: "#5A5450", whiteSpace: "pre-wrap", maxHeight: 420, overflowY: "auto", padding: "16px 20px", background: "#FDFCFA", borderRadius: 8, border: "1px solid #F5F0EB", fontFamily: "'Noto Sans SC', sans-serif" },
  chunkCard: { background: "#FFFFFF", borderRadius: 10, border: "1px solid #EDE8E2", overflow: "hidden", animation: "fadeUp 0.3s ease", transition: "border-color 0.15s" },
  chunkHead: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 16px", borderBottom: "1px solid #F5F0EB", gap: 8 },
  levelTag: { padding: "2px 8px", background: "#A0522D12", color: "#A0522D", borderRadius: 4, fontSize: 10, fontWeight: 600, flexShrink: 0, textTransform: "uppercase", letterSpacing: 0.5 },
  chunkBody: { padding: "12px 16px", fontSize: 13, lineHeight: 1.8, color: "#5A5450", maxHeight: 140, overflow: "auto", whiteSpace: "pre-wrap" },
  editArea: { width: "100%", border: "none", padding: "14px 16px", fontSize: 13, lineHeight: 1.8, resize: "vertical", fontFamily: "inherit", color: "#2D2A26", background: "#FFFBF5" },
  tinyBtn: { display: "flex", alignItems: "center", gap: 4, padding: "4px 10px", background: "#A0522D", color: "#fff", border: "none", borderRadius: 5, fontSize: 11, cursor: "pointer", fontWeight: 600 },
  tinyBtnGhost: { display: "flex", alignItems: "center", padding: "4px 8px", background: "transparent", color: "#C4B9AB", border: "1px solid #EDE8E2", borderRadius: 5, fontSize: 11, cursor: "pointer", opacity: 0, transition: "opacity 0.15s" },
  entityGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(190px,1fr))", gap: 8 },
  entityCard: { background: "#FFFFFF", border: "1px solid #EDE8E2", borderRadius: 10, padding: 14, animation: "fadeUp 0.3s ease", transition: "all 0.2s", cursor: "default" },
  entityBadge: { display: "inline-block", padding: "2px 8px", borderRadius: 4, fontSize: 10, fontWeight: 600, color: "#8B7355", letterSpacing: 0.3, textTransform: "uppercase" },
  relRow: { display: "flex", alignItems: "center", gap: 10, padding: "8px 12px", background: "#FFFFFF", borderRadius: 8, border: "1px solid #F5F0EB", fontSize: 13 },
  overlay: { position: "fixed", inset: 0, background: "rgba(45,42,38,0.35)", backdropFilter: "blur(8px)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 },
  overlayCard: { background: "#FFFFFF", borderRadius: 20, padding: "44px 60px", display: "flex", flexDirection: "column", alignItems: "center", boxShadow: "0 24px 80px rgba(45,42,38,0.12)", minWidth: 300 },
  overlayBar: { width: 200, height: 3, background: "#F5F0EB", borderRadius: 2, overflow: "hidden", marginTop: 20 },
  overlayBarFill: { width: "40%", height: "100%", borderRadius: 2, background: "linear-gradient(90deg, #A0522D, #D4A541, #A0522D)", backgroundSize: "200% 100%", animation: "shimmer 1.5s ease infinite" },
  toast: { position: "fixed", top: 24, right: 24, background: "#FFFFFF", color: "#A0522D", padding: "12px 20px", borderRadius: 10, fontSize: 13, fontWeight: 500, display: "flex", alignItems: "center", gap: 8, boxShadow: "0 8px 32px rgba(45,42,38,0.12)", border: "1px solid #EDE8E2", animation: "slideDown 0.3s ease", zIndex: 1001 },
};